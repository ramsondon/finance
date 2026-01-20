import React, { useState, useEffect } from 'react'
import { createRoot } from 'react-dom/client'
import Dashboard from './components/Dashboard'
import TransactionsTable from './components/TransactionsTable'
import RulesManager from './components/RulesManager'
import CategoriesManager from './components/CategoriesManager'
import RecurringTransactionsView from './components/RecurringTransactionsView'
import InsightsPanel from './components/InsightsPanel'
import LoginPage from './components/LoginPage'
import LandingPage from './components/LandingPage'
import axios from 'axios'
import { getCsrfToken } from './utils/csrf'
import { getFormatPreferences, saveFormatPreferences, updateFormatPreferences, DATE_FORMATS, CURRENCY_OPTIONS, NUMBER_FORMATS, TIME_FORMATS } from './utils/format'
import { getSupportedLanguages, setLanguage as setLanguagePreference } from './utils/i18n'
import { useTranslate } from './hooks/useLanguage'
import { BarChart3, CreditCard, RotateCw, Folder, Settings, Zap, LogOut, Bell, Lock, Moon, Package } from 'lucide-react'

// Configure axios to include CSRF token in all requests
axios.interceptors.request.use((config) => {
  // Ensure config and headers exist
  if (!config) {
    return config
  }
  if (!config.headers) {
    config.headers = {}
  }

  const csrfToken = getCsrfToken()
  if (csrfToken) {
    config.headers['X-CSRFToken'] = csrfToken
  }
  return config
}, (error) => {
  return Promise.reject(error)
})

