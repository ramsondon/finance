/**
 * Format preferences and utilities (non-JSX)
 */

// Date format options
export const DATE_FORMATS = {
  'MM/DD/YYYY': { locale: 'en-US', format: 'short' },
  'DD/MM/YYYY': { locale: 'en-GB', format: 'short' },
  'YYYY-MM-DD': { locale: 'sv-SE', format: 'short' },
  'DD.MM.YYYY': { locale: 'de-DE', format: 'short' },
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
 * Save format preferences to localStorage AND sync to server
 *
 * This function:
 * 1. Updates localStorage immediately (for instant UI change)
 * 2. Syncs to server asynchronously (UserProfile.preferences)
 * 3. Does not block - server sync happens in background
 */
export function saveFormatPreferences(prefs) {
  // Update localStorage immediately (client-side cache)
  if (prefs.dateFormat) localStorage.setItem('dateFormat', prefs.dateFormat)
  if (prefs.currencyCode) localStorage.setItem('currencyCode', prefs.currencyCode)
  if (prefs.numberFormat) localStorage.setItem('numberFormat', prefs.numberFormat)
  if (prefs.timeFormat) localStorage.setItem('timeFormat', prefs.timeFormat)
  if (prefs.language) localStorage.setItem('language', prefs.language)

  // Sync to server asynchronously (don't block UI)
  syncPreferencesToServer(prefs).catch(err => {
    console.warn('Failed to sync format preferences to server:', err)
    // Continue anyway - localStorage is the fallback
  })
}

/**
 * Sync preferences to server (UserProfile.preferences)
 *
 * Non-blocking call to sync user preferences to backend.
 * Preferences are stored in UserProfile.preferences JSONField.
 *
 * @param {Object} prefs - Preferences object
 *   - dateFormat: Date format ('MM/DD/YYYY', 'DD/MM/YYYY', etc.)
 *   - currencyCode: Currency code ('USD', 'EUR', etc.)
 *   - numberFormat: Number format ('1,000.00', '1.000,00', etc.)
 *   - timeFormat: Time format ('12-hour', '24-hour')
 *   - language: Language code ('en', 'de', etc.)
 * @returns {Promise} Resolves when sync completes
 */
async function syncPreferencesToServer(prefs) {
  // Only import when needed (avoid circular dependencies)
  const { syncPreferencesToServer: syncToServer } = await import('./preferences.js')

  // Build preferences object for server
  const serverPrefs = {}
  if (prefs.dateFormat) serverPrefs.dateFormat = prefs.dateFormat
  if (prefs.currencyCode) serverPrefs.currencyCode = prefs.currencyCode
  if (prefs.numberFormat) serverPrefs.numberFormat = prefs.numberFormat
  if (prefs.timeFormat) serverPrefs.timeFormat = prefs.timeFormat
  if (prefs.language) serverPrefs.language = prefs.language

  // Sync to server
  if (Object.keys(serverPrefs).length > 0) {
    await syncToServer(serverPrefs)
  }
}

/**
 * Update all format preferences (syncs to both localStorage and server)
 *
 * Convenience function that:
 * 1. Updates localStorage immediately (instant UI update)
 * 2. Syncs to server asynchronously (non-blocking)
 *
 * @param {Object} prefs - Format preferences object
 *   - dateFormat: Date format preference
 *   - currencyCode or currency: Currency preference
 *   - numberFormat: Number format preference
 *   - timeFormat: Time format preference
 *   - language: Language preference
 * @returns {Promise} Resolves when server sync completes
 */
export async function updateFormatPreferences(prefs) {
  // Update localStorage immediately for instant UI change
  if (prefs.dateFormat) localStorage.setItem('dateFormat', prefs.dateFormat)
  if (prefs.currencyCode) localStorage.setItem('currencyCode', prefs.currencyCode)
  if (prefs.currency) localStorage.setItem('currencyCode', prefs.currency)
  if (prefs.numberFormat) localStorage.setItem('numberFormat', prefs.numberFormat)
  if (prefs.timeFormat) localStorage.setItem('timeFormat', prefs.timeFormat)
  if (prefs.language) localStorage.setItem('language', prefs.language)

  // Sync to server asynchronously (don't block UI)
  try {
    await syncPreferencesToServer(prefs)
    console.log('Format preferences synced to server')
  } catch (error) {
    console.warn('Failed to sync format preferences to server, but localStorage updated:', error)
    // Continue anyway - localStorage is the fallback
  }
}

/**
 * Format date according to user preference
 */
export function formatDate(date, dateFormat = null) {
  const prefs = getFormatPreferences()
  const format = dateFormat || prefs.dateFormat

  // Parse date
  let d = date
  if (typeof date === 'string') {
    d = new Date(date)
  }

  // Handle invalid dates
  if (isNaN(d.getTime())) {
    return ''
  }

  // Extract date parts
  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')

  // Format according to user preference
  switch(format) {
    case 'MM/DD/YYYY':
      return `${month}/${day}/${year}`
    case 'DD/MM/YYYY':
      return `${day}/${month}/${year}`
    case 'DD.MM.YYYY':
      return `${day}.${month}.${year}`
    case 'YYYY-MM-DD':
      return `${year}-${month}-${day}`
    default:
      return `${month}/${day}/${year}` // Fallback to US format
  }
}

/**
 * Format datetime (ISO string with time) according to user preferences
 * Converts UTC to user's browser timezone and formats as "Date Time" (e.g., "01/14/2026 14:30")
 */
export function formatDateTime(dateTimeString, dateFormat = null, timeFormat = null) {
  const prefs = getFormatPreferences()
  const format = dateFormat || prefs.dateFormat
  const tFormat = timeFormat || prefs.timeFormat

  // Parse datetime
  let d = dateTimeString
  if (typeof dateTimeString === 'string') {
    d = new Date(dateTimeString)
  }

  // Handle invalid dates
  if (isNaN(d.getTime())) {
    return ''
  }

  // Extract date parts
  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')

  // Format date part according to user preference
  let dateStr
  switch(format) {
    case 'MM/DD/YYYY':
      dateStr = `${month}/${day}/${year}`
      break
    case 'DD/MM/YYYY':
      dateStr = `${day}/${month}/${year}`
      break
    case 'DD.MM.YYYY':
      dateStr = `${day}.${month}.${year}`
      break
    case 'YYYY-MM-DD':
      dateStr = `${year}-${month}-${day}`
      break
    default:
      dateStr = `${month}/${day}/${year}` // Fallback to US format
  }

  // Format time part according to user preference
  let hours = d.getHours()
  const minutes = String(d.getMinutes()).padStart(2, '0')

  let timeStr
  if (tFormat === '12-hour') {
    const ampm = hours >= 12 ? 'PM' : 'AM'
    hours = hours % 12 || 12 // Convert to 12-hour format
    const hoursStr = String(hours).padStart(2, '0')
    timeStr = `${hoursStr}:${minutes} ${ampm}`
  } else {
    const hoursStr = String(hours).padStart(2, '0')
    timeStr = `${hoursStr}:${minutes}`
  }

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
 * Get currency symbol for a currency code
 */
export function getCurrencySymbol(currencyCode) {
  const currency = CURRENCY_OPTIONS.find(c => c.code === currencyCode)
  return currency ? currency.symbol : currencyCode
}

/**
 * Format number according to user preference
 */
export function formatNumber(num, numberFormat = null) {
  const format = numberFormat || getFormatPreferences().numberFormat
  const formatConfig = NUMBER_FORMATS[format]
  if (!formatConfig) return num.toString()

  // Split into integer and decimal parts
  const parts = num.toFixed(2).split('.')
  let integerPart = parts[0]
  const decimalPart = parts[1]

  // Handle negative numbers
  const isNegative = integerPart.startsWith('-')
  if (isNegative) {
    integerPart = integerPart.substring(1)
  }

  // Add thousands separator by manually inserting from right to left
  let formatted = ''
  for (let i = 0; i < integerPart.length; i++) {
    const posFromRight = integerPart.length - i
    if (posFromRight !== integerPart.length && posFromRight % 3 === 0) {
      formatted += formatConfig.separator
    }
    formatted += integerPart[i]
  }

  // Combine with decimal part
  let result = formatted + formatConfig.decimal + decimalPart

  // Re-add negative sign if needed
  if (isNegative) {
    result = '-' + result
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
 * @returns {string} Date in ISO format (YYYY-MM-DD) or empty string if invalid
 */
export function inputDateToISO(inputDate, dateFormat = null) {
  if (!inputDate || typeof inputDate !== 'string') return ''

  const trimmedInput = inputDate.trim()
  if (trimmedInput.length === 0) return ''

  const format = dateFormat || getFormatPreferences().dateFormat

  let year, month, day

  // Try to parse based on user's format preference
  switch(format) {
    case 'MM/DD/YYYY': {
      const parts = trimmedInput.split('/')
      if (parts.length === 3 && parts[0] && parts[1] && parts[2]) {
        [month, day, year] = parts
      } else {
        return '' // Return empty string if can't parse
      }
      break
    }
    case 'DD/MM/YYYY': {
      const parts = trimmedInput.split('/')
      if (parts.length === 3 && parts[0] && parts[1] && parts[2]) {
        [day, month, year] = parts
      } else {
        return ''
      }
      break
    }
    case 'DD.MM.YYYY': {
      const parts = trimmedInput.split('.')
      if (parts.length === 3 && parts[0] && parts[1] && parts[2]) {
        [day, month, year] = parts
      } else {
        return ''
      }
      break
    }
    case 'YYYY-MM-DD': {
      // Already in ISO format
      if (/^\d{4}-\d{2}-\d{2}$/.test(trimmedInput)) {
        return trimmedInput
      }
      return ''
    }
    default:
      return ''
  }

  // Validate and format as ISO (YYYY-MM-DD)
  if (year && month && day) {
    // Validate numeric values
    const monthNum = parseInt(month, 10)
    const dayNum = parseInt(day, 10)
    const yearNum = parseInt(year, 10)

    // Basic validation
    if (monthNum < 1 || monthNum > 12 || dayNum < 1 || dayNum > 31 || yearNum < 1900) {
      return ''
    }

    // Pad month and day with zeros if needed
    const paddedMonth = String(month).padStart(2, '0')
    const paddedDay = String(day).padStart(2, '0')
    const paddedYear = String(yearNum).padStart(4, '0')

    const isoDate = `${paddedYear}-${paddedMonth}-${paddedDay}`

    // Validate the resulting ISO date
    if (/^\d{4}-\d{2}-\d{2}$/.test(isoDate)) {
      return isoDate
    }
  }

  return ''
}

