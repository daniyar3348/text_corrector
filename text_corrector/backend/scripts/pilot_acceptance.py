#!/usr/bin/env python3
"""
pilot_acceptance.py — приёмочная проверка пилота через ЖИВОЙ HTTP API.

Проверяет всё, что нужно зафиксировать для этапа 5:
  1. /health — загружена ли реальная модель (TransformerModel, не placeholder);
  2. функционал — исправление набора казахских фраз (показывает before→after);
  3. крайние случаи — чистый текст (без переисправления), русский (placeholder), короткое;
  4. производительность — latency/throughput под конкурентной нагрузкой;
  5. логирование запросов — есть ли строки 'correction |' в логе сервера.

Запуск (сервер должен быть поднят):
  ./.venv-train/bin/python scripts/pilot_acceptance.py [BASE_URL] [SERVER_LOG]
"""
from __future__ import annotations

import asyncio
import os
import sys
import time

import httpx

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8010"
LOG = sys.argv[2] if len(sys.argv) > 2 else os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "pilot_server.log")

FUNCTIONAL = [
    "Бугін мектепте жана кітап окыдык.",
    "Мен қазак тілін уйренип жатырмын.",
    "Астанада жана гимарат салынды.",
    "Биылғы жазда коп адам демалды.",
    "Оқушылар сабакка жаксы дайындалды.",
    "Бул маселе оте манызды болып тур.",
]
EDGE = [
    ("чистый KK (без правок)", "Бүгін мектепте жаңа кітап оқыдық."),
    ("русский (placeholder)", "Сегодня мы читали новую книгу в школе."),
    ("короткое", "Сәлем!"),
]


def post(client, text):
    r = client.post(f"{BASE}/correct-text", json={"text": text})
    return r.json()


def main():
    with httpx.Client(timeout=30) as c:
        print("=" * 72)
        print("1) /health")
        h = c.get(f"{BASE}/health").json()
        det = h.get("details", {})
        print(f"   service={h['service_status']} | kazakh_model={det.get('kazakh_model')}")
        print(f"   kazakh_ready={det.get('kazakh_model_ready')}  (ожидаем TransformerModel/True)")

        print("=" * 72)
        print("2) Функционал — исправление казахского (before → after)")
        for s in FUNCTIONAL:
            o = post(c, s)
            mark = "✎" if o["corrected_text"] != o["original_text"] else "="
            print(f"   {mark} {o['original_text']}")
            if o["corrected_text"] != o["original_text"]:
                print(f"     → {o['corrected_text']}  [{o['detected_language']}, {o['processing_time_ms']}ms]")

        print("=" * 72)
        print("3) Крайние случаи")
        for label, s in EDGE:
            o = post(c, s)
            changed = o["corrected_text"] != o["original_text"]
            print(f"   [{label}] lang={o['detected_language']} changed={changed}")
            print(f"     in : {o['original_text']}")
            print(f"     out: {o['corrected_text']}")

    print("=" * 72)
    print("4) Производительность (нагрузка)")

    async def load(N, CONC):
        lat = []
        sem = asyncio.Semaphore(CONC)
        async with httpx.AsyncClient(timeout=60) as c:
            async def one(i):
                async with sem:
                    t = time.perf_counter()
                    await c.post(f"{BASE}/correct-text", json={"text": FUNCTIONAL[i % len(FUNCTIONAL)]})
                    lat.append((time.perf_counter() - t) * 1000)
            t0 = time.perf_counter()
            await asyncio.gather(*[one(i) for i in range(N)])
            tot = time.perf_counter() - t0
        lat.sort()
        p = lambda q: lat[min(int(q * len(lat)), len(lat) - 1)]
        print(f"   {N} req @ conc {CONC}: {N/tot:.0f} req/s | "
              f"p50 {p(.5):.0f} | p95 {p(.95):.0f} | p99 {p(.99):.0f} ms")
    asyncio.run(load(500, 20))

    print("=" * 72)
    print("5) Логирование запросов (последние строки 'correction |' из лога)")
    try:
        lines = [ln for ln in open(LOG, encoding="utf-8") if "correction |" in ln]
        print(f"   найдено {len(lines)} записей; пример:")
        if lines:
            print("   " + lines[-1].strip())
    except FileNotFoundError:
        print(f"   лог не найден: {LOG}")
    print("=" * 72)
    print("ПРИЁМКА ЗАВЕРШЕНА")


if __name__ == "__main__":
    main()
