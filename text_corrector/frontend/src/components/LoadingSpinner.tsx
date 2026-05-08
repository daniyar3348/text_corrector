import React from 'react'

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg'
  label?: string
}

const SIZE = {
  sm: 'h-4 w-4 border-2',
  md: 'h-6 w-6 border-2',
  lg: 'h-8 w-8 border-[3px]',
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  size = 'md',
  label = 'Loading…',
}) => (
  <span className="inline-flex items-center gap-2" aria-label={label}>
    <span
      className={`${SIZE[size]} rounded-full border-primary-200 border-t-primary-600 animate-spin inline-block`}
    />
    {label && <span className="text-sm text-gray-500">{label}</span>}
  </span>
)
