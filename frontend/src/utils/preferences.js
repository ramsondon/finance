/**
 * User Preferences Synchronization
 * Syncs preferences between localStorage (client-side cache) and server (UserProfile)
 */
import axios from 'axios'
import { getCsrfToken } from './csrf'

const API_BASE = '/api/accounts/auth/preferences/'

/**
 * Get preferences from server
 * @returns {Object} User preferences from server
 */
export async function getServerPreferences() {
  try {
    const response = await axios.get(API_BASE)
    return response.data
  } catch (error) {
    console.error('Failed to fetch preferences from server:', error)
    return null
  }
}

/**
 * Sync preferences to server
 * @param {Object} preferences - Preferences object to sync
 *   Supported keys:
 *   - language: Language code ('en', 'de', etc.)
 *   - currency: Currency code ('USD', 'EUR', etc.)
 *   - currencyCode: Alias for currency
 *   - dateFormat: Date format ('MM/DD/YYYY', 'DD/MM/YYYY', etc.)
 *   - timeFormat: Time format ('12-hour', '24-hour')
 *   - numberFormat: Number format ('1,000.00', '1.000,00', etc.)
 *   - Any custom preference key
 * @returns {Object} Updated preferences from server
 */
export async function syncPreferencesToServer(preferences) {
  try {
    // Normalize currencyCode to currency for server
    const serverPrefs = { ...preferences }
    if (serverPrefs.currencyCode) {
      serverPrefs.currency = serverPrefs.currencyCode
      delete serverPrefs.currencyCode
    }

    const response = await axios.post(API_BASE, serverPrefs, {
      headers: {
        'X-CSRFToken': getCsrfToken()
      }
    })
    return response.data
  } catch (error) {
    console.error('Failed to sync preferences to server:', error)
    throw error
  }
}

/**
 * Update language preference (syncs to both localStorage and server)
 * @param {string} language - Language code ('en', 'de', etc.)
 * @returns {Promise} Resolves when sync is complete
 */
export async function updateLanguagePreference(language) {
  // Update localStorage immediately for instant UI change
  localStorage.setItem('language', language)

  // Sync to server asynchronously
  try {
    const result = await syncPreferencesToServer({ language })
    console.log('Language preference synced to server:', result.language)
    return result
  } catch (error) {
    console.warn('Failed to sync language to server, but localStorage updated:', error)
    // Continue even if server sync fails - localStorage is the fallback
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
 * Load preferences from server and update localStorage if needed
 * Runs on app initialization to sync server state back to client
 */
export async function loadAndSyncPreferences() {
  try {
    const serverData = await getServerPreferences()
    if (!serverData || !serverData.preferences) {
      console.log('No server preferences found')
      return
    }

    const serverPrefs = serverData.preferences
    const localPrefs = {
      language: localStorage.getItem('language') || 'en',
      dateFormat: localStorage.getItem('dateFormat'),
      timeFormat: localStorage.getItem('timeFormat'),
      currencyCode: localStorage.getItem('currencyCode'),
      numberFormat: localStorage.getItem('numberFormat'),
    }

    // Update localStorage with server values (server is source of truth)
    if (serverPrefs.language && serverPrefs.language !== localPrefs.language) {
      console.log('Syncing language from server:', serverPrefs.language)
      localStorage.setItem('language', serverPrefs.language)
    }
    if (serverPrefs.dateFormat) {
      localStorage.setItem('dateFormat', serverPrefs.dateFormat)
    }
    if (serverPrefs.timeFormat) {
      localStorage.setItem('timeFormat', serverPrefs.timeFormat)
    }
    if (serverPrefs.currencyCode) {
      localStorage.setItem('currencyCode', serverPrefs.currencyCode)
    }
    if (serverPrefs.numberFormat) {
      localStorage.setItem('numberFormat', serverPrefs.numberFormat)
    }

    return serverData
  } catch (error) {
    console.warn('Failed to load preferences from server:', error)
    // Continue with localStorage only
  }
}
