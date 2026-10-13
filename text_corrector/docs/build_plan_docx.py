"""
Generate a presentation-ready Word document (.docx) of the project completion
plan, with native tables and matplotlib charts (progress, Gantt, pie, milestones).

Run:  backend/.venv/bin/python docs/build_plan_docx.py
Output: docs/Turan_Completion_Plan.docx
"""
from __future__ import annotations

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import matplotlib.dates as mdates
from datetime import date

from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "_assets")
os.makedirs(ASSETS, exist_ok=True)

# Palette
GREEN = "#16a34a"
AMBER = "#f59e0b"
RED = "#dc2626"
BLUE = "#4f46e5"
GREY = "#d1d5db"

plt.rcParams.update({"font.size": 11, "axes.titlesize": 13, "figure.dpi": 150})


# ── Chart 1: progress per stage ───────────────────────────────────────────────
def chart_progress() -> str:
    stages = [
        "1. Разработка", "2. Интеграция", "3. Апробация",
        "4. Оптимизация", "5. Пилот", "6. Обучение", "7. Отчётность",
    ]
    values = [100, 100, 100, 70, 0, 0, 0]
    colors = [GREEN, GREEN, GREEN, AMBER, RED, RED, RED]

    fig, ax = plt.subplots(figsize=(8, 3.6))
    y = range(len(stages))
    ax.barh(y, values, color=colors, edgecolor="white")
    ax.barh(y, [100] * len(stages), color=GREY, alpha=0.25, zorder=0)
    ax.set_yticks(list(y))
    ax.set_yticklabels(stages)
    ax.invert_yaxis()
    ax.set_xlim(0, 100)
    ax.set_xlabel("Готовность, %")
    ax.set_title("Готовность по этапам")
    for i, v in enumerate(values):
        ax.text(min(v + 2, 96), i, f"{v}%", va="center", fontsize=10)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    path = os.path.join(ASSETS, "progress.png")
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path


# ── Chart 2: Gantt ────────────────────────────────────────────────────────────
def chart_gantt() -> str:
    # (label, start, end, color, stage_color_group)
    tasks = [
        ("Морфоанализатор (готово)", date(2026, 6, 15), date(2026, 6, 16), GREEN),
        ("Датасет орфо-ошибок", date(2026, 6, 15), date(2026, 6, 18), RED),
        ("Fine-tune KazRoBERTa", date(2026, 6, 18), date(2026, 6, 21), RED),
        ("Интеграция модели", date(2026, 6, 21), date(2026, 6, 23), RED),
        ("Тест точности", date(2026, 6, 23), date(2026, 6, 24), AMBER),
        ("Инфраструктура пилота", date(2026, 6, 24), date(2026, 6, 26), BLUE),
        ("Деплой в тест-среду", date(2026, 6, 26), date(2026, 6, 28), BLUE),
        ("Нагрузочный тест", date(2026, 6, 28), date(2026, 6, 30), BLUE),
        ("Руководство пользователя", date(2026, 6, 30), date(2026, 7, 3), BLUE),
        ("Инструкция администратора", date(2026, 7, 3), date(2026, 7, 5), BLUE),
        ("Обучающее мероприятие", date(2026, 7, 5), date(2026, 7, 7), BLUE),
        ("Свод + рекомендации", date(2026, 7, 7), date(2026, 7, 10), BLUE),
        ("Оформление отчёта", date(2026, 7, 10), date(2026, 7, 12), BLUE),
        ("Буфер / защита", date(2026, 7, 12), date(2026, 7, 14), AMBER),
    ]
    fig, ax = plt.subplots(figsize=(9, 5))
    for i, (label, s, e, c) in enumerate(tasks):
        ax.barh(i, (e - s).days, left=mdates.date2num(s),
                color=c, edgecolor="white", height=0.6)
    ax.set_yticks(range(len(tasks)))
    ax.set_yticklabels([t[0] for t in tasks])
    ax.invert_yaxis()
    ax.xaxis_date()
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d.%m"))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=3))
    ax.set_title("Календарный план (Gantt) — 4 недели")
    ax.grid(axis="x", linestyle=":", alpha=0.5)
    ax.spines[["top", "right"]].set_visible(False)
    legend = [
        Patch(color=GREEN, label="Готово"),
        Patch(color=RED, label="Критический путь (этап 4)"),
        Patch(color=BLUE, label="Этапы 5–7"),
        Patch(color=AMBER, label="Проверка / буфер"),
    ]
    ax.legend(handles=legend, loc="lower right", fontsize=9, framealpha=0.9)
    fig.autofmt_xdate()
    fig.tight_layout()
    path = os.path.join(ASSETS, "gantt.png")
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path


