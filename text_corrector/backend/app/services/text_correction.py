"""
Dictionary + edit-distance text correction service.

Architecture
------------
* `correct_text(text)`      – language-aware entry point
* `correct_russian(text)`   – Russian-specific pipeline
* `correct_kazakh(text)`    – Kazakh-specific pipeline

Each pipeline:
  1. Tokenises the text into (word, non-word) runs to preserve punctuation
     and spacing exactly.
  2. For every word token, looks it up in the vocabulary set.
     If found  → keep as is.
     If absent → find the best candidate via rapidfuzz edit distance.
  3. Accepts a candidate only if similarity ≥ threshold and edit distance ≤ max.
  4. Returns the corrected string and a list of CorrectionItem dicts.

Replacing with a trained model
--------------------------------
Set RUSSIAN_MODEL_PATH / KAZAKH_MODEL_PATH in .env.
`correction_pipeline.py` will call `TransformerModel.correct()` instead
of calling these functions, so nothing here needs to change.
"""
from __future__ import annotations

import re
from typing import Callable, Dict, List, Optional, Set, Tuple

from rapidfuzz import process as rfprocess
from rapidfuzz import fuzz

from app.core.config import settings
from app.core.logging_config import logger
from app.services.morphology import analyze, is_analyzable

# ═══════════════════════════════════════════════════════════════════════════════
# RUSSIAN VOCABULARY
# ═══════════════════════════════════════════════════════════════════════════════
RUSSIAN_VOCABULARY: Set[str] = {
    # ── Greetings / phrases ──────────────────────────────────────────────────
    "привет", "здравствуйте", "здравствуй", "добрый", "добро",
    "пожалуйста", "спасибо", "прощай", "до", "свидания", "пока", "удачи",
    "добрый", "утро", "день", "вечер",
    # ── Pronouns ─────────────────────────────────────────────────────────────
    "я", "ты", "он", "она", "оно", "мы", "вы", "они",
    "меня", "тебя", "его", "её", "нас", "вас", "их",
    "мне", "тебе", "ему", "ей", "нам", "вам", "им",
    "себя", "себе", "собой",
    "этот", "эта", "это", "эти", "тот", "та", "те",
    "свой", "своя", "своё", "свои",
    "весь", "вся", "всё", "все",
    "каждый", "каждая", "каждое", "каждые",
    "другой", "другая", "другое", "другие",
    "такой", "такая", "такое", "такие",
    "какой", "какая", "какое", "какие",
    "кто", "что", "где", "когда", "почему", "зачем", "как", "куда", "откуда",
    "сколько",
    # ── Prepositions / conjunctions / particles ───────────────────────────────
    "в", "на", "и", "не", "с", "к", "за", "из", "по", "то", "от",
    "для", "до", "при", "про", "под", "над", "без", "через", "после",
    "перед", "между", "против", "вдоль", "около", "среди", "кроме",
    "но", "да", "нет", "или", "если", "то", "же", "ли",
    "так", "уже", "ещё", "очень", "тоже", "только", "даже", "вот",
    "вдруг", "здесь", "там", "тут", "вместе",
    # ── To be / auxiliaries ───────────────────────────────────────────────────
    "есть", "был", "была", "было", "были",
    "буду", "будешь", "будет", "будем", "будете", "будут",
    "бы", "бывает", "бывало",
    # ── Common verbs ──────────────────────────────────────────────────────────
    "делать", "делаю", "делаешь", "делает", "делаем", "делаете", "делают",
    "сделать", "сделал", "сделала", "сделали",
    "помочь", "помощь", "помогать", "помогаю", "помогаешь", "помогает",
    "помогаем", "помогаете", "помогают", "помог", "помогла", "помогли",
    "учиться", "учится", "учатся", "учился", "училась", "учились",
    "работу", "работе", "работой", "школу", "школе", "школой",
    "говорить", "говорю", "говоришь", "говорит", "говорим", "говорите", "говорят",
    "сказать", "сказал", "сказала", "сказали", "скажи", "скажу",
    "знать", "знаю", "знаешь", "знает", "знаем", "знаете", "знают",
    "видеть", "вижу", "видишь", "видит", "видим", "видите", "видят",
    "идти", "иду", "идёшь", "идёт", "идём", "идёте", "идут",
    "пойти", "пойду", "пойдёшь", "пойдёт", "пойдём", "пойдут",
    "хотеть", "хочу", "хочешь", "хочет", "хотим", "хотите", "хотят",
    "мочь", "могу", "можешь", "может", "можем", "можете", "могут",
    "давать", "даю", "даёшь", "даёт", "даём", "даёте", "дают",
    "дать", "дал", "дала", "дали",
    "брать", "беру", "берёшь", "берёт", "берём", "берёте", "берут",
    "взять", "взял", "взяла", "взяли",
    "читать", "читаю", "читаешь", "читает", "читаем", "читаете", "читают",
    "писать", "пишу", "пишешь", "пишет", "пишем", "пишете", "пишут",
    "слушать", "слушаю", "слушает", "слушаем",
    "смотреть", "смотрю", "смотришь", "смотрит", "смотрим", "смотрят",
    "думать", "думаю", "думаешь", "думает", "думаем", "думают",
    "понимать", "понимаю", "понимаешь", "понимает", "понимают",
    "работать", "работаю", "работаешь", "работает", "работаем", "работают",
    "учиться", "учусь", "учишься", "учится", "учимся", "учатся",
    "жить", "живу", "живёшь", "живёт", "живём", "живут",
    "любить", "люблю", "любишь", "любит", "любим", "любят",
    "помочь", "помогать", "помогаю", "помогает",
    "найти", "искать", "ищу", "ищет",
    "купить", "продать", "открыть", "закрыть",
    "начать", "начинать", "кончить", "заканчивать",
    "спать", "сплю", "спишь", "спит",
    "есть", "ем", "ешь", "ест", "едим", "едят",
    "пить", "пью", "пьёшь", "пьёт", "пьём", "пьют",
    "знать", "уметь", "умею", "умеет",
    "верить", "надеяться", "отдыхать",
    "нравиться", "нравится", "нравлюсь",
    "считать", "считаю", "считает",
    "ждать", "жду", "ждёшь", "ждёт", "ждём",
    "играть", "играю", "играет", "играем",
    "бежать", "бегу", "бежишь", "бежит", "бегут",
    # ── Modal / impersonal ────────────────────────────────────────────────────
    "можно", "нельзя", "нужно", "надо", "необходимо", "следует",
    # ── Common nouns ──────────────────────────────────────────────────────────
    "человек", "люди", "мир", "время", "рука", "руки",
    "глаз", "глаза", "жизнь", "дело", "дела", "место", "места",
    "лицо", "страна", "страны", "слово", "слова",
    "работа", "дом", "дома", "путь", "город", "города",
    "голова", "сторона", "система", "год", "годы", "месяц", "месяцы",
    "неделя", "недели", "час", "часы", "часа", "минута", "минуты",
    "секунда", "секунды", "вода", "еда",
    # ── Education ─────────────────────────────────────────────────────────────
    "школа", "школы", "школу", "школе",
    "учитель", "учителя", "учителю", "учителем",
    "ученик", "ученики", "ученику",
    "студент", "студенты", "студенту",
    "университет", "университете",
    "урок", "уроки", "уроку", "уроке",
    "класс", "классы", "класса",
    "задание", "задания", "заданию",
    "книга", "книги", "книгу", "книге",
    "тетрадь", "тетради", "ручка", "ручки",
    "карандаш", "карандаши",
    "стол", "столы", "стул", "стулья", "доска", "мел",
    "знание", "знания", "образование", "обучение",
    "учёба", "учебник", "учебники",
    "экзамен", "оценка", "оценки", "задача", "задачи",
    # ── Technology ────────────────────────────────────────────────────────────
    "компьютер", "компьютеры", "телефон", "телефоны",
    "интернет", "программа", "программы", "приложение", "приложения",
    "сайт", "сайты", "текст", "тексты", "слово", "слова",
    "предложение", "предложения", "язык", "языки",
    "русский", "казахский", "система", "информация",
    "данные", "анализ", "исправление", "ошибка", "ошибки",
    "модель", "обучение", "алгоритм",
    # ── Body ──────────────────────────────────────────────────────────────────
    "голова", "глаза", "нос", "рот", "ухо", "уши",
    "нога", "ноги", "сердце", "спина", "живот",
    # ── Family ────────────────────────────────────────────────────────────────
    "мама", "папа", "брат", "сестра", "бабушка", "дедушка",
    "ребёнок", "дети", "семья", "муж", "жена", "сын", "дочь",
    # ── Nature ────────────────────────────────────────────────────────────────
    "солнце", "луна", "звезда", "небо", "земля", "море",
    "река", "гора", "лес", "поле", "цветок", "дерево",
    # ── Food ──────────────────────────────────────────────────────────────────
    "хлеб", "молоко", "мясо", "рыба", "овощи", "фрукты", "чай", "кофе", "суп",
    # ── Adjectives ────────────────────────────────────────────────────────────
    "большой", "большая", "большое", "большие",
    "маленький", "маленькая", "маленькое", "маленькие",
    "новый", "новая", "новое", "новые",
    "старый", "старая", "старое", "старые",
    "хороший", "хорошая", "хорошее", "хорошие",
    "плохой", "плохая", "плохое", "плохие",
    "красивый", "красивая", "красивое", "красивые",
    "умный", "умная", "умное", "умные",
    "добрый", "добрая", "доброе", "добрые",
    "злой", "злая", "злое", "злые",
    "белый", "белая", "белое", "белые",
    "чёрный", "чёрная", "чёрное", "чёрные",
    "красный", "красная", "красное", "красные",
    "зелёный", "зелёная", "зелёное", "зелёные",
    "синий", "синяя", "синее", "синие",
    "жёлтый", "жёлтая", "жёлтое", "жёлтые",
    "первый", "первая", "первое", "первые",
    "последний", "последняя", "последнее", "последние",
    "важный", "важная", "важное", "важные",
    "нужный", "нужная", "нужное", "нужные",
    "правильный", "правильная", "правильное", "правильные",
    # ── Numbers ───────────────────────────────────────────────────────────────
    "один", "одна", "одно", "два", "две", "три", "четыре", "пять",
    "шесть", "семь", "восемь", "девять", "десять",
    "двадцать", "тридцать", "сорок", "пятьдесят",
    "сто", "двести", "тысяча", "миллион",
    # ── Temporal / adverbs ────────────────────────────────────────────────────
    "сейчас", "теперь", "всегда", "никогда", "иногда", "часто", "редко",
    "завтра", "вчера", "сегодня", "утром", "днём", "вечером", "ночью",
    "рано", "поздно", "быстро", "медленно", "хорошо", "плохо",
    "правильно", "неправильно", "точно", "примерно",
    "много", "мало", "немного", "совсем", "совсем",
    "здесь", "там", "тут", "рядом", "далеко", "близко",
    "вместе", "отдельно", "снова", "опять",
}

