import React, { useState, useCallback, useRef } from 'react'
import { Link } from 'react-router-dom'
import { LanguageBadge } from '@/components/LanguageBadge'
import { CorrectionResult } from '@/components/CorrectionResult'
import { StatusMessage } from '@/components/StatusMessage'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { DemoExamples } from '@/components/DemoExamples'
import { FileUploadButton } from '@/components/FileUploadButton'
import { FileCorrectionResult } from '@/components/FileCorrectionResult'
import { useLanguageDetection } from '@/hooks/useLanguageDetection'
import { useTextCorrection } from '@/hooks/useTextCorrection'
import { useFileCorrection } from '@/hooks/useFileCorrection'

const MAX_CHARS = 5000

export default function App() {
  const [inputText, setInputText] = useState('')
  const [dragging, setDragging] = useState(false)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const { language, confidence, loading: langLoading } = useLanguageDetection(inputText)
  const { result, status, error, correct, reset } = useTextCorrection()
  const {
    result: fileResult,
    status: fileStatus,
    error: fileError,
    filename,
    upload: uploadFile,
    reset: resetFile,
  } = useFileCorrection()

  const charCount = inputText.length
  const isOverLimit = charCount > MAX_CHARS
  const fileLoading = fileStatus === 'loading'
  const isLoading = status === 'loading' || fileLoading

  // ── Actions ──────────────────────────────────────────────────────────────

  const handleCorrect = useCallback(async () => {
    if (!inputText.trim() || isOverLimit || isLoading) return
    resetFile()
    await correct(inputText)
  }, [inputText, isOverLimit, isLoading, correct, resetFile])

  const handleClear = useCallback(() => {
    setInputText('')
    reset()
    resetFile()
    textareaRef.current?.focus()
  }, [reset, resetFile])

  // A file and a pasted snippet are two different jobs — starting one clears
  // the other's result so the right column never shows a stale answer.
  const handleFileSelect = useCallback(
    async (file: File) => {
      reset()
      await uploadFile(file)
    },
    [reset, uploadFile],
  )

  const handleInsertIntoEditor = useCallback(
    (text: string) => {
      setInputText(text)
      resetFile()
      textareaRef.current?.focus()
    },
    [resetFile],
  )

  // Dropping a file onto the textarea does the same as the upload button
  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault()
      setDragging(false)
      const file = e.dataTransfer.files?.[0]
      if (file) handleFileSelect(file)
    },
    [handleFileSelect],
  )

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        e.preventDefault()
        handleCorrect()
      }
    },
    [handleCorrect],
  )

  // When a demo card is clicked: fill input + auto-run correction
  const handleDemoSelect = useCallback(
    async (text: string) => {
      setInputText(text)
      reset()
      textareaRef.current?.focus()
      // Small delay lets state settle before correction
      await new Promise((r) => setTimeout(r, 80))
      await correct(text)
    },
    [correct, reset],
  )

  // ── Render ────────────────────────────────────────────────────────────────

  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-br from-slate-50 via-blue-50/40 to-indigo-50/60">

      {/* ── Navigation bar ─────────────────────────────────────────────── */}
      <header className="sticky top-0 z-20 bg-white/80 backdrop-blur-md border-b border-gray-200/80 shadow-sm">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary-500 to-primary-700
                            flex items-center justify-center shadow-sm">
              <span className="text-white text-base">✏️</span>
            </div>
            <div>
              <span className="font-bold text-gray-900 text-sm tracking-tight">
                Turan Text Corrector
              </span>
              <span className="hidden sm:inline text-gray-400 text-xs ml-2">
                v1.0 — Исследовательский прототип
              </span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Link
              to="/visualization"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full border border-gray-200
                         text-xs font-medium text-gray-600 hover:bg-gray-50 transition-colors"
            >
              🔬 Визуализация модели
            </Link>
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full
                             bg-green-50 border border-green-200 text-green-700 text-xs font-medium">
              <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
              Система активна
            </span>
          </div>
        </div>
      </header>

      <main className="flex-1 max-w-6xl mx-auto w-full px-4 sm:px-6 py-8 sm:py-10 space-y-8">

        {/* ── Hero ───────────────────────────────────────────────────────── */}
        <section className="text-center space-y-4 pt-2">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full
                          bg-primary-50 border border-primary-200 text-primary-700 text-xs font-semibold
                          uppercase tracking-wider">
            <span>NLP Исследовательская платформа</span>
            <span className="text-primary-400">·</span>
            <span>Морфологический анализ</span>
          </div>

          <h1 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold text-gray-900
                         tracking-tight leading-tight">
            Автоматическое исправление текста
            <br />
            <span className="bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
              Казахский язык
            </span>
          </h1>
          <p className="text-sm text-gray-500">
            Русский текст распознаётся, но не исправляется.
          </p>

        </section>

        {/* ── Main workspace (two-column on lg+) ─────────────────────────── */}
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">

          {/* Left column: input + demo examples */}
          <div className="lg:col-span-3 space-y-6">

            {/* Input card */}
            <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">

              {/* Card header */}
              <div className="flex items-center justify-between px-5 py-3.5
                              bg-gradient-to-r from-gray-50 to-white border-b border-gray-100">
                <div className="flex items-center gap-3">
                  <span className="text-sm font-semibold text-gray-700">Входной текст</span>
                  <LanguageBadge
                    language={language}
                    confidence={confidence}
                    loading={langLoading}
                  />
                </div>
                <span className={`text-xs font-mono tabular-nums
                  ${isOverLimit ? 'text-red-500 font-bold' : 'text-gray-400'}`}>
                  {charCount.toLocaleString()}&thinsp;/&thinsp;{MAX_CHARS.toLocaleString()}
                </span>
              </div>

              {/* Textarea */}
              <div
                className="p-4 relative"
                onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
                onDragLeave={() => setDragging(false)}
                onDrop={handleDrop}
              >
                {dragging && (
                  <div className="absolute inset-4 z-10 rounded-xl border-2 border-dashed
                                  border-primary-400 bg-primary-50/90 backdrop-blur-[1px]
                                  flex items-center justify-center pointer-events-none">
                    <span className="text-sm font-semibold text-primary-700">
                      📄 Отпустите файл, чтобы исправить его
                    </span>
                  </div>
                )}
                <textarea
                  ref={textareaRef}
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder={
                    'Введите казахский текст здесь…\n\nПримеры:\n' +
                    '  Салем                → Сәлем\n' +
                    '  Бул маселе манызды  → Бұл мәселе маңызды\n' +
                    '  кітп оқиды           → кітап оқиды'
                  }
                  rows={9}
                  spellCheck={false}
                  autoComplete="off"
                  className={`
                    w-full resize-y font-mono text-[15px] leading-relaxed text-gray-800
                    placeholder-gray-300 outline-none rounded-xl border
                    transition-colors duration-150 px-4 py-3 bg-gray-50 focus:bg-white
                    ${isOverLimit
                      ? 'border-red-300 focus:border-red-400 focus:ring-2 focus:ring-red-100'
                      : 'border-gray-200 focus:border-primary-400 focus:ring-2 focus:ring-primary-100'}
                  `}
                  aria-label="Input text for correction"
                />
                {isOverLimit && (
                  <p className="mt-1.5 text-xs text-red-500 flex items-center gap-1">
                    <span>⚠</span>
                    <span>Текст превышает лимит {MAX_CHARS.toLocaleString()} символов.</span>
                  </p>
                )}
              </div>

              {/* Action bar */}
              <div className="flex items-center gap-3 px-4 pb-4">
                <button
                  onClick={handleCorrect}
                  disabled={isLoading || !inputText.trim() || isOverLimit}
                  className="
                    inline-flex items-center gap-2 px-6 py-2.5 rounded-xl
                    bg-gradient-to-r from-primary-600 to-indigo-600
                    text-white font-semibold text-sm
                    hover:from-primary-700 hover:to-indigo-700
                    active:scale-[0.98]
                    disabled:opacity-50 disabled:cursor-not-allowed
                    transition-all duration-150 shadow-sm hover:shadow-md
                    focus:outline-none focus:ring-2 focus:ring-primary-400 focus:ring-offset-2
                  "
                >
                  {isLoading
                    ? <LoadingSpinner size="sm" label="" />
                    : <span className="text-base leading-none">✨</span>}
                  {isLoading ? 'Исправление…' : 'Исправить текст'}
                </button>

                <FileUploadButton
                  onSelect={handleFileSelect}
                  disabled={isLoading}
                  busy={fileLoading}
                />

                <button
                  onClick={handleClear}
                  disabled={isLoading}
                  className="
                    px-5 py-2.5 rounded-xl border border-gray-200 text-gray-600
                    font-medium text-sm hover:bg-gray-50 hover:border-gray-300
                    disabled:opacity-50 disabled:cursor-not-allowed
                    transition-colors duration-150
                    focus:outline-none focus:ring-2 focus:ring-gray-300 focus:ring-offset-1
                  "
                >
                  Очистить
                </button>

                <span className="ml-auto text-xs text-gray-400 hidden md:inline select-none">
                  <kbd className="px-1.5 py-0.5 rounded bg-gray-100 border border-gray-300
                                  font-mono text-[11px] text-gray-500">Ctrl</kbd>
                  {' + '}
                  <kbd className="px-1.5 py-0.5 rounded bg-gray-100 border border-gray-300
                                  font-mono text-[11px] text-gray-500">↵</kbd>
                  {' для исправления'}
                </span>
              </div>
            </div>

            {/* Demo examples */}
            <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-5">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h2 className="text-sm font-bold text-gray-800">Примеры</h2>
                  <p className="text-xs text-gray-500 mt-0.5">
                    Нажмите на карточку, чтобы загрузить и исправить
                  </p>
                </div>
                <span className="text-lg">🧪</span>
              </div>
              <DemoExamples onSelect={handleDemoSelect} disabled={isLoading} />
            </div>
          </div>

          {/* Right column: results */}
          <div className="lg:col-span-2 space-y-6">

            {/* Status message */}
            <StatusMessage status={status} error={error} />

            {/* File: in progress */}
            {fileLoading && (
              <div className="bg-white rounded-2xl border border-gray-200 shadow-sm
                              p-5 flex items-center gap-3">
                <LoadingSpinner size="sm" label="" />
                <div className="min-w-0">
                  <p className="text-sm font-semibold text-gray-700 truncate">
                    {filename}
                  </p>
                  <p className="text-xs text-gray-500">
                    Читаем файл и исправляем текст целиком…
                  </p>
                </div>
              </div>
            )}

            {/* File: failed */}
            {fileStatus === 'error' && fileError && (
              <div className="bg-red-50 rounded-2xl border border-red-200 p-4
                              flex items-start gap-2.5">
                <span className="text-lg leading-none">⚠</span>
                <div className="min-w-0">
                  <p className="text-sm font-semibold text-red-700 truncate">
                    {filename}
                  </p>
                  <p className="text-xs text-red-600 mt-0.5">{fileError}</p>
                </div>
              </div>
            )}

            {/* File: result */}
            {fileStatus === 'success' && fileResult && (
              <div className="bg-white rounded-2xl border border-gray-200 shadow-sm
                              p-5 animate-slide-up">
                <FileCorrectionResult
                  result={fileResult}
                  onInsert={handleInsertIntoEditor}
                  insertLimit={MAX_CHARS}
                />
              </div>
            )}

            {/* Idle state placeholder */}
            {status === 'idle' && fileStatus === 'idle' && (
              <div className="bg-white rounded-2xl border border-dashed border-gray-200
                              p-8 flex flex-col items-center justify-center text-center
                              min-h-[200px] space-y-3">
                <div className="w-12 h-12 rounded-full bg-gray-100 flex items-center
                                justify-center text-2xl">
                  📋
                </div>
              </div>
            )}

            {/* Result */}
            {status === 'success' && result && (
              <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-5 animate-slide-up">
                <CorrectionResult result={result} />
              </div>
            )}

            {/* How it works — only shown in idle */}
            {status === 'idle' && fileStatus === 'idle' && (
              <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-5 space-y-4">
                <h3 className="text-sm font-bold text-gray-800">Как это работает</h3>
                <ol className="space-y-3">
                  {[
                    {
                      step: '1',
                      title: 'Определение языка',
                      body: 'Казахские символы (Ә Ғ Қ Ң Ө Ұ Ү Һ І) и лексические паттерны автоматически определяют язык.',
                    },
                    {
                      step: '2',
                      title: 'Поиск кандидатов',
                      body: 'Для каждого неизвестного слова находится ближайшее слово в словаре по расстоянию Левенштейна.',
                    },
                    {
                      step: '3',
                      title: 'Вывод исправлений',
                      body: 'Возвращается исправленный текст с метаданными по каждому исправлению и визуальным diff.',
                    },
                  ].map(({ step, title, body }) => (
                    <li key={step} className="flex gap-3">
                      <span className="flex-shrink-0 w-6 h-6 rounded-full bg-primary-100
                                       text-primary-700 text-xs font-bold flex items-center
                                       justify-center">
                        {step}
                      </span>
                      <div>
                        <p className="text-sm font-semibold text-gray-700">{title}</p>
                        <p className="text-xs text-gray-500 leading-relaxed mt-0.5">{body}</p>
                      </div>
                    </li>
                  ))}
                </ol>
              </div>
            )}
          </div>
        </div>

      </main>

    </div>
  )
}
