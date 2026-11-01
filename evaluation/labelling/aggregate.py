"""Step 3: combine the judges, measure agreement, and write the human review and spot-check sheets.
Step 4 (after you fill the sheets): apply them and export final labels in ConFit v2's format.

    python aggregate.py --pairs pairs                       # writes review_sheet.csv and spotcheck_sheet.csv
    python aggregate.py --pairs pairs --apply               # reads the filled sheets, writes final labels + ConFit files

Label rule per pair: each judge's answer counts only if it passed every check (valid JSON, exact quotes).
- unanimous: every judge that gave a valid 0/1 agrees, and at least 2 did  -> label, no review
- majority:  2 of 3 valid votes agree, 1 disagrees                         -> label, listed for review
- unresolved: fewer than 2 agreeing valid votes, or any "unsure" without a majority -> review required
A human label in review_sheet.csv always wins.
"""
from __future__ import annotations

import argparse
import csv
import itertools
import json
import random
from collections import Counter, defaultdict
from pathlib import Path


def cohen_kappa(a, b):
    n = len(a)
    if n == 0:
        return float("nan")
    po = sum(x == y for x, y in zip(a, b)) / n
    pa, pb = Counter(a), Counter(b)
    pe = sum((pa[k] / n) * (pb[k] / n) for k in set(pa) | set(pb))
    return (po - pe) / (1 - pe) if pe < 1 else 1.0


def fleiss_kappa(rows):
    """rows: list of label lists, same number of raters each, labels 0/1."""
    if not rows:
        return float("nan")
    n = len(rows[0]); N = len(rows)
    cats = (0, 1)
    p = {c: sum(r.count(c) for r in rows) / (N * n) for c in cats}
    P = [(sum(r.count(c) ** 2 for c in cats) - n) / (n * (n - 1)) for r in rows]
    Pbar, Pe = sum(P) / N, sum(v * v for v in p.values())
    return (Pbar - Pe) / (1 - Pe) if Pe < 1 else 1.0


def load(pdir: Path, labdir: Path):
    pairs = {r["pair_id"]: r for r in csv.DictReader((pdir / "pairs.csv").open(encoding="utf-8"))}
    jobs = {j["id"]: j for j in map(json.loads, (pdir / "docs" / "jobs.jsonl").open(encoding="utf-8"))}
    cvs = {c["id"]: c for c in map(json.loads, (pdir / "docs" / "cvs.jsonl").open(encoding="utf-8"))}
    judges = [p.stem for p in sorted(labdir.glob("*.jsonl"))]
    votes = defaultdict(dict)   # pair -> judge -> record (latest ok record per batch wins)
    for jn in judges:
        latest = {}
        for line in (labdir / f"{jn}.jsonl").open(encoding="utf-8"):
            r = json.loads(line)
            if r.get("status") == "ok":
                latest[r["batch_id"]] = r
        for r in latest.values():
            for pid, lab in r["labels"].items():
                votes[pid][jn] = lab
    return pairs, jobs, cvs, judges, votes


