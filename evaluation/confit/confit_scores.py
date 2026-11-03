# Extracted verbatim from ConFit_v2_Djinni.ipynb cell 4
"""Score every (test job, pool candidate) pair with a trained ConFit v2 checkpoint, using the official
model and dataset code, and write job_id,cv_id,score for score_on_panel.py.

Run from the ConFit-v2 repo root with PYTHONPATH set to it:
    python confit_scores.py --run model_checkpoints/confit_v2_djinni --pairs /content/pairs --out confit_scores.csv
"""
import argparse
import csv
import json
import os
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import DataLoader
from transformers import AutoTokenizer

from src.config.dataset import DATASET_CONFIG
from src.model.confit import ConFitModel, ConFitModelArguments
from src.preprocess.dataset import RJPairSimplifiedDataset, rj_pair_collate_fn


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True, help="the --save_path of the training run")
    ap.add_argument("--ckpt", default=None, help="checkpoint file (default: the best one recorded in the run folder)")
    ap.add_argument("--pairs", required=True)
    ap.add_argument("--out", default="confit_scores.csv")
    ap.add_argument("--dataset-type", default="recruiting_data_v2")
    ap.add_argument("--batch-size", type=int, default=16)
    ap.add_argument("--jobs-csv", default=None, help="jd_no,text_job file used in training (for example with HyRe text)")
    a = ap.parse_args()
    dev = os.environ.get("CONFIT_DEVICE", "cuda" if torch.cuda.is_available() else "cpu")

    run = Path(a.run)
    margs = ConFitModelArguments(**json.loads((run / "model_args.json").read_text()))
    ckpt = a.ckpt
    if ckpt is None:
        cands = sorted(run.glob("epoch=*.ckpt"), key=lambda p: p.stat().st_mtime)
        ckpt = str(cands[-1] if cands else run / "last.ckpt")
    state = torch.load(ckpt, map_location="cpu", weights_only=False)["state_dict"]
    model = ConFitModel(margs)
    model.load_state_dict(state)
    model = model.float().to(dev).eval()
    print("loaded", ckpt)

    pdir = Path(a.pairs)
    pool = [json.loads(l) for l in (pdir / "docs" / "pool.jsonl").open(encoding="utf-8")]
    jobs = {j["id"]: j for j in map(json.loads, (pdir / "docs" / "jobs.jsonl").open(encoding="utf-8"))}
    test_jobs = sorted({r["job_id"] for r in csv.DictReader((pdir / "final_labels.csv").open(encoding="utf-8"))
                        if r["split"] == "test"})
    resumes = [{"user_id": c["id"], "text_resume": c["text"]} for c in pool]
    if a.jobs_csv:
        jt = {r["jd_no"]: r["text_job"] for r in csv.DictReader(open(a.jobs_csv, encoding="utf-8"))}
        jds = [{"jd_no": j, "text_job": jt.get(j, jobs[j]["text"])} for j in test_jobs]
    else:
        jds = [{"jd_no": j, "text_job": jobs[j]["text"]} for j in test_jobs]
    n = max(len(resumes), len(jds))            # pair every id with something so each gets embedded once
    pairs = [{"user_id": resumes[i % len(resumes)]["user_id"], "jd_no": jds[i % len(jds)]["jd_no"], "satisfied": 0}
             for i in range(n)]

    cfg = DATASET_CONFIG[a.dataset_type]
    tok = AutoTokenizer.from_pretrained(margs.pretrained_encoder)
    ds = RJPairSimplifiedDataset(
        tok, max_seq_length_per_key=cfg["max_seq_len_per_feature"], resume_key_names=cfg["resume_key_names"],
        job_key_names=cfg["job_key_names"], tokenizer_args={"padding": "max_length", "return_tensors": "pt", "truncation": True},
        all_resume_dict=resumes, all_job_dict=jds, label_pairs=pairs, resume_taxon_token=cfg["resume_taxon_token"],
        job_taxon_token=cfg["job_taxon_token"], query_prefix="", encode_all=margs.encode_all)
    dl = DataLoader(ds, batch_size=a.batch_size, shuffle=False, collate_fn=rj_pair_collate_fn, num_workers=2)
    R, J = {}, {}
    for bi, batch in enumerate(dl):
        with torch.no_grad():
            out = model.predict_step(batch, bi)
        for off in range(out.batched_resume_representation.shape[0]):
            p = pairs[bi * a.batch_size + off]
            R[p["user_id"]] = out.batched_resume_representation[off].float().cpu().numpy()
            J[p["jd_no"]] = out.batched_job_representation[off].float().cpu().numpy()
    rid = list(R); Rm = np.stack([R[r] for r in rid])
    with open(a.out, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["job_id", "cv_id", "score"])
        for j in test_jobs:
            s = Rm @ J[j]
            w.writerows(zip([j] * len(rid), rid, s.tolist()))
    print(f"wrote {a.out}: {len(test_jobs)} jobs x {len(rid)} candidates")


if __name__ == "__main__":
    main()
