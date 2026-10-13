#!/usr/bin/env python3
"""
eval_full.py — rigorous evaluation for the paper: FULL 25k test split, three
detection modes (heuristic / model / oracle) in one pass, bootstrap 95% CIs,
clean-pair-excluded end-to-end, and per-error-type corrector accuracy with CIs.

Writes a JSON report to backend/data/eval/eval_full.json and prints a summary.
Run from backend/ with the torch venv:
  KAZAKH_MODEL_PATH=$PWD/models/kazakh_detector ./.venv-train/bin/python scripts/eval_full.py
"""
from __future__ import annotations
import json, os, sys, time
import numpy as np

_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _BACKEND)
from app.services.kazakh_corrector import WORD_RE, KazakhCorrector

TEST = os.path.join(_BACKEND, "data", "kazakh_spellcheck", "test.jsonl")
OUTDIR = os.path.join(_BACKEND, "data", "eval")
os.makedirs(OUTDIR, exist_ok=True)
RNG = np.random.default_rng(42)
B = 1000  # bootstrap resamples

c = KazakhCorrector()

def detect_heuristic(words):
    return {i for i, w in enumerate(words)
            if (m := WORD_RE.search(w)) and m.group().lower() not in c.valid}

# model detector
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

MODES = ["heuristic", "model", "oracle"]
# per-sentence records: for each mode (tp,fp,fn, fixed_bool); plus clean_bool
rec = {m: {"tp": [], "fp": [], "fn": [], "fixed": []} for m in MODES}
clean_flags = []
# per-edit-type (oracle/force): list of (type, fixed_bool, changed_bool)
edits_rec = []
skipped = 0
n = 0
t0 = time.time()
for line in open(TEST, encoding="utf-8"):
    o = json.loads(line)
    cw, rw = o["corrupted"].split(), o["correct"].split()
    if len(cw) != len(rw):
        skipped += 1
        continue
    n += 1
    true_err = {i for i in range(len(cw)) if cw[i] != rw[i]}
    mpred = detect_model(cw)
    preds = {"heuristic": detect_heuristic(cw), "model": mpred, "oracle": set(true_err)}
    for m in MODES:
        p = preds[m]
        rec[m]["tp"].append(len(p & true_err))
        rec[m]["fp"].append(len(p - true_err))
        rec[m]["fn"].append(len(true_err - p))
        rec[m]["fixed"].append(1 if c.correct(o["corrupted"], only_positions=p) == o["correct"] else 0)
    clean_flags.append(1 if o["clean"] else 0)
    for e in o["edits"]:
        pred = c.correct_word(e["after"], force=True)
        edits_rec.append((e["type"], 1 if pred == e["before"] else 0,
                          0 if pred == e["after"] else 1))
    if n % 2000 == 0:
        print(f"  {n} sentences, {time.time()-t0:.0f}s", flush=True)

print(f"processed {n} sentences ({skipped} skipped for word-count mismatch), {time.time()-t0:.0f}s", flush=True)

clean = np.array(clean_flags)
nonclean_idx = np.where(clean == 0)[0]

def prf(tp, fp, fn):
    p = 100*tp/(tp+fp) if tp+fp else 0.0
    r = 100*tp/(tp+fn) if tp+fn else 0.0
    f = 2*p*r/(p+r) if p+r else 0.0
    return p, r, f

def ci(vals):
    lo, hi = np.percentile(vals, [2.5, 97.5])
    return round(float(lo), 2), round(float(hi), 2)

report = {"n": n, "skipped": skipped, "modes": {}}
idx_all = np.arange(n)
for m in MODES:
    tp = np.array(rec[m]["tp"]); fp = np.array(rec[m]["fp"]); fn = np.array(rec[m]["fn"])
    fixed = np.array(rec[m]["fixed"])
    P, R, F = prf(tp.sum(), fp.sum(), fn.sum())
    e2e_all = 100*fixed.mean()
    e2e_nc = 100*fixed[nonclean_idx].mean()
    # bootstrap
    f1s, e2eas, e2encs = [], [], []
    for _ in range(B):
        s = RNG.integers(0, n, n)
        _, _, f = prf(tp[s].sum(), fp[s].sum(), fn[s].sum())
        f1s.append(f); e2eas.append(100*fixed[s].mean())
        snc = s[clean[s] == 0]
        e2encs.append(100*fixed[snc].mean() if len(snc) else 0.0)
    report["modes"][m] = {
        "detection": {"P": round(P, 2), "R": round(R, 2), "F1": round(F, 2),
                       "F1_CI": ci(f1s), "fp_total": int(fp.sum())},
        "e2e_all": {"pct": round(e2e_all, 2), "CI": ci(e2eas)},
        "e2e_nonclean": {"pct": round(e2e_nc, 2), "CI": ci(e2encs)},
    }

# per-error-type at oracle/force
types = ["ka2ru", "harmony", "swap", "drop", "dup", "sub"]
et = np.array([t for t, _, _ in edits_rec], dtype=object)
ef = np.array([f for _, f, _ in edits_rec])
ech = np.array([ch for _, _, ch in edits_rec])
pertype = {}
for ty in types:
    mask = et == ty
    nt = int(mask.sum())
    fx = 100*ef[mask].mean() if nt else 0.0
    idx = np.where(mask)[0]
    boot = [100*ef[RNG.choice(idx, len(idx))].mean() for _ in range(B)] if nt else [0]
    pertype[ty] = {"n": nt, "fixed_pct": round(fx, 2), "CI": ci(boot)}
overall_fixed = 100*ef.mean()
overall_prec = 100*ef.sum()/max(1, ech.sum())
report["corrector_oracle"] = {"overall_fixed_pct": round(overall_fixed, 2),
                              "overall_precision_pct": round(overall_prec, 2),
                              "per_type": pertype, "n_edits": int(len(ef))}

with open(os.path.join(OUTDIR, "eval_full.json"), "w", encoding="utf-8") as f:
    json.dump(report, f, ensure_ascii=False, indent=2)

# print summary
print("\n==== DETECTION & END-TO-END (95% bootstrap CI) ====")
for m in MODES:
    d = report["modes"][m]
    print(f"{m:9s} det F1 {d['detection']['F1']:.1f}% (P{d['detection']['P']:.1f}/R{d['detection']['R']:.1f}, fp={d['detection']['fp_total']}) "
          f"CI{d['detection']['F1_CI']} | E2E all {d['e2e_all']['pct']:.1f}% CI{d['e2e_all']['CI']} | "
          f"E2E no-clean {d['e2e_nonclean']['pct']:.1f}% CI{d['e2e_nonclean']['CI']}")
print("\n==== CORRECTOR PER TYPE (oracle) ====")
for ty in types:
    p = report["corrector_oracle"]["per_type"][ty]
    print(f"{ty:8s} n={p['n']:6d} fixed {p['fixed_pct']:.1f}% CI{p['CI']}")
print(f"OVERALL  fixed {overall_fixed:.1f}% | precision-of-changes {overall_prec:.1f}% | edits={len(ef)}")
print(f"\nwrote {os.path.join(OUTDIR,'eval_full.json')}")
