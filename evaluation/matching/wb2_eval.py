"""Workbook 2 baseline experiments: matching baselines on Djinni and the extraction baseline on SkillSpan.

Everything here is plain Python + numpy so it can be unit-tested without models or network.
Model loading lives in the notebook cells.
"""
from __future__ import annotations

import hashlib
import json
import math
import platform
import random
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

# --------------------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------------------

DJINNI_JOBS = "lang-uk/recruitment-dataset-job-descriptions-english"
DJINNI_CVS = "lang-uk/recruitment-dataset-candidate-profiles-english"
SKILLSPAN_TEST_URL = "https://raw.githubusercontent.com/kris927b/SkillSpan/main/data/json/test.json"
JOBBERT_SKILL = "jjzha/jobbert_skill_extraction"
JOBBERT_KNOWLEDGE = "jjzha/jobbert_knowledge_extraction"
MINILM = "sentence-transformers/all-MiniLM-L6-v2"


@dataclass
class Config:
    seed: int = 295
    n_job_queries: int = 300          # job -> candidates direction
    n_cv_pool: int = 5000
    n_cv_queries: int = 300           # candidate -> jobs direction
    n_job_pool: int = 3000
    dev_fraction: float = 0.2         # share of queries used only for tuning (split by query)
    min_category_size: int = 200      # categories smaller than this in either corpus are dropped
    max_chars: int = 4000             # documents are cut to this many characters
    max_cyrillic_ratio: float = 0.15  # documents above this share of Cyrillic letters are dropped
    bootstrap_samples: int = 1000
    ks: tuple = (10, 50, 100)
    bm25_k1_grid: tuple = (0.9, 1.2, 1.5, 2.0, 2.5, 3.0, 4.0)
    bm25_b_grid: tuple = (0.4, 0.6, 0.75, 0.9, 1.0)
    tune_metric: str = "ndcg@10"
    explain_top_k: int = 10           # explain each matcher's top-10 results per test query
    explain_terms: int = 5            # an explanation names at most this many matched terms


# --------------------------------------------------------------------------------------
# Text cleaning and parsing
# --------------------------------------------------------------------------------------

_CYR = re.compile(r"[Ѐ-ӿ]")
_LETTER = re.compile(r"[^\W\d_]")
_TOKEN = re.compile(r"[a-z0-9][a-z0-9+#.]*")
STOPWORDS = frozenset(
    """a an and are as at be been but by can could do does for from had has have he her his i if in
    into is it its may me more most my no not of on or our out over she should so such than that the
    their them then there these they this those to under up us was we were what when where which who
    will with would you your""".split()
)


def cyrillic_ratio(text: str) -> float:
    n_letters = len(_LETTER.findall(text or ""))
    return len(_CYR.findall(text or "")) / n_letters if n_letters else 0.0


def clean_text(text: str, max_chars: int) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    return text[:max_chars]


def tokenize(text: str) -> list[str]:
    toks = [t.rstrip(".") for t in _TOKEN.findall((text or "").lower())]
    return [t for t in toks if t and t not in STOPWORDS]


