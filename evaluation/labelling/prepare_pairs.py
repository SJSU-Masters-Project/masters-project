"""Step 1: build the job-candidate pairs the LLM panel will label.

Test set (pooled, for ranking metrics): N test jobs; for each, the top candidates from BM25 and from
MiniLM, plus random same-category and other-category candidates, so every method's top results are
judged. Train/valid sets (for ConFit v2): other jobs, each with BM25's top candidates (likely
positives and hard negatives) plus random ones. Jobs never cross splits (Workbook 1, Section 3.1).

    python prepare_pairs.py --out pairs            # downloads Djinni from Hugging Face
    python prepare_pairs.py --out pairs --no-dense # skip MiniLM (no sentence-transformers)
"""
from __future__ import annotations

import argparse
import json
import random
import time
from collections import defaultdict
from pathlib import Path

import numpy as np

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "matching"))
import wb2_eval as W


def load_djinni(cfg):
    from datasets import load_dataset

    jobs_raw = load_dataset(W.DJINNI_JOBS, split="train")
    cvs_raw = load_dataset(W.DJINNI_CVS, split="train")
    jobs, _ = W.prepare_docs(jobs_raw, ["Long Description"], "Primary Keyword", "Exp Years", "Long Description_lang", cfg)
    cvs, _ = W.prepare_docs(cvs_raw, ["CV"], "Primary Keyword", "Experience Years", "CV_lang", cfg)
    return jobs, cvs


