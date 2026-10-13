# Turan Text Corrector — Инструкция администратора

> Аудитория: администратор / DevOps.
> Назначение документа: развернуть, настроить, обслуживать и диагностировать сервинг корректора казахского текста.
> Последнее обновление: 2026-06-20.

---

## 0. Что это за сервис (коротко)

**Turan Text Corrector** — автоматический корректор орфографии **казахского** текста.

- Русский путь — **NO-OP**: текст не меняется (обученной русской модели нет, отдаётся как есть).
- Архитектура казахского пути:
  1. **Языковой роутер** (`language_detection.py`) определяет язык;
  2. для казахского — **KazRoBERTa-ДЕТЕКТОР ошибок** (token-classification, базовый чекпойнт `kz-transformers/kaz-roberta-conversational`) размечает каждый токен меткой `KEEP` или `ERROR` (`id2label {0:KEEP, 1:ERROR}`);
  3. **КОРРЕКТОР** (`kazakh_corrector.py`: инверсные правила ru↔kk + лексикон 174k словоформ + OSA edit-distance) чинит только помеченные слова.
- Качество (тест 8000): детекция F1 **97.3 %** (P 97.1 / R 97.4); сквозная коррекция **80.5 %** предложений идеально; корректор при oracle-детекции — **88 %**.
- Производительность: тёплый запрос ~**9 мс**; под нагрузкой ~**150–200 req/s** (упирается в CPU); контейнер потребляет ~**373 МБ RAM**.
- Эндпоинты (FastAPI):
  - `POST /correct-text` `{"text":"..."}` → `{original_text, corrected_text, detected_language, confidence, corrections[], processing_time_ms, status}`
  - `POST /detect-language` `{"text":"..."}` → `{detected_language, confidence, status}`
  - `GET /health` → в `details` поля `kazakh_model` и `kazakh_model_ready`
  - Интерактивная документация: `/docs`

**Важно про модель и placeholder.** Если torch/transformers недоступны или путь к модели не задан/неверен, приложение **тихо** деградирует на `PlaceholderModel` (заглушка), а `/health` на первый взгляд может выглядеть «зелёным». Поэтому healthcheck в Docker специально проверяет, что загружена **реальная** модель `TransformerModel`, а не заглушка (см. раздел «Управление → Healthcheck»).

---

## 1. Требования

### Для ML-пути (реальная модель)
- **Python 3.13** + **torch** (плюс `transformers`, `safetensors`, `rapidfuzz`, `fastapi`, `uvicorn`, `pydantic-settings`, `python-dotenv`).
  - В репозитории это окружение `backend/.venv-train` (Python 3.13, `torch==2.12.1+cpu` (как в `backend/requirements-serve.txt`), `transformers==5.12.1`).
  - ⚠️ Окружение `backend/.venv` — Python **3.14**, в нём **нет torch** (под 3.14 нет колёс) → модель НЕ грузится, происходит фолбэк на заглушку. Для сервинга модели его использовать **нельзя**.
- Артефакт модели: `backend/models/kazakh_detector/` (`config.json`, `model.safetensors` ~316 МБ, `tokenizer.json`, `tokenizer_config.json`).
- Лексикон: `backend/data/kk_lexicon.tsv`.
- ~1 ГБ свободной RAM на воркер (каждый воркер грузит свою копию модели ~316 МБ; рабочий контейнер ~373 МБ RAM).

### Для Docker-пути
- **colima** + **docker** CLI (на этой машине Docker daemon — colima, arm64):
  ```bash
  brew install colima docker
  ```
- ~3 ГБ под образ (`turan-serve:latest` ~**2.84 ГБ**, arm64). Модель и лексикон **вшиты** в образ — путь к хосту/volume не нужен.
- colima рекомендуется поднимать с ресурсами `--cpu 4 --memory 4` (так делает `deploy.sh`).

---

## 2. Запуск ЛОКАЛЬНО (uvicorn, без Docker)

Запускать из каталога `backend/` (пути относительные). `.env` лежит в `text_corrector/.env` (НЕ в `backend/`).

```bash
cd /Users/daniyar/Desktop/Turan_project/text_corrector/backend

# Один воркер:
KAZAKH_MODEL_PATH=$PWD/models/kazakh_detector \
  ./.venv-train/bin/uvicorn app.main:app --host 127.0.0.1 --port 8010

# Несколько воркеров (throughput; каждый воркер = своя копия модели ~316 МБ RAM):
KAZAKH_MODEL_PATH=$PWD/models/kazakh_detector \
  ./.venv-train/bin/uvicorn app.main:app --host 127.0.0.1 --port 8010 --workers 4
```

