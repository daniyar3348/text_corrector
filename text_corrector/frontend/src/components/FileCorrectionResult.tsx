import React, { useMemo, useState } from 'react'
import type { FileCorrectionResponse } from '@/types'

interface FileCorrectionResultProps {
  result: FileCorrectionResponse
  /** Offered only when the corrected text fits the editor's character limit. */
  onInsert?: (text: string) => void
  insertLimit?: number
}

const LANG_BADGE: Record<string, { bg: string; text: string; emoji: string }> = {
  Russian: { bg: 'bg-blue-100', text: 'text-blue-700', emoji: '🇷🇺' },
  Kazakh: { bg: 'bg-green-100', text: 'text-green-700', emoji: '🇰🇿' },
  Mixed: { bg: 'bg-purple-100', text: 'text-purple-700', emoji: '🌐' },
  Unknown: { bg: 'bg-gray-100', text: 'text-gray-600', emoji: '❓' },
}

const PREVIEW_CHARS = 1500

/** `отчёт.docx` → `отчёт_исправленный.txt` */
function downloadName(filename: string): string {
  const dot = filename.lastIndexOf('.')
  const base = dot > 0 ? filename.slice(0, dot) : filename
  return `${base}_исправленный.txt`
}

export const FileCorrectionResult: React.FC<FileCorrectionResultProps> = ({
  result,
  onInsert,
  insertLimit = 5000,
}) => {
  const [copied, setCopied] = useState(false)
  const [expanded, setExpanded] = useState(false)

  const lang = LANG_BADGE[result.detected_language] ?? LANG_BADGE['Unknown']
  const unchanged = result.corrected_words === 0

  // Long documents are truncated for display only — copy and download always
  // use the full corrected text.
  const preview = useMemo(() => {
    if (expanded || result.corrected_text.length <= PREVIEW_CHARS) {
      return result.corrected_text
    }
    return result.corrected_text.slice(0, PREVIEW_CHARS)
  }, [result.corrected_text, expanded])

  const isTruncated = result.corrected_text.length > PREVIEW_CHARS

  const handleCopy = async () => {
    await navigator.clipboard.writeText(result.corrected_text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleDownload = () => {
    const blob = new Blob([result.corrected_text], {
      type: 'text/plain;charset=utf-8',
    })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = downloadName(result.filename)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }

  const canInsert =
    onInsert && result.corrected_text.length <= insertLimit

  return (
    <div className="space-y-5">

      {/* ── Header ──────────────────────────────────────────────────────── */}
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-2 min-w-0">
          <span className="text-lg flex-shrink-0">📄</span>
          <h2
            className="text-base font-bold text-gray-800 truncate"
            title={result.filename}
          >
            {result.filename}
          </h2>
        </div>
        <div className="flex items-center gap-2">
          <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full
                           text-xs font-semibold ${lang.bg} ${lang.text}`}>
            <span>{lang.emoji}</span>
            {result.detected_language}
            <span className="opacity-60">
              {Math.round(result.confidence * 100)}%
            </span>
          </span>
          <span className="text-xs text-gray-400 font-mono">
            {result.processing_time_ms < 1000
              ? `${Math.round(result.processing_time_ms)} мс`
              : `${(result.processing_time_ms / 1000).toFixed(1)} с`}
          </span>
        </div>
      </div>

      {/* ── Stats ───────────────────────────────────────────────────────── */}
      <div className="grid grid-cols-3 gap-2">
        {[
          { label: 'Слов', value: result.total_words.toLocaleString('ru') },
          {
            label: 'Исправлено',
            value: result.corrected_words.toLocaleString('ru'),
            accent: result.corrected_words > 0,
          },
          { label: 'Проходов', value: result.chunks.toLocaleString('ru') },
        ].map(({ label, value, accent }) => (
          <div
            key={label}
            className="rounded-xl border border-gray-200 bg-gray-50 px-3 py-2.5 text-center"
          >
            <p className={`text-lg font-bold tabular-nums
                          ${accent ? 'text-indigo-600' : 'text-gray-700'}`}>
              {value}
            </p>
            <p className="text-[11px] text-gray-500 uppercase tracking-wide">
              {label}
            </p>
          </div>
        ))}
      </div>

      {/* ── Server note (truncation, skipped fragments…) ─────────────────── */}
      {result.message && (
        <p className="text-xs text-amber-700 bg-amber-50 border border-amber-200
                      rounded-lg px-3 py-2">
          ⚠ {result.message}
        </p>
      )}

      {/* ── Nothing to fix ──────────────────────────────────────────────── */}
      {unchanged && (
        <div className="flex items-center gap-2.5 rounded-xl bg-green-50 border
                        border-green-200 px-4 py-3 text-sm text-green-700">
          <span className="text-lg">✅</span>
          <span>Ошибок не найдено — файл оставлен без изменений.</span>
        </div>
      )}

      {/* ── Corrected text ──────────────────────────────────────────────── */}
      <div className="rounded-xl border border-indigo-200 bg-indigo-50 p-4">
        <p className="text-[11px] font-semibold text-indigo-400 uppercase
                      tracking-wider mb-2">
          Исправленный текст
        </p>
        <pre className="font-mono text-[13px] leading-relaxed text-gray-800
                        whitespace-pre-wrap break-words max-h-80 overflow-y-auto">
          {preview}
          {isTruncated && !expanded && '…'}
        </pre>
        {isTruncated && (
          <button
            onClick={() => setExpanded((v) => !v)}
            className="mt-2 text-xs font-semibold text-primary-600
                       hover:text-primary-800 transition-colors"
          >
            {expanded
              ? 'Свернуть'
              : `Показать целиком (${result.corrected_text.length.toLocaleString('ru')} символов)`}
          </button>
        )}
      </div>

      {/* ── Actions ─────────────────────────────────────────────────────── */}
      <div className="flex flex-wrap items-center gap-2">
        <button
          onClick={handleDownload}
          className="
            inline-flex items-center gap-2 px-4 py-2 rounded-xl
            bg-gradient-to-r from-primary-600 to-indigo-600 text-white
            font-semibold text-sm hover:from-primary-700 hover:to-indigo-700
            active:scale-[0.98] transition-all duration-150 shadow-sm
            focus:outline-none focus:ring-2 focus:ring-primary-400 focus:ring-offset-2
          "
        >
          <span className="text-base leading-none">⬇</span>
          Скачать
        </button>

        <button
          onClick={handleCopy}
          className="inline-flex items-center gap-1.5 text-sm px-4 py-2
                     rounded-xl bg-white border border-gray-200 text-gray-600
                     hover:text-indigo-600 hover:border-indigo-300
                     transition-colors duration-150 shadow-sm"
        >
          {copied ? '✓ Скопировано' : '⎘ Копировать'}
        </button>

        {canInsert && (
          <button
            onClick={() => onInsert!(result.corrected_text)}
            className="inline-flex items-center gap-1.5 text-sm px-4 py-2
                       rounded-xl bg-white border border-gray-200 text-gray-600
                       hover:text-indigo-600 hover:border-indigo-300
                       transition-colors duration-150 shadow-sm"
          >
            ↩ В редактор
          </button>
        )}
      </div>

      {/* ── Correction list ─────────────────────────────────────────────── */}
      {result.corrections.length > 0 && (
        <div>
          <p className="text-xs font-semibold text-gray-500 uppercase
                        tracking-wide mb-2">
            Замены
            {result.corrections_total > result.corrections.length && (
              <span className="ml-1 normal-case font-normal text-gray-400">
                — показаны {result.corrections.length} из {result.corrections_total}
              </span>
            )}
          </p>
          <div className="flex flex-wrap gap-2 max-h-56 overflow-y-auto">
            {result.corrections.map((c, i) => (
              <div
                key={`${c.position}-${i}`}
                className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full
                           bg-white border border-gray-200 text-sm shadow-sm"
              >
                <span className="font-mono text-red-500 line-through">{c.before}</span>
                <span className="text-gray-300">→</span>
                <span className="font-mono text-green-600 font-semibold">{c.after}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
