import React, { useState } from 'react'
import type { CorrectionResponse } from '@/types'
import { DiffViewer } from './DiffViewer'

interface CorrectionResultProps {
  result: CorrectionResponse
}

const LANG_BADGE: Record<string, { bg: string; text: string; emoji: string }> = {
  Russian: { bg: 'bg-blue-100', text: 'text-blue-700', emoji: '🇷🇺' },
  Kazakh:  { bg: 'bg-green-100', text: 'text-green-700', emoji: '🇰🇿' },
  Mixed:   { bg: 'bg-purple-100', text: 'text-purple-700', emoji: '🌐' },
  Unknown: { bg: 'bg-gray-100', text: 'text-gray-600', emoji: '❓' },
}

/** 1 исправление · 2 исправления · 5 исправлений */
function pluralCorrections(n: number): string {
  const mod10 = n % 10
  const mod100 = n % 100
  if (mod10 === 1 && mod100 !== 11) return 'исправление'
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) return 'исправления'
  return 'исправлений'
}

export const CorrectionResult: React.FC<CorrectionResultProps> = ({ result }) => {
  const [copied, setCopied] = useState(false)
  const [showDiff, setShowDiff] = useState(true)

  const hasCorrections = result.corrections.length > 0
  const noChange = result.original_text === result.corrected_text
  const lang = LANG_BADGE[result.detected_language] ?? LANG_BADGE['Unknown']
  // Only Kazakh is corrected; anything else comes back unchecked, so "no
  // changes" must not be presented as "the text is correct".
  const unchecked = result.detected_language !== 'Kazakh'
  const notice = result.message
    ?? (unchecked ? 'Исправляется только казахский текст — этот текст не проверялся.' : null)

  const handleCopy = async () => {
    await navigator.clipboard.writeText(result.corrected_text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="space-y-5">

      {/* ── Header row ──────────────────────────────────────────────────── */}
      <div className="flex items-center justify-between flex-wrap gap-2">
        <h2 className="text-base font-bold text-gray-800">Результат исправления</h2>
        <div className="flex items-center gap-2">
          {/* Language badge */}
          <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full
                           text-xs font-semibold ${lang.bg} ${lang.text}`}>
            <span>{lang.emoji}</span>
            {result.detected_language}
            <span className="opacity-60">
              {Math.round(result.confidence * 100)}%
            </span>
          </span>
          {/* Timing */}
          <span className="text-xs text-gray-400 font-mono">
            {result.processing_time_ms.toFixed(1)} ms
          </span>
        </div>
      </div>

      {/* ── Corrected text box ───────────────────────────────────────────── */}
      <div className="rounded-xl border border-indigo-200 bg-indigo-50 p-4">
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1 min-w-0">
            <p className="text-[11px] font-semibold text-indigo-400 uppercase tracking-wider mb-2">
              Исправленный текст
            </p>
            <p className="font-mono text-base leading-relaxed text-gray-800 break-words
                          whitespace-pre-wrap">
              {result.corrected_text}
            </p>
          </div>
          <button
            onClick={handleCopy}
            title="Copy to clipboard"
            className="flex-shrink-0 inline-flex items-center gap-1.5 text-xs px-2.5 py-1.5
                       rounded-lg bg-white border border-gray-200 text-gray-500
                       hover:text-indigo-600 hover:border-indigo-300
                       transition-colors duration-150 shadow-sm"
          >
            {copied ? '✓ Скопировано' : '⎘ Копировать'}
          </button>
        </div>
      </div>

      {/* ── Server note (unchecked language, truncation…) ────────────────── */}
      {notice && (
        <p className="text-xs text-amber-700 bg-amber-50 border border-amber-200
                      rounded-lg px-3 py-2">
          ⚠ {notice}
        </p>
      )}

      {/* ── No-change message ────────────────────────────────────────────── */}
      {noChange && !unchecked && (
        <div className="flex items-center gap-2.5 rounded-xl bg-green-50 border
                        border-green-200 px-4 py-3 text-sm text-green-700">
          <span className="text-lg">✅</span>
          <span>Исправления не нужны — текст написан верно.</span>
        </div>
      )}

      {/* ── Corrections list ─────────────────────────────────────────────── */}
      {hasCorrections && (
        <div>
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
            {result.corrections.length} {pluralCorrections(result.corrections.length)}
          </p>
          <div className="flex flex-wrap gap-2">
            {result.corrections.map((c, i) => (
              <div
                key={i}
                className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full
                           bg-white border border-gray-200 text-sm shadow-sm"
              >
                <span className="font-mono text-red-500 line-through">{c.before}</span>
                <span className="text-gray-300">→</span>
                <span className="font-mono text-green-600 font-semibold">{c.after}</span>
                <span className="ml-0.5 text-xs text-gray-400 bg-gray-100 rounded-full
                                 px-1.5 py-0.5">
                  {c.type}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── Diff section ─────────────────────────────────────────────────── */}
      {!noChange && (
        <div>
          <button
            onClick={() => setShowDiff((v) => !v)}
            className="flex items-center gap-1.5 text-xs font-semibold text-primary-600
                       hover:text-primary-800 transition-colors mb-3"
          >
            <span className={`transition-transform duration-200 ${showDiff ? 'rotate-90' : ''}`}>
              ▶
            </span>
            {showDiff ? 'Скрыть' : 'Показать'} сравнение
          </button>

          {showDiff && <DiffViewer
            original={result.original_text}
            corrected={result.corrected_text}
          />}
        </div>
      )}
    </div>
  )
}