// Main app content component that uses translations
function AppContent() {
  const t = useTranslate() // This hook listens for language changes
  const [activeTab, setActiveTab] = useState('dashboard')
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [isAuthenticated, setIsAuthenticated] = useState(null)
  const [loading, setLoading] = useState(true)
  const [showSettingsMenu, setShowSettingsMenu] = useState(false)
  const [sensitiveMode, setSensitiveMode] = useState(localStorage.getItem('sensitiveMode') === 'true')
  const [darkMode, setDarkMode] = useState(localStorage.getItem('darkMode') === 'true')
  const [compactView, setCompactView] = useState(localStorage.getItem('compactView') === 'true')
  const [formatPrefs, setFormatPrefs] = useState(getFormatPreferences())

  // Get current path
  const currentPath = window.location.pathname

  useEffect(() => {
    // Check if user is authenticated using the public endpoint
    axios.get('/api/accounts/auth/check')
      .then(res => {
        setIsAuthenticated(res.data.is_authenticated)
        setLoading(false)

        // If authenticated, fetch preferences from server (including dark mode)
        if (res.data.is_authenticated) {
          axios.get('/api/accounts/auth/preferences/')
            .then(prefRes => {
              const serverPrefs = prefRes.data.preferences || {}
              if (serverPrefs.darkMode !== undefined) {
                setDarkMode(serverPrefs.darkMode)
                localStorage.setItem('darkMode', serverPrefs.darkMode)
              }
            })
            .catch(err => {
              console.error('Failed to fetch preferences:', err)
            })
        }
      })
      .catch(err => {
        setIsAuthenticated(false)
        setLoading(false)
      })
  }, [])

  // Save format preferences whenever they change
  useEffect(() => {
    localStorage.setItem('dateFormat', formatPrefs.dateFormat)
    localStorage.setItem('currencyCode', formatPrefs.currencyCode)
    localStorage.setItem('numberFormat', formatPrefs.numberFormat)
    localStorage.setItem('timeFormat', formatPrefs.timeFormat)
    localStorage.setItem('language', formatPrefs.language)
  }, [formatPrefs])

  useEffect(() => {
    const handler = () => {
      setActiveTab('transactions')
    }
    window.addEventListener('nav-to-transactions', handler)
    return () => window.removeEventListener('nav-to-transactions', handler)
  }, [])

  // Sync dark mode to server whenever it changes
  useEffect(() => {
    const syncDarkMode = async () => {
      try {
        await axios.post('/api/accounts/auth/preferences/', {
          darkMode: darkMode
        })
      } catch (error) {
        console.error('Failed to sync dark mode:', error)
      }
    }
    syncDarkMode()
  }, [darkMode])

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyPress = (e) => {
      // Alt+Shift+S: Toggle sensitive mode
      if (e.altKey && e.shiftKey && e.code === 'KeyS') {
        e.preventDefault()
        setSensitiveMode(prev => {
          const newValue = !prev
          localStorage.setItem('sensitiveMode', newValue)
          // Dispatch custom event for instant updates across all components
          window.dispatchEvent(new CustomEvent('sensitiveModeChanged', { detail: { sensitiveMode: newValue } }))
          return newValue
        })
      }
      // Alt+Shift+D: Toggle dark mode
      if (e.altKey && e.shiftKey && e.code === 'KeyD') {
        e.preventDefault()
        setDarkMode(prev => {
          const newValue = !prev
          localStorage.setItem('darkMode', newValue)
          // Dispatch custom event for instant updates across all components
          window.dispatchEvent(new CustomEvent('darkModeChanged', { detail: { darkMode: newValue } }))
          return newValue
        })
      }
      // Alt+Shift+C: Toggle compact view
      if (e.altKey && e.shiftKey && e.code === 'KeyC') {
        e.preventDefault()
        setCompactView(prev => {
          const newValue = !prev
          localStorage.setItem('compactView', newValue)
          return newValue
        })
      }
    }
    window.addEventListener('keydown', handleKeyPress)
    return () => window.removeEventListener('keydown', handleKeyPress)
  }, [])

  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 to-gray-800 flex items-center justify-center">
        <div className="relative">
          <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-blue-600"></div>
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="w-8 h-8 bg-blue-600 rounded-full opacity-20 animate-pulse"></div>
          </div>
        </div>
      </div>
    )
  }

  // Show login page for /login path
  if (currentPath === '/login') {
    return <LoginPage />
  }

  // Show landing page if not authenticated
  if (!isAuthenticated) {
    return <LandingPage />
  }

  // Dashboard menu items - use translations
  const menuItems = [
    { id: 'dashboard', label: t('nav.dashboard'), icon: BarChart3 },
    { id: 'transactions', label: t('nav.transactions'), icon: CreditCard },
    { id: 'recurring', label: t('nav.recurring'), icon: RotateCw },
    { id: 'categories', label: t('nav.categories'), icon: Folder },
    { id: 'rules', label: t('nav.rules'), icon: Settings },
    { id: 'insights', label: t('nav.insights'), icon: Zap },
  ]

  const handleLogout = async () => {
    try {
      // Get CSRF token from cookies
      const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
                        Array.from(document.cookie.split(';'))
                          .find(c => c.trim().startsWith('csrftoken='))
                          ?.split('=')[1] || ''

      // Make POST request to logout endpoint
      await axios.post('/accounts/logout/', {}, {
        headers: {
          'X-CSRFToken': csrftoken,
        }
      })

      // Redirect to home/login page
      window.location.href = '/'
    } catch (error) {
      console.error('Logout failed:', error)
      // Fallback: redirect anyway
      window.location.href = '/accounts/logout/'
    }
  }

  return (
    <div className={`min-h-screen ${darkMode ? 'dark bg-gray-900' : 'bg-gray-50'}`}>
      {/* Sidebar */}
      <aside className={`fixed left-0 top-0 h-full ${darkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'} border-r text-gray-900 transition-all duration-300 z-50 shadow-sm ${sidebarCollapsed ? 'w-20' : 'w-64'}`}>
        {/* Logo */}
        <div className={`flex items-center justify-between p-6 ${darkMode ? 'border-gray-700' : 'border-gray-200'} border-b`}>
          {!sidebarCollapsed && (
            <div className="flex items-center space-x-3">
              <img
                src="/static/img/finance_forecast_logo.svg"
                alt="Finance Logo"
                className="w-10 h-10 rounded-lg"
              />
              <span className={`text-xl font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>Finance</span>
            </div>
          )}
          {sidebarCollapsed && (
            <img
              src="/static/img/finance_forecast_logo.svg"
              alt="Finance Logo"
              className="w-10 h-10 rounded-lg mx-auto"
            />
          )}
          <button
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            className={`p-2 rounded-lg transition-colors ${darkMode ? 'hover:bg-gray-700 text-gray-300' : 'hover:bg-gray-100 text-gray-700'}`}
          >
            {sidebarCollapsed ? '→' : '←'}
          </button>
        </div>

        {/* Menu Items */}
        <nav className="p-4 space-y-2">
          {menuItems.map((item) => (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition-all ${
                activeTab === item.id
                  ? 'bg-blue-600 text-white shadow-sm'
                  : darkMode
                  ? 'text-gray-300 hover:bg-gray-700'
                  : 'text-gray-700 hover:bg-gray-100'
              }`}
            >
              <item.icon
                size={24}
                className={activeTab === item.id ? 'text-white' : darkMode ? 'text-gray-400' : 'text-gray-700'}
              />
              {!sidebarCollapsed && (
                <span className="font-medium">{item.label}</span>
              )}
            </button>
          ))}
        </nav>

        {/* Bottom Actions */}
        <div className={`absolute bottom-0 left-0 right-0 p-4 ${darkMode ? 'border-gray-700' : 'border-gray-200'} border-t`}>
          <button
            onClick={handleLogout}
            className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${darkMode ? 'hover:bg-gray-700 text-gray-300' : 'hover:bg-gray-100 text-gray-700'}`}
          >
            <LogOut size={24} className={darkMode ? 'text-gray-400' : 'text-gray-700'} />
            {!sidebarCollapsed && <span>{t('common.logout')}</span>}
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className={`transition-all duration-300 ${sidebarCollapsed ? 'ml-20' : 'ml-64'}`}>
        {/* Top Header */}
        <header className={`${darkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'} border-b sticky top-0 z-40 shadow-sm`}>
          <div className="px-6 py-4">
            <div className="flex items-center justify-between">
              <div>
                <h1 className={`text-2xl font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                  {menuItems.find(item => item.id === activeTab)?.label}
                </h1>
                <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-500'} mt-1`}>
                  {activeTab === 'dashboard' && t('dashboard.description')}
                  {activeTab === 'transactions' && t('transactions.description')}
                  {activeTab === 'recurring' && t('recurring.description')}
                  {activeTab === 'categories' && t('categories.description')}
                  {activeTab === 'rules' && t('rules.description')}
                  {activeTab === 'insights' && t('insights.description')}
                </p>
              </div>
              <div className="flex items-center space-x-3">
                <button className={`p-2.5 rounded-lg transition-colors ${darkMode ? 'bg-gray-700 hover:bg-gray-600 text-gray-300' : 'bg-gray-100 hover:bg-gray-200 text-gray-700'}`}>
                  <Bell size={20} />
                </button>
                <div className="relative">
                  <button
                    onClick={() => setShowSettingsMenu(!showSettingsMenu)}
                    className={`p-2.5 rounded-lg transition-colors ${darkMode ? 'bg-gray-700 hover:bg-gray-600 text-gray-300' : 'bg-gray-100 hover:bg-gray-200 text-gray-700'}`}
                  >
                    <Settings size={20} />
                  </button>
                  {showSettingsMenu && (
                    <SettingsMenu
                      sensitiveMode={sensitiveMode}
                      setSensitiveMode={(value) => {
                        setSensitiveMode(value)
                        localStorage.setItem('sensitiveMode', value)
                        // Dispatch custom event for instant updates across all components
                        window.dispatchEvent(new CustomEvent('sensitiveModeChanged', { detail: { sensitiveMode: value } }))
                      }}
                      darkMode={darkMode}
                      setDarkMode={(value) => {
                        setDarkMode(value)
                        localStorage.setItem('darkMode', value)
                        // Dispatch custom event for instant updates
                        window.dispatchEvent(new CustomEvent('darkModeChanged', { detail: { darkMode: value } }))
                      }}
                      compactView={compactView}
                      setCompactView={(value) => {
                        setCompactView(value)
                        localStorage.setItem('compactView', value)
                      }}
                      formatPrefs={formatPrefs}
                      setFormatPrefs={(prefs) => {
                        setFormatPrefs(prefs)
                        // Sync to localStorage AND server
                        updateFormatPreferences(prefs)
                      }}
                      onClose={() => setShowSettingsMenu(false)}
                      t={t}
                    />
                  )}
                </div>
              </div>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className={darkMode ? 'p-6 bg-gray-900' : 'p-6'}>
          <div className="max-w-7xl mx-auto">
            {activeTab === 'dashboard' && <Dashboard darkMode={darkMode} />}
            {activeTab === 'transactions' && <TransactionsTable darkMode={darkMode} />}
            {activeTab === 'recurring' && <RecurringTransactionsView darkMode={darkMode} />}
            {activeTab === 'categories' && <CategoriesManager darkMode={darkMode} />}
            {activeTab === 'rules' && <RulesManager darkMode={darkMode} />}
            {activeTab === 'insights' && <InsightsPanel darkMode={darkMode} />}
          </div>
        </main>
      </div>
    </div>
  )
}

