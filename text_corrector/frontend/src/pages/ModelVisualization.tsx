import { Link } from 'react-router-dom'
import NeuralNetDiagram from '@/components/NeuralNetDiagram'

const steps = [
  {
    id: 1,
    icon: '📥',
    title: 'Входной текст',
    description: 'Пользователь вводит текст на русском или казахском языке.',
    detail: 'До 5 000 символов. Поддерживаются смешанные тексты.',
    color: 'from-blue-500 to-blue-600',
    bg: 'bg-blue-50',
    border: 'border-blue-200',
    text: 'text-blue-700',
  },
  {
    id: 2,
    icon: '🔍',
    title: 'Определение языка',
    description: 'Анализ символов и лексических паттернов для автоопределения языка.',
    detail: 'Казахские символы: Ә Ғ Қ Ң Ө Ұ Ү Һ І. Уверенность возвращается в процентах.',
    color: 'from-violet-500 to-violet-600',
    bg: 'bg-violet-50',
    border: 'border-violet-200',
    text: 'text-violet-700',
  },
  {
    id: 3,
    icon: '✂️',
    title: 'Токенизация',
    description: 'Текст разбивается на слова с сохранением пунктуации и пробелов.',
    detail: 'Каждый токен обрабатывается независимо. Служебные символы не изменяются.',
    color: 'from-amber-500 to-amber-600',
    bg: 'bg-amber-50',
    border: 'border-amber-200',
    text: 'text-amber-700',
  },
  {
    id: 4,
    icon: '📖',
    title: 'Поиск в словаре',
    description: 'Каждое слово сверяется со встроенным словарём языка.',
    detail: 'Если слово найдено — оно остаётся без изменений. Иначе запускается поиск кандидатов.',
    color: 'from-green-500 to-green-600',
    bg: 'bg-green-50',
    border: 'border-green-200',
    text: 'text-green-700',
  },
  {
    id: 5,
    icon: '📐',
    title: 'Расстояние Левенштейна',
    description: 'Для неизвестных слов алгоритм находит ближайшие словарные кандидаты.',
    detail: 'Максимальное редакционное расстояние — 3. Порог схожести — 55%. Используется rapidfuzz.',
    color: 'from-rose-500 to-rose-600',
    bg: 'bg-rose-50',
    border: 'border-rose-200',
    text: 'text-rose-700',
  },
  {
    id: 6,
    icon: '✅',
    title: 'Исправленный текст',
    description: 'Возвращается исправленный текст с метаданными по каждому изменению.',
    detail: 'Визуальный diff, список исправлений, количество изменённых слов и уверенность.',
    color: 'from-indigo-500 to-indigo-600',
    bg: 'bg-indigo-50',
    border: 'border-indigo-200',
    text: 'text-indigo-700',
  },
]

const architecture = [
  { layer: 'Frontend', tech: 'React 18 + TypeScript + Vite', role: 'UI, ввод текста, отображение результатов' },
  { layer: 'API Layer', tech: 'FastAPI + Pydantic v2', role: 'REST-эндпоинты, валидация, CORS' },
  { layer: 'Detection', tech: 'Символьный анализ + эвристики', role: 'Определение языка по символам' },
  { layer: 'Correction', tech: 'rapidfuzz + словарь', role: 'Редактирование и поиск кандидатов' },
  { layer: 'Model slot', tech: 'HuggingFace / ONNX ready', role: 'Подключение обученной модели' },
]

