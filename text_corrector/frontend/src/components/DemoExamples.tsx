/**
 * Interactive demo examples panel.
 *
 * Clicking an example card loads the text into the main input
 * and immediately triggers correction via the provided callback.
 */
import React, { useState } from 'react'

export interface DemoExample {
  id: string
  label: string
  input: string
  expected: string
  note: string
}

interface DemoExamplesProps {
  onSelect: (text: string) => void
  disabled?: boolean
}

// ── Demo data ────────────────────────────────────────────────────────────────

const RUSSIAN_DEMOS: DemoExample[] = [
  {
    id: 'ru-1',
    label: 'Простое приветствие',
    input: 'прмвет',
    expected: 'привет',
    note: 'Пропущена буква «и»',
  },
  {
    id: 'ru-2',
    label: 'Длинное слово',
    input: 'здраствуйте',
    expected: 'здравствуйте',
    note: 'Пропущена буква «в»',
  },
  {
    id: 'ru-3',
    label: 'Технический текст',
    input: 'кампютер не рабтает',
    expected: 'компьютер не работает',
    note: 'Два слова исправлены одновременно',
  },
  {
    id: 'ru-4',
    label: 'Учебная фраза',
    input: 'Спасбо учтель',
    expected: 'Спасибо учитель',
    note: 'Регистр сохраняется',
  },
]

const KAZAKH_DEMOS: DemoExample[] = [
  {
    id: 'kz-1',
    label: 'Қарапайым сәлем',
    input: 'сәем',
    expected: 'сәлем',
    note: 'Missing «л» — Kazakh detected via «ә»',
  },
  {
    id: 'kz-2',
    label: 'Екі сөз қатесі',
    input: 'Сәем рахет',
    expected: 'Сәлем рахмет',
    note: 'Two corrections in one phrase',
  },
  {
    id: 'kz-3',
    label: 'Мектеп сөйлемі',
    input: 'мен мектпте оқиды',
    expected: 'мен мектепте оқиды',
    note: 'Missing «е» in мектеп',
  },
  {
    id: 'kz-4',
    label: 'Кітап сөзі',
    input: 'кітп оқиды',
    expected: 'кітап оқиды',
    note: 'Missing «а» — detected via «і»',
  },
]

// ── Sub-components ────────────────────────────────────────────────────────────

const DemoCard: React.FC<{
  demo: DemoExample
  langColor: string
  onSelect: (text: string) => void
  disabled?: boolean
}> = ({ demo, langColor, onSelect, disabled }) => (
  <button
    onClick={() => onSelect(demo.input)}
    disabled={disabled}
    className={`
      group w-full text-left rounded-xl border p-4 transition-all duration-150
      hover:shadow-md hover:-translate-y-0.5
      disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:translate-y-0
      ${langColor}
    `}
  >
    <div className="flex items-start justify-between gap-2 mb-2">
      <span className="text-xs font-semibold uppercase tracking-wide opacity-60">
        {demo.label}
      </span>
      <span className="text-xs opacity-0 group-hover:opacity-60 transition-opacity whitespace-nowrap">
        Нажмите →
      </span>
    </div>

    {/* Input → Output */}
    <div className="flex items-center gap-2 flex-wrap">
      <span className="font-mono text-sm bg-red-100 text-red-700 line-through px-2 py-0.5 rounded">
        {demo.input}
      </span>
      <span className="text-gray-400 text-sm">→</span>
      <span className="font-mono text-sm bg-green-100 text-green-700 font-semibold px-2 py-0.5 rounded">
        {demo.expected}
      </span>
    </div>

    {/* Note */}
    <p className="mt-2 text-xs opacity-50">{demo.note}</p>
  </button>
)

// ── Main component ────────────────────────────────────────────────────────────

type Tab = 'russian' | 'kazakh'

export const DemoExamples: React.FC<DemoExamplesProps> = ({
  onSelect,
  disabled,
}) => {
  const [activeTab, setActiveTab] = useState<Tab>('russian')

  return (
    <div className="space-y-4">
      {/* Tab bar */}
      <div className="flex items-center gap-1 bg-gray-100 rounded-xl p-1 w-fit">
        <button
          onClick={() => setActiveTab('russian')}
          className={`px-4 py-1.5 rounded-lg text-sm font-semibold transition-all duration-150
            ${activeTab === 'russian'
              ? 'bg-white text-blue-700 shadow-sm'
              : 'text-gray-500 hover:text-gray-700'}`}
        >
          🇷🇺 Russian
        </button>
        <button
          onClick={() => setActiveTab('kazakh')}
          className={`px-4 py-1.5 rounded-lg text-sm font-semibold transition-all duration-150
            ${activeTab === 'kazakh'
              ? 'bg-white text-green-700 shadow-sm'
              : 'text-gray-500 hover:text-gray-700'}`}
        >
          🇰🇿 Kazakh
        </button>
      </div>

      {/* Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {activeTab === 'russian'
          ? RUSSIAN_DEMOS.map((d) => (
              <DemoCard
                key={d.id}
                demo={d}
                langColor="bg-blue-50 border-blue-200 text-blue-900 hover:border-blue-400"
                onSelect={onSelect}
                disabled={disabled}
              />
            ))
          : KAZAKH_DEMOS.map((d) => (
              <DemoCard
                key={d.id}
                demo={d}
                langColor="bg-green-50 border-green-200 text-green-900 hover:border-green-400"
                onSelect={onSelect}
                disabled={disabled}
              />
            ))}
      </div>

      <p className="text-xs text-gray-400 text-center">
        Нажмите на карточку — пример загрузится и исправится автоматически
      </p>
    </div>
  )
}