# ── Chart 3: pie ──────────────────────────────────────────────────────────────
def chart_pie() -> str:
    fig, ax = plt.subplots(figsize=(5, 4))
    sizes = [43, 10, 47]
    labels = ["Завершено\n(этапы 1–3)", "Этап 4\n(в работе)", "Осталось\n(этапы 5–7)"]
    ax.pie(sizes, labels=labels, colors=[GREEN, AMBER, GREY],
           autopct="%1.0f%%", startangle=90,
           wedgeprops={"edgecolor": "white", "linewidth": 2})
    ax.set_title("Общая готовность проекта (~67%)")
    fig.tight_layout()
    path = os.path.join(ASSETS, "pie.png")
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path


# ── DOCX helpers ──────────────────────────────────────────────────────────────
def add_table(doc, headers, rows, widths=None):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Light Grid Accent 1"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr = t.rows[0].cells
    for i, h in enumerate(headers):
        hdr[i].paragraphs[0].add_run(h).bold = True
    for row in rows:
        cells = t.add_row().cells
        for i, val in enumerate(row):
            cells[i].text = str(val)
    if widths:
        for row in t.rows:
            for i, w in enumerate(widths):
                row.cells[i].width = Inches(w)
    return t


def h(doc, text, level):
    p = doc.add_heading(text, level=level)
    return p