Почему порт **8010**, а не 8000: порт 8000 на этой машине занят другим приложением (Crypto Bata).

Переменные окружения, важные для локального запуска:
- `KAZAKH_MODEL_PATH` — путь к каталогу модели. **Обязателен** для активации реальной модели. Если пустой/не задан → заглушка.
- Остальные настройки берутся из `text_corrector/.env` (см. раздел «Конфигурация»).

### Проверка после старта
```bash
# Здоровье (должно быть kazakh_model_ready: "True" и TransformerModel в kazakh_model):
curl -s http://127.0.0.1:8010/health | python3 -m json.tool

# Smoke-коррекция казахского:
curl -s -X POST http://127.0.0.1:8010/correct-text \
  -H 'Content-Type: application/json' \
  --data-binary '{"text":"Бул маселе оте манызды болып тур."}' | python3 -m json.tool
```

Если `/health` показывает `PlaceholderModel` или `kazakh_model_ready` ≠ `"True"` — модель НЕ загрузилась (см. TROUBLESHOOTING).

---

## 3. Запуск через DOCKER

### 3.1. Быстрый путь — `deploy.sh` (рекомендуется)

```bash
bash /Users/daniyar/Desktop/Turan_project/text_corrector/backend/scripts/deploy.sh
```

Скрипт идемпотентный (можно гонять повторно), запускается из любого каталога. Что он делает по шагам:

1. **1/5 — Docker daemon (colima).** Проверяет наличие `docker` CLI (иначе подсказывает `brew install colima docker` и выходит). Если colima не запущена — поднимает её: `colima start --cpu 4 --memory 4`.
2. **2/5 — Сборка образа.** `docker build -f backend/Dockerfile.serve -t turan-serve:latest backend`.
3. **3/5 — Запуск контейнера.** Сносит старый контейнер `turan-serve` (если есть), затем `docker run -d --name turan-serve -p 8010:8000 -e KAZAKH_MODEL_PATH=/app/models/kazakh_detector turan-serve:latest`. Хост-порт можно переопределить переменной `PORT` (по умолчанию **8010**).
4. **4/5 — Ожидание healthy.** Поллит `docker inspect` до состояния `healthy` (загрузка модели ~1–2 мин; до 120 попыток по 2 с). Если `unhealthy` или таймаут — печатает последние 40 строк логов и выходит с ошибкой.
5. **5/5 — Гейт-проверка + smoke.** Проверяет, что в логах есть `TransformerModel (detector+corrector) loaded` (значит загружена реальная модель, а не placeholder), затем шлёт тестовый запрос на `/correct-text` и печатает `original → corrected`.

По завершении сервис доступен на `http://127.0.0.1:8010`, контейнер называется `turan-serve`, логи — `docker logs -f turan-serve`.

Переопределить порт:
```bash
PORT=8020 bash /Users/daniyar/Desktop/Turan_project/text_corrector/backend/scripts/deploy.sh
```

### 3.2. Ручная сборка и запуск (одиночный контейнер)

```bash
# Контекст сборки ДОЛЖЕН быть ./backend:
docker build \
  -f /Users/daniyar/Desktop/Turan_project/text_corrector/backend/Dockerfile.serve \
  -t turan-serve \
  /Users/daniyar/Desktop/Turan_project/text_corrector/backend

docker run -d --name turan-serve \
  -p 8010:8000 \
  -e KAZAKH_MODEL_PATH=/app/models/kazakh_detector \
  turan-serve
```

Что заложено в `Dockerfile.serve` (полезно знать админу):
- Двухстадийная сборка: builder ставит зависимости из `requirements-serve.txt` (включая `torch==2.12.1+cpu` с CPU-индекса PyTorch), runtime — лёгкий `python:3.13-slim`.
- В runtime обязательно ставится **`libgomp1`** — CPU-колесо torch динамически линкует OpenMP (`libgomp.so.1`) при `import torch`; без него импорт падает и сервис тихо уходит в placeholder. Это «несущая» строка.
- Модель (`models/kazakh_detector/`) и лексикон (`data/kk_lexicon.tsv`) **копируются внутрь образа** — образ самодостаточный, volume не нужен.
- `ENV KAZAKH_MODEL_PATH=/app/models/kazakh_detector`, `HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1` (офлайн, без обращений к Hub).
- Контейнер слушает порт **8000** внутри; наружу прокидывается хост-порт.
- По умолчанию **один воркер**. Для throughput: добавьте `--workers N` в `CMD` (RAM растёт линейно с числом воркеров).
- `HEALTHCHECK` проверяет, что загружена реальная модель (см. раздел «Управление»).

