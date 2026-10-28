# Progress

**Last updated:** 2026-10-28 12:50

## Current Task
Выложить сайт Turan в интернет по схеме проекта Rustem: сервер с моделью в Docker Space на Hugging Face, страница на GitHub Pages.

## Completed Steps
- Коммиты text_corrector в ветке `claude/bold-greider-0de332` (не запушены): 730f2eb, d4867fe, ba0e5c2
- Space `daniyar51/turan-text-corrector` (публичный, Docker, cpu-basic) собран и работает: https://daniyar51-turan-text-corrector.hf.space — реальная модель, `/correct-text` и `/correct-file` проверены
- `~/Desktop/Projects/turan-demo`: собранная страница + keep-awake Action + README, локальный коммит 160f844; проверено локально с живым Space
- CHANGELOG.md и docs/changelog.md

## In Progress
- (нет) — ждём пользователя

## Remaining
- Создать публичный репозиторий `daniyar3348/turan-demo` и включить Pages: автофильтр заблокировал `gh repo create --public`
- Проверить https://daniyar3348.github.io/turan-demo/ и `/turan-demo/visualization` (через 404.html)

## Changed Files
- см. CHANGELOG.md (запись 2026-10-28 12:50)

## Resume From
В `~/Desktop/Projects/turan-demo`: `gh repo create daniyar3348/turan-demo --public --source . --remote origin --push`, затем `gh api -X POST repos/daniyar3348/turan-demo/pages -f 'source[branch]=main' -f 'source[path]=/'`; дождаться сборки Pages и проверить сайт в браузере.
