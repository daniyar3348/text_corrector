#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# deploy.sh — собрать, запустить и ПРОВЕРИТЬ serving-образ Turan (colima/docker).
# Идемпотентно: можно гонять повторно. Запуск из любого места:
#     bash backend/scripts/deploy.sh
# Переменные: PORT (хост-порт, по умолчанию 8010; 8000 занят Crypto Bata).
# ──────────────────────────────────────────────────────────────────────────────
set -euo pipefail

BACKEND="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"   # .../backend
IMAGE="turan-serve:latest"
NAME="turan-serve"
HOST_PORT="${PORT:-8010}"

echo "==> 1/5 Docker daemon (colima)"
if ! command -v docker >/dev/null 2>&1; then
  echo "    docker CLI не найден — установите: brew install colima docker"; exit 1
fi
colima status >/dev/null 2>&1 || { echo "    стартую colima..."; colima start --cpu 4 --memory 4; }

echo "==> 2/5 Сборка образа ($IMAGE)"
docker build -f "$BACKEND/Dockerfile.serve" -t "$IMAGE" "$BACKEND"

echo "==> 3/5 Запуск контейнера ($NAME, порт $HOST_PORT→8000)"
docker rm -f "$NAME" >/dev/null 2>&1 || true
docker run -d --name "$NAME" -p "${HOST_PORT}:8000" \
  -e KAZAKH_MODEL_PATH=/app/models/kazakh_detector "$IMAGE" >/dev/null

echo "==> 4/5 Ожидание healthy (загрузка модели ~1–2 мин)"
ok=""
for _ in $(seq 1 120); do
  st="$(docker inspect -f '{{.State.Health.Status}}' "$NAME" 2>/dev/null || echo starting)"
  [ "$st" = "healthy" ] && { ok=1; break; }
  if [ "$st" = "unhealthy" ]; then echo "    UNHEALTHY:"; docker logs --tail 40 "$NAME"; exit 1; fi
  sleep 2
done
[ -n "$ok" ] || { echo "    таймаут ожидания healthy"; docker logs --tail 40 "$NAME"; exit 1; }

echo "==> 5/5 Гейт-проверка + smoke"
if docker logs "$NAME" 2>&1 | grep -q "TransformerModel (detector+corrector) loaded"; then
  echo "    ✓ реальная модель загружена (не placeholder)"
else
  echo "    ✗ модель НЕ загружена — деградация на placeholder"; docker logs --tail 40 "$NAME"; exit 1
fi
curl -s -X POST "http://127.0.0.1:${HOST_PORT}/correct-text" \
  -H 'Content-Type: application/json' \
  --data-binary '{"text":"Бул маселе оте манызды болып тур."}' \
  | python3 -c "import sys,json;d=json.load(sys.stdin);print('    smoke:',d['original_text'],'→',d['corrected_text'])"

echo "==> ГОТОВО → http://127.0.0.1:${HOST_PORT}  (контейнер $NAME; логи: docker logs -f $NAME)"
