# Turan Text Corrector — журнал работы (handoff)

> Документ для переноса работы в новую сессию без потери контекста.
> Последнее обновление: 2026-06-19. Ветка git: `stage4-morphology-integration`.

## 1. Что это и где мы

**Проект:** `~/Desktop/Turan_project/text_corrector` — RU/KK корректор орфографии.
FastAPI backend (порт 8000) + React/Vite frontend (порт 5173).
**7-этапный план:** разработка → интеграция → апробация → **оптимизация (этап 4)** → пилот (5) → обучение (6) → отчётность (7). Этапы 1–3 готовы.

**Этап 4 — ЗАВЕРШЁН (2026-06-19).** Цель была: «единый механизм» коррекции казахского =
**KazRoBERTa-детектор ошибок + корректор (морфология/правила/лексикон)**. Сделано и провалидировано.

Следующий — **этап 5 (пилотный запуск)**.

---

## 2. Итоговые метрики (eval_end2end.py, 8000 тестовых записей)

| Система | Детекция F1 | Сквозь (предложений исправлено полностью) |
|---|---|---|
| Baseline: эвристика (нет в лексиконе) + корректор | 86.3% | 64.6% |
| **Обученный KazRoBERTa-детектор + корректор** | **97.3%** (P 97.1 / R 97.4) | **80.5%** |
| Потолок: oracle-детекция + корректор | 100% | 83.5% |

**Корректор при oracle-детекции по типам ошибок:** ka2ru 97.6% · harmony 97.9% · dup 93% · swap 83% · sub 70% · drop 62%. Итого 88% исправлено, точность изменений 91.6%.

Вывод: детекция фактически решена (почти потолок), остаток — пределы корректора на drop/sub.

---

## 3. Окружения (важно!)

- **`backend/.venv`** — Python **3.14**. Это API-venv: есть `rapidfuzz`, `pydantic`, `fastapi`, НО **нет torch** (под 3.14 нет колёс). На нём ML-модель НЕ грузится → graceful-фолбэк на PlaceholderModel.
- **`backend/.venv-train`** — Python **3.13**. ML/serving-окружение: `torch 2.12`, `transformers 5.12`, `datasets 5.0`, `accelerate 1.14`, `rapidfuzz`, `pydantic-settings`, `python-dotenv`. Запускать инференс/eval модели **только отсюда**.
- Запускать скрипты из каталога `backend/` (пути относительные). `.env` лежит в `text_corrector/.env` (НЕ в backend).

---

## 4. Файлы, созданные/изменённые на этапе 4

**Очистка/данные (`backend/scripts/`):**
- `kk_text.py` — общий модуль очистки корпуса: NFC, нормализация двойников (`ə→ә`, `ћ→һ`), сегментация со склейками, удаление иноязычных вставок и невидимых/PUA символов, проверка сингармонизма, потоковый JSON-ридер, `sentences_from_text()`.
- `assess_corpus.py` — оценка «грамотности» корпуса (сингармонизм, чистота письма).
- `build_kazakh_dataset.py` — сборщик датасета (стадии `extract`→`inject`; модель ошибок; аугментация `--variants`; чистые пары `--clean-ratio`).
- `build_lexicon.py` — частотный лексикон → `data/kk_lexicon.tsv`.

**Детектор:**
- `train_detector.py` — обучение KazRoBERTa (token-classification), локально/smoke.
- `colab_train_detector.ipynb` — обучение на Colab GPU (то, чем обучили финально).

**Корректор:**
- `app/services/kazakh_corrector.py` — **каноничный** `KazakhCorrector` (инверсные правила ru↔kk + лексикон + OSA edit-distance; `force=True` для слов, помеченных детектором).
- `scripts/kk_corrector.py` — тонкий реэкспорт `KazakhCorrector` (для совместимости/CLI).

**Интеграция:**
- `app/models/model_loader.py` — **изменён**: `TransformerModel` теперь = детектор+корректор.
  `_load()` лениво импортирует torch/transformers (фолбэк, если их нет), грузит HF-детектор + `KazakhCorrector`.
  `_run_inference()` = детектор размечает токены KEEP/ERROR → корректор чинит помеченные слова (пунктуация/дефисы сохраняются).

**Оценка:**
- `eval_corrector.py` — качество корректора при oracle-детекции, по типам ошибок.
- `demo_pipeline.py` — sentence-level при oracle-детекции.
- `eval_end2end.py` — сквозная оценка; режимы `heuristic` | `oracle` | `model`.

---

## 5. Данные и модель

**Источник:** `~/Desktop/Turan_project/merged_dissertation.json` (568 МБ, 93 218 казахских статей `ehistory`). Полностью скачан.

