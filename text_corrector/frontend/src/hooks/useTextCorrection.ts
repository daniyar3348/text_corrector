/**
 * Hook for triggering text correction and managing its state.
 */
import { useState, useCallback } from 'react'
import { correctText } from '@/services/api'
import type { CorrectionResponse, RequestStatus } from '@/types'

interface CorrectionState {
  result: CorrectionResponse | null
  status: RequestStatus
  error: string | null
}

interface UseCorrectionReturn extends CorrectionState {
  correct: (text: string) => Promise<void>
  reset: () => void
}

export function useTextCorrection(): UseCorrectionReturn {
  const [state, setState] = useState<CorrectionState>({
    result: null,
    status: 'idle',
    error: null,
  })

  const correct = useCallback(async (text: string) => {
    if (!text.trim()) {
      setState({
        result: null,
        status: 'error',
        error: 'Please enter some text before correcting.',
      })
      return
    }

    setState({ result: null, status: 'loading', error: null })

    try {
      const result = await correctText(text)
      setState({ result, status: 'success', error: null })
    } catch (err) {
      const message =
        err instanceof Error ? err.message : 'Correction failed. Please try again.'
      setState({ result: null, status: 'error', error: message })
    }
  }, [])

  const reset = useCallback(() => {
    setState({ result: null, status: 'idle', error: null })
  }, [])

  return { ...state, correct, reset }
}
