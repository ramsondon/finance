import React, { useState, useEffect } from 'react'
import { createRoot } from 'react-dom/client'
import Dashboard from './components/Dashboard'
import TransactionsTable from './components/TransactionsTable'
import ImportCsvModal from './components/ImportCsvModal'
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
import { BarChart3, CreditCard, RotateCw, Folder, Settings, Zap, LogOut, Bell } from 'lucide-react'

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
  const [showImportModal, setShowImportModal] = useState(false)
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
    <div className="min-h-screen bg-gray-50">
      {/* Sidebar */}
      <aside className={`fixed left-0 top-0 h-full bg-white border-r border-gray-200 text-gray-900 transition-all duration-300 z-50 shadow-sm ${sidebarCollapsed ? 'w-20' : 'w-64'}`}>
        {/* Logo */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          {!sidebarCollapsed && (
            <div className="flex items-center space-x-3">
              <img
                src="/static/img/finance_forecast_logo.png"
                alt="Finance Logo"
                className="w-10 h-10 rounded-lg"
              />
              <span className="text-xl font-bold text-gray-900">Finance</span>
            </div>
          )}
          {sidebarCollapsed && (
            <img
              src="/static/img/finance_forecast_logo.png"
              alt="Finance Logo"
              className="w-10 h-10 rounded-lg mx-auto"
            />
          )}
          <button
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors text-gray-700"
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
                  : 'text-gray-700 hover:bg-gray-100'
              }`}
            >
              <item.icon
                size={24}
                className={activeTab === item.id ? 'text-white' : 'text-gray-700'}
              />
              {!sidebarCollapsed && (
                <span className="font-medium">{item.label}</span>
              )}
            </button>
          ))}
        </nav>

        {/* Bottom Actions */}
        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-gray-200">
          <button
            onClick={handleLogout}
            className="w-full flex items-center space-x-3 px-4 py-3 hover:bg-gray-100 rounded-lg transition-colors text-gray-700"
          >
            <LogOut size={24} className="text-gray-700" />
            {!sidebarCollapsed && <span>{t('common.logout')}</span>}
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className={`transition-all duration-300 ${sidebarCollapsed ? 'ml-20' : 'ml-64'}`}>
        {/* Top Header */}
        <header className="bg-white border-b border-gray-200 sticky top-0 z-40 shadow-sm">
          <div className="px-6 py-4">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-2xl font-bold text-gray-900">
                  {menuItems.find(item => item.id === activeTab)?.label}
                </h1>
                <p className="text-sm text-gray-500 mt-1">
                  {activeTab === 'dashboard' && t('dashboard.description')}
                  {activeTab === 'transactions' && t('transactions.description')}
                  {activeTab === 'categories' && t('categories.description')}
                  {activeTab === 'rules' && t('rules.description')}
                  {activeTab === 'insights' && t('insights.description')}
                </p>
              </div>
              <div className="flex items-center space-x-3">
                <button
                  onClick={() => setShowImportModal(true)}
                  className="px-5 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-all font-medium"
                >
                  {t('common.import')}
                </button>
                <button className="p-2.5 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors text-gray-700">
                  <Bell size={20} className="text-gray-700" />
                </button>
                <div className="relative">
                  <button
                    onClick={() => setShowSettingsMenu(!showSettingsMenu)}
                    className="p-2.5 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors text-gray-700"
                  >
                    <Settings size={20} className="text-gray-700" />
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
        <main className="p-6">
          <div className="max-w-7xl mx-auto">
            {activeTab === 'dashboard' && <Dashboard />}
            {activeTab === 'transactions' && <TransactionsTable />}
            {activeTab === 'recurring' && <RecurringTransactionsView />}
            {activeTab === 'categories' && <CategoriesManager />}
            {activeTab === 'rules' && <RulesManager />}
            {activeTab === 'insights' && <InsightsPanel />}
          </div>
        </main>
      </div>

      {/* Import Modal */}
      {showImportModal && (
        <ImportCsvModal onClose={() => setShowImportModal(false)} />
      )}
    </div>
  )
}

const SettingsMenu = ({ sensitiveMode, setSensitiveMode, darkMode, setDarkMode, compactView, setCompactView, formatPrefs, setFormatPrefs, onClose, t }) => {
  return (
    <div className="absolute right-0 mt-2 w-96 bg-white rounded-lg shadow-xl border border-gray-200 z-50 max-h-[90vh] overflow-y-auto">
      <div className="p-4 border-b border-gray-200 sticky top-0 bg-white">
        <h3 className="text-lg font-bold text-gray-900">{t('settings.title')}</h3>
      </div>

      <div className="p-4 space-y-4">
        {/* Sensitive Mode */}
        <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
          <div>
            <div className="font-medium text-gray-900">{t('settings.sensitiveMode')}</div>
            <div className="text-xs text-gray-500">{t('settings.sensitiveModeDesc')}</div>
          </div>
          <label className="flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={sensitiveMode}
              onChange={(e) => setSensitiveMode(e.target.checked)}
              className="sr-only"
            />
            <div className={`w-10 h-6 rounded-full transition-colors ${sensitiveMode ? 'bg-blue-600' : 'bg-gray-300'}`}>
              <div className={`w-5 h-5 rounded-full bg-white shadow-md transition-transform ${sensitiveMode ? 'translate-x-5' : 'translate-x-0'}`}></div>
            </div>
          </label>
        </div>

        <div className="border-t border-gray-200 pt-4">
          <h4 className="font-semibold text-gray-900 mb-3 text-sm">{t('settings.formatPreferences')}</h4>

          {/* Date Format */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">{t('settings.dateFormat')}</label>
            <select
              value={formatPrefs.dateFormat}
              onChange={(e) => setFormatPrefs({ ...formatPrefs, dateFormat: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {Object.keys(DATE_FORMATS).map(fmt => (
                <option key={fmt} value={fmt}>{fmt}</option>
              ))}
            </select>
          </div>

          {/* Time Format */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">{t('settings.timeFormat')}</label>
            <select
              value={formatPrefs.timeFormat}
              onChange={(e) => setFormatPrefs({ ...formatPrefs, timeFormat: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {Object.keys(TIME_FORMATS).map(fmt => (
                <option key={fmt} value={fmt}>{fmt}</option>
              ))}
            </select>
          </div>

          {/* Currency */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">{t('settings.currency')}</label>
            <select
              value={formatPrefs.currencyCode}
              onChange={(e) => setFormatPrefs({ ...formatPrefs, currencyCode: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
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
            <label className="block text-sm font-medium text-gray-700 mb-2">{t('settings.numberFormat')}</label>
            <select
              value={formatPrefs.numberFormat}
              onChange={(e) => setFormatPrefs({ ...formatPrefs, numberFormat: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {Object.keys(NUMBER_FORMATS).map(fmt => (
                <option key={fmt} value={fmt}>{fmt} (example)</option>
              ))}
            </select>
          </div>

          {/* Language */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">{t('settings.language')}</label>
            <select
              value={formatPrefs.language}
              onChange={(e) => {
                const newPrefs = { ...formatPrefs, language: e.target.value }
                setFormatPrefs(newPrefs)
                setLanguagePreference(e.target.value)
              }}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {getSupportedLanguages().map(lang => (
                <option key={lang.code} value={lang.code}>{lang.name}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="border-t border-gray-200 pt-4">
          <h4 className="font-semibold text-gray-900 mb-3 text-sm">{t('settings.display')}</h4>

          {/* Dark Mode */}
          <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors opacity-50">
            <div>
              <div className="font-medium text-gray-900">{t('settings.darkMode')}</div>
              <div className="text-xs text-gray-500">{t('settings.darkModeDesc')}</div>
            </div>
            <label className="flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={darkMode}
                onChange={(e) => setDarkMode(e.target.checked)}
                disabled
                className="sr-only"
              />
              <div className={`w-10 h-6 rounded-full transition-colors ${darkMode ? 'bg-blue-600' : 'bg-gray-300'}`}>
                <div className={`w-5 h-5 rounded-full bg-white shadow-md transition-transform ${darkMode ? 'translate-x-5' : 'translate-x-0'}`}></div>
              </div>
            </label>
          </div>

          <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors opacity-50 mt-2">
            <div>
              <div className="font-medium text-gray-900">{t('settings.compactView')}</div>
              <div className="text-xs text-gray-500">{t('settings.compactViewDesc')}</div>
            </div>
            <label className="flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={compactView}
                onChange={(e) => setCompactView(e.target.checked)}
                disabled
                className="sr-only"
              />
              <div className={`w-10 h-6 rounded-full transition-colors ${compactView ? 'bg-blue-600' : 'bg-gray-300'}`}>
                <div className={`w-5 h-5 rounded-full bg-white shadow-md transition-transform ${compactView ? 'translate-x-5' : 'translate-x-0'}`}></div>
              </div>
            </label>
          </div>
        </div>

        <div className="border-t border-gray-200 pt-4">
          <div className="text-xs text-gray-500 space-y-2 bg-blue-50 p-3 rounded-lg">
            <div className="font-semibold text-gray-700">{t('settings.keyboardShortcuts')}</div>
            <div>{t('settings.toggleSensitive')}</div>
            <div>{t('settings.toggleDark')}</div>
            <div>{t('settings.toggleCompact')}</div>
          </div>
        </div>
      </div>

      <div className="p-4 border-t border-gray-200 flex justify-end sticky bottom-0 bg-white">
        <button
          onClick={onClose}
          className="px-4 py-2 bg-gray-100 text-gray-900 rounded-lg hover:bg-gray-200 font-medium text-sm"
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

