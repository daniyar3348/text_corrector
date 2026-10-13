#!/usr/bin/env python3
"""
kk_corrector.py — тонкий реэкспорт KazakhCorrector.

Каноничный модуль теперь живёт в приложении: app/services/kazakh_corrector.py.
Здесь оставлен реэкспорт для совместимости с scripts/eval_corrector.py и CLI-демо.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.services.kazakh_corrector import (  # noqa: E402,F401
    ALT, DEFAULT_LEXICON, WORD_RE, KazakhCorrector,
)

if __name__ == "__main__":
    c = KazakhCorrector()
    print(f"лексикон: {len(c.valid):,} валидных форм")
    for w in (sys.argv[1:] or ["казак", "мемлекеттык", "олтірген", "шиккен"]):
        print(f"  {w} → {c.correct_word(w, force=True)}")
