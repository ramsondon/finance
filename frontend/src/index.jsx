import React, { useState, useEffect } from 'react'
import { createRoot } from 'react-dom/client'
import Dashboard from './components/Dashboard'
import TransactionsTable from './components/TransactionsTable'
import ImportCsvModal from './components/ImportCsvModal'
import RulesManager from './components/RulesManager'
import CategoriesManager from './components/CategoriesManager'
import InsightsPanel from './components/InsightsPanel'
import LoginPage from './components/LoginPage'
import LandingPage from './components/LandingPage'
import axios from 'axios'
import { getCsrfToken } from './utils/csrf'

// Configure axios to include CSRF token in all requests
axios.interceptors.request.use((config) => {
  const csrfToken = getCsrfToken()
  if (csrfToken) {
    config.headers['X-CSRFToken'] = csrfToken
  }
  return config
}, (error) => {
  return Promise.reject(error)
})

function App() {
  const [activeTab, setActiveTab] = useState('dashboard')
  const [showImportModal, setShowImportModal] = useState(false)
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [isAuthenticated, setIsAuthenticated] = useState(null)
  const [loading, setLoading] = useState(true)

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

  useEffect(() => {
    const handler = () => {
      setActiveTab('transactions')
    }
    window.addEventListener('nav-to-transactions', handler)
    return () => window.removeEventListener('nav-to-transactions', handler)
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

  // Dashboard menu items
  const menuItems = [
    { id: 'dashboard', label: 'Dashboard', icon: '📊' },
    { id: 'transactions', label: 'Transactions', icon: '💳' },
    { id: 'categories', label: 'Categories', icon: '📁' },
    { id: 'rules', label: 'Rules', icon: '⚙️' },
    { id: 'insights', label: 'AI Insights', icon: '🤖' },
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
              <span className="text-2xl">{item.icon}</span>
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
            <span className="text-2xl">🚪</span>
            {!sidebarCollapsed && <span>Logout</span>}
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
                  {activeTab === 'dashboard' && 'Overview of your financial data'}
                  {activeTab === 'transactions' && 'Manage your transactions'}
                  {activeTab === 'categories' && 'Organize your transactions'}
                  {activeTab === 'rules' && 'Configure categorization rules'}
                  {activeTab === 'insights' && 'AI-powered financial insights'}
                </p>
              </div>
              <div className="flex items-center space-x-3">
                <button
                  onClick={() => setShowImportModal(true)}
                  className="px-5 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-all font-medium"
                >
                  + Import
                </button>
                <button className="p-2.5 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors text-gray-700">
                  <span className="text-xl">🔔</span>
                </button>
                <button className="p-2.5 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors text-gray-700">
                  <span className="text-xl">⚙️</span>
                </button>
              </div>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="p-6">
          <div className="max-w-7xl mx-auto">
            {activeTab === 'dashboard' && <Dashboard />}
            {activeTab === 'transactions' && <TransactionsTable />}
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

const root = createRoot(document.getElementById('root'))
root.render(<App />)

