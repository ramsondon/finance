/**
 * Internationalization (i18n) utility
 * Supports multiple languages with fallback to English
 * Syncs language preference between localStorage and server
 */

import enMessages from '../locales/en.json'
import deMessages from '../locales/de.json'
import { updateLanguagePreference } from './preferences'

const messages = {
  en: enMessages,
  de: deMessages,
}

const SUPPORTED_LANGUAGES = [
  { code: 'en', name: 'English' },
  { code: 'de', name: 'Deutsch' },
]

/**
 * Get the current language from localStorage or browser default
 */
export function getLanguage() {
  return localStorage.getItem('language') || 'en'
}

/**
 * Set the language preference (syncs to server)
 * Updates localStorage immediately for instant UI change,
 * and syncs to server asynchronously
 */
export function setLanguage(language) {
  if (SUPPORTED_LANGUAGES.find(l => l.code === language)) {
    // Update localStorage immediately for instant UI change
    localStorage.setItem('language', language)

    // Dispatch event for instant language change across all components
    window.dispatchEvent(new CustomEvent('languageChanged', { detail: { language } }))

    // Sync to server asynchronously (don't wait for it)
    updateLanguagePreference(language).catch(err => {
      console.error('Failed to sync language to server:', err)
      // Continue anyway - localStorage is the fallback
    })
  }
}

/**
 * Get message for a key and language
 * Supports nested keys with dot notation: 'dashboard.title'
 */
export function getMessage(key, language = null) {
  const lang = language || getLanguage()
  const translations = messages[lang] || messages.en

  // Navigate through nested object using dot notation
  const keys = key.split('.')
  let value = translations

  for (const k of keys) {
    value = value?.[k]
    if (value === undefined) {
      // Fallback to English if translation not found
      let fallbackValue = messages.en
      for (const fk of keys) {
        fallbackValue = fallbackValue?.[fk]
        if (fallbackValue === undefined) break
      }
      return fallbackValue || key
    }
  }

  return value || key
}

/**
 * Translate a string, optionally with variable interpolation
 * Example: t('messages.pageOf', { current: 1, total: 5 })
 */
export function t(key, vars = null) {
  let message = getMessage(key)

  if (vars) {
    Object.entries(vars).forEach(([varKey, value]) => {
      message = message.replace(`{${varKey}}`, value)
    })
  }

  return message
}

/**
 * Get all supported languages
 */
export function getSupportedLanguages() {
  return SUPPORTED_LANGUAGES
}

/**
 * Get language name from code
 */
export function getLanguageName(code) {
  const lang = SUPPORTED_LANGUAGES.find(l => l.code === code)
  return lang?.name || code
}