def parse_years(value) -> float | None:
    """Djinni experience fields: numbers ('2', 2.0) or strings like '3y', 'no_exp'."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return None if (isinstance(value, float) and math.isnan(value)) else float(value)
    s = str(value).strip().lower()
    if not s:
        return None
    if "no" in s and "exp" in s:
        return 0.0
    m = re.search(r"\d+(?:\.\d+)?", s)
    return float(m.group()) if m else None


# --------------------------------------------------------------------------------------
# Data preparation
# --------------------------------------------------------------------------------------

@dataclass
class Doc:
    id: str
    text: str
    category: str
    years: float | None


def prepare_docs(rows, text_fields, category_field, years_field, lang_field, cfg: Config):
    """rows: iterable of dicts. Keeps English, non-empty, mostly non-Cyrillic documents."""
    docs, dropped = [], {"lang": 0, "empty": 0, "cyrillic": 0, "no_category": 0}
    for r in rows:
        lang = (r.get(lang_field) or "").lower() if lang_field else "en"
        if lang_field and lang not in ("en", "eng", "english"):
            dropped["lang"] += 1
            continue
        text = clean_text(" ".join(str(r.get(f) or "") for f in text_fields), cfg.max_chars)
        if len(text) < 50:
            dropped["empty"] += 1
            continue
        if cyrillic_ratio(text) > cfg.max_cyrillic_ratio:
            dropped["cyrillic"] += 1
            continue
        cat = (r.get(category_field) or "").strip()
        if not cat:
            dropped["no_category"] += 1
            continue
        docs.append(Doc(str(r.get("id")), text, cat, parse_years(r.get(years_field))))
    return docs, dropped


def shared_categories(jobs: list[Doc], cvs: list[Doc], min_size: int) -> list[str]:
    from collections import Counter

    cj, cc = Counter(d.category for d in jobs), Counter(d.category for d in cvs)
    return sorted(c for c in cj if cj[c] >= min_size and cc.get(c, 0) >= min_size)


def stratified_sample(docs: list[Doc], n: int, rng: random.Random) -> list[Doc]:
    """Sample n docs keeping each category's share of the input (largest-remainder rounding)."""
    from collections import defaultdict

    by = defaultdict(list)
    for d in docs:
        by[d.category].append(d)
    total = len(docs)
    quotas = {c: n * len(v) / total for c, v in by.items()}
    alloc = {c: int(q) for c, q in quotas.items()}
    for c in sorted(quotas, key=lambda c: quotas[c] - alloc[c], reverse=True)[: n - sum(alloc.values())]:
        alloc[c] += 1
    out = []
    for c in sorted(by):
        out.extend(rng.sample(by[c], min(alloc[c], len(by[c]))))
    rng.shuffle(out)
    return out


def relevance(query: Doc, cand: Doc, direction: str) -> int:
    """Proxy graded relevance. 0: other category. 1: same category. 2: same category and the
    candidate's experience meets the job's requirement (both known).
    direction 'job2cv': query is a job; 'cv2job': query is a candidate."""
    if query.category != cand.category:
        return 0
    job, cv = (query, cand) if direction == "job2cv" else (cand, query)
    if job.years is not None and cv.years is not None and cv.years >= job.years:
        return 2
    return 1


def relevance_matrix(queries: list[Doc], pool: list[Doc], direction: str) -> np.ndarray:
    return np.array([[relevance(q, p, direction) for p in pool] for q in queries], dtype=np.int8)


def split_queries(n: int, dev_fraction: float, rng: random.Random):
    idx = list(range(n))
    rng.shuffle(idx)
    k = int(round(n * dev_fraction))
    return sorted(idx[:k]), sorted(idx[k:])


# --------------------------------------------------------------------------------------
# Rankers (score matrices of shape [n_queries, n_pool])
# --------------------------------------------------------------------------------------

def random_scores(nq: int, npool: int, seed: int) -> np.ndarray:
    return np.random.default_rng(seed).random((nq, npool))


