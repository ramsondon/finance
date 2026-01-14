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

// Time format options
export const TIME_FORMATS = {
  '12-hour': { format: 'numeric', hour12: true },
  '24-hour': { format: 'numeric', hour12: false },
}

/**
 * Get default preferences or from localStorage
 */
export function getFormatPreferences() {
  return {
    dateFormat: localStorage.getItem('dateFormat') || 'MM/DD/YYYY',
    currencyCode: localStorage.getItem('currencyCode') || 'USD',
    numberFormat: localStorage.getItem('numberFormat') || '1,000.00',
    timeFormat: localStorage.getItem('timeFormat') || '24-hour',
    language: localStorage.getItem('language') || 'en',
  }
}

/**
 * Save format preferences to localStorage
 */
export function saveFormatPreferences(prefs) {
  if (prefs.dateFormat) localStorage.setItem('dateFormat', prefs.dateFormat)
  if (prefs.currencyCode) localStorage.setItem('currencyCode', prefs.currencyCode)
  if (prefs.numberFormat) localStorage.setItem('numberFormat', prefs.numberFormat)
  if (prefs.timeFormat) localStorage.setItem('timeFormat', prefs.timeFormat)
  if (prefs.language) localStorage.setItem('language', prefs.language)
}

/**
 * Format date according to user preference
 */
export function formatDate(date, dateFormat = null) {
  const prefs = getFormatPreferences()
  const format = dateFormat || prefs.dateFormat
  const d = typeof date === 'string' ? new Date(date) : date

  const options = DATE_FORMATS[format]
  if (!options) return d.toLocaleDateString('en-US')

  // Use user's language preference, with fallback to locale from DATE_FORMATS
  const locale = prefs.language === 'de' ? 'de-DE' : options.locale

  return d.toLocaleDateString(locale, {
    year: format === 'Long' ? 'numeric' : '2-digit',
    month: format === 'Long' ? 'long' : '2-digit',
    day: '2-digit',
  })
}

/**
 * Format datetime (ISO string with time) according to user preferences
 * Converts UTC to user's browser timezone and formats as "Date Time" (e.g., "01/14/2026 14:30")
 */
export function formatDateTime(dateTimeString, dateFormat = null, timeFormat = null) {
  const prefs = getFormatPreferences()
  const format = dateFormat || prefs.dateFormat
  const tFormat = timeFormat || prefs.timeFormat

  // Parse ISO datetime string
  const d = typeof dateTimeString === 'string' ? new Date(dateTimeString) : dateTimeString

  // Get date options
  const dateOptions = DATE_FORMATS[format]
  if (!dateOptions) {
    return d.toLocaleString('en-US')
  }

  // Use user's language preference, with fallback to locale from DATE_FORMATS
  const locale = prefs.language === 'de' ? 'de-DE' : dateOptions.locale

  // Format date part
  const dateStr = d.toLocaleDateString(locale, {
    year: format === 'Long' ? 'numeric' : '2-digit',
    month: format === 'Long' ? 'long' : '2-digit',
    day: '2-digit',
  })

  // Format time part (HH:MM only)
  const timeOptions = {
    hour: '2-digit',
    minute: '2-digit',
    hour12: tFormat === '12-hour',
  }
  const timeStr = d.toLocaleTimeString(locale, timeOptions)

  return `${dateStr} ${timeStr}`
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
 * Custom hook to listen for sensitive mode changes in real-time
 * NOTE: This must be called from a React component context
 */
export function useSensitiveModeListener() {
  // This hook must be imported in a JSX file and called from React
  // See sensitive.js for the actual implementation
  throw new Error('useSensitiveModeListener must be imported from utils/sensitive (JSX file), not from format.js')
}

/**
 * Apply sensitive mode blur to any text
 */
export function getSensitiveClass(sensitiveMode) {
  if (!sensitiveMode) return ''
  return 'blur-sm select-none'
}

/**
 * Convert ISO date string (YYYY-MM-DD) to user's preferred format
 * Used for displaying dates in form inputs with user-friendly format
 *
 * @param {string} isoDate - Date in ISO format (YYYY-MM-DD)
 * @param {string} dateFormat - User's preferred date format (optional)
 * @returns {string} Date in user's preferred format
 */
export function dateToInputFormat(isoDate, dateFormat = null) {
  if (!isoDate) return ''

  const format = dateFormat || getFormatPreferences().dateFormat

  // Parse ISO date (YYYY-MM-DD)
  const [year, month, day] = isoDate.split('-')

  switch(format) {
    case 'MM/DD/YYYY':
      return `${month}/${day}/${year}`
    case 'DD/MM/YYYY':
      return `${day}/${month}/${year}`
    case 'DD.MM.YYYY':
      return `${day}.${month}.${year}`
    case 'YYYY-MM-DD':
      return `${year}-${month}-${day}` // Already in ISO format
    case 'Long':
      // For long format, return ISO and let display handle it
      return `${year}-${month}-${day}`
    default:
      return `${year}-${month}-${day}`
  }
}

/**
 * Convert date from user's preferred format to ISO format (YYYY-MM-DD)
 * Used when submitting forms with user-entered dates
 *
 * @param {string} inputDate - Date in user's preferred format or ISO
 * @param {string} dateFormat - User's preferred date format (optional)
 * @returns {string} Date in ISO format (YYYY-MM-DD)
 */
export function inputDateToISO(inputDate, dateFormat = null) {
  if (!inputDate) return ''

  const format = dateFormat || getFormatPreferences().dateFormat

  let year, month, day

  // Try to parse based on user's format preference
  switch(format) {
    case 'MM/DD/YYYY': {
      const parts = inputDate.split('/')
      if (parts.length === 3) {
        [month, day, year] = parts
      } else {
        return inputDate // Return as-is if can't parse
      }
      break
    }
    case 'DD/MM/YYYY': {
      const parts = inputDate.split('/')
      if (parts.length === 3) {
        [day, month, year] = parts
      } else {
        return inputDate
      }
      break
    }
    case 'DD.MM.YYYY': {
      const parts = inputDate.split('.')
      if (parts.length === 3) {
        [day, month, year] = parts
      } else {
        return inputDate
      }
      break
    }
    case 'YYYY-MM-DD':
    case 'Long':
      // Already in ISO format or try parsing as ISO
      if (inputDate.includes('-')) {
        return inputDate // Already ISO
      }
      return inputDate
    default:
      return inputDate
  }

  // Format as ISO (YYYY-MM-DD)
  if (year && month && day) {
    // Pad month and day with zeros if needed
    const paddedMonth = String(month).padStart(2, '0')
    const paddedDay = String(day).padStart(2, '0')
    return `${year}-${paddedMonth}-${paddedDay}`
  }

  return inputDate
}

