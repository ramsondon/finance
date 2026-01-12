/**
 * Format preferences and utilities (non-JSX)
 */

// Date format options
export const DATE_FORMATS = {
  'MM/DD/YYYY': { locale: 'en-US', format: 'short' },
  'DD/MM/YYYY': { locale: 'en-GB', format: 'short' },
  'YYYY-MM-DD': { locale: 'sv-SE', format: 'short' },
  'DD.MM.YYYY': { locale: 'de-DE', format: 'short' },
  'Long': { locale: 'en-US', format: 'long' },
}

// Currency options
export const CURRENCY_OPTIONS = [
  { code: 'USD', symbol: '$', name: 'US Dollar' },
  { code: 'EUR', symbol: '€', name: 'Euro' },
  { code: 'GBP', symbol: '£', name: 'British Pound' },
  { code: 'CHF', symbol: 'CHF', name: 'Swiss Franc' },
  { code: 'CAD', symbol: 'C$', name: 'Canadian Dollar' },
  { code: 'AUD', symbol: 'A$', name: 'Australian Dollar' },
  { code: 'JPY', symbol: '¥', name: 'Japanese Yen' },
]

// Number format options
export const NUMBER_FORMATS = {
  '1,000.00': { locale: 'en-US', separator: ',', decimal: '.' },
  '1.000,00': { locale: 'de-DE', separator: '.', decimal: ',' },
  '1 000,00': { locale: 'fr-FR', separator: ' ', decimal: ',' },
  '1 000.00': { locale: 'sv-SE', separator: ' ', decimal: '.' },
}

/**
 * Get default preferences or from localStorage
 */
export function getFormatPreferences() {
  return {
    dateFormat: localStorage.getItem('dateFormat') || 'MM/DD/YYYY',
    currencyCode: localStorage.getItem('currencyCode') || 'USD',
    numberFormat: localStorage.getItem('numberFormat') || '1,000.00',
  }
}

/**
 * Save format preferences to localStorage
 */
export function saveFormatPreferences(prefs) {
  if (prefs.dateFormat) localStorage.setItem('dateFormat', prefs.dateFormat)
  if (prefs.currencyCode) localStorage.setItem('currencyCode', prefs.currencyCode)
  if (prefs.numberFormat) localStorage.setItem('numberFormat', prefs.numberFormat)
}

/**
 * Format date according to user preference
 */
export function formatDate(date, dateFormat = null) {
  const format = dateFormat || getFormatPreferences().dateFormat
  const d = typeof date === 'string' ? new Date(date) : date

  const options = DATE_FORMATS[format]
  if (!options) return d.toLocaleDateString('en-US')

  return d.toLocaleDateString(options.locale, {
    year: format === 'Long' ? 'numeric' : '2-digit',
    month: format === 'Long' ? 'long' : '2-digit',
    day: '2-digit',
  })
}

/**
 * Format currency according to user preference
 */
export function formatCurrency(amount, currencyCode = null) {
  const code = currencyCode || getFormatPreferences().currencyCode
  const currency = CURRENCY_OPTIONS.find(c => c.code === code)
  if (!currency) return amount.toString()

  return `${currency.symbol} ${formatNumber(Math.abs(amount))}`
}

/**
 * Format number according to user preference
 */
export function formatNumber(num, numberFormat = null) {
  const format = numberFormat || getFormatPreferences().numberFormat
  const formatConfig = NUMBER_FORMATS[format]
  if (!formatConfig) return num.toString()

  const parts = num.toFixed(2).split('.')
  const integerPart = parseInt(parts[0]).toLocaleString(formatConfig.locale, { useGrouping: true })
  const decimalPart = parts[1]

  // Replace separators based on format
  let result = integerPart + formatConfig.decimal + decimalPart

  // Handle thousands separator replacement
  if (formatConfig.separator !== ',') {
    result = result.replace(/,/g, formatConfig.separator)
  }

  return result
}

/**
 * Format currency with sensitive mode support
 */
export function formatMonetary(amount, sensitiveMode = false, currencyCode = null) {
  const formatted = formatCurrency(amount, currencyCode)

  if (!sensitiveMode) {
    return formatted
  }

  return {
    __html: `<span class="select-none" style="filter: blur(6px); user-select: none;">${formatted}</span>`
  }
}

/**
 * Hook to get sensitive mode state from context
 */
export function useSensitiveMode() {
  const sensitiveMode = localStorage.getItem('sensitiveMode') === 'true'
  return sensitiveMode
}

/**
 * Apply sensitive mode blur to any text
 */
export function getSensitiveClass(sensitiveMode) {
  if (!sensitiveMode) return ''
  return 'blur-sm select-none'
}