### 3.3. Полный стек через docker-compose (backend + frontend)

```bash
cd /Users/daniyar/Desktop/Turan_project/text_corrector
BACKEND_PORT=8010 docker-compose up --build
```

- `BACKEND_PORT=8010` — потому что хост-порт 8000 занят (Crypto Bata). По умолчанию compose взял бы 8000.
- Сервисы:
  - `backend` (`turan_backend`) — порт `${BACKEND_PORT:-8000}:8000`, `restart: unless-stopped`, читает `.env`, принудительно ставит `KAZAKH_MODEL_PATH=/app/models/kazakh_detector` (перекрывает пустое значение из `.env`).
  - `frontend` (`turan_frontend`) — порт `${FRONTEND_PORT:-3000}:80`, поднимается только после `backend` → `service_healthy`.
- Чтобы итерировать по модели без пересборки образа — в compose есть закомментированный volume:
  ```yaml
  volumes:
    - ./backend/models/kazakh_detector:/app/models/kazakh_detector:ro
  ```

Остановить стек:
```bash
cd /Users/daniyar/Desktop/Turan_project/text_corrector
BACKEND_PORT=8010 docker-compose down
```

---

## 4. Конфигурация

### Файл `.env`
Расположение: **`/Users/daniyar/Desktop/Turan_project/text_corrector/.env`** (в корне проекта, НЕ в `backend/`). Читается через Pydantic Settings (`app/core/config.py`).

Ключевые переменные (имена чувствительны к регистру):

| Переменная | По умолчанию | Назначение |
|---|---|---|
| `KAZAKH_MODEL_PATH` | `None` (в `config.py`); в репозиторном `.env` задано пустой строкой | Путь к каталогу модели. **Пусто/не задано → заглушка** (русско-пассивный режим, казахский НЕ исправляется). В Docker задаётся `=/app/models/kazakh_detector`. |
| `RUSSIAN_MODEL_PATH` | `None` (в `config.py`); в репозиторном `.env` задано пустой строкой | Путь к русской модели. Её нет → русский всегда pass-through. |
| `MAX_TEXT_LENGTH` | `5000` | Максимум символов на входе. |
| `MIN_TEXT_LENGTH` | `1` | Минимум символов. **В `.env` не задаётся** — берётся значение по умолчанию из `config.py` (`1`). |
| `LOG_REQUESTS` | `true` | Логировать ли входящие запросы. |
| `LOG_LEVEL` | `INFO` | Уровень логирования. |
| `HOST` | `0.0.0.0` | Адрес привязки. |
| `PORT` | `8000` | Порт **внутри** приложения/контейнера. |
| `CORRECTION_SIMILARITY_THRESHOLD` | `0.55` | Мин. сходство (rapidfuzz) для принятия кандидата коррекции. |
| `MAX_EDIT_DISTANCE` | `3` | Макс. расстояние редактирования при подборе кандидата. |
| `DEBUG` | `false` | Режим отладки. |
| `BACKEND_PORT` | `8000` | Хост-порт backend (только compose; ставьте `8010`). |
| `FRONTEND_PORT` | `3000` | Хост-порт frontend (только compose). |

### Порты — сводка
- Внутри контейнера/приложения backend всегда слушает **8000**.
- Наружу мапим **8010** (8000 занят Crypto Bata): `-p 8010:8000` или `BACKEND_PORT=8010`.
- Frontend (если поднимается): хост **3000** → контейнер **80**; dev-сервер Vite — **5173**.

### Приоритет источников `KAZAKH_MODEL_PATH`
1. Переменная окружения / флаг `-e` в `docker run` / блок `environment` в compose (наивысший приоритет — compose жёстко ставит правильный путь).
2. Значение из `.env`.
3. Если пусто/только пробелы → `load_model()` считает путь незаданным и возвращает `PlaceholderModel`.

---

## 5. Управление

### Docker-контейнер
```bash
docker ps                       # список запущенных контейнеров
docker logs -f turan-serve      # живые логи (Ctrl+C для выхода)
docker logs --tail 40 turan-serve   # последние 40 строк
docker stop turan-serve         # остановить
docker start turan-serve        # запустить снова
docker restart turan-serve      # перезапуск
docker rm -f turan-serve        # удалить контейнер (образ останется)
docker stats turan-serve        # CPU / RAM в реальном времени
```

### colima (Docker daemon)
```bash
colima status                   # состояние daemon
colima start --cpu 4 --memory 4 # запустить daemon
colima stop                     # остановить daemon (контейнеры тоже встанут)
```

