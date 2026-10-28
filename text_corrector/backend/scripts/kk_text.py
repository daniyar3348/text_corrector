#!/usr/bin/env python3
"""
kk_text.py — общий модуль очистки/сегментации казахского текста.

Используется и оценкой корпуса (assess_corpus.py), и сборщиком датасета.
Конвейер на один сырой текст статьи:

    clean_text(raw)            # убрать подписи/ссылки/nbsp + нормализовать двойники
      -> split_sentences(t)    # резать по .!?… в т.ч. «точка+Заглавная без пробела»
         -> strip_foreign(s)   # убрать иноязычные токены/вставки (кириллицу сохранить)
            -> is_clean_kazakh(s)  # финальный строгий фильтр эталона
"""
from __future__ import annotations

import re
import unicodedata

# ── Казахский кириллический алфавит ─────────────────────────────────────────────
KK_SPECIAL = set("әғқңөұүһі")
KK_CYR = set("абвгдеёжзийклмнопрстуфхцчшщъыьэюя") | KK_SPECIAL
KK_UPPER = "А-ЯЁӘҒҚҢӨҰҮҺІ"
KK_LOWER = "а-яёәғқңөұүһі"

# ── (2) Нормализация букв-двойников (высокая точность) ──────────────────────────
# Только систематические подмены в КАЗАХСКИХ словах. Иноязычные слова целиком
# (Twórczość, Sakaoğlı) сюда не попадают — их снимет strip_foreign().
LOOKALIKE = str.maketrans({
    "ə": "ә", "Ə": "Ә",   # LATIN SMALL/CAPITAL SCHWA  → ә/Ә  (жəне→және)
    "ћ": "һ", "Ћ": "Һ",   # CYRILLIC TSHE              → һ/Һ  (Жаћангер→Жаһангер)
})

# ── Гласные для проверки сингармонизма (без словаря) ───────────────────────────
BACK_STRONG = set("аоұы")
FRONT_STRONG = set("әеөүі")

# ── Регэкспы ────────────────────────────────────────────────────────────────────
WORD_RE = re.compile(r"[Ѐ-ӿ]+")
# Невидимые/форматирующие символы: мягкий перенос, zero-width, директивные,
# BOM. Убираем (склеивают «яғ­ни»→«яғни»); обычный дефис «-» НЕ трогаем.
INVISIBLE_RE = re.compile("[\u00ad\u200b-\u200f\u202a-\u202e\u2060-\u206f\ue000-\uf8ff\ufeff]")
CAPTION_RE = re.compile(
    r"^(сурет|фото|видео|дереккөз|дереккөзі|автор|фото\s*:|photo|caption)\b[:\-—.]?",
    re.I,
)
# Сегментация в два шага:
#   RUNON_FIX — вставить разрыв в «склейке» (точка+Заглавная без пробела),
#               допуская закрывающие кавычки/скобки (они остаются в левом
#               предложении). Требование «2 строчные перед знаком» защищает
#               инициалы (Н.К) и сокращения (т.б.) от ложного разреза.
#   SPACE_SPLIT — обычная граница: знак конца + пробел + заглавная/кавычка.
RUNON_FIX = re.compile(
    rf"([{KK_LOWER}][{KK_LOWER}][.!?…][»\")\]]*)(?=[{KK_UPPER}])"
)
SPACE_SPLIT = re.compile(rf"(?<=[.!?…])\s+(?=[«\"{KK_UPPER}])")
# скобочные/кавычечные группы (для удаления иноязычных вставок целиком)
BRACKET_RE = re.compile(r"\([^()]*\)|\[[^\[\]]*\]|«[^«»]*»|\"[^\"]*\"")

# фильтр эталонного предложения
MIN_CHARS, MAX_CHARS, MIN_WORDS = 25, 300, 5


def _has_foreign_letter(s: str) -> bool:
    """True, если в строке есть буква вне казахской кириллицы."""
    return any(ch.isalpha() and ch.lower() not in KK_CYR for ch in s)


def clean_text(raw: str) -> str:
    """Убрать служебный мусор + нормализовать двойники. Регистр сохраняется."""
    t = unicodedata.normalize("NFC", raw).translate(LOOKALIKE)
    t = INVISIBLE_RE.sub("", t)
    t = t.replace("\xa0", " ").replace("​", "").replace(" ", " ").replace("﻿", "")
    lines = []
    for ln in t.split("\n"):
        s = ln.strip()
        if not s:
            continue
        low = s.lower()
        if CAPTION_RE.match(s):
            continue
        if low.startswith("http") or "instagram" in low or "facebook" in low or "t.me" in low:
            continue
        lines.append(s)
    return "\n".join(lines)


def split_sentences(t: str):
    """Резать текст на предложения (в т.ч. склейки 'точка+Заглавная')."""
    for para in t.split("\n"):
        para = para.strip()
        if not para:
            continue
        para = RUNON_FIX.sub(r"\1\n", para)   # развести беспробельные склейки
        for chunk in para.split("\n"):
            for p in SPACE_SPLIT.split(chunk):
                p = re.sub(r"\s+", " ", p).strip()
                if p:
                    yield p


def strip_foreign(s: str) -> str:
    """
    (3) Убрать иноязычные вставки, сохранив казахскую кириллицу.

    Шаги: снять скобочные/кавычечные группы с иноязычными буквами целиком →
    выкинуть отдельные иноязычные токены → подчистить пробелы и висячую
    пунктуацию.
    """
    s = BRACKET_RE.sub(lambda m: "" if _has_foreign_letter(m.group()) else m.group(), s)
    toks = [tok for tok in s.split(" ") if not _has_foreign_letter(tok)]
    s = " ".join(toks)
    s = re.sub(r"\(\s*\)|\[\s*\]|«\s*»", "", s)        # пустые скобки
    s = re.sub(r"\s+([,.;:!?…])", r"\1", s)            # пробел перед пунктуацией
    s = re.sub(r"\s{2,}", " ", s).strip()
    s = re.sub(r"^[\s,.;:—\-»)\]]+", "", s)            # висячая пунктуация в начале
    return s


def is_clean_kazakh(s: str) -> bool:
    """Строгий финальный фильтр эталона."""
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
    # после strip_foreign все буквы обязаны быть казахской кириллицей
    if any(c not in KK_CYR for c in letters):
        return False
    if sum(c.isdigit() for c in s) / n > 0.15:
        return False
    return True


def word_is_harmonic(w: str):
    """(гармонично?, есть_сильные_гласные?) по сильным гласным."""
    classes = set()
    for ch in w:
        if ch in BACK_STRONG:
            classes.add("back")
        elif ch in FRONT_STRONG:
            classes.add("front")
    return (len(classes) <= 1, len(classes) >= 1)


def iter_json_array(path: str, max_items: int):
    """Потоково отдаёт первые max_items объектов из JSON-массива (терпит обрыв)."""
    import json
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
            buf = buf.lstrip()
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
            except __import__("json").JSONDecodeError:
                more = f.read(1 << 20)
                if not more:
                    break
                buf += more
                continue
            yield obj
            count += 1
            buf = buf[end:]


def sentences_from_text(raw: str):
    """Полный конвейер: сырой текст → список чистых эталонных предложений."""
    for s in split_sentences(clean_text(raw)):
        s2 = strip_foreign(s)
        if is_clean_kazakh(s2):
            yield s2
