import { useState, useEffect } from 'react'
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
 * Supports ICU MessageFormat for plurals and advanced features
 */
export function useTranslate() {
  const language = useLanguage()

  return (key, vars = null) => {
    let message = getMessage(key, language)

    if (vars) {
      // Handle ICU plural forms: {varName, plural, one {...} other {...}}
      message = message.replace(
        /\{(\w+),\s*plural,\s*one\s*{([^}]+)}\s*other\s*{([^}]+)}\s*}/g,
        (match, varName, singular, plural) => {
          const value = vars[varName]
          if (value === undefined) return match

          // Handle the # placeholder which represents the count in plural form
          const form = value === 1 ? singular : plural
          return form.replace(/#/g, value)
        }
      )

      // Then handle regular variable replacements
      Object.entries(vars).forEach(([varKey, value]) => {
        message = message.replace(`{${varKey}}`, value)
      })
    }

    return message
  }
}