# ═══════════════════════════════════════════════════════════════════════════════
# KAZAKH VOCABULARY
# ═══════════════════════════════════════════════════════════════════════════════
KAZAKH_VOCABULARY: Set[str] = {
    # ── Greetings ─────────────────────────────────────────────────────────────
    "сәлем", "сәлеметсіз", "сәлеметсіздер", "сау", "болыңыз",
    "рахмет", "кешіріңіз", "өтінемін", "иә", "жоқ",
    # ── Pronouns ─────────────────────────────────────────────────────────────
    "мен", "сен", "ол", "біз", "сіз", "олар",
    "маған", "саған", "оған", "бізге", "сізге", "оларға",
    "менің", "сенің", "оның", "біздің", "сіздің", "олардың",
    # ── Demonstratives ────────────────────────────────────────────────────────
    "бұл", "сол", "осы", "мынау", "анау", "ол",
    # ── Conjunctions / particles ──────────────────────────────────────────────
    "және", "немесе", "бірақ", "егер", "онда", "себебі", "өйткені",
    "да", "де", "та", "те", "ма", "ме", "ба", "бе", "па", "пе",
    "ғой", "ғой", "ал", "не", "бе", "ші",
    # ── To be / predicates ────────────────────────────────────────────────────
    "бар", "жоқ", "болды", "болсын", "болады", "болмайды",
    "болған", "болса", "болу", "болмақ",
    # ── Common verbs ──────────────────────────────────────────────────────────
    "айту", "айтады", "айтты", "айтпайды", "айт",
    "жазу", "жазады", "жазды", "жазбайды", "жаз",
    "оқу", "оқиды", "оқыды", "оқымайды", "оқы",
    "білу", "біледі", "білді", "білмейді",
    "көру", "көреді", "көрді", "көрмейді",
    "келу", "келеді", "келді", "келмейді", "кел",
    "кету", "кетеді", "кетті", "кетпейді", "кет",
    "бару", "барады", "барды", "бармайды", "бар",
    "алу", "алады", "алды", "алмайды",
    "беру", "береді", "берді", "бермейді",
    "жасау", "жасайды", "жасады", "жасамайды",
    "сөйлеу", "сөйлейді", "сөйледі",
    "тыңдау", "тыңдайды", "тыңдады",
    "ойлау", "ойлайды", "ойлады",
    "түсіну", "түсінеді", "түсінді",
    "жүру", "жүреді", "жүрді",
    "тұру", "тұрады", "тұрды",
    "отыру", "отырады", "отырды",
    "жату", "жатады", "жатты",
    "жеу", "жейді", "жеді",
    "ішу", "ішеді", "ішті",
    "ұйықтау", "ұйықтайды", "ұйықтады",
    "ойнау", "ойнайды", "ойнады",
    # ── Common nouns ──────────────────────────────────────────────────────────
    "адам", "адамдар", "жер", "су", "от", "ауа",
    "күн", "ай", "жыл", "жылдар",
    "ай", "апта", "күн", "сағат", "минут",
    "үй", "үйде", "қала", "қалада", "ауыл", "ауылда",
    "мектеп", "мектепте", "мектепті", "мектептің",
    "сабақ", "сабақта", "сабақты",
    "кітап", "кітапта", "кітапты", "кітаптар",
    "тіл", "тілі", "тілде",
    "халық", "ел", "бала", "балалар",
    "ата", "ана", "апа", "аға", "іні", "қарындас",
    "достар", "дос", "жолдас",
    "оқушы", "оқушылар",
    "мұғалім", "мұғалімдер",
    "студент", "студенттер",
    "университет", "университетте",
    # ── Adjectives ────────────────────────────────────────────────────────────
    "жақсы", "жаман", "үлкен", "кіші", "жаңа", "ескі",
    "ақ", "қара", "қызыл", "жасыл", "көк", "сары",
    "биік", "аласа", "ұзын", "қысқа",
    "жылы", "суық", "ыстық",
    "жылдам", "баяу", "қатты", "жұмсақ",
    # ── Numbers ───────────────────────────────────────────────────────────────
    "бір", "екі", "үш", "төрт", "бес",
    "алты", "жеті", "сегіз", "тоғыз", "он",
    "жиырма", "отыз", "қырық", "елу",
    "жүз", "мың", "миллион",
    # ── Kazakh-specific / cultural words ─────────────────────────────────────
    "қазақ", "қазақша", "қазақстан", "астана",
    "мәдениет", "дәстүр", "тарих",
    "дала", "жазира", "өрен",
    "бауырмал", "қонақжай", "батыр",
    # ── Extra demo-critical words ─────────────────────────────────────────────
    "устаз", "мұғалімге", "мектепке", "мектептен",
    "кітапты", "кітапқа", "балаға", "баладан",
    "студентке", "оқушыға",
    # ── Common adverbs / temporal ─────────────────────────────────────────────
    "қазір", "енді", "бұрын", "кейін",
    "бүгін", "ертең", "кеше",
    "таңертең", "кешке", "түнде",
    "жиі", "сирек", "әрқашан", "ешқашан",
    "мұнда", "сонда", "онда", "қайда",
    "жақсы", "жаман", "тез", "жай",
    "бірге", "жеке",
    "өте", "аса", "тым",
    "көп", "аз", "аздап",
}

