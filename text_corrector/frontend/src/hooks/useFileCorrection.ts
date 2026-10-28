/**
 * Hook for uploading a document and correcting all of its text.
 *
 * Kept separate from `useTextCorrection` because a file carries state the
 * textarea flow has no use for — the chosen file itself, a client-side size
 * check, and an abort handle for long documents.
 */
import { useCallback, useRef, useState } from 'react'
import {
  MAX_FILE_SIZE_MB,
  SUPPORTED_FILE_EXTENSIONS,
  correctFile,
} from '@/services/api'
import type { FileCorrectionResponse, RequestStatus } from '@/types'

interface FileCorrectionState {
  result: FileCorrectionResponse | null
  status: RequestStatus
  error: string | null
  filename: string | null
}

interface UseFileCorrectionReturn extends FileCorrectionState {
  upload: (file: File) => Promise<void>
  cancel: () => void
  reset: () => void
}

const IDLE: FileCorrectionState = {
  result: null,
  status: 'idle',
  error: null,
  filename: null,
}

function isSupported(name: string): boolean {
  const lower = name.toLowerCase()
  return SUPPORTED_FILE_EXTENSIONS.some((ext) => lower.endsWith(ext))
}

export function useFileCorrection(): UseFileCorrectionReturn {
  const [state, setState] = useState<FileCorrectionState>(IDLE)
  const abortRef = useRef<AbortController | null>(null)

  const upload = useCallback(async (file: File) => {
    // Reject locally what the server would reject anyway — no point uploading
    // megabytes just to be told the format is wrong.
    if (!isSupported(file.name)) {
      setState({
        result: null,
        status: 'error',
        filename: file.name,
        error:
          `Формат не поддерживается. Доступно: ${SUPPORTED_FILE_EXTENSIONS.join(', ')}`,
      })
      return
    }
    if (file.size > MAX_FILE_SIZE_MB * 1024 * 1024) {
      setState({
        result: null,
        status: 'error',
        filename: file.name,
        error: `Файл больше ${MAX_FILE_SIZE_MB} МБ. Разделите его на части.`,
      })
      return
    }

    abortRef.current?.abort()
    const controller = new AbortController()
    abortRef.current = controller

    setState({ result: null, status: 'loading', error: null, filename: file.name })

    try {
      const result = await correctFile(file, controller.signal)
      setState({ result, status: 'success', error: null, filename: file.name })
    } catch (err) {
      if (controller.signal.aborted) {
        setState(IDLE)
        return
      }
      setState({
        result: null,
        status: 'error',
        filename: file.name,
        error: err instanceof Error ? err.message : 'Не удалось обработать файл.',
      })
    } finally {
      if (abortRef.current === controller) abortRef.current = null
    }
  }, [])

  const cancel = useCallback(() => {
    abortRef.current?.abort()
    abortRef.current = null
    setState(IDLE)
  }, [])

  const reset = useCallback(() => {
    abortRef.current?.abort()
    abortRef.current = null
    setState(IDLE)
  }, [])

  return { ...state, upload, cancel, reset }
}
