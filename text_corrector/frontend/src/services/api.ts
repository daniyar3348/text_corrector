/**
 * API client for the Turan Text Corrector backend.
 *
 * All requests go through the Vite dev-proxy (/api → http://localhost:8000).
 * In production, set VITE_API_BASE_URL to the full backend URL.
 */
import axios, { AxiosError } from 'axios'
import type {
  CorrectionResponse,
  LanguageDetectionResponse,
  HealthResponse,
} from '@/types'

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '/api'

const client = axios.create({
  baseURL: BASE_URL,
  timeout: 15_000,
  headers: { 'Content-Type': 'application/json' },
})

// ── Helpers ───────────────────────────────────────────────────────────────

function extractErrorMessage(error: unknown): string {
  if (error instanceof AxiosError) {
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

export async function checkHealth(): Promise<HealthResponse> {
  try {
    const { data } = await client.get<HealthResponse>('/health')
    return data
  } catch (error) {
    throw new Error(extractErrorMessage(error))
  }
}
