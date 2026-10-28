# Progress

**Last updated:** 2026-10-28 12:55

## Current Task
Выложить сайт Turan в интернет: сервер с моделью в Docker Space на Hugging Face, страница на GitHub Pages.

## Completed Steps
- Space `daniyar51/turan-text-corrector` (публичный, Docker, cpu-basic): https://daniyar51-turan-text-corrector.hf.space
- Репозиторий `daniyar3348/turan-demo` (публичный) + GitHub Pages: https://daniyar3348.github.io/turan-demo/
- Сайт проверен вживую (десктоп и 375 px), keep-awake Action проходит
- Коммиты text_corrector в ветке `claude/bold-greider-0de332`: 730f2eb, d4867fe, ba0e5c2, bfc65cb + правка кнопок и этот файл

## In Progress
- (нет)

## Remaining
- Запушить ветку `claude/bold-greider-0de332` в daniyar3348/text_corrector (описание Space и README демо ссылаются на `deploy_space.py` и `build_pages.sh`) — по решению пользователя
- По желанию: свой домен (.kz на hoster.kz), как у iuth-cyberbullying.kz

## Changed Files
- см. CHANGELOG.md

## Resume From
Обновление: сервер — `python text_corrector/backend/scripts/deploy_space.py`; страница — `bash text_corrector/frontend/scripts/build_pages.sh ~/Desktop/Projects/turan-demo`, затем commit + push в turan-demo.