### Healthcheck — проверяет РЕАЛЬНУЮ модель, а не placeholder
Healthcheck (в `Dockerfile.serve` и `docker-compose.yml`) дёргает `GET /health` и считает контейнер здоровым **только если**:
- `details.kazakh_model_ready == "True"`, И
- в `details.kazakh_model` присутствует подстрока `TransformerModel`.

Параметры: `interval=30s`, `timeout=10s`, `start-period=120s` (на импорт torch + загрузку модели 316 МБ + лексикона), `retries=3`.

То есть если приложение тихо деградировало на `PlaceholderModel[Kazakh]`, healthcheck это **поймает** и контейнер станет `unhealthy` (а не ложно-зелёным).

Ручная проверка состояния health:
```bash
docker inspect -f '{{.State.Health.Status}}' turan-serve
curl -s http://127.0.0.1:8010/health | python3 -m json.tool
```

Признак успешной загрузки в логах:
```
TransformerModel (detector+corrector) loaded for language=Kazakh from ...
```

---

## 6. Обновление модели

Модель **вшита в образ** (volume по умолчанию не используется), поэтому новую версию надо положить на место и **пересобрать образ**.

1. Заменить артефакт модели на хосте:
   ```
   /Users/daniyar/Desktop/Turan_project/text_corrector/backend/models/kazakh_detector/
   ```
   Должны быть файлы: `config.json`, `model.safetensors`, `tokenizer.json`, `tokenizer_config.json` (берите только файлы корня модели, без `checkpoint-*`).
2. Пересобрать образ и перезапустить:
   ```bash
   bash /Users/daniyar/Desktop/Turan_project/text_corrector/backend/scripts/deploy.sh
   ```
   либо вручную `docker build ...` + `docker run ...` (см. раздел 3.2), либо `BACKEND_PORT=8010 docker-compose up --build`.
3. Дождаться `healthy` и убедиться, что в логах есть `TransformerModel (detector+corrector) loaded`, а `/health` отдаёт `kazakh_model_ready: "True"`.

**Быстрая итерация без пересборки** (только для отладки): раскомментировать volume в `docker-compose.yml` (см. 3.3) и монтировать `./backend/models/kazakh_detector` внутрь контейнера — тогда смена файлов модели не требует `docker build`.

> Если меняете и лексикон — кладите новый `backend/data/kk_lexicon.tsv` и так же пересоберите образ (он копируется внутрь).

---

## 7. Логи и мониторинг

- **Логи приложения** — в stdout/stderr контейнера: `docker logs -f turan-serve`. Для compose: `docker-compose logs -f backend`.
- **Логирование запросов** управляется `LOG_REQUESTS` (по умолчанию `true`), уровень — `LOG_LEVEL` (`INFO`).
- **Метрики ресурсов**: `docker stats turan-serve` (ожидаемо ~**373 МБ RAM** на 1 воркер).
- **Health**: `docker inspect -f '{{.State.Health.Status}}' turan-serve` + периодический `curl /health`.
- **Производительность**: тёплый запрос ~9 мс; потолок ~150–200 req/s (CPU-bound). При росте нагрузки добавляйте воркеры (`--workers N`), помня про RAM на воркер.

Ключевые строки в логах, на которые стоит настроить алерты/grep:
- `TransformerModel (detector+corrector) loaded` — норма (модель поднялась).
- `torch/transformers unavailable` — деградация на placeholder (нет torch).
- `Failed to load detector from ...` — модель не загрузилась (битые файлы / нехватка памяти).
- `path ... does not exist. Falling back to placeholder` — неверный `KAZAKH_MODEL_PATH`.
- `using PlaceholderModel instead` — итоговый фолбэк на заглушку.

---

## 8. TROUBLESHOOTING

### Контейнер `unhealthy` / в логах `Failed to load detector` или `torch/transformers unavailable`
Причина: модель не поднялась → приложение работает как заглушка (казахский не исправляется).
- **Нет `libgomp1`** в runtime-образе → `import torch` падает. В `Dockerfile.serve` строка установки `libgomp1` обязательна; если собирали кастомный образ — верните её. Проверка внутри контейнера:
  ```bash
  docker exec turan-serve python -c "import torch; print(torch.__version__)"
  ```
  Если падает с ошибкой про `libgomp.so.1` — это оно.
- **Нет torch/transformers** (например, локально запустили на `.venv` с Python 3.14) → используйте `.venv-train` (Python 3.13 с torch) для локального сервинга.
- После исправления: пересобрать образ (`deploy.sh`) и дождаться `healthy`.

