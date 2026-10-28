/**
 * Evaluation results of the KazRoBERTa detector + corrector.
 *
 * Numbers come from backend/scripts/eval_end2end.py (model mode, 8 000 test
 * sentences) and backend/scripts/eval_stress.py — re-run both and update this
 * file whenever the model or the corrector changes.
 */
import React from 'react'

interface Stat {
  value: string
  label: string
  note: string
  limitation?: boolean
}

const STATS: Stat[] = [
  {
    value: '97,3%',
    label: 'F1 поиска ошибок',
    note: 'точность 97,1% · полнота 97,4%',
  },
  {
    value: '81,2%',
    label: 'предложений исправлено целиком',
    note: 'детектор + корректор; при идеальном детекторе 83,8%',
  },
  {
    value: '0,34%',
    label: 'ложных срабатываний',
    note: 'доля правильных слов, помеченных как ошибка',
  },
  {
    value: '70%',
    label: 'ошибок находится в тексте без казахских букв',
    note: 'если весь текст набран на русской раскладке; целиком исправлено 55% таких предложений',
    limitation: true,
  },
]

export const ModelResults: React.FC = () => (
  <section className="bg-white rounded-2xl border border-gray-200 shadow-sm p-5 sm:p-6 space-y-5">
    <div>
      <h2 className="text-sm font-bold text-gray-800">Результаты модели</h2>
      <p className="text-xs text-gray-500 mt-1 leading-relaxed">
        KazRoBERTa (6 слоёв, ~83 млн параметров), дообучена на 2,57 млн пар предложений
        с синтетическими ошибками. Тест — 8 000 предложений, которых не было в обучении.
      </p>
    </div>

    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {STATS.map((s) => (
        <div
          key={s.label}
          className={`rounded-xl border px-4 py-3.5 ${
            s.limitation ? 'border-amber-200 bg-amber-50/60' : 'border-gray-100 bg-gray-50/60'
          }`}
        >
          {s.limitation && (
            <p className="text-[11px] font-semibold uppercase tracking-wide text-amber-700 mb-1">
              ⚠ Ограничение
            </p>
          )}
          <p className="text-2xl font-extrabold text-gray-900 tabular-nums">{s.value}</p>
          <p className="text-sm font-semibold text-gray-700 mt-0.5">{s.label}</p>
          <p className="text-xs text-gray-500 mt-1 leading-relaxed">{s.note}</p>
        </div>
      ))}
    </div>

    <p className="text-xs text-gray-500 leading-relaxed">
      Ошибки в тесте синтетические и того же вида, что в обучении: казахские буквы
      заменены русскими, нарушена гармония гласных, буквы переставлены, пропущены,
      повторены или заменены — не больше трёх ошибок на предложение. На реальных текстах
      цифры могут быть ниже. Русский текст не исправляется.
    </p>
  </section>
)
