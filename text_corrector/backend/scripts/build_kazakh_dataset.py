#!/usr/bin/env python3
"""
build_kazakh_dataset.py — синтетический датасет орфо-ошибок казахского языка
(этап 4 плана завершения Turan Text Corrector).

Две стадии:
  extract : merged_dissertation.json → чистые эталонные предложения (sentences.txt).
            Потоковое чтение (терпит ещё не докачанный файл) + проверенный
            конвейер очистки из kk_text.py (нормализация двойников, фикс склеек,
            удаление иноязычных вставок) + дедупликация. Медленный шаг — гонять
            только когда меняется исходный корпус.
  inject  : sentences.txt → пары «с ошибкой → правильно» + ~clean-ratio «чистых»
            пар (правильно→правильно, чтобы модель не переисправляла), перемешать
            и разбить на train/val/test (JSONL) + meta.json + sample_preview.txt.

Формат строки — параллельная пара, модельно-нейтральная (годится и для seq2seq
fine-tune KazRoBERTa, и для токен-классификации):

    {"correct": "...", "corrupted": "...", "n_errors": 2, "clean": false,
     "edits": [{"type": "ka2ru", "wi": 4, "before": "қазақ", "after": "казак"}, ...]}

Без сторонних зависимостей (stdlib). Запуск:
  python scripts/build_kazakh_dataset.py --stage all
"""
from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
import time
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kk_text as K  # noqa: E402

_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PROJECT_ROOT = os.path.dirname(os.path.dirname(_BACKEND))
DEFAULT_SOURCE = os.path.join(_PROJECT_ROOT, "merged_dissertation.json")
DEFAULT_OUT_DIR = os.path.join(_BACKEND, "data", "kazakh_spellcheck")

# ── Модель ошибок (по реальной частоте) ─────────────────────────────────────────
# (1) ka2ru   — казахская спецбуква → русский визуальный двойник (типичнейшая
#               ошибка: набор на русской раскладке).
KA2RU = {"ә": "а", "ө": "о", "ұ": "у", "ү": "у",
         "қ": "к", "ғ": "г", "ң": "н", "і": "и", "һ": "х"}
# (2) harmony — нарушение сингармонизма: гласная → пара противоположного ряда
#               (именно это ловит морфоанализатор).
PAIR = {"а": "ә", "ә": "а", "о": "ө", "ө": "о",
        "ұ": "ү", "ү": "ұ", "ы": "і", "і": "ы", "у": "ү"}
# (3) sub     — близкие по виду/звучанию замены.
SUB = {"е": "и", "и": "е", "н": "м", "м": "н", "ш": "щ", "щ": "ш",
       "з": "с", "с": "з", "б": "п", "п": "б", "о": "а"}

OPS = ["ka2ru", "harmony", "swap", "drop", "dup", "sub"]
WEIGHTS = [0.45, 0.18, 0.13, 0.10, 0.07, 0.07]

TOKEN_RE = re.compile(r"([Ѐ-ӿ]+|[^Ѐ-ӿ]+)")
WORD_RE = re.compile(r"[Ѐ-ӿ]+")


def _case(orig: str, new_lower: str) -> str:
    return new_lower.upper() if orig.isupper() else new_lower


def _sub_map(word: str, mp: dict, rng) -> str | None:
    idx = [i for i, ch in enumerate(word) if ch.lower() in mp]
    if not idx:
        return None
    i = rng.choice(idx)
    return word[:i] + _case(word[i], mp[word[i].lower()]) + word[i + 1:]


def _err_swap(w, rng):
    cand = [i for i in range(len(w) - 1) if w[i].lower() != w[i + 1].lower()]
    if not cand:
        return None
    i = rng.choice(cand)
    return w[:i] + w[i + 1] + w[i] + w[i + 2:]


def _err_drop(w, rng):
    if len(w) < 4:
        return None
    i = rng.randint(1, len(w) - 2)        # сохраняем первую/последнюю букву
    return w[:i] + w[i + 1:]


def _err_dup(w, rng):
    i = rng.randint(0, len(w) - 1)
    return w[:i + 1] + w[i] + w[i + 1:]


OP_FUNC = {
    "ka2ru": lambda w, r: _sub_map(w, KA2RU, r),
    "harmony": lambda w, r: _sub_map(w, PAIR, r),
    "sub": lambda w, r: _sub_map(w, SUB, r),
    "swap": _err_swap, "drop": _err_drop, "dup": _err_dup,
}


