# Evaluation

Matching evaluation harness, LLM labelling panel and ConFit v2 scripts for "Beyond Keyword Matching"
(CMPE 295A). No raw data, embeddings, judge outputs or model checkpoints are stored here (see `.gitignore`).

## Layout

| Folder | Contents |
|---|---|
| `matching/` | `wb2_eval.py` (cleaning, sampling, rankers, metrics, bootstrap statistics, explanations) and `WB2_Baseline_Experiments_v2.ipynb`, the Colab notebook that runs it on Djinni and SkillSpan. The notebook writes its own copy of `wb2_eval.py` with `%%writefile`, so it runs on its own in Colab. |
| `labelling/` | The LLM labelling panel: `prepare_pairs.py` (build job-candidate pairs), `label_panel.py` (ask each judge CLI), `aggregate.py` (combine votes, review sheets, final labels and ConFit input files), `score_on_panel.py` (score matchers on the panel labels), `prompt.md` (judge prompt) and `judges.example.json` (judge configuration template). |
| `confit/` | `ConFit_v2_Djinni.ipynb` (Colab notebook that trains ConFit v2 on the panel labels), `patch_confit.py` (compatibility patches for the official ConFit v2 code) and `confit_scores.py` (scores test pairs with a trained checkpoint). Both scripts were extracted verbatim from the notebook's `%%writefile` cells. |
| `results/matching/` | `manifest.json`, `bm25_tuning.json`, `data_stats.json` from the full-scale baseline run. |
| `results/labelling/` | `panel_stats.json`, `prep_manifest.json`, `judges_used.json`, and `review_votes.csv` (the panel's votes and reasons for the majority and unresolved pairs: the review sheet without the `job_text`, `cv_text` and empty `human_label` columns). |

## Install

Python 3.12. From the repository root:

```
python3.12 -m venv evaluation/.venv
source evaluation/.venv/bin/activate
pip install numpy scipy scikit-learn rank_bm25==0.2.2 pytest
```

`prepare_pairs.py` on real data also needs `datasets` (Djinni download) and, unless `--no-dense` is given,
`sentence-transformers`. The notebooks install their own dependencies in their first cell.

## Tests

```
python -m py_compile evaluation/*/*.py
cd evaluation/labelling
python prepare_pairs.py --synthetic --no-dense --out /tmp/synth
```

`--synthetic` builds toy Djinni-shaped data and makes no network calls. A unit-test file for `wb2_eval.py` is
not included in this folder yet.

## Full-scale baseline run on Colab A100 (Workbook §7.6, Step 4b)

1. Open `matching/WB2_Baseline_Experiments_v2.ipynb` in Google Colab.
2. Runtime → Change runtime type → A100 GPU.
3. In the Settings cell, keep `QUICK = False` (`True` is a short smoke run on smaller samples).
4. Runtime → Run all. The first cell installs the libraries; Djinni, the models and the SkillSpan test file
   download from Hugging Face and GitHub. No account or token is needed.
5. The last cell downloads `wb2_results.zip`. Its `manifest.json` records the config, seed, package versions,
   GPU and timings.

## Labelling panel

Create `judges.json` locally from the template, then edit the commands for the judge CLIs you have.
`judges.json` is gitignored and must never be committed.

```
cd evaluation/labelling
cp judges.example.json judges.json
```

Run, in order:

```
python prepare_pairs.py --out pairs
python label_panel.py --pairs pairs --judges judges.json
python aggregate.py --pairs pairs
python aggregate.py --pairs pairs --apply
python score_on_panel.py --pairs pairs --k1 4.0 --b 0.9
```

`aggregate.py` (without `--apply`) writes `review_sheet.csv` and `spotcheck_sheet.csv`. Fill in their
`human_label` column, then run `--apply` to write `final_labels.csv`, `panel_stats.json` and `pairs/confit/`
(ConFit v2 input files). The `pairs/` folder holds Djinni text and raw judge outputs and is gitignored.

## ConFit v2

The official ConFit v2 code (github.com/jasonyux/ConFit-v2, commit `8022a9e`, MIT licence) is not vendored here.
`ConFit_v2_Djinni.ipynb` clones it separately and patches it with `patch_confit.py`:

```
git clone https://github.com/jasonyux/ConFit-v2.git
cd ConFit-v2 && git checkout 8022a9e
python /path/to/evaluation/confit/patch_confit.py .
```

In Colab: Runtime → Change runtime type → A100 GPU → Run all, and upload `pairs.zip` (the whole `pairs` folder
after `aggregate.py --apply`) when asked. The notebook downloads `confit_results.zip`, which contains
`confit_scores.csv`. Score it with:

```
python score_on_panel.py --pairs pairs --extra "ConFit v2=confit_scores.csv"
```
