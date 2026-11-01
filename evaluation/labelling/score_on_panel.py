"""Step 5: score every matcher on the panel-labelled test set.

Each of the 40 test jobs ranks the same 5,000-profile pool. Judged pairs carry the panel label (1 or 0).
Two standard ways to treat profiles nobody judged are reported:
  - unjudged = not relevant (the usual convention; slightly favours the methods that built the pool,
    here BM25 and MiniLM),
  - judged only ("condensed lists": unjudged profiles are removed before scoring, which removes that bias).
Extra methods (ConFit v2) plug in with --extra name=scores.csv, a CSV of job_id,cv_id,score over the pool.

    python score_on_panel.py --pairs pairs
    python score_on_panel.py --pairs pairs --extra "ConFit v2=confit_scores.csv"
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "matching"))
import wb2_eval as W


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pairs", default="pairs")
    ap.add_argument("--extra", nargs="*", default=[], help='"Name=path/to/scores.csv" (job_id,cv_id,score)')
    ap.add_argument("--k1", type=float, default=2.0)
    ap.add_argument("--b", type=float, default=0.9)
    ap.add_argument("--bootstrap", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=295)
    a = ap.parse_args()
    pdir = Path(a.pairs)

    pool = [json.loads(l) for l in (pdir / "docs" / "pool.jsonl").open(encoding="utf-8")]
    jobs = {j["id"]: j for j in map(json.loads, (pdir / "docs" / "jobs.jsonl").open(encoding="utf-8"))}
    lab = [r for r in csv.DictReader((pdir / "final_labels.csv").open(encoding="utf-8")) if r["split"] == "test"]
    test_jobs = sorted({r["job_id"] for r in lab})
    pos = {c["id"]: i for i, c in enumerate(pool)}
    qrels = np.full((len(test_jobs), len(pool)), -1, dtype=np.int8)       # -1 = not judged
    for r in lab:
        qrels[test_jobs.index(r["job_id"]), pos[r["cv_id"]]] = int(r["label"])
    qt, pt = [jobs[j]["text"] for j in test_jobs], [c["text"] for c in pool]

    runs = {"Random": W.random_scores(len(qt), len(pt), a.seed)}
    idx = W.BM25Index(pt)
    runs["BM25 (k1=1.5, b=0.75)"] = idx.scores(qt, 1.5, 0.75)
    runs[f"BM25 tuned (k1={a.k1:g}, b={a.b:g})"] = idx.scores(qt, a.k1, a.b)
    runs["TF-IDF (1-2 grams)"] = W.tfidf_scores(qt, pt)
    emb = pdir / "docs" / "pool_minilm.npy"
    if emb.exists():
        from sentence_transformers import SentenceTransformer

        st = SentenceTransformer(W.MINILM)
        runs["MiniLM-L6-v2 embeddings"] = W.dense_scores(st.encode(qt, normalize_embeddings=True), np.load(emb))
    for spec in a.extra:
        name, path = spec.split("=", 1)
        S = np.full((len(qt), len(pt)), -1e9)
        for r in csv.DictReader(open(path, encoding="utf-8")):
            if r["job_id"] in test_jobs and r["cv_id"] in pos:
                S[test_jobs.index(r["job_id"]), pos[r["cv_id"]]] = float(r["score"])
        runs[name] = S

    out, per_query = [], {}
    tuned = next(n for n in runs if n.startswith("BM25 tuned"))
    for mode in ("unjudged = not relevant", "judged only"):
        per_query[mode] = {}
        for name, S in runs.items():
            if mode == "unjudged = not relevant":
                m = W.per_query_metrics(S, np.clip(qrels, 0, None), (5, 10))
            else:   # condensed lists: drop unjudged profiles per query
                parts = {}
                for qi in range(len(qt)):
                    keep = qrels[qi] >= 0
                    n = int(keep.sum())
                    mm = W.per_query_metrics(S[qi:qi + 1, keep], qrels[qi:qi + 1, keep], (5, 10))
                    for k in (5, 10):        # a judged list shorter than k is scored over its full length
                        for base in ("ndcg", "recall"):
                            mm[f"{base}@{k}"] = mm.get(f"{base}@{k}", mm.get(f"{base}@{min(k, n)}"))
                    for k, v in mm.items():
                        parts.setdefault(k, []).append(v[0])
                m = {k: np.array(v) for k, v in parts.items()}
            per_query[mode][name] = m
            row = {"setting": mode, "method": name}
            for met in ("ndcg@10", "ndcg@5", "p@10", "map", "mrr"):
                if met in m:
                    mean, lo, hi = W.bootstrap_ci(m[met], a.bootstrap, a.seed)
                    row[met] = round(mean, 4); row[met + "_lo"] = round(lo, 4); row[met + "_hi"] = round(hi, 4)
            out.append(row)
    paired = []
    for mode, ms in per_query.items():
        for name, m in ms.items():
            if name != tuned:
                for met in ("ndcg@10", "map"):
                    paired.append({"setting": mode, "method": name, "vs": tuned, "metric": met,
                                   **W.paired_bootstrap(m[met], ms[tuned][met], a.bootstrap, a.seed)})
    res = pdir / "panel_eval"; res.mkdir(exist_ok=True)
    for fn, rows in (("results.csv", out), ("paired_vs_bm25_tuned.csv", paired)):
        with (res / fn).open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    judged = qrels >= 0
    W.save_json({"test_jobs": len(test_jobs), "pool": len(pool), "judged_pairs": int(judged.sum()),
                 "relevant_pairs": int((qrels == 1).sum()), "jobs_with_no_relevant": int(((qrels == 1).sum(1) == 0).sum()),
                 "bm25_tuned": {"k1": a.k1, "b": a.b}}, res / "summary.json")
    for row in out:
        print(f"{row['setting']:24s} {row['method']:30s} nDCG@10 {row['ndcg@10']:.3f} [{row['ndcg@10_lo']:.3f}, {row['ndcg@10_hi']:.3f}]  "
              f"P@10 {row['p@10']:.3f}  MAP {row['map']:.3f}")
    print(f"\nWritten to {res}/ (results.csv, paired_vs_bm25_tuned.csv, summary.json)")


if __name__ == "__main__":
    main()