class BM25Index:
    """Vectorised BM25 with exactly the scoring of rank_bm25.BM25Okapi (same idf, the same
    epsilon floor for negative idf, query terms counted with repetition), so results match the
    reference library (checked in the tests) but tuning a grid takes seconds instead of minutes.
    Also gives per-term contributions, which the explanation baseline needs."""

    def __init__(self, pool_texts, epsilon: float = 0.25):
        from collections import Counter

        from scipy.sparse import csr_matrix

        self.docs = [tokenize(t) or ["<empty>"] for t in pool_texts]
        self.vocab: dict[str, int] = {}
        rows, cols, vals = [], [], []
        for i, toks in enumerate(self.docs):
            for term, c in Counter(toks).items():
                j = self.vocab.setdefault(term, len(self.vocab))
                rows.append(i); cols.append(j); vals.append(c)
        n = len(self.docs)
        self.tf = csr_matrix((np.array(vals, float), (rows, cols)), shape=(n, len(self.vocab)))
        self.dl = np.array([len(d) for d in self.docs], float)
        self.avgdl = self.dl.sum() / n
        df = np.bincount(self.tf.indices, minlength=len(self.vocab)).astype(float)
        idf = np.log(n - df + 0.5) - np.log(df + 0.5)
        idf[idf < 0] = epsilon * idf.mean()
        self.idf = idf
        self.terms = np.array(list(self.vocab), dtype=object)

    def _weights(self, k1: float, b: float):
        tf = self.tf.tocoo()
        norm = k1 * (1 - b + b * self.dl[tf.row] / self.avgdl)
        data = self.idf[tf.col] * tf.data * (k1 + 1) / (tf.data + norm)
        from scipy.sparse import csr_matrix

        return csr_matrix((data, (tf.row, tf.col)), shape=self.tf.shape)

    def query_vector(self, text: str):
        from collections import Counter

        from scipy.sparse import csr_matrix

        c = Counter(t for t in tokenize(text) if t in self.vocab)
        cols = [self.vocab[t] for t in c]
        return csr_matrix((np.array(list(c.values()), float), ([0] * len(cols), cols)), shape=(1, len(self.vocab)))

    def scores(self, query_texts, k1: float, b: float) -> np.ndarray:
        from scipy.sparse import vstack

        Q = vstack([self.query_vector(q) for q in query_texts]).tocsr()
        return (Q @ self._weights(k1, b).T).toarray()

    def contributions(self, query_text: str, doc: int, k1: float, b: float, removed=()) -> dict:
        """Per-term BM25 contribution of each matched query term to one document's score.
        `removed` drops terms from this document only (their counts also leave its length);
        idf and average length stay those of the pool."""
        from collections import Counter

        q = Counter(t for t in tokenize(query_text) if t in self.vocab)
        d = Counter(self.docs[doc])
        gone = set(removed)
        dl = self.dl[doc] - sum(d[t] for t in gone)
        norm = k1 * (1 - b + b * dl / self.avgdl)
        out = {}
        for term, qc in q.items():
            f = d.get(term, 0)
            if f and term not in gone:
                out[term] = qc * self.idf[self.vocab[term]] * f * (k1 + 1) / (f + norm)
        return out


def bm25_scores(query_texts, pool_texts, k1: float, b: float, index: BM25Index | None = None) -> np.ndarray:
    return (index or BM25Index(pool_texts)).scores(query_texts, k1, b)


def bm25_scores_reference(query_texts, pool_texts, k1: float, b: float) -> np.ndarray:
    """The rank_bm25 library itself, kept to check BM25Index against."""
    from rank_bm25 import BM25Okapi

    bm = BM25Okapi([tokenize(t) or ["<empty>"] for t in pool_texts], k1=k1, b=b)
    return np.vstack([bm.get_scores(tokenize(q)) for q in query_texts])


def tfidf_scores(query_texts, pool_texts) -> np.ndarray:
    from sklearn.feature_extraction.text import TfidfVectorizer

    vec = TfidfVectorizer(tokenizer=tokenize, lowercase=False, token_pattern=None,
                          sublinear_tf=True, ngram_range=(1, 2), min_df=2)
    P = vec.fit_transform(pool_texts)
    Q = vec.transform(query_texts)
    return (Q @ P.T).toarray()


def dense_scores(query_emb: np.ndarray, pool_emb: np.ndarray) -> np.ndarray:
    q = query_emb / np.linalg.norm(query_emb, axis=1, keepdims=True).clip(1e-12)
    p = pool_emb / np.linalg.norm(pool_emb, axis=1, keepdims=True).clip(1e-12)
    return q @ p.T


# --------------------------------------------------------------------------------------
# Ranking metrics (per query)
# --------------------------------------------------------------------------------------