# ── Pre-compute sorted vocabulary lists for rapidfuzz ─────────────────────────
_RU_VOCAB_LIST: List[str] = sorted(RUSSIAN_VOCABULARY)
_KZ_VOCAB_LIST: List[str] = sorted(KAZAKH_VOCABULARY)

# ── Kazakh stem lexicon for the morphological analyzer ────────────────────────
# Every vocabulary entry may act as a stem. The analyzer uses this set to decide
# whether an out-of-vocabulary word is a legitimate inflected form (stem + valid
# suffix chain) and therefore must NOT be "corrected" away.
_KZ_STEMS: Set[str] = {w.lower() for w in KAZAKH_VOCABULARY}

# ── Tokenisation regex ────────────────────────────────────────────────────────
# Splits text into (cyrillic-word, non-word) runs preserving everything.
_TOKEN_RE = re.compile(r"([\u0400-\u04FF]+|[^\u0400-\u04FF]+)", re.UNICODE)


# ═══════════════════════════════════════════════════════════════════════════════
# Core correction helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _find_best_candidate(
    word: str,
    vocab: List[str],
    similarity_threshold: float,
    max_edit_distance: int,
) -> Tuple[Optional[str], float]:
    """
    Return (best_match, similarity) or (None, 0.0) if nothing is good enough.

    Strategy:
    1. Pre-filter by word length (±max_edit_distance chars) to prune the
       search space and avoid short common words getting spurious high scores.
    2. Find the candidate with minimum Levenshtein edit distance.
    3. Accept only if edit_dist <= max_edit_distance and computed similarity
       meets the threshold.
    """
    if not word:
        return None, 0.0

    from rapidfuzz.distance import Levenshtein

    word_len = len(word)
    # Length-band filter: only consider words with similar length
    candidates = [
        w for w in vocab
        if abs(len(w) - word_len) <= max_edit_distance
    ]
    if not candidates:
        return None, 0.0

    # Find candidate with minimum edit distance
    best_word: Optional[str] = None
    best_dist = max_edit_distance + 1

    for candidate in candidates:
        dist = Levenshtein.distance(
            word, candidate, score_cutoff=best_dist
        )
        if dist <= best_dist:
            if dist < best_dist or (dist == best_dist and candidate == word):
                best_dist = dist
                best_word = candidate

    if best_word is None or best_dist > max_edit_distance:
        return None, 0.0

    # Compute normalised similarity (1 - normalised edit distance)
    similarity = 1.0 - best_dist / max(word_len, len(best_word))
    if similarity < similarity_threshold:
        return None, 0.0

    return best_word, similarity


