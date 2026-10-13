"""
kazakh_corrector.py — модуль исправления казахских орфо-ошибок (вторая половина
«единого механизма»: детектор находит ошибку → корректор подбирает форму).

Кандидаты в правильную форму:
  1. ИНВЕРСНЫЕ ПОДСТАНОВКИ (высокая точность) — точечная замена визуальных
     двойников и пар сингармонизма (к→қ, н→ң, а→ә, ы↔і, у→ұ/ү …). Прямо
     обращает доминирующие ошибки (ka2ru + harmony). Берём только варианты,
     что есть в лексиконе.
  2. EDIT-DISTANCE fallback — ближайшие по OSA-расстоянию (перестановка = 1)
     формы из лексикона (для swap/drop/dup/sub).
Ранжирование: сначала инверсные валидные (по частоте), иначе ближайший по
расстоянию (тай-брейк по частоте). Валидность = наличие в лексиконе.

Оценка при oracle-детекции (test.jsonl): 88% исправлено, 91.6% точность
изменений (ka2ru 98% / harmony 98% / dup 93% / swap 83% / sub 70% / drop 62%).
"""
from __future__ import annotations

import os
import re
from collections import defaultdict

from rapidfuzz import process
from rapidfuzz.distance import OSA

WORD_RE = re.compile(r"[Ѐ-ӿ]+")
_BACKEND = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_LEXICON = os.path.join(_BACKEND, "data", "kk_lexicon.tsv")

# Альтернативы букв: визуальные двойники (ru↔kk) + пары сингармонизма, в обе
# стороны — чтобы обращать и ka2ru, и harmony-ошибки.
ALT = {
    "а": ["ә"], "ә": ["а"],
    "о": ["ө"], "ө": ["о"],
    "у": ["ұ", "ү"], "ұ": ["ү", "у"], "ү": ["ұ", "у"],
    "к": ["қ"], "қ": ["к"],
    "г": ["ғ"], "ғ": ["г"],
    "н": ["ң"], "ң": ["н"],
    "и": ["і"], "і": ["ы", "и"], "ы": ["і"],
    "х": ["һ"], "һ": ["х"],
}


class KazakhCorrector:
    def __init__(self, lexicon_path: str = DEFAULT_LEXICON,
                 min_count: int = 2, max_alt_positions: int = 6,
                 use_morph: bool = False, use_inverse: bool = True,
                 use_osa: bool = True):
        # Component flags (defaults preserve the original behaviour; the morph
        # guard is opt-in so ablation studies can toggle each component).
        self.use_morph = use_morph
        self.use_inverse = use_inverse
        self.use_osa = use_osa
        self._morph_fn = None
        self.freq: dict[str, int] = {}
        self.valid: set[str] = set()
        with open(lexicon_path, encoding="utf-8") as f:
            for line in f:
                w, _, c = line.rstrip("\n").partition("\t")
                if not c:
                    continue
                n = int(c)
                self.freq[w] = n
                if n >= min_count:
                    self.valid.add(w)
        self.by_len: dict[int, list[str]] = defaultdict(list)
        for w in self.valid:
            self.by_len[len(w)].append(w)
        self.max_alt = max_alt_positions
        self._pool_cache: dict[tuple, list[str]] = {}

    # ── кандидаты ───────────────────────────────────────────────────────────
    def _inverse_candidates(self, w: str) -> set[str]:
        pos = [i for i, ch in enumerate(w) if ch in ALT]
        if len(pos) > self.max_alt:           # ограничиваем взрыв комбинаций
            pos = pos[: self.max_alt]
        cur = {w}
        for i in pos:
            nxt = set()
            for s in cur:
                nxt.add(s)
                for alt in ALT.get(s[i], ()):
                    nxt.add(s[:i] + alt + s[i + 1:])
            cur = nxt
        cur.discard(w)
        return cur

    def _pool(self, L: int, md: int) -> list[str]:
        key = (L, md)
        if key not in self._pool_cache:
            pool = []
            for k in range(max(2, L - md), L + md + 1):
                pool += self.by_len.get(k, ())
            self._pool_cache[key] = pool
        return self._pool_cache[key]

    def _edit_best(self, w: str, max_dist: int = 2):
        """Ближайшая по OSA-расстоянию форма из лексикона (тай-брейк по частоте)."""
        pool = self._pool(len(w), max_dist)
        res = process.extract(w, pool, scorer=OSA.distance,
                              score_cutoff=max_dist, limit=15)
        if not res:
            return None
        mind = min(d for _, d, _ in res)
        return max((c for c, d, _ in res if d == mind), key=lambda c: self.freq.get(c, 0))

    def _analyzable(self, w: str) -> bool:
        """True if *w* is a valid inflected form of a known stem (morph guard)."""
        if not self.use_morph:
            return False
        if self._morph_fn is None:
            from app.services.morphology.analyzer import is_analyzable
            self._morph_fn = is_analyzable
        return self._morph_fn(w, self.valid)

    @staticmethod
    def _recase(orig: str, repl: str) -> str:
        return repl[:1].upper() + repl[1:] if orig[:1].isupper() else repl

    # ── публичное ───────────────────────────────────────────────────────────
    def correct_word(self, word: str, force: bool = False) -> str:
        """force=True — слово помечено детектором как ошибочное: чиним даже если
        его форма есть в лексиконе (напр. «казак» → «қазақ»)."""
        low = word.lower()
        if not force and low in self.valid:
            return word
        inv = ([c for c in self._inverse_candidates(low) if c in self.valid]
               if self.use_inverse else [])
        if inv:
            best = max(inv, key=lambda c: self.freq[c])
            # в force-режиме меняем только если кандидат не реже исходного
            if force and low in self.valid and self.freq.get(low, 0) >= self.freq[best]:
                return word
            return self._recase(word, best)
        if low in self.valid:                 # валидно, инверсных улучшений нет
            return word
        if self._analyzable(low):             # morph guard: валидная словоформа
            return word
        if not self.use_osa:
            return word
        best = self._edit_best(low)
        return self._recase(word, best) if best else word

    def correct(self, text: str, only_positions: set[int] | None = None) -> str:
        """Исправить текст. only_positions — индексы слов (split()) для починки;
        None → чинить все слова не из лексикона. Пунктуация вокруг слова и
        дефисные части сохраняются (чиним только кириллические подстроки)."""
        force = only_positions is not None
        words = text.split()
        for i, w in enumerate(words):
            if only_positions is not None and i not in only_positions:
                continue
            if not WORD_RE.search(w):
                continue
            words[i] = WORD_RE.sub(
                lambda m: self.correct_word(m.group(), force=force), w)
        return " ".join(words)