def per_query_metrics(scores: np.ndarray, rel: np.ndarray, ks=(10, 50, 100)) -> dict[str, np.ndarray]:
    """Ties are broken by pool index (stable sort), so results are deterministic.
    nDCG uses gain 2^rel - 1 and the ideal ranking over the whole pool.
    Recall, precision, MRR and AP treat rel >= 1 as relevant. Queries with no relevant
    document in the pool get NaN and are excluded from means."""
    order = np.argsort(-scores, axis=1, kind="stable")
    ranked = np.take_along_axis(rel, order, axis=1).astype(float)
    binary = (ranked >= 1).astype(float)
    n_rel = (rel >= 1).sum(axis=1).astype(float)
    has = n_rel > 0
    out = {}
    disc = 1.0 / np.log2(np.arange(2, rel.shape[1] + 2))
    ideal = -np.sort(-rel.astype(float), axis=1)
    for k in ks:
        k = min(k, rel.shape[1])
        dcg = ((2 ** ranked[:, :k] - 1) * disc[:k]).sum(axis=1)
        idcg = ((2 ** ideal[:, :k] - 1) * disc[:k]).sum(axis=1)
        out[f"ndcg@{k}"] = np.where(idcg > 0, dcg / np.where(idcg > 0, idcg, 1), np.nan)
        out[f"recall@{k}"] = np.where(has, binary[:, :k].sum(axis=1) / np.where(has, n_rel, 1), np.nan)
    k10 = min(10, rel.shape[1])
    out["p@10"] = np.where(has, binary[:, :k10].mean(axis=1), np.nan)
    first = np.where(binary.any(axis=1), binary.argmax(axis=1) + 1, 0)
    out["mrr"] = np.where(has, np.where(first > 0, 1.0 / np.maximum(first, 1), 0.0), np.nan)
    cum = np.cumsum(binary, axis=1)
    prec_at_hit = cum / np.arange(1, rel.shape[1] + 1)
    out["map"] = np.where(has, (prec_at_hit * binary).sum(axis=1) / np.where(has, n_rel, 1), np.nan)
    return out


# --------------------------------------------------------------------------------------
# Statistics
# --------------------------------------------------------------------------------------

def bootstrap_ci(values: np.ndarray, n: int, seed: int, alpha: float = 0.05):
    v = values[~np.isnan(values)]
    if len(v) == 0:
        return float("nan"), float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    means = v[rng.integers(0, len(v), size=(n, len(v)))].mean(axis=1)
    return float(v.mean()), float(np.quantile(means, alpha / 2)), float(np.quantile(means, 1 - alpha / 2))


def paired_bootstrap(a: np.ndarray, b: np.ndarray, n: int, seed: int, alpha: float = 0.05):
    """Mean difference a - b over queries where both are defined, its 95% CI, and a two-sided
    bootstrap p-value (share of resampled differences on the other side of zero, doubled)."""
    mask = ~(np.isnan(a) | np.isnan(b))
    d = a[mask] - b[mask]
    if len(d) == 0:
        return {"diff": float("nan"), "lo": float("nan"), "hi": float("nan"), "p": float("nan"), "n": 0}
    rng = np.random.default_rng(seed)
    means = d[rng.integers(0, len(d), size=(n, len(d)))].mean(axis=1)
    p = 2 * min((means <= 0).mean(), (means >= 0).mean())
    return {"diff": float(d.mean()), "lo": float(np.quantile(means, alpha / 2)),
            "hi": float(np.quantile(means, 1 - alpha / 2)), "p": float(min(1.0, p)), "n": int(len(d))}


# --------------------------------------------------------------------------------------
# BM25 tuning on dev queries only
# --------------------------------------------------------------------------------------

def tune_bm25(query_texts, pool_texts, rel, dev_idx, cfg: Config, index: BM25Index | None = None):
    grid = []
    dq = [query_texts[i] for i in dev_idx]
    index = index or BM25Index(pool_texts)
    for k1 in cfg.bm25_k1_grid:
        for b in cfg.bm25_b_grid:
            s = index.scores(dq, k1, b)
            m = per_query_metrics(s, rel[dev_idx], cfg.ks)[cfg.tune_metric]
            grid.append({"k1": k1, "b": b, cfg.tune_metric: float(np.nanmean(m))})
    best = max(grid, key=lambda g: g[cfg.tune_metric])
    best["at_grid_edge"] = best["k1"] in (min(cfg.bm25_k1_grid), max(cfg.bm25_k1_grid)) or \
        best["b"] in (min(cfg.bm25_b_grid), max(cfg.bm25_b_grid))
    return best, grid


