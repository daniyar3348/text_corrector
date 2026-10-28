# Progress

**Last updated:** 2026-10-28 13:35

## Current Task
Вынести обученную модель в отдельный репозиторий на Hugging Face; Space берёт её оттуда, сайт по-прежнему шлёт текст в Space и показывает исправленный текст.

## Completed Steps
- Репозиторий модели `daniyar51/kazroberta-kazakh-spelling-detector` (публичный): веса, токенизатор, `kk_lexicon.tsv`, описание модели; ревизия d0459c3
- `backend/model_card/README.md`, `backend/scripts/publish_model.py`; `backend/space/Dockerfile` скачивает модель по зафиксированной ревизии; `deploy_space.py` заливает только код (из Space удалены веса и словарь)
- На сайте ссылка «Модель на Hugging Face» в блоке «Результаты модели»

## In Progress
- (нет)

## Remaining
- Слить PR #1 в main
- Хостинг ps.kz не отключать, пока DNS-зона correctecor.kz в его Plesk: сначала перенести зону в «Управление DNS» консоли ps.kz
- Продлить домен correctecor.kz до 15.10.2027 (автопродление выключено); подписка HF PRO нужна для Docker Space

## Changed Files
- см. CHANGELOG.md

## Resume From
Когда Space в RUNNING и `/health` = TransformerModel: `python text_corrector/backend/scripts/deploy_space.py` (README), `bash text_corrector/frontend/scripts/build_pages.sh ~/Desktop/Projects/turan-demo`, commit + push в turan-demo и в ветку.
