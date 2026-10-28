/**
 * API client for the Turan Text Corrector backend.
 *
 * All requests go through the Vite dev-proxy (/api → http://localhost:8000).
 * In production, set VITE_API_BASE_URL to the full backend URL.
 */
import axios, { AxiosError } from 'axios'
import type {
  CorrectionResponse,
  FileCorrectionResponse,
  LanguageDetectionResponse,
  HealthResponse,
} from '@/types'

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '/api'

// Generous: the hosted server shares a small CPU, and a 5000-character text is
// tens of model passes (one per sentence).
const client = axios.create({
  baseURL: BASE_URL,
  timeout: 60_000,
  headers: { 'Content-Type': 'application/json' },
})

const SERVER_DOWN_MESSAGE =
  'Сервер недоступен или ещё просыпается — попробуйте через минуту.'

// ── Helpers ───────────────────────────────────────────────────────────────

function extractErrorMessage(error: unknown): string {
  if (error instanceof AxiosError) {
    // No answer at all, or the hosting proxy answering for a sleeping server
    const status = error.response?.status
    if (!error.response || status === 502 || status === 503 || status === 504) {
      return SERVER_DOWN_MESSAGE
    }
    const detail = error.response?.data?.detail
    if (typeof detail === 'string') return detail
    if (Array.isArray(detail)) {
      return detail.map((d: { msg?: string }) => d.msg ?? JSON.stringify(d)).join('; ')
    }
    if (error.message) return error.message
  }
  return 'An unexpected error occurred. Please try again.'
}

// ── API functions ─────────────────────────────────────────────────────────

export async function detectLanguage(
  text: string,
): Promise<LanguageDetectionResponse> {
  try {
    const { data } = await client.post<LanguageDetectionResponse>(
      '/detect-language',
      { text },
    )
    return data
  } catch (error) {
    throw new Error(extractErrorMessage(error))
  }
}

export async function correctText(text: string): Promise<CorrectionResponse> {
  try {
    const { data } = await client.post<CorrectionResponse>('/correct-text', {
      text,
    })
    return data
  } catch (error) {
    throw new Error(extractErrorMessage(error))
  }
}

/** Accepted by POST /correct-file — mirrors `file_extraction.supported_extensions()`. */
export const SUPPORTED_FILE_EXTENSIONS = [
  '.txt', '.md', '.csv', '.tsv', '.log', '.docx', '.pdf',
] as const

export const MAX_FILE_SIZE_MB = 5

/**
 * Upload a document and correct all of its text.
 *
 * Uses a much longer timeout than the other calls: the backend runs one model
 * pass per sentence, so a long document legitimately takes tens of seconds.
 */
export async function correctFile(
  file: File,
  signal?: AbortSignal,
): Promise<FileCorrectionResponse> {
  const form = new FormData()
  form.append('file', file)

  try {
    const { data } = await client.post<FileCorrectionResponse>(
      '/correct-file',
      form,
      {
        // Let the browser set the multipart boundary itself
        headers: { 'Content-Type': undefined },
        timeout: 180_000,
        signal,
      },
    )
    return data
  } catch (error) {
    throw new Error(extractErrorMessage(error))
  }
}

export async function checkHealth(): Promise<HealthResponse> {
  try {
    const { data } = await client.get<HealthResponse>('/health', { timeout: 10_000 })
    return data
  } catch (error) {
    throw new Error(extractErrorMessage(error))
  }
}
