#!/usr/bin/env python3
"""
publish_model.py — выложить обученный детектор и словарь корректора в
репозиторий модели на Hugging Face.

Заливает одним коммитом models/kazakh_detector (без training_args.bin),
data/kk_lexicon.tsv и model_card/README.md. Неизменённые файлы повторно не
загружаются. Печатает хеш коммита — его надо вписать в MODEL_REVISION в
space/Dockerfile, чтобы Space собрался именно с этой версией модели.

Нужны huggingface_hub и вход в HF (`hf auth login`):
    python backend/scripts/publish_model.py [--repo daniyar51/kazroberta-kazakh-spelling-detector]
"""
from __future__ import annotations

import argparse
import os
import sys

from huggingface_hub import CommitOperationAdd, HfApi

_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DEFAULT_REPO = "daniyar51/kazroberta-kazakh-spelling-detector"

# local path (relative to backend/) -> path in the model repo
FILES = {
    "models/kazakh_detector/config.json": "config.json",
    "models/kazakh_detector/model.safetensors": "model.safetensors",
    "models/kazakh_detector/tokenizer.json": "tokenizer.json",
    "models/kazakh_detector/tokenizer_config.json": "tokenizer_config.json",
    "data/kk_lexicon.tsv": "kk_lexicon.tsv",
    "model_card/README.md": "README.md",
}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--repo", default=DEFAULT_REPO)
    ap.add_argument("--message", default="Upload KazRoBERTa detector and corrector lexicon")
    args = ap.parse_args()

    paths = {os.path.join(_BACKEND, src): dst for src, dst in FILES.items()}
    missing = [p for p in paths if not os.path.isfile(p)]
    if missing:
        sys.exit("нет файлов (веса и словарь не в git):\n  " + "\n  ".join(missing))

    api = HfApi()
    api.create_repo(args.repo, repo_type="model", exist_ok=True)
    commit = api.create_commit(
        args.repo, repo_type="model", commit_message=args.message,
        operations=[CommitOperationAdd(path_in_repo=dst, path_or_fileobj=src)
                    for src, dst in paths.items()],
    )
    print(f"{len(paths)} файлов → https://huggingface.co/{args.repo}")
    print(f"MODEL_REVISION={commit.oid}")


if __name__ == "__main__":
    main()
