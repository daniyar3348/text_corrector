#!/usr/bin/env python3
"""
eval_router.py — quantify the "russified-lexicon" language-routing signal.

Compares the FULL router (detect_language, with the russified-lexicon signal)
against a NAIVE ablation (same code with the russified set emptied) on:
  • clean Kazakh   (real test sentences, have Kazakh-exclusive letters) — control
  • ka2ru-Kazakh   (those sentences with special letters mapped to Russian
                    look-alikes) — the novel case that otherwise misroutes
  • Russian        (a small indicative negative set) — false-positive check

Metric: fraction routed to "Kazakh" (the correction path). For Kazakh sets
higher is better (recall); for the Russian set lower is better (precision).
Pure-Python (no model). Run from backend/:
  ./.venv-train/bin/python scripts/eval_router.py
"""
from __future__ import annotations
import json, os, sys
_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _BACKEND)
import app.services.language_detection as ld

TEST = os.path.join(_BACKEND, "data", "kazakh_spellcheck", "test.jsonl")
OUTDIR = os.path.join(_BACKEND, "data", "eval"); os.makedirs(OUTDIR, exist_ok=True)
SAMPLE = 3000

# real Kazakh sentences (non-clean rows still have a correct reference)
kaz = []
for line in open(TEST, encoding="utf-8"):
    o = json.loads(line)
    s = o["correct"]
    if len(s.split()) >= 3:
        kaz.append(s)
    if len(kaz) >= SAMPLE:
        break
ka2ru = [s.translate(ld._KA2RU_MAP) for s in kaz]   # strip special letters -> looks Russian

# small indicative Russian negative set (test fixture, not a data claim)
russian = [
    "Сегодня хорошая погода и мы идём гулять в парк.",
    "Я не знаю, что он сказал вчера на собрании.",
    "Это очень большой и красивый новый дом.",
    "Мы работаем над проектом уже несколько месяцев.",
    "Где находится ближайшая остановка автобуса?",
    "Книга лежит на столе рядом с компьютером.",
    "Спасибо за помощь, это было очень полезно.",
    "Они приехали из другого города на поезде.",
    "После работы я обычно читаю или смотрю фильмы.",
    "Каждый день он ходит в школу пешком.",
    "Погода резко изменилась, начался сильный дождь.",
    "Наша команда выиграла важный матч в субботу.",
    "Этот вопрос требует серьёзного обсуждения завтра.",
    "Дети играли во дворе до позднего вечера.",
    "Новый закон вступит в силу с первого января.",
    "Она купила свежие овощи и фрукты на рынке.",
    "Мне нужно закончить отчёт до конца недели.",
    "Врач сказал, что нужно больше отдыхать.",
    "Машина сломалась посреди дороги вечером.",
    "Мы обсудили все детали будущего путешествия.",
]

def frac_kazakh(texts):
    k = sum(1 for t in texts if ld.detect_language(t)["language"] == "Kazakh")
    return 100.0 * k / len(texts) if texts else 0.0

def run_all():
    return {
        "clean_kazakh": round(frac_kazakh(kaz), 1),
        "ka2ru_kazakh": round(frac_kazakh(ka2ru), 1),
        "russian": round(frac_kazakh(russian), 1),
    }

# FULL router (russified signal active)
full = run_all()
# NAIVE ablation: empty the russified lexicon set
_saved = ld._KAZ_RUSSIFIED
ld._KAZ_RUSSIFIED = set()
naive = run_all()
ld._KAZ_RUSSIFIED = _saved

report = {"n_kazakh": len(kaz), "n_russian": len(russian),
          "pct_routed_kazakh": {"full_router": full, "naive_no_russified": naive}}
with open(os.path.join(OUTDIR, "eval_router.json"), "w", encoding="utf-8") as f:
    json.dump(report, f, ensure_ascii=False, indent=2)

print(f"router eval | Kazakh n={len(kaz)} | Russian n={len(russian)}")
print(f"{'set':16s} {'FULL %Kaz':>10s} {'NAIVE %Kaz':>11s}")
for k in ("clean_kazakh", "ka2ru_kazakh", "russian"):
    print(f"{k:16s} {full[k]:10.1f} {naive[k]:11.1f}")
print("(Kazakh sets: higher=better recall; Russian: lower=better precision)")
print(f"wrote {os.path.join(OUTDIR,'eval_router.json')}")
