// ── API response types ─────────────────────────────────────────────────────

export type Language = 'Russian' | 'Kazakh' | 'Mixed' | 'Unknown'

export interface LanguageDetectionResponse {
  detected_language: Language
  confidence: number
  status: 'success' | 'error'
  message?: string | null
}

export interface CorrectionItem {
  before: string
  after: string
  type: string
  position?: number | null
}

export interface CorrectionResponse {
  original_text: string
  corrected_text: string
  detected_language: Language
  confidence: number
  corrections: CorrectionItem[]
  processing_time_ms: number
  status: 'success' | 'error'
  message?: string | null
}

export interface HealthResponse {
  service_status: string
  model_status: string
  version: string
  details?: Record<string, string> | null
}

// ── UI state types ─────────────────────────────────────────────────────────

export type RequestStatus = 'idle' | 'loading' | 'success' | 'error'

export interface AppState {
  inputText: string
  detectedLanguage: Language | null
  languageConfidence: number
  correctionResult: CorrectionResponse | null
  status: RequestStatus
  error: string | null
}

// ── Diff types ─────────────────────────────────────────────────────────────

export interface DiffToken {
  value: string
  changed: boolean
  type: 'added' | 'removed' | 'unchanged'
}