**Датасет** `backend/data/kazakh_spellcheck/` (gitignored):
- `sentences.txt` — 922 798 уникальных чистых предложений (эталон).
- `train.jsonl` — 2 565 771 пара (×3 аугментация на train), `val.jsonl` / `test.jsonl` — по 25 000.
- ~11% «чистых» пар (правильно→правильно, против переисправления). 0 утечки между split.
- Формат строки: `{"correct","corrupted","n_errors","clean","edits":[{"type","wi","before","after"}]}`.
- `meta.json`, `sample_preview.txt`.
- `colab/{train,val,test}.jsonl.gz` — компактный бандл для Colab (только `corrupted`/`correct`).

**Лексикон** `backend/data/kk_lexicon.tsv` — 339 717 словоформ; валидные (freq≥2) = 174 100.

**Модель** `backend/models/kazakh_detector/` (gitignored):
- база `kz-transformers/kaz-roberta-conversational` (MLM-энкодер, byte-BPE vocab 52 000, 6 слоёв / 12 голов / hidden 768).
- дообучена на Colab GPU, **2 эпохи = 80 182 шага**, голова token-classification `id2label {0:KEEP, 1:ERROR}`.
- файлы: `config.json`, `model.safetensors` (316 МБ), `tokenizer.json`, `tokenizer_config.json`.

---

## 6. Модель ошибок в датасете
`ka2ru` (казахская спецбуква → русский двойник, ~31%, доминирует) · `harmony` (сингармонизм) ·
`swap` (перестановка) · `drop` (пропуск) · `dup` (удвоение) · `sub` (близкая замена).

---

## 7. Ключевые решения и почему
- **Корпус чистили** перед использованием как эталон: были склейки предложений (9%→0.04%), латинская schwa `ə→ә`, сербская `ћ→һ`, иноязычные вставки, мягкие переносы/PUA.
- **Архитектура — токен-классификация (детектор), не seq2seq:** KazRoBERTa это энкодер; так нативнее, быстрее, стыкуется с морфологией. Корректор отделён.
- **OSA edit-distance** (а не полный Damerau): та же точность на перестановках, ~×10 быстрее.
- **Аугментация ×3 только train**, val/test ×1 (иначе оценка раздувается).

---

## 8. Известные ограничения (проверено эмпирически)
- **Корректор ограничен лексиконом:** если правильной формы нет в `kk_lexicon.tsv` (редкие имена, неологизмы) — он её НЕ сгенерирует. Failure mode безопасный: **оставляет слово как есть, не калечит**.
- **Детектор слабее на коротких обрывках** (мало контекста; обучался на полных предложениях).
- **drop/sub ~62/70%** — неоднозначны без контекста.

---

## 9. Как воспроизвести (команды; из `backend/`)
```bash
# Датасет (extract уже сделан → sentences.txt; пересборка пар):
./.venv/bin/python scripts/build_kazakh_dataset.py --stage inject --variants 3
# Лексикон:
./.venv/bin/python scripts/build_lexicon.py
# Оценка корректора (oracle), по типам:
./.venv/bin/python scripts/eval_corrector.py 5000
# Сквозная оценка (режимы heuristic|oracle|model):
./.venv-train/bin/python scripts/eval_end2end.py model 8000
# Живой тест полного пути:
KAZAKH_MODEL_PATH=models/kazakh_detector ./.venv-train/bin/python -c "
from app.models.model_loader import load_model
m=load_model('Kazakh','models/kazakh_detector')
print(m.correct('Бугін мектепте жана кітап окыдык.'))"
```
**Обучение (Colab):** залить `data/colab/*.jsonl.gz` в Google Drive `turan_kk_spell/`, открыть `scripts/colab_train_detector.ipynb`, Runtime→GPU, Run all. Модель сохраняется в `Drive/turan_kk_spell/kazakh_detector` (качать только файлы корня, без `checkpoint-*`).

---

## 10. Следующие шаги — этап 5 (пилот)
1. **Сервинг-окружение:** запустить backend на torch-окружении (3.13) — добавить `fastapi`/`uvicorn` в `.venv-train` (или новый serving-venv); прописать `KAZAKH_MODEL_PATH=models/kazakh_detector` в `text_corrector/.env`.
2. **Проверить роутинг** `app/services/correction_pipeline.py`: для казахского при загруженной модели должен вызываться `TransformerModel.correct()`, а не словарь-заглушка.
3. **Живой тест через API** (эндпоинт, не только напрямую).
4. **Docker/compose**, healthcheck, логирование; **нагрузочный тест** (latency/throughput) + фиксация метрик пилота.

**Опциональные апгрейды качества (обсуждались):**
- морфологическая валидация кандидата (FST / apertium-kaz **генератор**) — чинить даже OOV-формы, если они грамматически правильны;
- порог уверенности детектора — меньше пропусков/ложных правок на редких словах;
- контекстное переранжирование (MLM / n-gram LM) — добить drop/sub.

