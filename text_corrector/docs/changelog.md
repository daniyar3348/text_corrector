# Changelog

## 2026-10-28 12:50

**Task:** Демо-сайт в интернете по схеме проекта Rustem: сервер с моделью в Docker Space на Hugging Face, страница на GitHub Pages

**Changed files:**
- `frontend/src/hooks/useServerStatus.ts` (новый) — опрос `/health`, пока модель не загрузится; статусы «Подключение… / Сервер просыпается… / Модель загружена / Сервер недоступен»
- `frontend/src/App.tsx` — настоящий статус сервера вместо «Система активна», плашка «Сервер просыпается», обновлён блок «Как это работает», блок «Результаты модели»
- `frontend/src/components/ModelResults.tsx` (новый) — F1 97,3% (P 97,1 / R 97,4), 81,2% предложений целиком (oracle 83,8%), ложные 0,34%, ограничение: русская раскладка 70,0% / 54,9%
- `frontend/src/services/api.ts` — таймаут 60 с (health 10 с), понятная ошибка для спящего сервера (нет ответа / 502–504)
- `frontend/src/main.tsx` — `basename` из `BASE_URL` для пути `/turan-demo/`
- `frontend/src/pages/ModelVisualization.tsx`, `components/NeuralNetDiagram.tsx` — описание реальной модели: 6 слоёв, ~83 млн параметров, голова KEEP/ERROR вместо MLM; шаги конвейера как в коде
- `frontend/index.html`, `frontend/public/favicon.svg` (новый) — описание без русского, иконка (раньше 404)
- `frontend/scripts/build_pages.sh` (новый) — сборка страницы в копию репозитория `turan-demo`
- `backend/scripts/deploy_space.py` (новый), `backend/space/README.md` (новый) — заливка Space одним коммитом, переменная `ALLOWED_ORIGINS`
- `backend/scripts/eval_stress.py` (новый) — стресс-тесты детектора (цифры для сайта)
- `backend/Dockerfile.serve` — пользователь с UID 1000 (так запускает Spaces)
- `~/Desktop/Projects/turan-demo` (отдельный репозиторий) — собранная страница, 404.html, .nojekyll, `keep-awake.yml`, README с результатами

**Notes:** Space `daniyar51/turan-text-corrector` публичный, Docker, cpu-basic; собрался за ~3 мин, `/health` показывает TransformerModel, `/correct-text` ~100 мс, `/correct-file` работает. Прокси Hugging Face сам отражает любой Origin в `access-control-allow-origin`, поэтому `ALLOWED_ORIGINS` на Space фактически ничего не ограничивает (API и так публичный, куки не используются). Собранная страница проверена локально с живым Space: «Салем» → «Сәлем», ошибок в консоли нет. Коммиты text_corrector: 730f2eb, d4867fe, ba0e5c2 (не запушены).

**Remaining:** Создать публичный репозиторий `daniyar3348/turan-demo` и включить Pages — `gh repo create … --public` заблокирован автофильтром разрешений, ждём пользователя. После этого проверить https://daniyar3348.github.io/turan-demo/ и переход на `/turan-demo/visualization`.

---
