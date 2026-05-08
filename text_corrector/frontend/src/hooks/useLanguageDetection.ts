/**
 * Hook for debounced language detection as the user types.
 */
import { useState, useEffect, useRef, useCallback } from 'react'
import { detectLanguage } from '@/services/api'
import type { Language } from '@/types'

const DEBOUNCE_MS = 400
const MIN_LENGTH = 2

interface DetectionState {
  language: Language | null
  confidence: number
  loading: boolean
}

export function useLanguageDetection(text: string): DetectionState {
  const [state, setState] = useState<DetectionState>({
    language: null,
    confidence: 0,
    loading: false,
  })
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const latestText = useRef(text)

  const runDetection = useCallback(async (value: string) => {
    if (value.trim().length < MIN_LENGTH) {
      setState({ language: null, confidence: 0, loading: false })
      return
    }

    setState((prev) => ({ ...prev, loading: true }))
    try {
      const result = await detectLanguage(value)
      // Only update if the text hasn't changed while we were waiting
      if (value === latestText.current) {
        setState({
          language: result.detected_language,
          confidence: result.confidence,
          loading: false,
        })
      }
    } catch {
      setState((prev) => ({ ...prev, loading: false }))
    }
  }, [])

  useEffect(() => {
    latestText.current = text

    if (timerRef.current) {
      clearTimeout(timerRef.current)
    }

    if (!text.trim()) {
      setState({ language: null, confidence: 0, loading: false })
      return
    }

    timerRef.current = setTimeout(() => {
      runDetection(text)
    }, DEBOUNCE_MS)

    return () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current)
      }
    }
  }, [text, runDetection])

  return state
}
