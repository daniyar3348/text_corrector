/**
 * Interactive demo examples panel.
 *
 * Clicking an example card loads the text into the main input
 * and immediately triggers correction via the provided callback.
 *
 * Only Kazakh examples: Russian text is passed through unchanged (there is no
 * Russian corrector), so a Russian card could only promise a fix that never
 * happens. Every `expected` value here is what the API actually returns.
 */
import React from 'react'

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

const KAZAKH_DEMOS: DemoExample[] = [
  {
    id: 'kz-1',
    label: 'Қарапайым сәлем',
    input: 'Салем',
    expected: 'Сәлем',
    note: 'Русская «а» вместо казахской «ә»',
  },
  {
    id: 'kz-2',
    label: 'Орыс пернетақтасы',
    input: 'Бул маселе оте манызды болып тур.',
    expected: 'Бұл мәселе өте маңызды болып тұр.',
    note: 'Набрано без казахских букв — исправлено 5 слов',
  },
  {
    id: 'kz-3',
    label: 'Жалғау',
    input: 'Казакстан Республикасынын астанасы',
    expected: 'Қазақстан Республикасының астанасы',
    note: '«к» вместо «қ» и «н» вместо «ң» в окончании',
  },
  {
    id: 'kz-4',
    label: 'Кітап сөзі',
    input: 'кітп оқиды',
    expected: 'кітап оқиды',
    note: 'Пропущена буква «а»',
  },
]

// ── Sub-components ────────────────────────────────────────────────────────────

const DemoCard: React.FC<{
  demo: DemoExample
  onSelect: (text: string) => void
  disabled?: boolean
}> = ({ demo, onSelect, disabled }) => (
  <button
    onClick={() => onSelect(demo.input)}
    disabled={disabled}
    className="group w-full text-left rounded-xl border p-4 transition-all duration-150
               hover:shadow-md hover:-translate-y-0.5
               disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:translate-y-0
               bg-green-50 border-green-200 text-green-900 hover:border-green-400"
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

export const DemoExamples: React.FC<DemoExamplesProps> = ({
  onSelect,
  disabled,
}) => (
  <div className="space-y-4">
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
      {KAZAKH_DEMOS.map((d) => (
        <DemoCard key={d.id} demo={d} onSelect={onSelect} disabled={disabled} />
      ))}
    </div>

    <p className="text-xs text-gray-400 text-center">
      Нажмите на карточку — пример загрузится и исправится автоматически
    </p>
  </div>
)