# --------------------------------------------------------------------------------------
# Extraction: BIO spans and span F1 (SkillSpan)
# --------------------------------------------------------------------------------------

def bio_spans(tags: list[str]) -> set[tuple[int, int]]:
    """Spans as (start, end_exclusive). Accepts 'B', 'I', 'O' with or without a type suffix
    ('B-Skill'). An 'I' without a preceding span starts a new span (conlleval convention)."""
    spans, start = set(), None
    for i, t in enumerate(list(tags) + ["O"]):
        p = (t or "O")[0].upper()
        if p == "B" or (p == "I" and start is None):
            if start is not None:
                spans.add((start, i))
            start = i
        elif p == "O":
            if start is not None:
                spans.add((start, i))
            start = None
    return spans


def span_prf(gold: list[set], pred: list[set], loose: bool = False):
    """Strict: exact boundaries. Loose: a predicted span counts as correct if it overlaps a gold
    span, and a gold span counts as found if any prediction overlaps it."""
    tp_p = tp_g = n_p = n_g = 0
    for g, p in zip(gold, pred):
        n_p += len(p)
        n_g += len(g)
        if loose:
            tp_p += sum(1 for a in p if any(a[0] < b[1] and b[0] < a[1] for b in g))
            tp_g += sum(1 for b in g if any(a[0] < b[1] and b[0] < a[1] for a in p))
        else:
            tp_p += len(g & p)
            tp_g += len(g & p)
    prec = tp_p / n_p if n_p else 0.0
    rec = tp_g / n_g if n_g else 0.0
    f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
    return {"precision": prec, "recall": rec, "f1": f1, "n_gold": n_g, "n_pred": n_p}


def word_tags_from_subwords(word_ids: list, label_ids: list, id2label: dict) -> list[str]:
    """First-subword labelling: each word takes the label predicted for its first sub-token."""
    out, seen = {}, set()
    for wid, lid in zip(word_ids, label_ids):
        if wid is None or wid in seen:
            continue
        seen.add(wid)
        out[wid] = id2label[int(lid)]
    n = (max(out) + 1) if out else 0
    return [out.get(i, "O") for i in range(n)]


# --------------------------------------------------------------------------------------
# Explanation baseline: matched-term explanations and a deletion test of their faithfulness
# --------------------------------------------------------------------------------------

def remove_terms(text: str, terms) -> str:
    """Delete every occurrence of each term (as the tokenizer sees it) from raw text."""
    for t in sorted(set(terms), key=len, reverse=True):
        text = re.sub(r"(?<![A-Za-z0-9+#])" + re.escape(t) + r"(?![A-Za-z0-9+#])", " ", text, flags=re.IGNORECASE)
    return text


def explain_matches(index: BM25Index, query_texts, pool_texts, test_idx, score_matrix, k1, b,
                    top_k: int, n_terms: int, seed: int):
    """For each test query's top_k results under `score_matrix` (any matcher), build the
    matched-term explanation: the query terms the document also contains, ranked by their
    tuned-BM25 contribution, keeping at most n_terms. A random control removes the same number of
    other terms of the same document. Returns one record per explained match."""
    rng = random.Random(seed)
    recs = []
    for row, qi in enumerate(test_idx):
        q = query_texts[qi]
        order = np.argsort(-score_matrix[row], kind="stable")[:top_k]
        for rank, d in enumerate(order, 1):
            contrib = index.contributions(q, int(d), k1, b)
            ranked = sorted(contrib.items(), key=lambda kv: -kv[1])
            terms = [t for t, _ in ranked[:n_terms]]
            total = sum(contrib.values())
            others = sorted(set(index.docs[int(d)]) - set(contrib) - {"<empty>"})
            rand = rng.sample(others, len(terms)) if len(others) >= len(terms) else []
            recs.append({"row": row, "query": int(qi), "doc": int(d), "rank": rank, "terms": terms,
                         "n_matched_terms": len(contrib),
                         "share_of_bm25_score": (sum(c for _, c in ranked[:n_terms]) / total) if total > 0 else float("nan"),
                         "random_terms": rand})
    return recs


