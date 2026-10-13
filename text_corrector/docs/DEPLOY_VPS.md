# Деплой Turan на VPS (всегда онлайн, HTTPS)

Поднимает полный стек **веб-страница + API** на сервере 24/7 с автоматическим HTTPS:
`Caddy (:443) → frontend (SPA + /api-прокси) → backend (KazRoBERTa-детектор + корректор)`.

## 0. Что понадобится
- **VPS** с Ubuntu/Debian, **≥ 2 ГБ RAM** (torch при загрузке модели ест ~1 ГБ; контейнер на простое ~373 МБ), ~10 ГБ диска. Подойдёт Hetzner CAX11 (ARM, ~€4/мес), DigitalOcean 2 ГБ, или Oracle Cloud free-tier ARM (бесплатно, 24 ГБ).
- **Домен** (или поддомен), у которого **A-запись указывает на IP сервера** — это обязательно для HTTPS (Let's Encrypt).
- Открытые порты **80 и 443** на сервере.
- SSH-доступ к серверу.

## 1. Установить Docker на сервере
```bash
ssh user@SERVER_IP
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER && newgrp docker   # docker без sudo
docker --version && docker compose version
```

## 2. Перенести проект НА сервер (включая модель)
Модель (`backend/models/kazakh_detector/`, ~316 МБ) и лексикон (`backend/data/kk_lexicon.tsv`) **не в git** — их надо скопировать. С локальной машины (из каталога `text_corrector/`):
```bash
rsync -avz --progress \
  --exclude '.venv' --exclude '.venv-train' --exclude 'node_modules' \
  --exclude 'backend/data/kazakh_spellcheck' --exclude 'backend/data/colab' \
  --exclude '__pycache__' --exclude '*.zip' --exclude '*.log' \
  ./ user@SERVER_IP:~/turan/
```
Это перенесёт код + модель + лексикон, без тяжёлого датасета и venv. Сборка образа произойдёт **на сервере** (правильная архитектура подберётся автоматически).

## 3. Указать домен и запустить
На сервере:
```bash
cd ~/turan
echo "DOMAIN=corrector.example.kz" > .env.prod        # ваш реальный домен
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build
```
Первый запуск: сборка (~3–6 мин), затем backend грузит модель (~1–2 мин) → станет healthy, Caddy получит TLS-сертификат.

## 4. Проверить
```bash
docker compose -f docker-compose.prod.yml ps          # backend healthy, frontend/caddy up
docker compose -f docker-compose.prod.yml logs backend | grep "TransformerModel (detector+corrector) loaded"
curl -s https://corrector.example.kz/api/health        # {"model_status":"loaded",...}
```
Открой в браузере **https://corrector.example.kz** — должна открыться веб-страница корректора. Готово ✅

## 5. Эксплуатация
```bash
# логи
docker compose -f docker-compose.prod.yml logs -f backend
# рестарт
docker compose -f docker-compose.prod.yml restart backend
# остановить / поднять весь стек
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d
```

### Обновление модели
1. Залить новую модель в `~/turan/backend/models/kazakh_detector/` (rsync, шаг 2).
2. `docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build backend`.

## 6. Заметки и типичные проблемы
- **Сертификат не выдаётся:** проверь, что A-запись домена указывает на IP сервера и порты 80/443 открыты (firewall/ufw). Caddy логи: `docker compose -f docker-compose.prod.yml logs caddy`.
- **Сертификаты переживают рестарт** — они в volume `caddy_data` (не удаляй его).
- **backend unhealthy / в логах `Failed to load detector`:** мало RAM при загрузке torch — возьми ≥2 ГБ; либо модель не скопировалась (проверь `~/turan/backend/models/kazakh_detector/model.safetensors`).
- **Нагрузка:** один воркер ~150–200 req/s. Для роста — добавь воркеры (`CMD ... --workers N` в `Dockerfile.serve`, RAM ×N) или сервер помощнее.
- **Только API (без сайта):** можно поднять без frontend/caddy и проксировать прямо на backend — но рекомендованный путь выше даёт и сайт, и HTTPS.
