#!/usr/bin/env python3
"""
eval_ablation.py — component ablation for the corrector (paper Table).
ONE model pass over the full 25k test split (predictions cached in memory),
then the corrector is run in several configurations on those cached predictions:

  full_morph    : inverse subs + OSA fallback + morphological guard   (proposed full system)
  no_morph      : inverse subs + OSA fallback                         (= currently evaluated system)
  inverse_only  : inverse subs only (no OSA, no morph)
  osa_only      : OSA fallback only (no inverse subs, no morph)

For each config we report end-to-end "fully corrected" at MODEL detection and at
ORACLE detection (all pairs and clean-excluded), and per-error-type fixed% at
oracle/force. Bootstrap 95% CIs for the two headline configs.

Run from backend/ with the torch venv:
  KAZAKH_MODEL_PATH=$PWD/models/kazakh_detector ./.venv-train/bin/python scripts/eval_ablation.py
"""
from __future__ import annotations
import json, os, sys, time
import numpy as np

_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _BACKEND)
from app.services.kazakh_corrector import KazakhCorrector

TEST = os.path.join(_BACKEND, "data", "kazakh_spellcheck", "test.jsonl")
OUTDIR = os.path.join(_BACKEND, "data", "eval"); os.makedirs(OUTDIR, exist_ok=True)
RNG = np.random.default_rng(42); B = 1000

# ── single model pass (cached to disk so re-runs skip the ~300s pass) ──
import pickle
CACHE = os.path.join(OUTDIR, "ablation_cache.pkl")
if os.path.exists(CACHE):
    with open(CACHE, "rb") as f:
        S = pickle.load(f)
    print(f"loaded cached model predictions: {len(S)} sentences", flush=True)
else:
    import torch
    from transformers import AutoModelForTokenClassification, AutoTokenizer
    mdir = os.environ.get("KAZAKH_MODEL_PATH", os.path.join(_BACKEND, "models", "kazakh_detector"))
    tok = AutoTokenizer.from_pretrained(mdir, use_fast=True)
    mdl = AutoModelForTokenClassification.from_pretrained(mdir).eval()
    torch.set_num_threads(1)

    def detect_model(words):
        enc = tok(words, is_split_into_words=True, truncation=True, max_length=512, return_tensors="pt")
        with torch.no_grad():
            preds = mdl(**enc).logits[0].argmax(-1).tolist()
        pos, prev = set(), None
        for i, wid in enumerate(enc.word_ids(0)):
            if wid is None or wid == prev:
                prev = wid; continue
            prev = wid
            if preds[i] == 1:
                pos.add(wid)
        return pos

    S = []  # (corrupted, correct, clean, true_err, model_pred, edits)
    t0 = time.time(); n = 0
    for line in open(TEST, encoding="utf-8"):
        o = json.loads(line)
        cw, rw = o["corrupted"].split(), o["correct"].split()
        if len(cw) != len(rw):
            continue
        n += 1
        true_err = frozenset(i for i in range(len(cw)) if cw[i] != rw[i])
        S.append((o["corrupted"], o["correct"], bool(o["clean"]), true_err,
                  frozenset(detect_model(cw)), o["edits"]))
        if n % 2500 == 0:
            print(f"  model pass {n}, {time.time()-t0:.0f}s", flush=True)
    with open(CACHE, "wb") as f:
        pickle.dump(S, f)
    print(f"model pass done: {len(S)} sentences, cached -> {CACHE}", flush=True)

clean = np.array([s[2] for s in S])
nc_idx = np.where(clean == 0)[0]
N = len(S)
TYPES = ["ka2ru", "harmony", "swap", "drop", "dup", "sub"]

CONFIGS = {
    "full_morph":   dict(use_morph=True,  use_inverse=True,  use_osa=True),
    "no_morph":     dict(use_morph=False, use_inverse=True,  use_osa=True),
    "inverse_only": dict(use_morph=False, use_inverse=True,  use_osa=False),
    "osa_only":     dict(use_morph=False, use_inverse=False, use_osa=True),
}

c = KazakhCorrector()  # one instance; toggle flags per config

def ci(vals):
    lo, hi = np.percentile(vals, [2.5, 97.5]); return [round(float(lo), 2), round(float(hi), 2)]

report = {"n": N, "configs": {}}
for name, flags in CONFIGS.items():
    c.use_morph, c.use_inverse, c.use_osa = flags["use_morph"], flags["use_inverse"], flags["use_osa"]
    fixed_model = np.zeros(N, dtype=np.int8)
    fixed_oracle = np.zeros(N, dtype=np.int8)
    for i, (corr, ref, cl, te, mp, ed) in enumerate(S):
        fixed_model[i] = 1 if c.correct(corr, only_positions=set(mp)) == ref else 0
        fixed_oracle[i] = 1 if c.correct(corr, only_positions=set(te)) == ref else 0
    # per-type at oracle/force
    per_type = {}
    tcnt = {t: [0, 0] for t in TYPES}  # [fixed, total]
    for (_, _, _, _, _, ed) in S:
        for e in ed:
            if e["type"] in tcnt:
                tcnt[e["type"]][1] += 1
                if c.correct_word(e["after"], force=True) == e["before"]:
                    tcnt[e["type"]][0] += 1
    for t in TYPES:
        fx, tot = tcnt[t]
        per_type[t] = {"n": tot, "fixed_pct": round(100*fx/tot, 2) if tot else 0.0}
    entry = {
        "e2e_model_all": round(100*fixed_model.mean(), 2),
        "e2e_model_nonclean": round(100*fixed_model[nc_idx].mean(), 2),
        "e2e_oracle_all": round(100*fixed_oracle.mean(), 2),
        "e2e_oracle_nonclean": round(100*fixed_oracle[nc_idx].mean(), 2),
        "per_type_oracle": per_type,
    }
    # bootstrap CI on E2E model-all for the two headline configs
    if name in ("full_morph", "no_morph"):
        boot = [100*fixed_model[RNG.integers(0, N, N)].mean() for _ in range(B)]
        entry["e2e_model_all_CI"] = ci(boot)
    report["configs"][name] = entry
    print(f"{name:13s} E2E model {entry['e2e_model_all']:.1f}% (no-clean {entry['e2e_model_nonclean']:.1f}%) | "
          f"oracle {entry['e2e_oracle_all']:.1f}% | "
          + " ".join(f"{t}:{per_type[t]['fixed_pct']:.0f}" for t in TYPES), flush=True)

with open(os.path.join(OUTDIR, "eval_ablation.json"), "w", encoding="utf-8") as f:
    json.dump(report, f, ensure_ascii=False, indent=2)
print(f"\nwrote {os.path.join(OUTDIR, 'eval_ablation.json')}")
