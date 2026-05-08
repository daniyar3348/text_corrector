import React from 'react'
import type { Language } from '@/types'

interface LanguageBadgeProps {
  language: Language | null
  confidence: number
  loading: boolean
}

const CONFIG: Record<Language, {
  emoji: string; bg: string; border: string; text: string; dot: string
}> = {
  Russian: {
    emoji: '🇷🇺',
    bg: 'bg-blue-50',
    border: 'border-blue-200',
    text: 'text-blue-800',
    dot: 'bg-blue-500',
  },
  Kazakh: {
    emoji: '🇰🇿',
    bg: 'bg-green-50',
    border: 'border-green-200',
    text: 'text-green-800',
    dot: 'bg-green-500',
  },
  Mixed: {
    emoji: '🌐',
    bg: 'bg-purple-50',
    border: 'border-purple-200',
    text: 'text-purple-800',
    dot: 'bg-purple-500',
  },
  Unknown: {
    emoji: '❓',
    bg: 'bg-gray-50',
    border: 'border-gray-200',
    text: 'text-gray-500',
    dot: 'bg-gray-400',
  },
}

export const LanguageBadge: React.FC<LanguageBadgeProps> = ({
  language,
  confidence,
  loading,
}) => {
  if (loading) {
    return (
      <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full
                      bg-gray-100 border border-gray-200 animate-pulse">
        <div className="w-2 h-2 rounded-full bg-gray-300" />
        <span className="text-xs text-gray-400 font-medium">Определение…</span>
      </div>
    )
  }

  if (!language) {
    return (
      <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full
                      bg-gray-50 border border-gray-200">
        <span className="text-xs text-gray-400">Язык: —</span>
      </div>
    )
  }

  const c = CONFIG[language]

  return (
    <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-full border
                     animate-fade-in ${c.bg} ${c.border}`}>
      <span className="text-sm leading-none">{c.emoji}</span>
      <span className={`text-xs font-semibold ${c.text}`}>{language}</span>
      {confidence > 0 && (
        <span className={`text-[11px] font-normal ${c.text} opacity-60`}>
          {Math.round(confidence * 100)}%
        </span>
      )}
    </div>
  )
}