def synthetic(n_jobs=600, n_cvs=1500, seed=1):
    """Djinni-shaped toy data for testing the pipeline without network."""
    rng = random.Random(seed)
    vocab = {"Python": "django flask pandas numpy pytest fastapi", "Java": "spring hibernate maven jvm kotlin",
             "QA": "selenium testing manual cypress jira", "Design": "figma ux typography prototype sketch"}
    common = "team remote agile communication english salary office growth product startup".split()

    def doc(i, kind):
        cat = rng.choice(list(vocab))
        words = rng.sample(vocab[cat].split(), 3) + rng.sample(common, 5)
        text = f"{kind} {i}. " + ". ".join(" ".join(words[j:j + 4]) for j in range(0, len(words), 4)) + "."
        return W.Doc(f"{kind[0]}{i}", text * 3, cat, float(rng.randint(0, 6)))

    return [doc(i, "job") for i in range(n_jobs)], [doc(i, "cv") for i in range(n_cvs)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="pairs")
    ap.add_argument("--seed", type=int, default=295)
    ap.add_argument("--test-jobs", type=int, default=40)
    ap.add_argument("--train-jobs", type=int, default=240)
    ap.add_argument("--valid-share", type=float, default=0.15)
    ap.add_argument("--cv-pool", type=int, default=5000)
    ap.add_argument("--test-top-bm25", type=int, default=5)
    ap.add_argument("--test-top-dense", type=int, default=5)
    ap.add_argument("--train-top-bm25", type=int, default=3)
    ap.add_argument("--random-same", type=int, default=2)
    ap.add_argument("--random-other", type=int, default=1)
    ap.add_argument("--batch-size", type=int, default=6, help="candidates per LLM call (same job)")
    ap.add_argument("--no-dense", action="store_true")
    ap.add_argument("--synthetic", action="store_true", help="toy data, for testing only")
    a = ap.parse_args()

    t0 = time.time()
    cfg = W.Config(seed=a.seed)
    rng = random.Random(a.seed)
    jobs, cvs = synthetic() if a.synthetic else load_djinni(cfg)
    cats = W.shared_categories(jobs, cvs, 10 if a.synthetic else cfg.min_category_size)
    jobs = [d for d in jobs if d.category in cats]
    cvs = [d for d in cvs if d.category in cats]
    print(f"{len(jobs):,} jobs, {len(cvs):,} profiles, {len(cats)} categories")

    pool = W.stratified_sample(cvs, min(a.cv_pool, len(cvs)), rng)
    picked = W.stratified_sample(jobs, a.test_jobs + a.train_jobs, rng)
    test_jobs, train_jobs = picked[:a.test_jobs], picked[a.test_jobs:]
    n_valid = int(round(len(train_jobs) * a.valid_share))
    valid_jobs, train_jobs = train_jobs[:n_valid], train_jobs[n_valid:]

    pt = [p.text for p in pool]
    idx = W.BM25Index(pt)
    k1, b = 2.0, 0.9   # best setting found on the dev queries in the Oct 26 baseline run
    by_cat = defaultdict(list)
    for i, p in enumerate(pool):
        by_cat[p.category].append(i)
    all_i = list(range(len(pool)))

    dense = None
    if not a.no_dense:
        from sentence_transformers import SentenceTransformer

        st = SentenceTransformer(W.MINILM)
        pe = st.encode(pt, batch_size=64, normalize_embeddings=True, show_progress_bar=True)
        dense = (st, pe)
        (Path(a.out) / "docs").mkdir(parents=True, exist_ok=True)
        np.save(Path(a.out) / "docs" / "pool_minilm.npy", pe)     # reused by score_on_panel.py

    def candidates(job, n_bm25, n_dense):
        chosen, src = [], {}
        def add(i, tag):
            if i not in src:
                chosen.append(i); src[i] = []
            src[i].append(tag)
        s = idx.scores([job.text], k1, b)[0]
        for i in np.argsort(-s, kind="stable")[:n_bm25]:
            add(int(i), "bm25_top")
        if n_dense and dense:
            q = dense[0].encode([job.text], normalize_embeddings=True)[0]
            for i in np.argsort(-(dense[1] @ q), kind="stable")[:n_dense]:
                add(int(i), "minilm_top")
        same = [i for i in by_cat[job.category] if i not in src]
        for i in rng.sample(same, min(a.random_same, len(same))):
            add(i, "random_same_category")
        other = [i for i in all_i if pool[i].category != job.category and i not in src]
        for i in rng.sample(other, min(a.random_other, len(other))):
            add(i, "random_other_category")
        rng.shuffle(chosen)           # judges never see the retrieval order
        return [(i, src[i]) for i in chosen]

    out = Path(a.out); (out / "docs").mkdir(parents=True, exist_ok=True)
    pairs, batches = [], []
    used_cvs = set()
    for split, js, nb, nd in (("test", test_jobs, a.test_top_bm25, a.test_top_dense),
                              ("valid", valid_jobs, a.train_top_bm25, 0), ("train", train_jobs, a.train_top_bm25, 0)):
        for job in js:
            cands = candidates(job, nb, nd)
            ids = []
            for i, tags in cands:
                cv = pool[i]; used_cvs.add(i)
                pid = f"P{len(pairs) + 1:05d}"
                pairs.append({"pair_id": pid, "split": split, "job_id": job.id, "cv_id": cv.id, "sources": "|".join(tags),
                              "same_category": int(cv.category == job.category),
                              "proxy_grade": W.relevance(job, cv, "job2cv")})
                ids.append(pid)
            for j in range(0, len(ids), a.batch_size):
                batches.append({"batch_id": f"B{len(batches) + 1:05d}", "split": split, "job_id": job.id,
                                "pair_ids": ids[j:j + a.batch_size]})

    with open(out / "docs" / "jobs.jsonl", "w") as f:
        for job in test_jobs + valid_jobs + train_jobs:
            f.write(json.dumps({"id": job.id, "text": job.text, "category": job.category, "years": job.years}) + "\n")
    with open(out / "docs" / "cvs.jsonl", "w") as f:
        for i in sorted(used_cvs):
            cv = pool[i]
            f.write(json.dumps({"id": cv.id, "text": cv.text, "category": cv.category, "years": cv.years}) + "\n")
    import csv
    with open(out / "pairs.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(pairs[0])); w.writeheader(); w.writerows(pairs)
    with open(out / "batches.jsonl", "w") as f:
        for bt in batches:
            f.write(json.dumps(bt) + "\n")
    # the whole candidate pool, so every method can later rank it for the judged test jobs
    with open(out / "docs" / "pool.jsonl", "w") as f:
        for p in pool:
            f.write(json.dumps({"id": p.id, "text": p.text, "category": p.category, "years": p.years}) + "\n")
    counts = {s: sum(p["split"] == s for p in pairs) for s in ("test", "valid", "train")}
    W.save_json({"seed": a.seed, "synthetic": a.synthetic, "args": vars(a), "bm25": {"k1": k1, "b": b},
                 "jobs": {"test": len(test_jobs), "valid": len(valid_jobs), "train": len(train_jobs)},
                 "pairs": counts, "batches": len(batches), "categories": cats,
                 "seconds": round(time.time() - t0, 1)}, out / "prep_manifest.json")
    print(f"pairs: {counts}; batches: {len(batches)}; written to {out}/  ({time.time() - t0:.0f}s)")


if __name__ == "__main__":
    main()