export default function ModelVisualization() {
  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-br from-slate-50 via-blue-50/40 to-indigo-50/60">

      {/* Header */}
      <header className="sticky top-0 z-20 bg-white/80 backdrop-blur-md border-b border-gray-200/80 shadow-sm">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary-500 to-primary-700
                            flex items-center justify-center shadow-sm">
              <span className="text-white text-base">✏️</span>
            </div>
            <span className="font-bold text-gray-900 text-sm tracking-tight">
              Turan Text Corrector
            </span>
          </div>
          <Link
            to="/"
            className="inline-flex items-center gap-1.5 px-4 py-1.5 rounded-full border border-gray-200
                       text-sm font-medium text-gray-600 hover:bg-gray-50 transition-colors"
          >
            ← Назад
          </Link>
        </div>
      </header>

      <main className="flex-1 max-w-6xl mx-auto w-full px-4 sm:px-6 py-10 space-y-12">

        {/* Hero */}
        <section className="text-center space-y-3">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full
                          bg-primary-50 border border-primary-200 text-primary-700 text-xs font-semibold
                          uppercase tracking-wider">
            Визуализация модели
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold text-gray-900 tracking-tight">
            Процесс исправления текста
          </h1>
          <p className="text-gray-500 text-sm max-w-xl mx-auto">
            Полный пайплайн от ввода до исправленного результата
          </p>
        </section>

        {/* Pipeline */}
        <section>
          <h2 className="text-lg font-bold text-gray-800 mb-6">Пайплайн обработки</h2>
          <div className="relative">
            {/* Connector line */}
            <div className="absolute left-6 top-8 bottom-8 w-0.5 bg-gradient-to-b from-blue-200 via-violet-200 to-indigo-200 hidden sm:block" />

            <div className="space-y-4">
              {steps.map((step) => (
                <div key={step.id} className="flex gap-4 items-start">
                  {/* Icon */}
                  <div className={`relative z-10 flex-shrink-0 w-12 h-12 rounded-xl
                                   bg-gradient-to-br ${step.color}
                                   flex items-center justify-center text-xl shadow-sm`}>
                    {step.icon}
                  </div>

                  {/* Card */}
                  <div className={`flex-1 ${step.bg} border ${step.border} rounded-2xl px-5 py-4`}>
                    <div className="flex items-center gap-2 mb-1">
                      <span className={`text-xs font-bold ${step.text} uppercase tracking-wide`}>
                        Шаг {step.id}
                      </span>
                    </div>
                    <p className="font-bold text-gray-800 text-sm">{step.title}</p>
                    <p className="text-gray-600 text-sm mt-1">{step.description}</p>
                    <p className="text-gray-400 text-xs mt-1">{step.detail}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Architecture table */}
        <section>
          <h2 className="text-lg font-bold text-gray-800 mb-4">Архитектура системы</h2>
          <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-100">
                  <th className="text-left px-5 py-3 font-semibold text-gray-600">Слой</th>
                  <th className="text-left px-5 py-3 font-semibold text-gray-600">Технология</th>
                  <th className="text-left px-5 py-3 font-semibold text-gray-600 hidden sm:table-cell">Роль</th>
                </tr>
              </thead>
              <tbody>
                {architecture.map((row, i) => (
                  <tr key={row.layer} className={i % 2 === 0 ? '' : 'bg-gray-50/50'}>
                    <td className="px-5 py-3 font-semibold text-gray-800">{row.layer}</td>
                    <td className="px-5 py-3 font-mono text-xs text-primary-700">{row.tech}</td>
                    <td className="px-5 py-3 text-gray-500 hidden sm:table-cell">{row.role}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {/* Neural Network Diagram */}
        <section>
          <h2 className="text-lg font-bold text-gray-800 mb-2">Архитектура модели: Hybrid LSTM + BERT</h2>
          <p className="text-sm text-gray-500 mb-4">
            Интерактивная схема. Используйте колесо мыши для масштабирования, перетаскивание — для перемещения.
          </p>
          <div className="rounded-2xl overflow-hidden shadow-sm">
            <NeuralNetDiagram />
          </div>
          <div className="flex flex-wrap gap-3 mt-4">
            {[
              { color: 'bg-blue-400', label: 'Входные данные' },
              { color: 'bg-violet-500', label: 'BERT компоненты' },
              { color: 'bg-orange-400', label: 'LSTM компоненты' },
              { color: 'bg-green-500', label: 'Слияние и выход' },
            ].map((item) => (
              <div key={item.label} className="flex items-center gap-1.5 text-xs text-gray-600">
                <span className={`w-3 h-3 rounded-full ${item.color}`} />
                {item.label}
              </div>
            ))}
          </div>
        </section>


      </main>
    </div>
  )
}