def apply_error(word: str, rng):
    """Одна случайная ошибка к слову → (new, op) или (None, None)."""
    for _ in range(6):
        op = rng.choices(OPS, weights=WEIGHTS)[0]
        res = OP_FUNC[op](word, rng)
        if res and res != word:
            return res, op
    return None, None


def corrupt_sentence(s: str, rng, error_rate: float, max_errors: int):
    tokens = TOKEN_RE.findall(s)
    word_pos = [i for i, t in enumerate(tokens)
                if WORD_RE.fullmatch(t) and len(t) >= 3]
    if not word_pos:
        return s, []
    k = max(1, min(sum(rng.random() < error_rate for _ in word_pos),
                   max_errors, len(word_pos)))
    edits = []
    for i in sorted(rng.sample(word_pos, k)):
        res, op = apply_error(tokens[i], rng)
        if res:
            edits.append({"type": op, "wi": i, "before": tokens[i], "after": res})
            tokens[i] = res
    if not edits:                          # форсируем хотя бы одну
        for i in rng.sample(word_pos, len(word_pos)):
            res, op = apply_error(tokens[i], rng)
            if res:
                edits.append({"type": op, "wi": i, "before": tokens[i], "after": res})
                tokens[i] = res
                break
    return "".join(tokens), edits


def _clean_rec(s: str) -> dict:
    return {"correct": s, "corrupted": s, "n_errors": 0, "clean": True, "edits": []}


def make_records(s: str, rng, clean_ratio, error_rate, max_errors, variants) -> list:
    """До `variants` записей на предложение: разные искажения (эталон тот же),
    дедуп вариантов; «чистую» пару эмитим максимум один раз."""
    recs, seen_corr, has_clean = [], set(), False
    for _ in range(variants):
        if rng.random() < clean_ratio:
            if not has_clean:
                recs.append(_clean_rec(s)); has_clean = True
            continue
        corr, edits = corrupt_sentence(s, rng, error_rate, max_errors)
        if not edits:                      # не удалось испортить → одна чистая
            if not has_clean:
                recs.append(_clean_rec(s)); has_clean = True
            continue
        if corr in seen_corr:              # такой же вариант уже был — пропускаем
            continue
        seen_corr.add(corr)
        recs.append({"correct": s, "corrupted": corr, "n_errors": len(edits),
                     "clean": False, "edits": edits})
    if not recs:                           # гарантируем хотя бы одну запись
        recs.append(_clean_rec(s))
    return recs


# ── extract ─────────────────────────────────────────────────────────────────────

def stage_extract(args):
    t0 = time.time()
    seen, kept, arts = set(), 0, 0
    out_path = os.path.join(args.out_dir, "sentences.txt")
    limit = args.limit_articles or 10**9
    print(f"[extract] поток {args.source}", flush=True)
    with open(out_path, "w", encoding="utf-8") as out:
        for art in K.iter_json_array(args.source, limit):
            arts += 1
            txt = art.get("text") if isinstance(art, dict) else None
            if txt:
                for s in K.sentences_from_text(txt):
                    h = hash(s)
                    if h in seen:
                        continue
                    seen.add(h)
                    out.write(s + "\n")
                    kept += 1
                    if args.max_sentences and kept >= args.max_sentences:
                        break
            if args.max_sentences and kept >= args.max_sentences:
                break
            if arts % 10000 == 0:
                print(f"[extract]   статей={arts:,}  предложений={kept:,}  "
                      f"({time.time()-t0:.0f}s)", flush=True)
    print(f"[extract] ГОТОВО: статей={arts:,}  уникальных предложений={kept:,}  "
          f"→ {out_path}  ({time.time()-t0:.0f}s)", flush=True)
    return kept


# ── inject ──────────────────────────────────────────────────────────────────────

