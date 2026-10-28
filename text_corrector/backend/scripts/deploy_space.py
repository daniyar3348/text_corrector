#!/usr/bin/env python3
"""
deploy_space.py — выложить сервер Turan в Docker Space на Hugging Face.

Заливает из backend/ ровно то, что копирует Dockerfile.serve (код, словарь,
модель, зависимости) одним коммитом; Dockerfile.serve уходит как Dockerfile,
space/README.md — как README.md (настройки Space). Неизменённые файлы, в том
числе веса модели, повторно не загружаются. Файлы app/, удалённые локально,
удаляются и в Space. Задаёт переменную ALLOWED_ORIGINS (CORS для страницы).

Нужны huggingface_hub и вход в HF (`hf auth login`):
    python backend/scripts/deploy_space.py [--space daniyar51/turan-text-corrector]
"""
from __future__ import annotations

import argparse
import os
import sys

from huggingface_hub import CommitOperationAdd, CommitOperationDelete, HfApi

_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DEFAULT_SPACE = "daniyar51/turan-text-corrector"
# Origins of the pages that call the API (GitHub Pages and its custom domain).
# JSON list: read by pydantic-settings into Settings.ALLOWED_ORIGINS.
DEFAULT_ORIGINS = ('["https://correctecor.kz", "https://www.correctecor.kz", '
                   '"https://daniyar3348.github.io"]')

# local path (relative to backend/) -> path in the Space repo
FIXED_FILES = {
    "Dockerfile.serve": "Dockerfile",
    "space/README.md": "README.md",
    "requirements-serve.txt": "requirements-serve.txt",
    "data/kk_lexicon.tsv": "data/kk_lexicon.tsv",
}
MODEL_FILES = ["config.json", "tokenizer.json", "tokenizer_config.json", "model.safetensors"]


def collect_files() -> dict[str, str]:
    files = {os.path.join(_BACKEND, src): dst for src, dst in FIXED_FILES.items()}
    for name in MODEL_FILES:
        rel = f"models/kazakh_detector/{name}"
        files[os.path.join(_BACKEND, rel)] = rel
    for root, dirs, names in os.walk(os.path.join(_BACKEND, "app")):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for name in names:
            if name.endswith(".py"):
                path = os.path.join(root, name)
                files[path] = os.path.relpath(path, _BACKEND)
    missing = [p for p in files if not os.path.isfile(p)]
    if missing:
        sys.exit("нет файлов (веса и словарь не в git):\n  " + "\n  ".join(missing))
    return files


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--space", default=DEFAULT_SPACE)
    ap.add_argument("--origins", default=DEFAULT_ORIGINS)
    ap.add_argument("--message", default="Deploy from text_corrector/backend")
    args = ap.parse_args()

    api = HfApi()
    api.create_repo(args.space, repo_type="space", space_sdk="docker", exist_ok=True)

    files = collect_files()
    ops = [CommitOperationAdd(path_in_repo=dst, path_or_fileobj=src) for src, dst in files.items()]
    wanted = set(files.values())
    stale = [p for p in api.list_repo_files(args.space, repo_type="space")
             if p.startswith("app/") and p not in wanted]
    ops += [CommitOperationDelete(path_in_repo=p) for p in stale]

    api.add_space_variable(args.space, "ALLOWED_ORIGINS", args.origins)
    commit = api.create_commit(args.space, repo_type="space", operations=ops,
                               commit_message=args.message)
    print(f"{len(files)} файлов, удалено {len(stale)} → {commit.commit_url}")
    host = args.space.replace("/", "-").replace("_", "-").lower()
    print(f"сборка: https://huggingface.co/spaces/{args.space} · API: https://{host}.hf.space")


if __name__ == "__main__":
    main()