def deletion_effect(full: float, after: float, row_scores: np.ndarray, doc: int, top_k: int):
    """Relative score drop and whether the document leaves the top_k once its own score changes."""
    others = np.delete(row_scores, doc)
    new_rank = 1 + int((others > after).sum())
    rel = (full - after) / full if full > 0 else float("nan")
    return rel, new_rank > top_k


def summarise_explanations(recs, cfg: Config):
    """Per query means, then paired bootstrap of (explanation deletion - random deletion)."""
    import collections

    by = collections.defaultdict(list)
    for r in recs:
        by[r["row"]].append(r)
    def qmean(key):
        return np.array([np.nanmean([r[key] for r in rs]) if rs else np.nan for rs in by.values()], float)
    out = {"matches_explained": len(recs),
           "coverage": float(np.mean([r["n_matched_terms"] > 0 for r in recs])),
           "mean_matched_terms": float(np.mean([r["n_matched_terms"] for r in recs])),
           "share_of_bm25_score_in_explanation": float(np.nanmean([r["share_of_bm25_score"] for r in recs]))}
    e, z = qmean("drop_explained"), qmean("drop_random")
    out["score_drop_explained"] = bootstrap_ci(e, cfg.bootstrap_samples, cfg.seed)
    out["score_drop_random"] = bootstrap_ci(z, cfg.bootstrap_samples, cfg.seed)
    out["drop_difference"] = paired_bootstrap(e, z, cfg.bootstrap_samples, cfg.seed)
    out["left_top_k_explained"] = float(np.mean([r["left_explained"] for r in recs]))
    out["left_top_k_random"] = float(np.mean([r["left_random"] for r in recs if r["random_terms"]]))
    return out


# --------------------------------------------------------------------------------------
# Labeling sample for the human-labelled set (Workbook 1, Section 3.1)
# --------------------------------------------------------------------------------------

def labeling_sample(jobs: list[Doc], cvs: list[Doc], n_pairs: int, rng: random.Random,
                    same_category_share: float = 0.5):
    """Half the pairs within a category (where qualified pairs are likely), half across."""
    from collections import defaultdict

    cv_by = defaultdict(list)
    for c in cvs:
        cv_by[c.category].append(c)
    rows, n_same = [], int(n_pairs * same_category_share)
    for i in range(n_pairs):
        j = rng.choice(jobs)
        if i < n_same and cv_by.get(j.category):
            c = rng.choice(cv_by[j.category])
        else:
            others = [k for k in cv_by if k != j.category]
            c = rng.choice(cv_by[rng.choice(others)]) if others else rng.choice(cvs)
        rows.append({"pair_id": f"P{i+1:04d}", "job_id": j.id, "job_category": j.category,
                     "cv_id": c.id, "cv_category": c.category, "job_text": j.text, "cv_text": c.text,
                     "label_invite_first_interview (0/1)": "", "labeler": "", "notes": ""})
    rng.shuffle(rows)
    return rows


# --------------------------------------------------------------------------------------
# Run manifest (Workbook 1, requirement N1)
# --------------------------------------------------------------------------------------

def sha256_of(items) -> str:
    h = hashlib.sha256()
    for it in items:
        h.update(str(it).encode())
        h.update(b"\x00")
    return h.hexdigest()


def manifest(cfg: Config, extra: dict) -> dict:
    import importlib.metadata as md

    vers = {}
    for p in ("numpy", "scikit-learn", "rank-bm25", "sentence-transformers", "transformers",
              "torch", "datasets"):
        try:
            vers[p] = md.version(p)
        except md.PackageNotFoundError:
            vers[p] = None
    return {"created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "python": sys.version.split()[0], "platform": platform.platform(),
            "packages": vers, "config": cfg.__dict__, **extra}


def save_json(obj, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, default=lambda o: list(o) if isinstance(o, (set, tuple)) else str(o)))
