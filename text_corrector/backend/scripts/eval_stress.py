#!/usr/bin/env python3
"""
eval_stress.py — стресс-тесты детектора KazRoBERTa за пределами тестового
распределения (цифры для блока «Результаты модели» на сайте).

  [A] как в обучении: P/R/F1, ложные срабатывания, полнота по типам ошибок
  [B] весь текст на русской раскладке (все казахские буквы заменены русскими)
  [C] слово без контекста против того же слова в предложении
  [D] несколько предложений за один проход модели
  [E] шум ka2ru в эталонной стороне данных

    N=8000 python backend/scripts/eval_stress.py      (нужны torch и transformers)
"""
import json
import os
import sys
import time
from collections import Counter, defaultdict

import torch
from transformers import AutoModelForTokenClassification, AutoTokenizer

W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # backend/
sys.path.insert(0, W)
from app.services.kazakh_corrector import KazakhCorrector  # noqa: E402

MDIR = os.path.join(W, "models", "kazakh_detector")
TEST = os.path.join(W, "data", "kazakh_spellcheck", "test.jsonl")
N = int(os.environ.get("N", 8000))

tok = AutoTokenizer.from_pretrained(MDIR, use_fast=True)
mdl = AutoModelForTokenClassification.from_pretrained(MDIR).eval()
torch.manual_seed(0)


def word_probs(words):
    """P(ERROR) for each word (first sub-token), None if truncated away."""
    enc = tok(words, is_split_into_words=True, truncation=True,
              max_length=512, return_tensors="pt")
    with torch.no_grad():
        p = mdl(**enc).logits[0].softmax(-1)[:, 1].tolist()
    out, prev = [None] * len(words), None
    for i, wid in enumerate(enc.word_ids(0)):
        if wid is None or wid == prev:
            prev = wid
            continue
        prev = wid
        out[wid] = p[i]
    return out


def prf(tp, fp, fn):
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    return p * 100, r * 100, (2 * p * r / (p + r) * 100 if p + r else 0.0)


recs = []
for line in open(TEST, encoding="utf-8"):
    o = json.loads(line)
    cw, rw = o["corrupted"].split(), o["correct"].split()
    if len(cw) == len(rw):
        recs.append(o)
    if len(recs) >= N:
        break

t0 = time.time()
# ── A. In-distribution: per error type + calibration ─────────────────────────
tp = fp = fn = 0
type_hit, type_tot = Counter(), Counter()
clean_words = clean_fp = 0
bins = Counter()
in_ctx = {}  # (rec_idx, word_idx) -> prob, for erroneous words
for ri, o in enumerate(recs):
    cw, rw = o["corrupted"].split(), o["correct"].split()
    probs = word_probs(cw)
    etype = {e["wi"]: e["type"] for e in o["edits"]}
    for i, (a, b, p) in enumerate(zip(cw, rw, probs)):
        pred = p is not None and p > 0.5
        gold = a != b
        bins[min(int((p or 0) * 10), 9)] += 1
        if gold:
            in_ctx[(ri, i)] = p or 0
            t = etype.get(i, "?")
            type_tot[t] += 1
            type_hit[t] += pred
        else:
            clean_words += 1
            clean_fp += pred
        tp += pred and gold
        fp += pred and not gold
        fn += (not pred) and gold
P, R, F = prf(tp, fp, fn)
print(f"[A] in-distribution ({len(recs)} sent.): P {P:.1f} R {R:.1f} F1 {F:.1f} | "
      f"false alarms on correct words: {clean_fp}/{clean_words} = {100*clean_fp/clean_words:.2f}%")
print("    recall by error type: " + ", ".join(
    f"{t} {100*type_hit[t]/type_tot[t]:.1f}% (n={type_tot[t]})" for t in sorted(type_tot, key=lambda t: -type_tot[t])))
total = sum(bins.values())
unsure = sum(bins[b] for b in range(2, 8))
print(f"    calibration: {100*unsure/total:.2f}% of word scores fall in 0.2–0.8 (rest are confident)")

# ── B. Fully russified sentences (Russian keyboard, every Kazakh letter lost) ─
RU = str.maketrans("әөұүқғңіһӘӨҰҮҚҒҢІҺ", "аоуукгнихАОУУКГНИХ")
c = KazakhCorrector()
tp = fp = fn = 0
ok = tot = 0
dens = []
for o in recs[:1500]:
    gold_s = o["correct"]
    bad_s = gold_s.translate(RU)
    if bad_s == gold_s:
        continue
    gw, bw = gold_s.split(), bad_s.split()
    probs = word_probs(bw)
    pos = {i for i, p in enumerate(probs) if p is not None and p > 0.5}
    gold = {i for i in range(len(bw)) if bw[i] != gw[i]}
    dens.append(len(gold) / len(bw))
    tp += len(pos & gold); fp += len(pos - gold); fn += len(gold - pos)
    tot += 1
    ok += c.correct(bad_s, only_positions=pos) == gold_s
P, R, F = prf(tp, fp, fn)
print(f"[B] fully russified ({tot} sent., avg {100*sum(dens)/len(dens):.0f}% of words broken): "
      f"P {P:.1f} R {R:.1f} F1 {F:.1f} | whole sentence fixed: {100*ok/tot:.1f}%")

# ── C. Short input: erroneous word alone vs. in its sentence ─────────────────
alone_hit = ctx_hit = n = 0
for (ri, wi), p_ctx in list(in_ctx.items())[:3000]:
    w = recs[ri]["corrupted"].split()[wi]
    p_alone = word_probs([w])[0] or 0
    alone_hit += p_alone > 0.5
    ctx_hit += p_ctx > 0.5
    n += 1
print(f"[C] short input: recall in context {100*ctx_hit/n:.1f}% → same word alone {100*alone_hit/n:.1f}% (n={n})")

# ── D. Several sentences in one pass ─────────────────────────────────────────
for k in (1, 3, 6, 10):
    tp = fp = fn = 0
    for s in range(0, min(1200, len(recs)) - k + 1, k):
        group = recs[s:s + k]
        cw = sum((g["corrupted"].split() for g in group), [])
        rw = sum((g["correct"].split() for g in group), [])
        probs = word_probs(cw)
        for a, b, p in zip(cw, rw, probs):
            pred = p is not None and p > 0.5
            gold = a != b
            tp += pred and gold; fp += pred and not gold; fn += (not pred) and gold
    P, R, F = prf(tp, fp, fn)
    print(f"[D] {k:2d} sentence(s) per pass: P {P:.1f} R {R:.1f} F1 {F:.1f}")

# ── E. Noise in the "correct" side of the data ───────────────────────────────
noisy = words = 0
examples = Counter()
for o in recs:
    for w in o["correct"].split():
        core = "".join(ch for ch in w.lower() if ch.isalpha())
        if not core:
            continue
        words += 1
        v = c._shadow_variant(core)
        if v:
            noisy += 1
            examples[(core, v)] += 1
print(f"[E] gold-side ka2ru noise: {noisy}/{words} words = {100*noisy/words:.2f}% "
      f"(rare form with a ≥20× more frequent Kazakh spelling); e.g. "
      + ", ".join(f"{a}→{b}" for (a, b), _ in examples.most_common(8)))
print(f"done in {time.time()-t0:.0f}s")
