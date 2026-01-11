/**
 * Get CSRF token from cookies
 */
export function getCsrfToken() {
  const name = 'csrftoken'
  let cookieValue = null
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';')
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim()
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1))
        break
      }
    }
  }
  return cookieValue
}

/**
 * Configure axios defaults for CSRF
 */
export function setupAxiosDefaults() {
  // Set CSRF token for all axios requests
  const token = getCsrfToken()
  if (token) {
    axios.defaults.headers.common['X-CSRFToken'] = token
  }

  // Add interceptor to refresh CSRF token before each request
  axios.interceptors.request.use((config) => {
    const currentToken = getCsrfToken()
    if (currentToken) {
      config.headers['X-CSRFToken'] = currentToken
    }
    return config
  }, (error) => {
    return Promise.reject(error)
  })
}

import axios from 'axios'

// Setup axios defaults when module loads
setupAxiosDefaults()

