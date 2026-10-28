# Changelog

## 2026-10-28 13:15

**Task:** Сайт демо переведён на свой домен correctecor.kz (ps.kz)

**Changed files:**
- DNS `correctecor.kz` в Plesk (srv-plesk62.ps.kz, хостинг ps.kz): A корня 194.39.65.24 → 185.199.108–111.153 (GitHub Pages), AAAA 2a00:5da0:1000::166 → 2606:50c0:8000–8003::153, `www` CNAME correctecor.kz → daniyar3348.github.io. Почтовые записи (MX, mail, webmail, SPF, DKIM, SRV) не тронуты
- `daniyar3348/turan-demo` — custom domain correctecor.kz, сертификат Let's Encrypt (корень + www), HTTPS обязателен; сборка под корень домена, файл `CNAME` (2320aae)
- `frontend/scripts/build_pages.sh` — `DOMAIN` (по умолчанию correctecor.kz, пишет CNAME), `BASE=/` по умолчанию
- `backend/scripts/deploy_space.py` — `ALLOWED_ORIGINS` с доменом; переменная в Space обновлена
- `backend/space/README.md` — ссылка на https://correctecor.kz (залито в Space)

**Notes:** До переключения на домене была только заглушка ps.kz «Домен припаркован» с недействительным сертификатом Plesk; хостинг в Plesk пустой, почтовых ящиков нет. Проверено: Google, Cloudflare, Quad9 и Яндекс DNS уже отдают адреса GitHub; https://correctecor.kz → 200, http → 301 на https, www и daniyar3348.github.io/turan-demo/ → 301 на https://correctecor.kz/, `/visualization` открывается через 404.html, CORS для https://correctecor.kz. У старых записей был TTL 86400, поэтому провайдерские и локальные кэши могут показывать заглушку ps.kz до 24 часов. Хостинг ps.kz (тариф M, 19 530 ₸/год) и SSL на ps.kz сайту больше не нужны.

---
## 2026-10-28 12:55

**Task:** Публикация демо завершена: отдельный публичный репозиторий `daniyar3348/turan-demo` с GitHub Pages

**Changed files:**
- `frontend/src/App.tsx` — кнопки под полем ввода переносятся на узком экране (на 375 px «Очистить» обрезалась)
- `~/Desktop/Projects/turan-demo` — репозиторий создан и запушен (160f844, aeb0f8b), Pages включены из `main` /

**Notes:** Сайт https://daniyar3348.github.io/turan-demo/ работает с сервером https://daniyar51-turan-text-corrector.hf.space: статус «Модель загружена», пример «Бул маселе оте манызды болып тур.» → «Бұл мәселе өте маңызды болып тұр.» (5 исправлений), ошибок в консоли нет, на 375 px нет горизонтальной прокрутки. Прямая ссылка `/turan-demo/visualization` открывается через 404.html (HTTP-код 404, страница рабочая). Ручной запуск `keep-awake.yml` прошёл успешно.

---
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

---
