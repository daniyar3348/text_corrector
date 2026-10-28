---
language:
- kk
library_name: transformers
pipeline_tag: token-classification
base_model: kz-transformers/kaz-roberta-conversational
tags:
- kazakh
- spelling-correction
- error-detection
- token-classification
metrics:
- precision
- recall
- f1
---

# KazRoBERTa — детектор орфографических ошибок в казахском тексте

Модель проекта **Turan Text Corrector**: для каждого слова предложения
предсказывает метку `KEEP` (слово верное) или `ERROR` (в слове ошибка).
Исправление делает второй шаг — корректор по словарю (`kk_lexicon.tsv` в этом
репозитории): для помеченного слова перебираются замены русских букв на
казахские (а→ә, к→қ, н→ң …) и пары гармонии гласных, затем ближайшее слово
словаря.

- **Демо:** https://correctecor.kz
- **API (детектор + корректор):** https://daniyar51-turan-text-corrector.hf.space/docs
- **Код:** https://github.com/daniyar3348/text_corrector

*English: a KazRoBERTa token classifier that flags misspelled words in Kazakh
text (KEEP / ERROR per word); the bundled lexicon-based corrector fixes them.*

## Модель

| | |
|---|---|
| Архитектура | `RobertaForTokenClassification`, 6 слоёв, d = 768, 12 голов, ~83 млн параметров |
| Основа | [`kz-transformers/kaz-roberta-conversational`](https://huggingface.co/kz-transformers/kaz-roberta-conversational) |
| Метки | `0 = KEEP`, `1 = ERROR`; метка слова — по его первому подтокену |
| Вход | одно предложение, слова через пробел, до 128 токенов (так обучалась) |

## Обучение

- **Данные:** корпус казахских текстов (~923 тыс. предложений). В предложения
  синтетически внесены ошибки: казахская буква заменена русской (30,5%),
  нарушена гармония гласных (21,3%), перестановка (17,9%), пропуск (11,9%),
  повтор (9,6%) и замена буквы (8,7%); от 0 до 3 ошибок на предложение (в
  среднем 1,45), 10,9% пар без ошибок.
- **Выборки** разбиты по предложениям до внесения ошибок: train 2 565 771 пар
  (872 798 предложений × 3 варианта), val 25 000, test 25 000.
- **Параметры:** 2 эпохи, lr 2e-5 (линейно, без прогрева), batch 64, weight
  decay 0,01, fp16, seed 42; лучший чекпоинт по F1 на ошибках (val).

## Результаты (test, 8 000 предложений)

| Метрика | Значение |
|---|---|
| Поиск ошибок: precision / recall / F1 | 97,1% / 97,4% / **97,3%** |
| Ложные срабатывания на правильных словах | 0,34% |
| Предложений исправлено целиком (детектор + корректор) | **81,2%** |
| То же при идеальном детекторе (потолок корректора) | 83,8% |
| Весь текст набран на русской раскладке: найдено ошибок / исправлено предложений | 70,0% / 54,9% |

## Ограничения

- Ошибки в тесте синтетические и того же вида, что в обучении; на реальных
  текстах цифры могут быть ниже.
- Слабое место — текст, целиком набранный без казахских букв: модель училась на
  предложениях максимум с тремя ошибками.
- Несколько предложений за один проход ухудшают поиск (6 предложений — F1 83,5%):
  подавайте по одному.
- Русский текст модель не исправляет.

## Как использовать

Поиск ошибок:

```python
import torch
from transformers import AutoModelForTokenClassification, AutoTokenizer

repo = "daniyar51/kazroberta-kazakh-spelling-detector"
tok = AutoTokenizer.from_pretrained(repo)
model = AutoModelForTokenClassification.from_pretrained(repo).eval()

words = "Бул маселе оте манызды болып тур.".split()
enc = tok(words, is_split_into_words=True, truncation=True, max_length=128,
          return_tensors="pt")
with torch.no_grad():
    pred = model(**enc).logits[0].argmax(-1).tolist()

labels, prev = {}, None
for i, w in enumerate(enc.word_ids(0)):
    if w is not None and w != prev:
        labels[w] = model.config.id2label[pred[i]]
    prev = w
print([(words[w], labels[w]) for w in sorted(labels)])
```

Исправление целиком (детектор + корректор) — через API:

```bash
curl -X POST https://daniyar51-turan-text-corrector.hf.space/correct-text \
  -H 'Content-Type: application/json' \
  -d '{"text": "Бул маселе оте манызды болып тур."}'
```

## Файлы

- `model.safetensors`, `config.json`, `tokenizer.json`, `tokenizer_config.json` — модель
- `kk_lexicon.tsv` — словарь корректора: словоформа и частота в корпусе
  (верными считаются формы с частотой ≥ 2, ~174 тыс.)
