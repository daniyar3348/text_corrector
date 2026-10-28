#!/usr/bin/env python3
"""
eval_corrector.py — оценка модуля исправления на test.jsonl при ORACLE-детекции.

Для каждой правки в `edits` известны искажённый токен (after), правильный (before)
и тип ошибки. Подаём искажённый токен корректору (force=True) и смотрим, получим
ли правильный. Метрики по типам ошибок и в целом:
  fixed     — исправил верно (pred == before)
  unchanged — не тронул (pred == after)
  wrong     — изменил, но неверно (pred != before, != after)
Это «потолок» исправления (детекция идеальна) — отделяет качество корректора
от качества детектора.
"""
from __future__ import annotations

import json
import os
import sys
import time
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kk_corrector import KazakhCorrector

_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    path = os.path.join(_BACKEND, "data", "kazakh_spellcheck", "test.jsonl")
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    c = KazakhCorrector()
    print(f"лексикон: {len(c.valid):,} валидных форм")

    by_type = defaultdict(Counter)
    overall = Counter()
    t0 = time.time()
    n = 0
    for line in open(path, encoding="utf-8"):
        o = json.loads(line)
        if o["clean"]:
            continue
        n += 1
        for e in o["edits"]:
            before, after, typ = e["before"], e["after"], e["type"]
            pred = c.correct_word(after, force=True)
            key = "fixed" if pred == before else ("unchanged" if pred == after else "wrong")
            overall[key] += 1
            overall["total"] += 1
            by_type[typ][key] += 1
            by_type[typ]["total"] += 1
        if limit and n >= limit:
            break

    def row(name, c_):
        t = c_["total"]
        fx = c_["fixed"]
        chg = c_["fixed"] + c_["wrong"]
        rec = 100 * fx / t if t else 0
        prec = 100 * fx / chg if chg else 0
        return (f"  {name:10s} n={t:7d} | fixed {rec:5.1f}% | "
                f"unchanged {100*c_['unchanged']/t:5.1f}% | wrong {100*c_['wrong']/t:5.1f}% | "
                f"precision(изменений) {prec:5.1f}%")

    print(f"\nОЦЕНКА КОРРЕКТОРА (oracle-детекция), записей={n:,}, "
          f"правок={overall['total']:,}, {time.time()-t0:.0f}s")
    print("по типам ошибок:")
    for typ in sorted(by_type, key=lambda k: -by_type[k]["total"]):
        print(row(typ, by_type[typ]))
    print("ИТОГО:")
    print(row("all", overall))


if __name__ == "__main__":
    main()
