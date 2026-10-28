# Progress

**Last updated:** 2026-10-28 13:35

## Current Task
Вынести обученную модель в отдельный репозиторий на Hugging Face; Space берёт её оттуда, сайт по-прежнему шлёт текст в Space и показывает исправленный текст.

## Completed Steps
- Репозиторий модели `daniyar51/kazroberta-kazakh-spelling-detector` (публичный): веса, токенизатор, `kk_lexicon.tsv`, описание модели; ревизия d0459c3
- `backend/model_card/README.md`, `backend/scripts/publish_model.py`; `backend/space/Dockerfile` скачивает модель по зафиксированной ревизии; `deploy_space.py` заливает только код (из Space удалены веса и словарь)
- На сайте ссылка «Модель на Hugging Face» в блоке «Результаты модели»

## In Progress
- Пересборка Space без весов внутри; проверка примера кода из описания модели

## Remaining
- Залить обновлённый `space/README.md` в Space, пересобрать страницу и запушить turan-demo, коммит + push ветки (PR #1 обновится), CHANGELOG

## Changed Files
- см. CHANGELOG.md

## Resume From
Когда Space в RUNNING и `/health` = TransformerModel: `python text_corrector/backend/scripts/deploy_space.py` (README), `bash text_corrector/frontend/scripts/build_pages.sh ~/Desktop/Projects/turan-demo`, commit + push в turan-demo и в ветку.
