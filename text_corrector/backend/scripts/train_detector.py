#!/usr/bin/env python3
"""
train_detector.py — fine-tune KazRoBERTa как ДЕТЕКТОР орфо-ошибок (token-tagger).

Архитектура (вариант A, выбранный): KazRoBERTa (энкодер, MLM-предобучение) +
голова token-classification. По каждому подслову модель предсказывает KEEP/ERROR.
Слово считается ошибочным, если его искажённая форма отличается от эталона —
метки берём прямо из пар датасета (corrupted vs correct выравниваются по словам
1:1, проверено: 0% рассинхрона).

Исправление найденных ошибок — отдельный модуль (инверсия правил ru→kk +
лексикон из sentences.txt + валидация морфоанализатором). Здесь только детектор.

Запуск (в venv с torch/transformers, Python 3.13):
  python scripts/train_detector.py --smoke           # быстрый прогон на подвыборке
  python scripts/train_detector.py --epochs 2        # полное обучение

Чекпойнт: kz-transformers/kaz-roberta-conversational
"""
from __future__ import annotations

import argparse
import os

import numpy as np
from datasets import load_dataset
from transformers import (
    AutoModelForTokenClassification,
    AutoTokenizer,
    DataCollatorForTokenClassification,
    Trainer,
    TrainingArguments,
)

MODEL_ID = "kz-transformers/kaz-roberta-conversational"
LABEL_NAMES = ["KEEP", "ERROR"]
_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DATA = os.path.join(_BACKEND, "data", "kazakh_spellcheck")
DEFAULT_OUT = os.path.join(_BACKEND, "models", "kazakh_detector")


def to_words_tags(ex):
    """corrupted/correct → слова + метка KEEP(0)/ERROR(1) по словам."""
    cw, rw = ex["corrupted"].split(), ex["correct"].split()
    if len(cw) != len(rw):                       # страховка (на данных не встречается)
        return {"words": cw, "tags": [0] * len(cw)}
    return {"words": cw, "tags": [int(a != b) for a, b in zip(cw, rw)]}


def make_tokenize_fn(tokenizer, max_len):
    def fn(batch):
        enc = tokenizer(batch["words"], is_split_into_words=True,
                        truncation=True, max_length=max_len)
        all_labels = []
        for i, tags in enumerate(batch["tags"]):
            word_ids = enc.word_ids(batch_index=i)
            prev, labels = None, []
            for wid in word_ids:
                if wid is None:
                    labels.append(-100)          # спецтокены
                elif wid != prev:
                    labels.append(tags[wid])     # первый подслово слова
                else:
                    labels.append(-100)          # продолжение слова — игнор
                prev = wid
            all_labels.append(labels)
        enc["labels"] = all_labels
        return enc
    return fn


def compute_metrics(eval_pred):
    """P/R/F1 по классу ERROR (главная метрика детектора) + accuracy."""
    logits, labels = eval_pred
    preds = np.argmax(logits, axis=-1)
    mask = labels != -100
    y_true, y_pred = labels[mask], preds[mask]
    tp = int(((y_pred == 1) & (y_true == 1)).sum())
    fp = int(((y_pred == 1) & (y_true == 0)).sum())
    fn = int(((y_pred == 0) & (y_true == 1)).sum())
    prec = tp / (tp + fp) if tp + fp else 0.0
    rec = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
    acc = float((y_true == y_pred).mean()) if y_true.size else 0.0
    return {"error_precision": prec, "error_recall": rec,
            "error_f1": f1, "accuracy": acc}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model-id", default=MODEL_ID)
    ap.add_argument("--data-dir", default=DEFAULT_DATA)
    ap.add_argument("--out-dir", default=DEFAULT_OUT)
    ap.add_argument("--max-len", type=int, default=128)
    ap.add_argument("--epochs", type=float, default=2.0)
    ap.add_argument("--batch-size", type=int, default=32)
    ap.add_argument("--lr", type=float, default=2e-5)
    ap.add_argument("--smoke", action="store_true",
                    help="быстрый прогон: 2000 train / 1000 eval, 1 эпоха")
    ap.add_argument("--max-train", type=int, default=0)   # 0 = всё
    ap.add_argument("--max-eval", type=int, default=0)
    args = ap.parse_args()

    tokenizer = AutoTokenizer.from_pretrained(args.model_id, use_fast=True)
    assert tokenizer.is_fast, "нужен fast-токенизатор (для word_ids)"

    data_files = {"train": os.path.join(args.data_dir, "train.jsonl"),
                  "validation": os.path.join(args.data_dir, "val.jsonl")}
    ds = load_dataset("json", data_files=data_files)

    if args.smoke:
        ds["train"] = ds["train"].select(range(2000))
        ds["validation"] = ds["validation"].select(range(1000))
        args.epochs = 1.0
    else:
        if args.max_train:
            ds["train"] = ds["train"].select(range(min(args.max_train, len(ds["train"]))))
        if args.max_eval:
            ds["validation"] = ds["validation"].select(range(min(args.max_eval, len(ds["validation"]))))

    keep = ds["train"].column_names
    ds = ds.map(to_words_tags)
    ds = ds.map(make_tokenize_fn(tokenizer, args.max_len),
                batched=True, remove_columns=keep + ["words", "tags"])

    model = AutoModelForTokenClassification.from_pretrained(
        args.model_id, num_labels=2,
        id2label=dict(enumerate(LABEL_NAMES)),
        label2id={l: i for i, l in enumerate(LABEL_NAMES)},
    )

    targs = TrainingArguments(
        output_dir=args.out_dir,
        eval_strategy="epoch",
        save_strategy="epoch",
        learning_rate=args.lr,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        num_train_epochs=args.epochs,
        weight_decay=0.01,
        logging_steps=100,
        load_best_model_at_end=True,
        metric_for_best_model="error_f1",
        report_to="none",
    )

    trainer = Trainer(
        model=model, args=targs,
        train_dataset=ds["train"], eval_dataset=ds["validation"],
        processing_class=tokenizer,
        data_collator=DataCollatorForTokenClassification(tokenizer),
        compute_metrics=compute_metrics,
    )
    trainer.train()
    metrics = trainer.evaluate()
    print("EVAL:", {k: round(v, 4) for k, v in metrics.items() if isinstance(v, float)})
    trainer.save_model(args.out_dir)
    tokenizer.save_pretrained(args.out_dir)
    print(f"Сохранено в {args.out_dir}")


if __name__ == "__main__":
    main()