# ── Build document ────────────────────────────────────────────────────────────
def build():
    progress = chart_progress()
    gantt = chart_gantt()
    pie = chart_pie()

    doc = Document()

    # Title
    title = doc.add_heading("Turan Text Corrector", level=0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub = doc.add_paragraph()
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = sub.add_run("План завершения проекта\nАвтоматизированная коррекция казахско- и русскоязычных текстов")
    r.italic = True
    r.font.size = Pt(13)
    meta = doc.add_paragraph()
    meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
    meta.add_run("Дата: 2026-06-15   •   Дедлайн: ~2026-07-13   •   Срок: 4 недели").font.size = Pt(10)
    doc.add_paragraph(
        "Логика проекта: Разработка → интеграция → апробация → "
        "оптимизация → внедрение → обучение → отчётность."
    ).alignment = WD_ALIGN_PARAGRAPH.CENTER

    # 1. Status
    h(doc, "1. Текущий статус", 1)
    doc.add_paragraph(
        "Этапы 1–3 (разработка, интеграция, апробация) полностью завершены. "
        "Этап 4 выполнен на ~70%: морфологический анализатор интегрирован в "
        "пайплайн коррекции; осталось дообучить и подключить модель KazRoBERTa. "
        "Этапы 5–7 ещё не начаты."
    )
    doc.add_picture(pie, width=Inches(4.2))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_picture(progress, width=Inches(6.2))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER

    add_table(
        doc,
        ["№", "Этап", "Готовность", "Комментарий"],
        [
            ["1", "Разработка", "100%", "Full-stack: FastAPI + React/Vite"],
            ["2", "Интеграция", "100%", "Пайплайн, API, Docker"],
            ["3", "Апробация", "100%", "Тесты, фидбэк, метрики"],
            ["4", "Оптимизация + интеграция ML/морфологии", "70%", "Морфология ✅; KazRoBERTa — дообучение"],
            ["5", "Запуск пилотной системы", "0%", "Не начат"],
            ["6", "Обучающие материалы", "0%", "Не начат"],
            ["7", "Итоговая отчётность", "0%", "Не начат"],
        ],
        widths=[0.4, 2.8, 1.0, 2.6],
    )

    # 2. Gantt
    doc.add_page_break()
    h(doc, "2. Календарный план (Gantt)", 1)
    doc.add_picture(gantt, width=Inches(6.6))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER

    add_table(
        doc,
        ["Неделя", "Период", "Этап", "Ключевой результат"],
        [
            ["W1", "15–21.06", "Этап 4", "Единый механизм ML + морфология"],
            ["W2", "22–28.06", "Этап 5", "Развёрнутый и нагруженный пилот"],
            ["W3", "29.06–05.07", "Этап 6", "Обучающие материалы + тренинг"],
            ["W4", "06–13.07", "Этап 7", "Итоговый отчёт + буфер"],
        ],
        widths=[0.8, 1.4, 1.0, 3.6],
    )

    # 3. Critical path
    h(doc, "3. Критический путь", 1)
    doc.add_paragraph(
        "Критический путь проходит через этап 4: "
        "Сбор датасета → Fine-tune KazRoBERTa → Интеграция модели. "
        "Задержка на этом участке сдвигает весь проект. Пилот (этап 5) при "
        "необходимости запускается на гибриде «морфология + словарь» "
        "параллельно дообучению, чтобы не блокироваться."
    )
    doc.add_paragraph(
        "Морфоанализатор ✅  →  Датасет  →  Fine-tune  →  Интеграция модели  →  "
        "Единый механизм  →  Пилот  →  Обучение  →  Отчётность"
    ).runs[0].bold = True

    # 4. Tasks per week
    doc.add_page_break()
    h(doc, "4. Детализация задач", 1)

    weeks = {
        "Неделя 1 — Этап 4 (ML + морфология)": [
            "✓ Подключить морфоанализатор в пайплайн (выполнено)",
            "Собрать/подготовить датасет орфо-ошибок KK (синтетика)",
            "Fine-tune KazRoBERTa под коррекцию",
            "Реализовать загрузку и инференс в TransformerModel",
            "Связать ML-кандидаты → морфо-валидация",
            "Замер точности до/после",
        ],
        "Неделя 2 — Этап 5 (Пилот)": [
            "Финализировать docker-compose, .env, healthcheck, логирование",
            "Развернуть в тестовой эксплуатационной среде",
            "Обеспечить доступ пользователей",
            "Нагрузочное тестирование (latency, throughput, стабильность)",
            "Зафиксировать метрики пилота",
        ],
        "Неделя 3 — Этап 6 (Обучение)": [
            "Руководство пользователя (UI, сценарии, скриншоты)",
            "Инструкция администратора (деплой, обновление модели)",
            "Описание функций + методичка внедрения",
            "Провести обучающее мероприятие (демо/презентация)",
        ],
        "Неделя 4 — Этап 7 (Отчётность) + буфер": [
            "Обобщить результаты реализации проекта",
            "Рекомендации по применению и масштабированию",
            "Оформить итоговую отчётную документацию",
            "Представить результаты",
            "Буфер на доработки по замечаниям",
        ],
    }
    for wk, items in weeks.items():
        h(doc, wk, 2)
        for it in items:
            doc.add_paragraph(it, style="List Bullet")

    # 5. Risks
    h(doc, "5. Матрица рисков", 1)
    add_table(
        doc,
        ["Риск", "Вероятность", "Влияние", "Митигация"],
        [
            ["Нет датасета для fine-tune", "Высокая", "Высокое", "Синтетическая генерация ошибок из чистого корпуса"],
            ["Fine-tune не успевает в срок", "Средняя", "Высокое", "Пилот на гибриде, модель догнать параллельно"],
            ["KazRoBERTa тяжёл для CPU", "Средняя", "Среднее", "ONNX-экспорт / квантизация, кэширование"],
            ["Нестабильность под нагрузкой", "Низкая", "Среднее", "Нагрузочный тест на неделе 2"],
            ["Замечания на защите", "Средняя", "Низкое", "2-дневный буфер в конце"],
        ],
        widths=[2.2, 1.0, 1.0, 2.6],
    )

    # 6. Milestones
    h(doc, "6. Контрольные точки", 1)
    add_table(
        doc,
        ["Веха", "Дата", "Содержание"],
        [
            ["M0", "15.06", "Морфология интегрирована (выполнено)"],
            ["M1", "21.06", "KazRoBERTa дообучена и подключена — этап 4 закрыт"],
            ["M2", "28.06", "Пилот развёрнут и протестирован — этап 5"],
            ["M3", "05.07", "Обучающие материалы готовы, тренинг проведён — этап 6"],
            ["M4", "13.07", "Итоговый отчёт сдан — проект завершён"],
        ],
        widths=[0.8, 1.2, 4.4],
    )

    out = os.path.join(HERE, "Turan_Completion_Plan.docx")
    doc.save(out)
    print("SAVED:", out)


if __name__ == "__main__":
    build()
