import React, { useMemo } from 'react'

interface DiffViewerProps {
  original: string
  corrected: string
}

type Op = { type: 'same' | 'changed'; original: string; corrected: string }

/** Word-level diff preserving whitespace / punctuation tokens. */
function buildDiff(original: string, corrected: string): Op[] {
  const tokenise = (s: string) => s.match(/\S+|\s+/g) ?? []
  const orig = tokenise(original)
  const corr = tokenise(corrected)
  const len = Math.max(orig.length, corr.length)
  const ops: Op[] = []
  for (let i = 0; i < len; i++) {
    const o = orig[i] ?? ''
    const c = corr[i] ?? ''
    ops.push({ type: o === c ? 'same' : 'changed', original: o, corrected: c })
  }
  return ops
}

export const DiffViewer: React.FC<DiffViewerProps> = ({ original, corrected }) => {
  const diff = useMemo(() => buildDiff(original, corrected), [original, corrected])

  if (original === corrected) return null

  return (
    <div className="space-y-2 animate-slide-up">

      {/* Original */}
      <div className="rounded-xl border border-red-200 bg-red-50/70 p-4">
        <p className="text-[10px] font-bold text-red-400 uppercase tracking-widest mb-2">
          Оригинал
        </p>
        <p className="font-mono text-sm leading-relaxed break-words text-gray-700">
          {diff.map((op, i) =>
            op.type === 'same' ? (
              <span key={i}>{op.original}</span>
            ) : op.original ? (
              <span key={i}
                className="bg-red-200 text-red-800 line-through rounded
                           px-0.5 mx-px decoration-red-500">
                {op.original}
              </span>
            ) : null,
          )}
        </p>
      </div>

      {/* Corrected */}
      <div className="rounded-xl border border-green-200 bg-green-50/70 p-4">
        <p className="text-[10px] font-bold text-green-500 uppercase tracking-widest mb-2">
          Исправлено
        </p>
        <p className="font-mono text-sm leading-relaxed break-words text-gray-700">
          {diff.map((op, i) =>
            op.type === 'same' ? (
              <span key={i}>{op.corrected}</span>
            ) : op.corrected ? (
              <span key={i}
                className="bg-green-200 text-green-800 font-semibold rounded px-0.5 mx-px">
                {op.corrected}
              </span>
            ) : null,
          )}
        </p>
      </div>
    </div>
  )
}
