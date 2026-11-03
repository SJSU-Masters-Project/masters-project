# Extracted verbatim from ConFit_v2_Djinni.ipynb cell 3
"""Minimal compatibility patches for running the official ConFit v2 code on one GPU with current libraries."""
import re, sys
from pathlib import Path
root = Path(sys.argv[1])
p = root / "src/model/confit.py"; s = p.read_text()
for name in ("job", "resume"):
    old = f"self.all_gather(batched_all_coarse_{name},sync_grads=True).flatten(0,1).contiguous()"
    new = f"self._gather_flat(batched_all_coarse_{name})"
    if new in s:
        continue            # already patched
    assert old in s, old
    s = s.replace(old, new)
if "_gather_flat" not in s.split("class ConFitModel", 1)[1].split("def __init__", 1)[0]:
    s = s.replace("class ConFitModel(BaseModel):\n", "class ConFitModel(BaseModel):\n"
                  "    def _gather_flat(self, x):\n"
                  "        # one process: all_gather returns x unchanged (2-D); several: (world, batch, dim)\n"
                  "        g = self.all_gather(x, sync_grads=True)\n"
                  "        return (g.flatten(0, 1) if g.dim() == 3 else g).contiguous()\n\n", 1)
p.write_text(s)
t = root / "runners/trainer/train_confit.py"; s = t.read_text()
s = s.replace('accelerator="gpu",', 'accelerator=os.environ.get("PL_ACCEL", "gpu"),')
t.write_text(s)
print("patched")
u = root / "src/utils/test_embedding_networks.py"; s = u.read_text()
s = s.replace('''        assert self.dataset_type in [
            "AliTianChi",
            "recruiting_data",
        ], f"Invalid dataset type: {self.dataset_type}"''', '''        assert self.dataset_type in [
            "AliTianChi",
            "recruiting_data",
            "recruiting_data_v1",
            "recruiting_data_v2",
        ], f"Invalid dataset type: {self.dataset_type}"''')
s = s.replace('model = model.to("cuda")', 'model = model.to(os.environ.get("CONFIT_DEVICE", "cuda"))')
if "\nimport os" not in s:
    s = "import os\n" + s
u.write_text(s)
print("patched test utilities")
e = root / "src/evaluation/eval.py"; s = e.read_text()
old = "        for k, v in self.test_ranking_data.items():\n            k = str(k)\n"
new = old + "            if len(v.get(\"satisfied\", [])) < 2 or sum(v.get(\"satisfied\", [])) == 0:   # needs two judged items and at least one positive\n                continue\n"
if new not in s:
    assert old in s
    s = s.replace(old, new, 1)
e.write_text(s)
print("patched evaluator")
h = root / "src/utils/hard_negative_mining.py"; s = h.read_text()
s = s.replace('assert self.dataset_type in ["AliTianChi", "recruiting_data"],',
              'assert self.dataset_type in ["AliTianChi", "recruiting_data", "recruiting_data_v1", "recruiting_data_v2"],')
s = s.replace('model = model.to("cuda")', 'model = model.to(os.environ.get("CONFIT_DEVICE", "cuda"))')
h.write_text(s)
m = root / "src/model/confit.py"; s = m.read_text()
# the repo's fallback for Jina v2 points at a placeholder folder; use its own local Jina implementation instead
s = s.replace('JinaBertModel.from_pretrained("path_to_cache_folder_jinav2")', 'JinaBertModel.from_pretrained(args.pretrained_encoder)')
m.write_text(s)
print("patched mining and Jina fallback")
