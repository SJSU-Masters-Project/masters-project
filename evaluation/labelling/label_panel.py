"""Step 2: run the LLM panel over the batches, one thread per judge, resumable.

Each call sends one job and up to 6 candidates through a judge's command-line tool, then checks the
answer: valid JSON, one entry per candidate, and every quoted phrase found word for word in the job
or candidate text. A candidate whose answer fails a check gets no label from that judge.

    python label_panel.py --pairs pairs --judges judges.json --limit 2   # try 2 batches per judge
    python label_panel.py --pairs pairs --judges judges.json             # full run (resumes)
    python label_panel.py --pairs pairs --judges judges.json --only opus --split test
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import subprocess
import sys
import tempfile
import threading
import time
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent
LIMIT_WORDS = ("rate limit", "usage limit", "quota", "too many requests", "429", "overloaded", "try again later")


# ------------------------------------------------------------------ text checks
def norm(s: str) -> str:
    s = unicodedata.normalize("NFKC", s or "")
    s = s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    s = re.sub(r"[‐-―]", "-", s)
    return re.sub(r"\s+", " ", s).strip().lower()


def quote_found(quote: str, text: str) -> bool:
    q = norm(quote).strip(" .,;:!\"'()[]")
    return len(q) >= 3 and "..." not in q and "…" not in q and q in norm(text)


def extract_json(out: str):
    """Take the outermost JSON object from a CLI's output (tolerates ``` fences and chatter)."""
    out = re.sub(r"```(?:json)?", "", out)
    start = out.find("{")
    if start < 0:
        raise ValueError("no JSON object in output")
    depth, in_str, esc = 0, False, False
    for i in range(start, len(out)):
        ch = out[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
        elif ch == '"':
            in_str = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return json.loads(out[start:i + 1])
    raise ValueError("unterminated JSON object")


def validate(parsed: dict, job_text: str, cands: list[dict]) -> dict:
    """Returns {pair_id: {"verdict": 0|1|"unsure"|None, "valid": bool, "problems": [...], ...}}."""
    by_cid = {c["candidate_id"]: c for c in cands}
    got = {}
    for e in parsed.get("candidates", []) if isinstance(parsed, dict) else []:
        if isinstance(e, dict) and e.get("candidate_id") in by_cid and e["candidate_id"] not in got:
            got[e["candidate_id"]] = e
    res = {}
    for cid, c in by_cid.items():
        e, probs = got.get(cid), []
        if e is None:
            res[c["pair_id"]] = {"verdict": None, "valid": False, "problems": ["missing"]}
            continue
        v = e.get("verdict")
        if isinstance(v, str) and v.strip() in ("0", "1"):
            v = int(v)
        if v not in (0, 1, "unsure"):
            probs.append(f"bad verdict {v!r}")
        reqs = e.get("requirements")
        if not isinstance(reqs, list) or (v in (0, 1) and not reqs):
            probs.append("no requirements")
            reqs = reqs if isinstance(reqs, list) else []
        n_met = 0
        for r in reqs[:8]:
            if not isinstance(r, dict):
                probs.append("bad requirement entry"); continue
            if not quote_found(str(r.get("requirement", "")), job_text):
                probs.append(f"requirement not in job: {str(r.get('requirement'))[:60]!r}")
            ev, met = r.get("evidence"), bool(r.get("met"))
            if ev not in (None, "", "null"):
                if not quote_found(str(ev), c["text"]):
                    probs.append(f"evidence not in candidate: {str(ev)[:60]!r}")
            elif met:
                probs.append("met without evidence")
            n_met += met
        if v == 1 and n_met == 0:
            probs.append("verdict 1 with no met requirement")
        res[c["pair_id"]] = {"verdict": v if not probs else None, "raw_verdict": v, "valid": not probs,
                             "problems": probs, "n_requirements": len(reqs), "n_met": n_met,
                             "reason": str(e.get("reason", ""))[:400]}
    return res


# ------------------------------------------------------------------ calling a judge
def build_prompt(template: str, job: dict, cands: list[dict], max_chars: int) -> str:
    block = "\n\n".join(f"### Candidate {c['candidate_id']}\n{c['text'][:max_chars]}" for c in cands)
    return (template.replace("{job_id}", job["id"]).replace("{job_text}", job["text"][:max_chars])
            .replace("{candidates}", block))


def call(judge: dict, prompt: str) -> tuple[str, float]:
    cmd, mode = list(judge["cmd"]), judge.get("input", "stdin")
    t0, stdin, tmp = time.time(), None, None
    if mode == "stdin":
        stdin = prompt
    elif mode == "arg":
        cmd = cmd + [prompt]
    elif mode == "file":
        tmp = tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8")
        tmp.write(prompt); tmp.close()
        cmd = [x.replace("{prompt_file}", tmp.name) for x in cmd]
    else:
        raise ValueError(f"unknown input mode {mode}")
    try:
        p = subprocess.run(cmd, input=stdin, capture_output=True, text=True, timeout=judge.get("timeout", 300),
                           env={**os.environ, **judge.get("env", {})}, cwd=judge["_cwd"], encoding="utf-8", errors="replace")
        out = (p.stdout or "") + ("\n[stderr]\n" + p.stderr if p.returncode != 0 and p.stderr else "")
        if p.returncode != 0 and not p.stdout.strip():
            raise RuntimeError(f"exit {p.returncode}: {(p.stderr or '')[:300]}")
        return out, time.time() - t0
    finally:
        if tmp:
            os.unlink(tmp.name)


def run_judge(judge, batches, jobs, cvs, pairs, template, outdir, a, lock):
    name = judge["name"]
    path = outdir / f"{name}.jsonl"
    done = set()
    if path.exists():
        for line in path.open(encoding="utf-8"):
            try:
                r = json.loads(line)
                if r.get("status") == "ok" and not (a.redo_invalid and not all(v["valid"] for v in r["labels"].values())):
                    done.add(r["batch_id"])
                elif r["batch_id"] in done and a.redo_invalid:
                    pass
            except json.JSONDecodeError:
                pass
    todo = [b for b in batches if b["batch_id"] not in done]
    if a.limit:
        todo = todo[:a.limit]
    with lock:
        print(f"[{name}] {len(done)} batches done earlier, {len(todo)} to go", flush=True)
    for n, b in enumerate(todo, 1):
        job = jobs[b["job_id"]]
        cands = [{"candidate_id": f"C{i + 1}", "pair_id": pid, "text": cvs[pairs[pid]["cv_id"]]["text"]}
                 for i, pid in enumerate(b["pair_ids"])]
        prompt = build_prompt(template, job, cands, a.max_chars)
        rec = {"batch_id": b["batch_id"], "judge": name, "job_id": b["job_id"],
               "candidate_map": {c["candidate_id"]: c["pair_id"] for c in cands}}
        for attempt in range(1, a.retries + 2):
            try:
                out, secs = call(judge, prompt)
                rec.update(raw=out[-20000:], seconds=round(secs, 1), attempt=attempt)
                low = out.lower()
                if any(w in low for w in LIMIT_WORDS) and "{" not in out:
                    raise RuntimeError("rate/usage limit: " + out[:200])
                parsed = extract_json(out)
                labels = validate(parsed, job["text"][:a.max_chars],
                                  [{**c, "text": c["text"][:a.max_chars]} for c in cands])
                rec.update(status="ok", labels=labels)
                break
            except Exception as ex:  # noqa: BLE001 - every failure is recorded and retried
                rec.update(status="error", error=str(ex)[:500])
                wait = a.limit_wait if "limit" in str(ex).lower() else a.retry_wait * attempt
                if attempt <= a.retries:
                    with lock:
                        print(f"[{name}] {b['batch_id']} attempt {attempt} failed ({str(ex)[:80]}); retry in {wait}s", flush=True)
                    time.sleep(wait)
        rec["ts"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        with lock:
            with path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(rec) + "\n")
            if rec["status"] == "ok":
                ok = sum(v["valid"] for v in rec["labels"].values())
                print(f"[{name}] {n}/{len(todo)} {b['batch_id']} ok: {ok}/{len(cands)} valid ({rec['seconds']}s)", flush=True)
            else:
                print(f"[{name}] {n}/{len(todo)} {b['batch_id']} FAILED: {rec['error'][:120]}", flush=True)
        if a.pause:
            time.sleep(a.pause)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pairs", default="pairs")
    ap.add_argument("--judges", default="judges.json")
    ap.add_argument("--prompt", default=str(HERE / "prompt.md"))
    ap.add_argument("--out", default=None, help="default: <pairs>/labels")
    ap.add_argument("--only", nargs="*", help="judge names to run")
    ap.add_argument("--split", choices=["test", "valid", "train"], help="only this split (test first is wise)")
    ap.add_argument("--limit", type=int, default=0, help="at most this many new batches per judge")
    ap.add_argument("--max-chars", type=int, default=4000)
    ap.add_argument("--retries", type=int, default=2)
    ap.add_argument("--retry-wait", type=int, default=20)
    ap.add_argument("--limit-wait", type=int, default=600, help="seconds to wait after a rate/usage-limit message")
    ap.add_argument("--pause", type=float, default=0.0, help="seconds between calls per judge")
    ap.add_argument("--redo-invalid", action="store_true", help="re-ask batches where any candidate's answer failed the checks")
    a = ap.parse_args()

    pdir = Path(a.pairs)
    jobs = {j["id"]: j for j in map(json.loads, (pdir / "docs" / "jobs.jsonl").open(encoding="utf-8"))}
    cvs = {c["id"]: c for c in map(json.loads, (pdir / "docs" / "cvs.jsonl").open(encoding="utf-8"))}
    pairs = {r["pair_id"]: r for r in csv.DictReader((pdir / "pairs.csv").open(encoding="utf-8"))}
    batches = [json.loads(l) for l in (pdir / "batches.jsonl").open(encoding="utf-8")]
    order = {"test": 0, "valid": 1, "train": 2}
    batches.sort(key=lambda b: (order[b["split"]], b["batch_id"]))   # test set first
    if a.split:
        batches = [b for b in batches if b["split"] == a.split]
    judges = json.loads(Path(a.judges).read_text())
    if a.only:
        judges = [j for j in judges if j["name"] in a.only]
    if not judges:
        sys.exit("no judges selected")
    template = Path(a.prompt).read_text(encoding="utf-8")
    outdir = Path(a.out) if a.out else pdir / "labels"
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "prompt_used.md").write_text(template, encoding="utf-8")
    (outdir / "judges_used.json").write_text(json.dumps([{k: v for k, v in j.items() if k != "env"} for j in judges], indent=2))
    for j in judges:   # run every CLI in an empty folder so it picks up no project files or instructions
        j["_cwd"] = j.get("cwd") or str((outdir / "_empty_cwd").resolve())
        Path(j["_cwd"]).mkdir(parents=True, exist_ok=True)
    lock = threading.Lock()
    threads = [threading.Thread(target=run_judge, args=(j, batches, jobs, cvs, pairs, template, outdir, a, lock), daemon=True)
               for j in judges]
    for t in threads:
        t.start()
    try:
        for t in threads:
            while t.is_alive():
                t.join(1)
    except KeyboardInterrupt:
        print("\nStopped. Rerun the same command to resume; finished batches are kept.")


if __name__ == "__main__":
    main()