---

## 11. Мелочи / артефакты
- `~/Desktop/Turan_project/kazakh_detector.zip` (294 МБ) — архив модели, уже распакован; можно удалить.
- `.gitignore` (root) закрывает: `merged_dissertation.json`, `text_corrector/backend/data/`, `*.jsonl`; `text_corrector/.gitignore` — `.venv-train/`, `models/*/`.
- Постоянная память сессий: `~/.claude/projects/-Users-daniyar/memory/turan-text-corrector.md` (автозагружается, самый свежий статус).

## 12. Этап 5 — статус (обновлено 2026-06-19)
**Сделано:**
- Сервинг на torch-окружении `.venv-train` (3.13) + fastapi/uvicorn. Роутинг пайплайна уже корректен (модель → `TransformerModel.correct()`).
- Живой API проверен: `/health` (модель loaded), `/correct-text` исправляет казахский.
- **Throughput-фиксы:** оба эндпоинта `async→def`, `torch.set_num_threads(1)`, прогрев модели на старте. Замеры: 1 воркер 193 req/s; 4 воркера ~200 req/s, p50 85мс. Потолок CPU ≈200 req/s (ок для пилота).
- **Docker сервинг написан + адверсариально проверен (SHIP, блокеров нет):** `backend/Dockerfile.serve`, `backend/requirements-serve.txt`, `backend/.dockerignore`, обновлён `docker-compose.yml`. Критичные фиксы: `libgomp1` в runtime, `torch==2.12.1+cpu` (wheel подтверждён на CPU-индексе), healthcheck проверяет реальную модель, `load_model` игнорирует пустой путь, `numpy<2.5`.

**Пилот принят live (2026-06-20):** `scripts/pilot_acceptance.py` зелёный — 6/6 фраз исправлены, чистый текст не тронут, логирование ок, ~150–200 req/s. Приёмка нашла и устранила баг роутинга (ka2ru-казахский без спецбукв уходил в русский) — фикс в `language_detection.py` (russify-lexicon сигнал), 48 тестов проходят. Отчёт: `docs/PILOT_REPORT.md`.

**Docker собран и развёрнут локально (2026-06-20):** поставлен colima (Docker daemon, arm64) через brew; собран `turan-serve:latest` (2.84 ГБ, arm64), контейнер **healthy** на :8010 (~373 МБ RAM). Адверсариальная проверка живого контейнера (wf turan-container-verify): целостность модели / устойчивость / resilience — PASS; казахская коррекция solid. Автоматизация: `scripts/deploy.sh` + субагент `.claude/agents/turan-deploy.md`. Управление: `docker stop/start turan-serve`, `colima stop`. Известное ограничение: русский placeholder портит валидный русский (вне фокуса).

**Осталось (только продакшен):** развернуть образ на реальном тест-сервере + удалённый доступ пользователям (образ и `deploy.sh` готовы).

## 13. Этап 6 — обучающие материалы (2026-06-20) ✅
Написаны 3 документа (мультиагентно + адверсариальная проверка на точность + правки):
- `docs/USER_GUIDE.md` — руководство пользователя (веб-UI, API, примеры, что умеет/не умеет, FAQ).
- `docs/ADMIN_GUIDE.md` — деплой (локально/Docker), конфиг (.env, KAZAKH_MODEL_PATH), управление, обновление модели, troubleshooting.
- `docs/FUNCTIONAL_DESCRIPTION.md` — функциональные возможности, архитектура, метрики, методичка внедрения.

Остался только пункт «провести обучающее мероприятие» (действие пользователя; живой пилот :8010 + документы это поддерживают).

## 14. Этап 7 — итоговая отчётность (2026-06-20) ✅
Оформлен `docs/FINAL_REPORT.md` — итоговый отчёт (цели, 7 этапов, архитектура, данные/обучение, метрики, деплой, ограничения, рекомендации, заключение, приложения).

**Статус проекта: ВСЕ 7 ЭТАПОВ ЗАВЕРШЕНЫ. Проект сдан** (дедлайн был ~13.07 — с большим запасом).

Документация проекта: FINAL_REPORT, PILOT_REPORT, USER_GUIDE, ADMIN_GUIDE, FUNCTIONAL_DESCRIPTION, WORKLOG, COMPLETION_PLAN.
**Сборка:** `docker build -f backend/Dockerfile.serve -t turan-serve ./backend`; запуск стека: `BACKEND_PORT=8010 docker-compose up` (хост 8000 занят Crypto Bata). Гейт после сборки: в логах `TransformerModel (detector+corrector) loaded`, контейнер healthy.