def decide(v: dict, judges: list[str]):
    bins = [v[j]["verdict"] for j in judges if j in v and v[j]["valid"] and v[j]["verdict"] in (0, 1)]
    c = Counter(bins)
    if not bins:
        return None, "unresolved"
    top, n = c.most_common(1)[0]
    other = len(bins) - n
    if n >= 2 and other == 0:
        return top, "unanimous"
    if n >= 2 and n > other:
        return top, "majority"
    return None, "unresolved"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pairs", default="pairs")
    ap.add_argument("--labels", default=None, help="default: <pairs>/labels")
    ap.add_argument("--spotcheck", type=int, default=50, help="random pairs for the blind human spot-check")
    ap.add_argument("--apply", action="store_true", help="apply the filled review and spot-check sheets and export")
    ap.add_argument("--seed", type=int, default=295)
    a = ap.parse_args()
    pdir = Path(a.pairs); labdir = Path(a.labels) if a.labels else pdir / "labels"
    pairs, jobs, cvs, judges, votes = load(pdir, labdir)
    if len(judges) < 2:
        raise SystemExit(f"need at least 2 judges with results in {labdir}")

    decisions = {pid: decide(votes.get(pid, {}), judges) for pid in pairs}
    stats = {"judges": judges, "pairs": len(pairs), "per_judge": {}, "outcome": Counter(s for _, s in decisions.values())}
    for j in judges:
        got = [votes[p][j] for p in pairs if j in votes.get(p, {})]
        valid = [g for g in got if g["valid"]]
        stats["per_judge"][j] = {
            "answered": len(got), "valid": len(valid),
            "valid_rate": round(len(valid) / len(got), 3) if got else None,
            "positive_rate": round(sum(g["verdict"] == 1 for g in valid) / max(1, sum(g["verdict"] in (0, 1) for g in valid)), 3),
            "unsure": sum(g["verdict"] == "unsure" for g in valid),
            "top_problems": Counter(p.split(":")[0] for g in got for p in g["problems"]).most_common(5)}
    def ok(p, j):
        v = votes.get(p, {}).get(j)
        return v is not None and v["valid"] and v["verdict"] in (0, 1)

    def pair_kappa(x, y):
        items = [(votes[p][x]["verdict"], votes[p][y]["verdict"]) for p in pairs if ok(p, x) and ok(p, y)]
        return (round(cohen_kappa([i for i, _ in items], [k for _, k in items]), 3), len(items)) if items else (None, 0)

    full = [p for p in pairs if all(ok(p, j) for j in judges)]
    stats["agreement"] = {"pairs_with_all_valid_binary": len(full),
                          "fleiss_kappa": round(fleiss_kappa([[votes[p][j]["verdict"] for j in judges] for p in full]), 3) if full else None,
                          "pairwise_cohen_kappa (kappa, pairs)": {f"{x} vs {y}": pair_kappa(x, y) for x, y in itertools.combinations(judges, 2)}}
    stats["outcome"] = dict(stats["outcome"])
    review_path, spot_path = pdir / "review_sheet.csv", pdir / "spotcheck_sheet.csv"

    def row(pid, with_votes=True):
        p = pairs[pid]
        r = {"pair_id": pid, "split": p["split"], "job_id": p["job_id"], "cv_id": p["cv_id"]}
        if with_votes:
            lab, st = decisions[pid]
            r.update(panel_label="" if lab is None else lab, panel_status=st)
            for j in judges:
                v = votes.get(pid, {}).get(j)
                r[f"{j}_verdict"] = "" if v is None else (v["raw_verdict"] if v["valid"] else f"invalid({v.get('raw_verdict')})")
                r[f"{j}_reason"] = "" if v is None else (v.get("reason") or "; ".join(v["problems"])[:300])
        r.update(human_label="", human_notes="", job_text=jobs[p["job_id"]]["text"], cv_text=cvs[p["cv_id"]]["text"])
        return r

    if not a.apply:
        need = [p for p in pairs if decisions[p][1] in ("majority", "unresolved")]
        need.sort(key=lambda p: (decisions[p][1] != "unresolved", pairs[p]["split"] != "test", pairs[p]["job_id"]))
        with review_path.open("w", newline="", encoding="utf-8") as f:
            rows = [row(p) for p in need]
            w = csv.DictWriter(f, fieldnames=list(rows[0]) if rows else ["pair_id"]); w.writeheader(); w.writerows(rows)
        rng = random.Random(a.seed)
        pool = [p for p in pairs if pairs[p]["split"] == "test" and decisions[p][1] == "unanimous"]
        spot = rng.sample(pool, min(a.spotcheck, len(pool)))
        if not spot_path.exists():         # never overwrite a sheet you may already be filling in
            with spot_path.open("w", newline="", encoding="utf-8") as f:
                rows = [row(p, with_votes=False) for p in sorted(spot, key=lambda p: pairs[p]["job_id"])]
                w = csv.DictWriter(f, fieldnames=list(rows[0]) if rows else ["pair_id"]); w.writeheader(); w.writerows(rows)
        stats["review_rows"] = {"unresolved (must label)": sum(decisions[p][1] == "unresolved" for p in need),
                                "majority (check, optional)": sum(decisions[p][1] == "majority" for p in need)}
        (pdir / "panel_stats.json").write_text(json.dumps(stats, indent=2, default=str))
        print(json.dumps(stats, indent=2, default=str))
        print(f"\nReview sheet: {review_path}  (fill human_label with 1 or 0; 'unresolved' rows must be filled)")
        print(f"Spot-check sheet (blind): {spot_path}  (fill human_label for every row, without looking at the panel)")
        return

    # ---------------------------------------------------------------- apply human sheets and export
    human = {}
    if review_path.exists():
        for r in csv.DictReader(review_path.open(encoding="utf-8")):
            if r.get("human_label", "").strip() in ("0", "1"):
                human[r["pair_id"]] = int(r["human_label"])
    final = {}
    for pid in pairs:
        lab, st = decisions[pid]
        if pid in human:
            final[pid] = (human[pid], "human_review")
        elif lab is not None:
            final[pid] = (lab, st)
    missing = [p for p in pairs if p not in final]
    spot = {}
    if spot_path.exists():
        for r in csv.DictReader(spot_path.open(encoding="utf-8")):
            if r.get("human_label", "").strip() in ("0", "1"):
                spot[r["pair_id"]] = int(r["human_label"])
    sc = [(spot[p], decisions[p][0]) for p in spot if decisions[p][0] is not None]
    stats["spotcheck"] = {"pairs": len(sc), "accuracy": round(sum(h == m for h, m in sc) / len(sc), 3) if sc else None,
                          "cohen_kappa_panel_vs_human": round(cohen_kappa([h for h, _ in sc], [m for _, m in sc]), 3) if sc else None}
    stats["final"] = {"labelled": len(final), "unlabelled (dropped)": len(missing),
                      "by_source": dict(Counter(s for _, s in final.values())),
                      "positives_by_split": {s: f"{sum(final[p][0] for p in final if pairs[p]['split'] == s)}/"
                                                f"{sum(pairs[p]['split'] == s for p in final)}" for s in ("test", "valid", "train")}}
    with (pdir / "final_labels.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["pair_id", "split", "job_id", "cv_id", "label", "label_source", "sources", "proxy_grade"])
        for p in pairs:
            if p in final:
                w.writerow([p, pairs[p]["split"], pairs[p]["job_id"], pairs[p]["cv_id"], final[p][0], final[p][1],
                            pairs[p]["sources"], pairs[p]["proxy_grade"]])
    export_confit(pdir, pairs, jobs, cvs, final)
    (pdir / "panel_stats.json").write_text(json.dumps(stats, indent=2, default=str))
    print(json.dumps(stats, indent=2, default=str))
    print(f"\nFinal labels: {pdir / 'final_labels.csv'}; ConFit files: {pdir / 'confit'}/")


def export_confit(pdir, pairs, jobs, cvs, final):
    """ConFit v2 'all-in-one text' format (dataset/recruiting_data_v2 layout of the official repo)."""
    out = pdir / "confit"; out.mkdir(exist_ok=True)
    used_j = sorted({pairs[p]["job_id"] for p in final}); used_c = sorted({pairs[p]["cv_id"] for p in final})
    with (out / "all_jd.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["jd_no", "text_job"]); w.writerows([[j, jobs[j]["text"]] for j in used_j])
    with (out / "all_resume.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["user_id", "text_resume"]); w.writerows([[c, cvs[c]["text"]] for c in used_c])
    names = {"train": "train_labeled_data.jsonl", "valid": "valid_classification_data.jsonl", "test": "test_classification_data.jsonl"}
    for split, fn in names.items():
        with (out / fn).open("w", encoding="utf-8") as f:
            for p in pairs:
                if p in final and pairs[p]["split"] == split:
                    f.write(json.dumps({"user_id": pairs[p]["cv_id"], "jd_no": pairs[p]["job_id"], "satisfied": final[p][0]}) + "\n")
    for split, prefix in (("test", ""), ("valid", "valid_")):
        rr, rj = defaultdict(lambda: {"user_ids": [], "satisfied": []}), defaultdict(lambda: {"jd_nos": [], "satisfied": []})
        for p in pairs:
            if p in final and pairs[p]["split"] == split:
                rr[pairs[p]["job_id"]]["user_ids"].append(pairs[p]["cv_id"]); rr[pairs[p]["job_id"]]["satisfied"].append(final[p][0])
                rj[pairs[p]["cv_id"]]["jd_nos"].append(pairs[p]["job_id"]); rj[pairs[p]["cv_id"]]["satisfied"].append(final[p][0])
        (out / f"{prefix}rank_resume.json").write_text(json.dumps(rr, indent=1))
        (out / f"{prefix}rank_job.json").write_text(json.dumps(rj, indent=1))


if __name__ == "__main__":
    main()
