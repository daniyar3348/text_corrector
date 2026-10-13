#!/usr/bin/env python3
"""
demo_pipeline.py — демонстрация сквозного потока «детектор → корректор» на
ORACLE-детекции (позиции ошибок берём из diff corrupted/correct, как будто
детектор идеален). Это ровно то, что делает TransformerModel._run_inference:
позиции ошибок → KazakhCorrector.correct(text, only_positions=...).

Так можно проверить интеграционную обвязку БЕЗ torch (детектор-заглушка =
истинные позиции). Реальный KazRoBERTa-детектор подставит позиции после Colab.
"""
from __future__ import annotations

import json
import os
import sys

_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _BACKEND)
from app.services.kazakh_corrector import KazakhCorrector


def oracle_positions(corrupted: str, correct: str) -> set[int]:
    cw, rw = corrupted.split(), correct.split()
    if len(cw) != len(rw):
        return set()
    return {i for i in range(len(cw)) if cw[i] != rw[i]}


def main():
    path = os.path.join(_BACKEND, "data", "kazakh_spellcheck", "test.jsonl")
    n_show = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    n_eval = int(sys.argv[2]) if len(sys.argv) > 2 else 3000
    c = KazakhCorrector()

    shown = 0
    sent_ok = sent_tot = 0
    for line in open(path, encoding="utf-8"):
        o = json.loads(line)
        if o["clean"]:
            continue
        pos = oracle_positions(o["corrupted"], o["correct"])
        if not pos:
            continue
        fixed = c.correct(o["corrupted"], only_positions=pos)
        sent_tot += 1
        if fixed == o["correct"]:
            sent_ok += 1
        if shown < n_show:
            shown += 1
            mark = "✓" if fixed == o["correct"] else "✗"
            print(f"{mark} вход : {o['corrupted']}")
            print(f"  выход: {fixed}")
            if fixed != o["correct"]:
                print(f"  эталон:{o['correct']}")
            print()
        if sent_tot >= n_eval:
            break

    print(f"Sentence-level (oracle-детекция): {sent_ok}/{sent_tot} = "
          f"{100*sent_ok/sent_tot:.1f}% предложений исправлены ПОЛНОСТЬЮ верно")


if __name__ == "__main__":
    main()