def stage_inject(args):
    t0 = time.time()
    rng = random.Random(args.seed)
    src = os.path.join(args.out_dir, "sentences.txt")
    if not os.path.exists(src):
        sys.exit(f"[inject] нет {src} — сначала прогоните стадию extract")
    with open(src, encoding="utf-8") as f:
        lines = [ln.rstrip("\n") for ln in f if ln.strip()]
    print(f"[inject] предложений: {len(lines):,}", flush=True)
    rng.shuffle(lines)

    val = lines[:args.val_size]
    test = lines[args.val_size:args.val_size + args.test_size]
    train = lines[args.val_size + args.test_size:]

    by_type, by_nerr = Counter(), Counter()
    total = clean_total = 0
    split_counts = {}
    # аугментация только train; val/test — по одной записи на предложение
    for name, data, vrs in (("train", train, args.variants),
                            ("val", val, 1), ("test", test, 1)):
        path = os.path.join(args.out_dir, f"{name}.jsonl")
        n_clean = n_pairs = 0
        with open(path, "w", encoding="utf-8") as f:
            for s in data:
                for rec in make_records(s, rng, args.clean_ratio, args.error_rate,
                                        args.max_errors, vrs):
                    n_pairs += 1
                    if rec["clean"]:
                        n_clean += 1
                    by_nerr[rec["n_errors"]] += 1
                    for e in rec["edits"]:
                        by_type[e["type"]] += 1
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        split_counts[name] = {"pairs": n_pairs, "clean": n_clean, "sentences": len(data)}
        total += n_pairs
        clean_total += n_clean
        print(f"[inject]   {name:5s}: {n_pairs:,} пар из {len(data):,} предлож. "
              f"(чистых {n_clean:,}) → {path}", flush=True)

    total_err = sum(by_type.values())
    meta = {
        "source": os.path.basename(args.source),
        "total_pairs": total,
        "clean_pairs": clean_total,
        "clean_ratio_actual": round(clean_total / max(total, 1), 4),
        "splits": split_counts,
        "error_type_distribution": {
            k: {"count": v, "pct": round(100 * v / total_err, 2)}
            for k, v in by_type.most_common()},
        "errors_per_sentence_histogram": dict(sorted(by_nerr.items())),
        "avg_errors_per_pair": round(total_err / max(total, 1), 3),
        "config": {"clean_ratio": args.clean_ratio, "error_rate": args.error_rate,
                   "max_errors": args.max_errors, "variants_train": args.variants,
                   "seed": args.seed, "val_size": args.val_size, "test_size": args.test_size},
        "error_model": {"ops": OPS, "weights": WEIGHTS},
    }
    with open(os.path.join(args.out_dir, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    # превью из реально записанных пар (только с ошибками)
    pv_path = os.path.join(args.out_dir, "sample_preview.txt")
    with open(os.path.join(args.out_dir, "train.jsonl"), encoding="utf-8") as fin, \
            open(pv_path, "w", encoding="utf-8") as pv:
        shown = 0
        for line in fin:
            if shown >= 25:
                break
            o = json.loads(line)
            if o["clean"]:
                continue
            pv.write(f"✗ {o['corrupted']}\n✓ {o['correct']}\n"
                     f"  [{', '.join(e['type'] for e in o['edits'])}]\n\n")
            shown += 1

    print(f"[inject] ГОТОВО: {total:,} пар, чистых {clean_total:,} "
          f"({meta['clean_ratio_actual']*100:.1f}%), "
          f"ср. ошибок/пара={meta['avg_errors_per_pair']}  ({time.time()-t0:.0f}s)",
          flush=True)
    print("[inject] микс ошибок: " + ", ".join(
        f"{k} {meta['error_type_distribution'][k]['pct']}%"
        for k in meta["error_type_distribution"]), flush=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--stage", choices=["extract", "inject", "all"], default="all")
    ap.add_argument("--source", default=DEFAULT_SOURCE)
    ap.add_argument("--out-dir", default=DEFAULT_OUT_DIR)
    ap.add_argument("--limit-articles", type=int, default=0)   # 0 = все
    ap.add_argument("--max-sentences", type=int, default=0)    # 0 = все
    ap.add_argument("--clean-ratio", type=float, default=0.12)
    ap.add_argument("--error-rate", type=float, default=0.12)
    ap.add_argument("--max-errors", type=int, default=3)
    ap.add_argument("--variants", type=int, default=1,
                    help="вариантов искажения на предложение (только train)")
    ap.add_argument("--val-size", type=int, default=25000)
    ap.add_argument("--test-size", type=int, default=25000)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    if args.stage in ("extract", "all"):
        stage_extract(args)
    if args.stage in ("inject", "all"):
        stage_inject(args)


if __name__ == "__main__":
    main()
