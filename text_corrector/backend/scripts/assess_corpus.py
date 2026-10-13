#!/usr/bin/env python3
"""
assess_corpus.py — оценка «грамотности» казахского корпуса перед тем, как
использовать его как эталон (ground truth) для синтетического датасета.

Идея: синтетический подход (инъекция ошибок в чистый текст) верен только если
исходные предложения действительно чистые. Здесь мы это измеряем БЕЗ словаря,
на лексиконо-независимых сигналах казахской фонетики и письма:

  1. Сингармонизм (vowel harmony) — все «сильные» гласные слова одного ряда.
     Это закон казахской фонетики; нарушают его в основном заимствования,
     сложные слова и ОШИБКИ. Высокий % гармоничных слов => корпус чистый.
  2. Чистота письма — нет латиницы/мусора внутри слов.
  3. Покрытие морфоанализатором проекта — справочно, с оговоркой (словарь
     крошечный + только именная парадигма, поэтому низкий % это норма).

Файл читается ПОТОКОВО (первые N статей), чтобы не грузить 568 МБ целиком и
пережить ещё не докачанный файл.
"""
from __future__ import annotations

import json
import os
import re
import sys
from collections import Counter

# ── make project morphology importable ─────────────────────────────────────────
BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND)

# ── Kazakh letter inventories ──────────────────────────────────────────────────
KK_SPECIAL = set("әғқңөұүһі")          # 9 спецбукв казахского
# «Сильные» гласные, задающие ряд (сингармонизм). и/у/э трактуем как нейтральные,
# чтобы не штрафовать слова вроде «университет», где они ведут себя смешанно.
BACK_STRONG = set("аоұы")
FRONT_STRONG = set("әеөүі")
NEUTRAL_V = set("иуэ")
ALL_VOWELS = BACK_STRONG | FRONT_STRONG | NEUTRAL_V
CYR = set("абвгдеёжзийклмнопрстуфхцчшщъыьэюя") | KK_SPECIAL
LATIN = re.compile(r"[a-z]", re.I)

WORD_RE = re.compile(r"[Ѐ-ӿ]+")
SENT_SPLIT = re.compile(r"(?<=[.!?…])\s+")

# фильтр предложений (тот же, что пойдёт в билдер)
MIN_CHARS, MAX_CHARS, MIN_WORDS = 25, 300, 5

CAPTION_RE = re.compile(r"^(сурет|фото|видео|дереккөз|дереккөзі|автор|photo|каз|kaz)\b[:\-—.]?", re.I)


def clean_text(t: str) -> str:
    t = t.replace("\xa0", " ").replace("​", "").replace(" ", " ").replace("﻿", "")
    lines = []
    for ln in t.split("\n"):
        s = ln.strip()
        if not s:
            continue
        low = s.lower()
        if CAPTION_RE.match(s):
            continue
        if "instagram" in low or "facebook" in low or "t.me" in low or low.startswith("http"):
            continue
        lines.append(s)
    return "\n".join(lines)


def split_sentences(t: str):
    for para in t.split("\n"):
        para = para.strip()
        if not para:
            continue
        for p in SENT_SPLIT.split(para):
            p = re.sub(r"\s+", " ", p).strip()
            if p:
                yield p


def is_kazakh_sentence(s: str) -> bool:
    n = len(s)
    if n < MIN_CHARS or n > MAX_CHARS:
        return False
    words = WORD_RE.findall(s)
    if len(words) < MIN_WORDS:
        return False
    if not any(ch in KK_SPECIAL for ch in s.lower()):
        return False
    letters = [c.lower() for c in s if c.isalpha()]
    if not letters:
        return False
    cyr = sum(1 for c in letters if c in CYR)
    if cyr / len(letters) < 0.85:
        return False
    digits = sum(1 for c in s if c.isdigit())
    if digits / n > 0.15:
        return False
    return True


def word_is_harmonic(w: str):
    """(harmonic?, has_strong_vowels?) — гармоничность по сильным гласным."""
    classes = set()
    for ch in w:
        if ch in BACK_STRONG:
            classes.add("back")
        elif ch in FRONT_STRONG:
            classes.add("front")
    return (len(classes) <= 1, len(classes) >= 1)


