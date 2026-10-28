#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# build_pages.sh — собрать страницу для GitHub Pages и положить её в копию
# репозитория демо (daniyar3348/turan-demo). Файлы репозитория, которых нет в
# сборке (.git, .github, README.md), не трогаются.
#     bash frontend/scripts/build_pages.sh ~/Desktop/Projects/turan-demo
# Переменные: API (адрес Space), BASE (путь сайта на github.io).
# ──────────────────────────────────────────────────────────────────────────────
set -euo pipefail

DEST="${1:?укажите папку репозитория turan-demo}"
API="${API:-https://daniyar51-turan-text-corrector.hf.space}"
BASE="${BASE:-/turan-demo/}"
FRONTEND="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$FRONTEND"
./node_modules/.bin/tsc
VITE_API_BASE_URL="$API" ./node_modules/.bin/vite build --base="$BASE"

# Old hashed bundles go away; everything else in the repo stays
rm -rf "$DEST/assets"
cp -R dist/. "$DEST/"
# GitHub Pages answers unknown paths (/turan-demo/visualization) with 404.html
cp dist/index.html "$DEST/404.html"
touch "$DEST/.nojekyll"
echo "готово: $DEST (API $API, base $BASE)"
