/**
 * Utility component for displaying sensitive data with blur effect
 * This is a JSX component file
 */
import React from 'react'

// Re-export formatting utilities and preferences
export {
  getFormatPreferences,
  saveFormatPreferences,
  formatDate,
  formatCurrency,
  formatNumber,
  formatMonetary,
  useSensitiveMode,
  getSensitiveClass,
  DATE_FORMATS,
  CURRENCY_OPTIONS,
  NUMBER_FORMATS,
} from './format'

/**
 * React component for displaying sensitive data with blur effect
 */
export function SensitiveValue({ value, sensitiveMode, isMonetary = true }) {
  if (!sensitiveMode) {
    return <span>{value}</span>
  }
  return (
    <span className="select-none" style={{
      filter: 'blur(6px)',
      WebkitUserSelect: 'none',
      userSelect: 'none'
    }}>
      {value}
    </span>
  )
}