def _correct_tokens(
    tokens: List[str],
    vocab: List[str],
    threshold: float,
    max_edit: int,
    accept_word: Optional[Callable[[str], bool]] = None,
) -> Tuple[str, List[Dict]]:
    """
    Correct each word-token against *vocab*.

    Parameters
    ----------
    accept_word :
        Optional predicate. When a token is absent from *vocab* but
        ``accept_word(token)`` returns True, the token is treated as valid and
        left unchanged. This is how the Kazakh morphological analyzer protects
        legitimate inflected forms (stem + suffix chain) from being "corrected".

    Returns (corrected_text, list_of_correction_dicts).
    """
    corrections: List[Dict] = []
    result_parts: List[str] = []
    vocab_set: Set[str] = set(vocab)

    for token in tokens:
        # Non-word token (spaces, punctuation) – pass through unchanged
        if not re.fullmatch(r"[\u0400-\u04FF]+", token, re.UNICODE):
            result_parts.append(token)
            continue

        word_lower = token.lower()

        # Already in vocabulary – keep original casing
        if word_lower in vocab_set:
            result_parts.append(token)
            continue

        # Morphologically valid inflected form – keep as is
        if accept_word is not None and accept_word(word_lower):
            result_parts.append(token)
            continue

        # Find best candidate
        candidate, similarity = _find_best_candidate(
            word_lower, vocab, threshold, max_edit
        )

        if candidate and candidate != word_lower:
            # Preserve original capitalisation style
            if token[0].isupper():
                candidate = candidate.capitalize()
            corrections.append({
                "before": token,
                "after": candidate,
                "type": "spelling",
            })
            result_parts.append(candidate)
        else:
            result_parts.append(token)

    corrected_text = "".join(result_parts)
    return corrected_text, corrections


