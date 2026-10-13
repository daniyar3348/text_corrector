#!/usr/bin/env python3
"""
eval_end2end.py — сквозная оценка системы исправления (детектор + корректор).

Поддерживает два детектора:
  • heuristic (по умолчанию) — слово ошибочно, если его кириллическое ядро не
    входит в лексикон. Работает БЕЗ модели → это рабочая базовая система прямо
    сейчас и нижняя планка, которую должен превзойти обученный KazRoBERTa.
  • oracle — истинные позиции ошибок (потолок корректора).

Метрики на test.jsonl:
  • Детекция: precision / recall / F1 по словам-ошибкам (+ ложные срабатывания
    на чистых словах — риск переисправления).
  • Сквозь: доля предложений, исправленных ПОЛНОСТЬЮ верно.
"""
from __future__ import annotations

import json
import os
import sys
import time

_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _BACKEND)
from app.services.kazakh_corrector import WORD_RE, KazakhCorrector


def main():
    path = os.path.join(_BACKEND, "data", "kazakh_spellcheck", "test.jsonl")
    mode = sys.argv[1] if len(sys.argv) > 1 else "heuristic"
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 8000
    c = KazakhCorrector()

    def detect_heuristic(words):
        pos = set()
        for i, w in enumerate(words):
            m = WORD_RE.search(w)
            if m and m.group().lower() not in c.valid:
                pos.add(i)
        return pos

    detect = detect_heuristic
    if mode == "model":
        import torch
        from transformers import AutoModelForTokenClassification, AutoTokenizer
        mdir = os.environ.get(
            "KAZAKH_MODEL_PATH",
            os.path.join(_BACKEND, "models", "kazakh_detector"),
        )
        tok = AutoTokenizer.from_pretrained(mdir, use_fast=True)
        mdl = AutoModelForTokenClassification.from_pretrained(mdir).eval()

        def detect_model(words):
            enc = tok(words, is_split_into_words=True, truncation=True,
                      max_length=512, return_tensors="pt")
            with torch.no_grad():
                preds = mdl(**enc).logits[0].argmax(-1).tolist()
            pos, prev = set(), None
            for i, wid in enumerate(enc.word_ids(0)):
                if wid is None or wid == prev:
                    prev = wid
                    continue
                prev = wid
                if preds[i] == 1:
                    pos.add(wid)
            return pos
        detect = detect_model

    tp = fp = fn = 0
    sent_ok = sent_tot = 0
    t0 = time.time()
    n = 0
    for line in open(path, encoding="utf-8"):
        o = json.loads(line)
        cw, rw = o["corrupted"].split(), o["correct"].split()
        if len(cw) != len(rw):
            continue
        n += 1
        true_err = {i for i in range(len(cw)) if cw[i] != rw[i]}
        pred = true_err if mode == "oracle" else detect(cw)
        tp += len(pred & true_err)
        fp += len(pred - true_err)
        fn += len(true_err - pred)
        fixed = c.correct(o["corrupted"], only_positions=pred)
        sent_tot += 1
        if fixed == o["correct"]:
            sent_ok += 1
        if n >= limit:
            break

    prec = 100 * tp / (tp + fp) if tp + fp else 0
    rec = 100 * tp / (tp + fn) if tp + fn else 0
    f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0
    print(f"режим детекции: {mode} | записей: {sent_tot:,} | {time.time()-t0:.0f}s")
    print(f"ДЕТЕКЦИЯ слов-ошибок: precision {prec:.1f}% | recall {rec:.1f}% | "
          f"F1 {f1:.1f}%  (ложных срабатываний fp={fp:,})")
    print(f"СКВОЗЬ: {sent_ok:,}/{sent_tot:,} = {100*sent_ok/sent_tot:.1f}% "
          f"предложений исправлены ПОЛНОСТЬЮ верно")


if __name__ == "__main__":
    main()
