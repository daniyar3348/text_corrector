/**
 * Displays validation errors and user-facing status messages.
 */
import React from 'react'
import type { RequestStatus } from '@/types'

interface StatusMessageProps {
  status: RequestStatus
  error: string | null
}

export const StatusMessage: React.FC<StatusMessageProps> = ({ status, error }) => {
  if (status === 'error' && error) {
    return (
      <div
        role="alert"
        className="flex items-start gap-3 rounded-xl border border-red-200 bg-red-50
                   px-4 py-3 text-sm text-red-700 animate-fade-in"
      >
        <span className="text-base mt-0.5">⚠️</span>
        <span>{error}</span>
      </div>
    )
  }

  return null
}