# ═══════════════════════════════════════════════════════════════════════════════
# Public API
# ═══════════════════════════════════════════════════════════════════════════════

def correct_russian(text: str) -> Tuple[str, List[Dict]]:
    """
    Apply Russian dictionary + edit-distance correction to *text*.
    Returns (corrected_text, corrections_list).
    """
    tokens = _TOKEN_RE.findall(text)
    return _correct_tokens(
        tokens,
        _RU_VOCAB_LIST,
        settings.CORRECTION_SIMILARITY_THRESHOLD,
        settings.MAX_EDIT_DISTANCE,
    )


def _kazakh_morph_accept(word: str) -> bool:
    """
    True if *word* is a valid Kazakh inflected form of a known stem.

    Bridges the morphological analyzer into the correction pipeline so that
    legitimate stem + suffix combinations (which the finite vocabulary cannot
    enumerate) are recognised and left untouched.
    """
    return is_analyzable(word, _KZ_STEMS)


def correct_kazakh(text: str) -> Tuple[str, List[Dict]]:
    """
    Apply Kazakh correction to *text*.

    The pipeline now combines two components into a single mechanism:
      1. morphological analysis — recognises valid inflected forms and protects
         them from spurious correction;
      2. dictionary + edit-distance — fixes genuine misspellings of the
         remaining out-of-vocabulary words.

    Returns (corrected_text, corrections_list).
    """
    tokens = _TOKEN_RE.findall(text)
    return _correct_tokens(
        tokens,
        _KZ_VOCAB_LIST,
        settings.CORRECTION_SIMILARITY_THRESHOLD,
        settings.MAX_EDIT_DISTANCE,
        accept_word=_kazakh_morph_accept,
    )


def correct_text(text: str, language: str) -> Tuple[str, List[Dict]]:
    """
    Language-aware entry point.

    Parameters
    ----------
    text     : raw input text
    language : "Russian" | "Kazakh" | "Mixed" | "Unknown"

    Returns
    -------
    (corrected_text, corrections_list)
    """
    if language == "Russian":
        return correct_russian(text)
    elif language == "Kazakh":
        return correct_kazakh(text)
    elif language == "Mixed":
        # Best-effort: run Russian correction (covers Cyrillic base)
        # A future version could segment by language and run each pipeline.
        return correct_russian(text)
    else:
        # Unknown language – return as-is
        return text, []
