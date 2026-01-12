/**
 * Custom React hook for language changes
 * Listens to language change events and updates component state
 */
import React, { useState, useEffect } from 'react'
import { getLanguage, getMessage } from '../utils/i18n'

/**
 * Hook that listens for language changes and returns current language
 * Components using this hook will re-render when language changes
 */
export function useLanguage() {
  const [language, setLanguage] = useState(getLanguage())

  useEffect(() => {
    const handleLanguageChange = (e) => {
      setLanguage(e.detail.language)
    }
    window.addEventListener('languageChanged', handleLanguageChange)
    return () => window.removeEventListener('languageChanged', handleLanguageChange)
  }, [])

  return language
}

/**
 * Hook that provides translation function
 * Returns a translate function that automatically uses current language
 */
export function useTranslate() {
  const language = useLanguage()

  return (key, vars = null) => {
    let message = getMessage(key, language)

    if (vars) {
      Object.entries(vars).forEach(([varKey, value]) => {
        message = message.replace(`{${varKey}}`, value)
      })
    }

    return message
  }
}

