#!/usr/bin/env python3
"""
build_lexicon.py — частотный лексикон казахских слов из чистого корпуса.

Из `sentences.txt` (эталонные предложения) считает частоты словоформ. Лексикон
используется модулем исправления:
  • множество валидных форм (что НЕ трогаем / целевые кандидаты),
  • набор основ для морфоанализатора (богаче встроенного словаря),
  • веса частот для ранжирования кандидатов.

Выход: data/kk_lexicon.tsv  (word<TAB>freq, по убыванию частоты).
"""
from __future__ import annotations

import os
import re
import sys
from collections import Counter

WORD_RE = re.compile(r"[Ѐ-ӿ]+")
_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else \
        os.path.join(_BACKEND, "data", "kazakh_spellcheck", "sentences.txt")
    out = sys.argv[2] if len(sys.argv) > 2 else \
        os.path.join(_BACKEND, "data", "kk_lexicon.tsv")

    freq: Counter[str] = Counter()
    n_sent = 0
    with open(src, encoding="utf-8") as f:
        for line in f:
            n_sent += 1
            for w in WORD_RE.findall(line.lower()):
                if len(w) >= 2:
                    freq[w] += 1

    with open(out, "w", encoding="utf-8") as f:
        for w, c in freq.most_common():
            f.write(f"{w}\t{c}\n")

    total = len(freq)
    ge2 = sum(1 for c in freq.values() if c >= 2)
    ge3 = sum(1 for c in freq.values() if c >= 3)
    ge5 = sum(1 for c in freq.values() if c >= 5)
    print(f"предложений: {n_sent:,}")
    print(f"уникальных словоформ: {total:,}")
    print(f"  freq>=2: {ge2:,} | freq>=3: {ge3:,} | freq>=5: {ge5:,}")
    print(f"токенов всего: {sum(freq.values()):,}")
    print(f"→ {out}")
    print("топ-15:", [w for w, _ in freq.most_common(15)])


if __name__ == "__main__":
    main()
