---
title: Turan Text Corrector
emoji: ✏️
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 8000
pinned: false
short_description: Kazakh spelling correction (KazRoBERTa + lexicon)
---

# Turan Text Corrector — сервер демо

Исправление орфографии казахского текста: детектор ошибок KazRoBERTa
(token classification, KEEP / ERROR) + корректор по словарю. Страница демо:
https://daniyar3348.github.io/turan-demo/

- `POST /correct-text` — `{"text": "Бул маселе оте манызды."}` → исправленный текст и список исправлений
- `POST /correct-file` — документ `.txt`, `.docx`, `.pdf` … до 5 МБ
- `POST /detect-language`, `GET /health`, документация API — `/docs`

Русский текст распознаётся, но не исправляется.

Код: https://github.com/daniyar3348/text_corrector — Space собирается из `backend/`
скриптом `backend/scripts/deploy_space.py` (Dockerfile = `backend/Dockerfile.serve`).