### `/health` зелёный, но казахский не исправляется (placeholder вместо модели)
- Проверьте `details.kazakh_model` в `/health`: должно быть `TransformerModel[Kazakh]@...`, а не `PlaceholderModel[Kazakh]`.
- Самые частые причины: пустой/неверный `KAZAKH_MODEL_PATH`, отсутствуют файлы модели, нет torch.
- Проверьте, что путь существует и в нём есть `model.safetensors`, `config.json`, `tokenizer.json`:
  ```bash
  docker exec turan-serve ls -la /app/models/kazakh_detector
  ```
- Напоминание: Docker healthcheck такое НЕ пропустит (он требует `TransformerModel`), но при ручном запуске uvicorn без healthcheck деградацию можно не заметить — всегда сверяйтесь с `/health`.

### Порт занят (`address already in use` / `bind: address already in use`)
- Хост-порт 8000 на этой машине занят Crypto Bata — используйте **8010** (`-p 8010:8000`, `PORT=8010 deploy.sh`, `BACKEND_PORT=8010`).
- Кто держит порт:
  ```bash
  lsof -nP -iTCP:8010 -sTCP:LISTEN
  ```
- Если занят старым контейнером Turan:
  ```bash
  docker rm -f turan-serve
  ```
  затем перезапустить.

### Нехватка памяти (контейнер падает / OOM при старте многих воркеров)
- Каждый воркер грузит свою копию модели (~316 МБ) → RAM растёт линейно с `--workers N`.
- Поднимите ресурсы colima:
  ```bash
  colima stop
  colima start --cpu 4 --memory 8
  ```
- Уменьшите число воркеров. Для пилота 1 воркер даёт ~193 req/s, 4 воркера ~200 req/s — рост невелик (упор в CPU), так что много воркеров обычно не нужно.

### Контейнер долго `starting`
- Это норма: `start-period=120s`. Загрузка torch + модели 316 МБ + лексикона занимает ~1–2 мин. Healthcheck не считается проваленным в течение start-period. Подождите.

### colima/docker не найдены
```bash
brew install colima docker
colima start --cpu 4 --memory 4
```

### Русский текст «портится» / меняется
- Русская модель не обучена; ожидаемое и гарантированное поведение — **pass-through (no-op) во всех режимах**: `correct_russian()` возвращает текст без изменений. Словарь к русскому **не применяется ни в каком режиме** (включая placeholder), так что риска повредить валидный русский нет. Если русский текст всё-таки изменился — ищите причину не в русском пути, а в неверном определении языка (роутер принял русский текст за казахский). Единственная причина не подавать русский — он просто не будет исправлен (русской модели нет), а не потому что он «портится».

---

## 9. Ограничения (чтобы не принять за баг)

- **OOV** (редкие имена / неологизмы вне лексикона 174k) — корректор их НЕ генерирует, но и **не калечит**: оставляет как есть. Безопасный failure mode.
- **Короткие обрывки (1–2 слова)** — язык труднее определить, детекция слабее (модель училась на полных предложениях).
- **Ошибки типа drop / sub** чинятся слабее (~62 % / ~70 %) — неоднозначны без контекста.
- **Русский путь** — всегда no-op (нет обученной русской модели).

---

## 10. Полезные пути (абсолютные)

- Корень проекта: `/Users/daniyar/Desktop/Turan_project/text_corrector/`
- `.env`: `/Users/daniyar/Desktop/Turan_project/text_corrector/.env`
- Скрипт деплоя: `/Users/daniyar/Desktop/Turan_project/text_corrector/backend/scripts/deploy.sh`
- Dockerfile сервинга: `/Users/daniyar/Desktop/Turan_project/text_corrector/backend/Dockerfile.serve`
- docker-compose: `/Users/daniyar/Desktop/Turan_project/text_corrector/docker-compose.yml`
- Зависимости сервинга: `/Users/daniyar/Desktop/Turan_project/text_corrector/backend/requirements-serve.txt`
- Конфиг (Settings): `/Users/daniyar/Desktop/Turan_project/text_corrector/backend/app/core/config.py`
- Загрузчик модели: `/Users/daniyar/Desktop/Turan_project/text_corrector/backend/app/models/model_loader.py`
- Артефакт модели: `/Users/daniyar/Desktop/Turan_project/text_corrector/backend/models/kazakh_detector/`
- Лексикон: `/Users/daniyar/Desktop/Turan_project/text_corrector/backend/data/kk_lexicon.tsv`
- ML/serving venv (Python 3.13 + torch): `/Users/daniyar/Desktop/Turan_project/text_corrector/backend/.venv-train`
- Справочные документы: `docs/PILOT_REPORT.md`, `docs/WORKLOG.md`, `README.md`