def iter_json_array(path: str, max_items: int):
    """Потоково отдаёт первые max_items объектов из JSON-массива, терпит обрыв."""
    dec = json.JSONDecoder()
    with open(path, "r", encoding="utf-8") as f:
        buf = f.read(1 << 20)
        i = buf.find("[")
        while i == -1:
            more = f.read(1 << 20)
            if not more:
                return
            buf += more
            i = buf.find("[")
        buf = buf[i + 1:]
        count = 0
        while count < max_items:
            s = buf.lstrip()
            buf = s
            if not buf:
                more = f.read(1 << 20)
                if not more:
                    break
                buf += more
                continue
            if buf[0] == ",":
                buf = buf[1:]
                continue
            if buf[0] == "]":
                break
            try:
                obj, end = dec.raw_decode(buf)
            except json.JSONDecodeError:
                more = f.read(1 << 20)
                if not more:
                    break
                buf += more
                continue
            yield obj
            count += 1
            buf = buf[end:]


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else \
        "/Users/daniyar/Desktop/Turan_project/merged_dissertation.json"
    n_articles = int(sys.argv[2]) if len(sys.argv) > 2 else 3000
    max_sents = int(sys.argv[3]) if len(sys.argv) > 3 else 20000

    # optional: project morphology coverage (with caveat)
    analyze_cov = None
    try:
        from app.services.morphology import is_analyzable
        from app.services.text_correction import _KZ_STEMS
        analyze_cov = (is_analyzable, _KZ_STEMS)
    except Exception as e:
        print(f"[i] морфоанализатор проекта не подключён ({e}); метрику покрытия пропускаю")

    sents = []
    seen = set()
    for art in iter_json_array(path, n_articles):
        txt = art.get("text") if isinstance(art, dict) else None
        if not txt:
            continue
        for s in split_sentences(clean_text(txt)):
            if is_kazakh_sentence(s):
                key = s.lower()
                if key not in seen:
                    seen.add(key)
                    sents.append(s)
        if len(sents) >= max_sents:
            break

    if not sents:
        print("Не нашёл подходящих предложений — проверь путь/файл.")
        return

    # ── метрики ────────────────────────────────────────────────────────────────
    tot_tokens = 0
    harmonic_tokens = 0
    strong_tokens = 0
    fully_harmonic_sents = 0
    latin_word_tokens = 0
    nonharm_counter = Counter()
    latin_examples = Counter()
    cov_ok = cov_tot = 0

    for s in sents:
        words = WORD_RE.findall(s)
        sent_ok = True
        for w in words:
            wl = w.lower()
            tot_tokens += 1
            harm, has_strong = word_is_harmonic(wl)
            if has_strong:
                strong_tokens += 1
                if harm:
                    harmonic_tokens += 1
                else:
                    sent_ok = False
                    nonharm_counter[wl] += 1
            if LATIN.search(w):
                latin_word_tokens += 1
                latin_examples[w] += 1
            if analyze_cov is not None and len(wl) >= 3:
                cov_tot += 1
                try:
                    if analyze_cov[0](wl, analyze_cov[1]):
                        cov_ok += 1
                except Exception:
                    pass
        if sent_ok:
            fully_harmonic_sents += 1

    def pct(a, b):
        return f"{100*a/b:.1f}%" if b else "n/a"

    print("=" * 72)
    print("ОЦЕНКА ГРАМОТНОСТИ КОРПУСА (выборка из начала файла)")
    print("=" * 72)
    print(f"Статей просмотрено (поток):   {n_articles}")
    print(f"Чистых KK-предложений:        {len(sents)}")
    print(f"Слов (токенов) всего:         {tot_tokens}")
    print("-" * 72)
    print("СИНГАРМОНИЗМ (главный сигнал, без словаря)")
    print(f"  Слов с сильными гласными:   {strong_tokens} ({pct(strong_tokens, tot_tokens)} от всех)")
    print(f"  Гармоничных среди них:      {pct(harmonic_tokens, strong_tokens)}")
    print(f"  Полностью гармоничных предложений: {pct(fully_harmonic_sents, len(sents))}")
    print("-" * 72)
    print("ЧИСТОТА ПИСЬМА")
    print(f"  Слов с латиницей внутри:    {latin_word_tokens} ({pct(latin_word_tokens, tot_tokens)})")
    if analyze_cov is not None:
        print("-" * 72)
        print("ПОКРЫТИЕ МОРФОАНАЛИЗАТОРОМ ПРОЕКТА (справочно!)")
        print(f"  is_analyzable: {pct(cov_ok, cov_tot)}  "
              f"(низко — это НОРМА: словарь ~сотни слов + только именная парадигма)")
    print("-" * 72)
    print("ТОП-25 НЕГАРМОНИЧНЫХ СЛОВ (заимствования/сложные/ошибки?):")
    for w, c in nonharm_counter.most_common(25):
        print(f"    {c:5d}  {w}")
    if latin_examples:
        print("-" * 72)
        print("ПРИМЕРЫ СЛОВ С ЛАТИНИЦЕЙ:")
        for w, c in latin_examples.most_common(15):
            print(f"    {c:5d}  {w}")
    print("-" * 72)
    print("15 СЛУЧАЙНЫХ ПРЕДЛОЖЕНИЙ (глазами оценить читаемость):")
    step = max(1, len(sents) // 15)
    for s in sents[::step][:15]:
        print(f"  • {s}")
    print("=" * 72)


if __name__ == "__main__":
    main()