const SettingsMenu = ({ sensitiveMode, setSensitiveMode, darkMode, setDarkMode, compactView, setCompactView, formatPrefs, setFormatPrefs, onClose, t }) => {
  return (
    <div className={`absolute right-0 mt-2 w-96 rounded-lg shadow-xl border z-50 max-h-[90vh] overflow-y-auto ${darkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
      <div className={`p-4 border-b sticky top-0 ${darkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
        <h3 className={`text-lg font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>{t('settings.title')}</h3>
      </div>

      <div className="p-4 space-y-4">
        {/* Sensitive Mode */}
        <div className={`flex items-center justify-between p-3 rounded-lg hover:opacity-80 transition-colors ${darkMode ? 'bg-gray-700' : 'bg-gray-50 hover:bg-gray-100'}`}>
          <div>
            <div className={`font-medium ${darkMode ? 'text-white' : 'text-gray-900'}`}>{t('settings.sensitiveMode')}</div>
            <div className={`text-xs ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>{t('settings.sensitiveModeDesc')}</div>
          </div>
          <label className="flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={sensitiveMode}
              onChange={(e) => setSensitiveMode(e.target.checked)}
              className="sr-only"
            />
            <div className={`w-10 h-6 rounded-full transition-colors ${sensitiveMode ? 'bg-blue-600' : darkMode ? 'bg-gray-600' : 'bg-gray-300'}`}>
              <div className={`w-5 h-5 rounded-full bg-white shadow-md transition-transform ${sensitiveMode ? 'translate-x-5' : 'translate-x-0'}`}></div>
            </div>
          </label>
        </div>

        <div className={`border-t pt-4 ${darkMode ? 'border-gray-700' : 'border-gray-200'}`}>
          <h4 className={`font-semibold mb-3 text-sm ${darkMode ? 'text-white' : 'text-gray-900'}`}>{t('settings.formatPreferences')}</h4>

          {/* Date Format */}
          <div className="mb-4">
            <label className={`block text-sm font-medium mb-2 ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>{t('settings.dateFormat')}</label>
            <select
              value={formatPrefs.dateFormat}
              onChange={(e) => setFormatPrefs({ ...formatPrefs, dateFormat: e.target.value })}
              className={`w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${darkMode ? 'bg-gray-700 border-gray-600 text-white' : 'border-gray-300 bg-white text-gray-900'}`}
            >
              {Object.keys(DATE_FORMATS).map(fmt => (
                <option key={fmt} value={fmt}>{fmt}</option>
              ))}
            </select>
          </div>

          {/* Time Format */}
          <div className="mb-4">
            <label className={`block text-sm font-medium mb-2 ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>{t('settings.timeFormat')}</label>
            <select
              value={formatPrefs.timeFormat}
              onChange={(e) => setFormatPrefs({ ...formatPrefs, timeFormat: e.target.value })}
              className={`w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${darkMode ? 'bg-gray-700 border-gray-600 text-white' : 'border-gray-300 bg-white text-gray-900'}`}
            >
              {Object.keys(TIME_FORMATS).map(fmt => (
                <option key={fmt} value={fmt}>{fmt}</option>
              ))}
            </select>
          </div>

          {/* Currency */}
          <div className="mb-4">
            <label className={`block text-sm font-medium mb-2 ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>{t('settings.currency')}</label>
            <select
              value={formatPrefs.currencyCode}
              onChange={(e) => setFormatPrefs({ ...formatPrefs, currencyCode: e.target.value })}
              className={`w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${darkMode ? 'bg-gray-700 border-gray-600 text-white' : 'border-gray-300 bg-white text-gray-900'}`}
            >
              {CURRENCY_OPTIONS.map(curr => (
                <option key={curr.code} value={curr.code}>
                  {curr.symbol} {curr.code} - {curr.name}
                </option>
              ))}
            </select>
          </div>

          {/* Number Format */}
          <div className="mb-4">
            <label className={`block text-sm font-medium mb-2 ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>{t('settings.numberFormat')}</label>
            <select
              value={formatPrefs.numberFormat}
              onChange={(e) => setFormatPrefs({ ...formatPrefs, numberFormat: e.target.value })}
              className={`w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${darkMode ? 'bg-gray-700 border-gray-600 text-white' : 'border-gray-300 bg-white text-gray-900'}`}
            >
              {Object.keys(NUMBER_FORMATS).map(fmt => (
                <option key={fmt} value={fmt}>{fmt} (example)</option>
              ))}
            </select>
          </div>

          {/* Language */}
          <div className="mb-4">
            <label className={`block text-sm font-medium mb-2 ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>{t('settings.language')}</label>
            <select
              value={formatPrefs.language}
              onChange={(e) => {
                const newPrefs = { ...formatPrefs, language: e.target.value }
                setFormatPrefs(newPrefs)
                setLanguagePreference(e.target.value)
              }}
              className={`w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${darkMode ? 'bg-gray-700 border-gray-600 text-white' : 'border-gray-300 bg-white text-gray-900'}`}
            >
              {getSupportedLanguages().map(lang => (
                <option key={lang.code} value={lang.code}>{lang.name}</option>
              ))}
            </select>
          </div>
        </div>

        <div className={`border-t pt-4 ${darkMode ? 'border-gray-700' : 'border-gray-200'}`}>
          <h4 className={`font-semibold mb-3 text-sm ${darkMode ? 'text-white' : 'text-gray-900'}`}>{t('settings.display')}</h4>

          {/* Dark Mode */}
          <div className={`flex items-center justify-between p-3 rounded-lg hover:opacity-80 transition-colors ${darkMode ? 'bg-gray-700' : 'bg-gray-50 hover:bg-gray-100'}`}>
            <div>
              <div className={`font-medium ${darkMode ? 'text-white' : 'text-gray-900'}`}>{t('settings.darkMode')}</div>
              <div className={`text-xs ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>{t('settings.darkModeDesc')}</div>
            </div>
            <label className="flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={darkMode}
                onChange={(e) => setDarkMode(e.target.checked)}
                className="sr-only"
              />
              <div className={`w-10 h-6 rounded-full transition-colors ${darkMode ? 'bg-blue-600' : 'bg-gray-300'}`}>
                <div className={`w-5 h-5 rounded-full bg-white shadow-md transition-transform ${darkMode ? 'translate-x-5' : 'translate-x-0'}`}></div>
              </div>
            </label>
          </div>

          <div className={`flex items-center justify-between p-3 rounded-lg hover:opacity-80 transition-colors mt-2 opacity-50 ${darkMode ? 'bg-gray-700' : 'bg-gray-50 hover:bg-gray-100'}`}>
            <div>
              <div className={`font-medium ${darkMode ? 'text-white' : 'text-gray-900'}`}>{t('settings.compactView')}</div>
              <div className={`text-xs ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>{t('settings.compactViewDesc')}</div>
            </div>
            <label className="flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={compactView}
                onChange={(e) => setCompactView(e.target.checked)}
                disabled
                className="sr-only"
              />
              <div className={`w-10 h-6 rounded-full transition-colors ${compactView ? 'bg-blue-600' : darkMode ? 'bg-gray-600' : 'bg-gray-300'}`}>
                <div className={`w-5 h-5 rounded-full bg-white shadow-md transition-transform ${compactView ? 'translate-x-5' : 'translate-x-0'}`}></div>
              </div>
            </label>
          </div>
        </div>

        <div className={`border-t pt-4 ${darkMode ? 'border-gray-700' : 'border-gray-200'}`}>
          <div className={`text-xs space-y-2 p-3 rounded-lg ${darkMode ? 'bg-blue-900 text-blue-100' : 'bg-blue-50 text-gray-700'}`}>
            <div className={`font-semibold ${darkMode ? 'text-blue-100' : 'text-gray-700'}`}>{t('settings.keyboardShortcuts')}</div>
            <div className="flex items-center gap-2">
              <Lock size={14} className={darkMode ? 'text-blue-300' : 'text-blue-600'} />
              {t('settings.toggleSensitive')}
            </div>
            <div className="flex items-center gap-2">
              <Moon size={14} className={darkMode ? 'text-blue-300' : 'text-blue-600'} />
              {t('settings.toggleDark')}
            </div>
            <div className="flex items-center gap-2">
              <Package size={14} className={darkMode ? 'text-blue-300' : 'text-blue-600'} />
              {t('settings.toggleCompact')}
            </div>
          </div>
        </div>
      </div>

      <div className={`p-4 border-t flex justify-end sticky bottom-0 ${darkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
        <button
          onClick={onClose}
          className={`px-4 py-2 rounded-lg hover:opacity-80 font-medium text-sm transition-colors ${darkMode ? 'bg-gray-700 text-white' : 'bg-gray-100 text-gray-900'}`}
        >
          {t('common.close')}
        </button>
      </div>
    </div>
  )
}

const SensitiveValue = ({ value, sensitiveMode, isMonetary = true }) => {
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

// Wrapper App component that provides translation context
function App() {
  return <AppContent />
}

const root = createRoot(document.getElementById('root'))
root.render(<App />)

