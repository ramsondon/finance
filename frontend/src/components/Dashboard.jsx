import React, { useEffect, useState } from 'react'
import axios from 'axios'
import { getCsrfToken } from '../utils/csrf'
import { SensitiveValue, useSensitiveModeListener } from '../utils/sensitive'
import CreateAccountModal from './CreateAccountModal'
import AccountDetailsView from './AccountDetailsView'
import { useTranslate } from '../hooks/useLanguage'
import { formatDateTime, getFormatPreferences, formatCurrency, getCurrencySymbol, formatNumber } from '../utils/format'
import { Pie } from 'react-chartjs-2'
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js'
ChartJS.register(ArcElement, Tooltip, Legend)

export default function Dashboard() {
  const t = useTranslate()
  const [overview, setOverview] = useState(null)
  const [accounts, setAccounts] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [selectedAccountId, setSelectedAccountId] = useState(null)
  const [deleteConfirm, setDeleteConfirm] = useState(null) // { id, name }
  const [deleting, setDeleting] = useState(false)
  const [categoryBreakdown, setCategoryBreakdown] = useState({ labels: [], values: [] })
  const [categoryLoading, setCategoryLoading] = useState(false)
  const [selectedPeriod, setSelectedPeriod] = useState('current_month')
  const [userCurrency, setUserCurrency] = useState(getFormatPreferences().currencyCode)
  const sensitiveMode = useSensitiveModeListener()

  const fetchData = () => {
    setLoading(true)
    Promise.all([
      axios.get('/api/analytics/overview').catch(() => ({ data: { total_balance: 0, income_expense_breakdown: { income: 0, expense: 0 }, monthly_trends: [] } })),
      axios.get('/api/banking/accounts/').catch(() => ({ data: { results: [] } })),
      axios.get(`/api/analytics/category-expense/?period=${selectedPeriod}`).catch(() => ({ data: { labels: [], values: [] } }))
    ]).then(([overviewRes, accountsRes, catRes]) => {
      setOverview(overviewRes.data)
      setAccounts(accountsRes.data.results || accountsRes.data || [])
      setCategoryBreakdown(catRes.data || { labels: [], values: [] })
      setLoading(false)
    }).catch(err => {
      setError(err.message)
      setLoading(false)
    })
  }

  const handlePeriodChange = (newPeriod) => {
    setSelectedPeriod(newPeriod)
    // Fetch new data with the selected period
    setCategoryLoading(true)
    axios.get(`/api/analytics/category-expense/?period=${newPeriod}`)
      .then(res => {
        setCategoryBreakdown(res.data || { labels: [], values: [] })
      })
      .catch(err => {
        console.error('Failed to fetch category data:', err)
      })
      .finally(() => {
        setCategoryLoading(false)
      })
  }

  const handleDelete = async () => {
    if (!deleteConfirm) return

    setDeleting(true)
    try {
      await axios.delete(`/api/banking/accounts/${deleteConfirm.id}/`, {
        headers: {
          'X-CSRFToken': getCsrfToken()
        }
      })
      setDeleteConfirm(null)
      fetchData() // Refresh the list
    } catch (err) {
      alert(`Failed to delete account: ${err.response?.data?.message || err.message}`)
    } finally {
      setDeleting(false)
    }
  }

  // ESC key handler to close delete confirmation dialog
  useEffect(() => {
    const handleEsc = (e) => {
      if (e.key === 'Escape' && deleteConfirm) {
        setDeleteConfirm(null)
      }
    }
    window.addEventListener('keydown', handleEsc)
    return () => window.removeEventListener('keydown', handleEsc)
  }, [deleteConfirm])

  // Listen for currency preference changes
  useEffect(() => {
    const handleStorageChange = () => {
      const newPrefs = getFormatPreferences()
      if (newPrefs.currencyCode !== userCurrency) {
        setUserCurrency(newPrefs.currencyCode)
        // Refetch accounts to get new converted_balance with updated currency
        fetchData()
      }
    }

    window.addEventListener('storage', handleStorageChange)

    // Also check for currency changes on an interval (localStorage changes in same tab don't trigger storage event)
    const interval = setInterval(() => {
      const newPrefs = getFormatPreferences()
      if (newPrefs.currencyCode !== userCurrency) {
        setUserCurrency(newPrefs.currencyCode)
        fetchData()
      }
    }, 500)

    return () => {
      window.removeEventListener('storage', handleStorageChange)
      clearInterval(interval)
    }
  }, [userCurrency])

  useEffect(() => {
    fetchData()
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="relative">
          <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-blue-600"></div>
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="w-8 h-8 bg-blue-600 rounded-full opacity-20 animate-pulse"></div>
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border-l-4 border-red-500 rounded-lg p-6 shadow-sm">
        <div className="flex items-center">
          <span className="text-3xl mr-3">⚠️</span>
          <div>
            <h3 className="text-lg font-semibold text-red-900">{t('dashboard.errorLoadingDashboard')}</h3>
            <p className="text-red-700 mt-1">{error}</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Total Balance Card */}
        <div className="bg-blue-600 rounded-lg p-6 text-white shadow-sm">
          <div className="flex items-center justify-between mb-3">
            <div className="text-blue-100 text-sm font-medium uppercase tracking-wider">{t('dashboard.totalBalance')}</div>
            <span className="text-4xl">💰</span>
          </div>
          <div className="text-4xl font-bold mb-2">
            {getCurrencySymbol(overview?.total_balance_currency || 'USD')} {(overview?.total_balance || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
          <div className="flex items-center text-blue-100 text-sm">
            <span className="mr-2">↗</span>
            <span>{t('dashboard.allAccountsCombined')}</span>
          </div>
        </div>

        {/* Income Card */}
        <div className="bg-green-600 rounded-lg p-6 text-white shadow-sm">
          <div className="flex items-center justify-between mb-3">
            <div className="text-green-100 text-sm font-medium uppercase tracking-wider">{t('dashboard.income')}</div>
            <span className="text-4xl">📈</span>
          </div>
          <div className="text-4xl font-bold mb-2">
            +${(overview?.income_expense_breakdown?.income || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
          <div className="flex items-center text-green-100 text-sm">
            <span className="mr-2">{t('dashboard.incomePercent')}</span>
            <span>{t('dashboard.vsLastMonth')}</span>
          </div>
        </div>

        {/* Expenses Card */}
        <div className="bg-red-600 rounded-lg p-6 text-white shadow-sm">
          <div className="flex items-center justify-between mb-3">
            <div className="text-red-100 text-sm font-medium uppercase tracking-wider">{t('dashboard.expenses')}</div>
            <span className="text-4xl">📉</span>
          </div>
          <div className="text-4xl font-bold mb-2">
            ${(overview?.income_expense_breakdown?.expense || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
          <div className="flex items-center text-red-100 text-sm">
            <span className="mr-2">{t('dashboard.expensePercent')}</span>
            <span>{t('dashboard.vsLastMonth')}</span>
          </div>
        </div>
      </div>

      {/* Expense by Category */}
      <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-xl font-bold text-gray-900">{t('dashboard.expensesByCategory')}</h3>
            <p className="text-gray-500 text-sm">{t('dashboard.uncategorized')}</p>
          </div>
          <div className="flex items-center gap-3">
            <label htmlFor="period-select" className="text-sm font-medium text-gray-700">
              {t('dashboard.periodSelector')}:
            </label>
            <select
              id="period-select"
              value={selectedPeriod}
              onChange={(e) => handlePeriodChange(e.target.value)}
              disabled={categoryLoading}
              className="px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900 text-sm font-medium hover:border-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <option value="current_month">{t('dashboard.periodCurrentMonth')}</option>
              <option value="last_month">{t('dashboard.periodLastMonth')}</option>
              <option value="current_week">{t('dashboard.periodCurrentWeek')}</option>
              <option value="last_week">{t('dashboard.periodLastWeek')}</option>
              <option value="current_year">{t('dashboard.periodCurrentYear')}</option>
              <option value="last_year">{t('dashboard.periodLastYear')}</option>
              <option value="all_time">{t('dashboard.periodAllTime')}</option>
            </select>
          </div>
        </div>
        {categoryBreakdown.values.length > 0 ? (
          <div className="flex flex-col lg:flex-row gap-6">
            <div className="max-w-xl">
              {categoryLoading && (
                <div className="flex items-center justify-center h-64">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
                </div>
              )}
              {!categoryLoading && (
                <Pie
                  data={{
                    labels: categoryBreakdown.labels,
                    datasets: [
                      {
                        label: 'Expenses',
                        data: categoryBreakdown.values,
                        backgroundColor: categoryBreakdown.colors || [],
                        borderWidth: 1,
                      }
                    ]
                  }}
                  options={{
                    plugins: {
                      legend: { display: false },
                      tooltip: { callbacks: { label: (ctx) => `${ctx.label}: ${ctx.raw.toLocaleString('en-US', { minimumFractionDigits: 2 })}` } }
                    }
                  }}
                />
              )}
            </div>
            <div className="flex-1">
              <ul className="divide-y divide-gray-100">
                {categoryBreakdown.items?.map((item) => (
                  <li key={item.id || 'unknown'} className="py-2 flex items-center justify-between">
                    <button
                      onClick={() => {
                        // Navigate to Transactions tab with category filter
                        window.location.hash = `category=${item.id || 'unknown'}`
                        const evt = new CustomEvent('nav-to-transactions')
                        window.dispatchEvent(evt)
                      }}
                      className="text-left flex items-center gap-3 hover:bg-gray-50 rounded px-2 py-1 w-full"
                    >
                      <span className="inline-block w-3 h-3 rounded-full" style={{ backgroundColor: item.color || '#9ca3af' }}></span>
                      <span className="text-sm text-gray-800">{item.name}</span>
                    </button>
                    <span className="text-sm font-medium text-gray-900">
                      <SensitiveValue
                        value={item.value.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                        sensitiveMode={sensitiveMode}
                      />
                    </span>
                  </li>
                ))}
              </ul>
              <p className="text-xs text-gray-500 mt-2">Tip: Click a category to view all matching transactions.</p>
            </div>
          </div>
        ) : (
          <div className="text-gray-500">No expense data available.</div>
        )}
      </div>

      {/* Accounts Section */}
      <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Your Accounts</h2>
            <p className="text-gray-500 mt-1">Manage your bank accounts and balances</p>
          </div>
          <button
            onClick={() => setShowCreateModal(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-all font-medium"
          >
            + Add Account
          </button>
        </div>

        {accounts.length === 0 ? (
          <div className="text-center py-16 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
            <div className="text-6xl mb-4">🏦</div>
            <h3 className="text-xl font-semibold text-gray-700 mb-2">No accounts yet</h3>
            <p className="text-gray-500 mb-6">Create your first account to start tracking your finances</p>
            <button
              onClick={() => setShowCreateModal(true)}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-all font-medium"
            >
              Create Account
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {accounts.map((account) => (
              <div
                key={account.id}
                className="bg-white border-2 border-gray-200 rounded-lg p-5 hover:shadow-md hover:border-blue-400 transition-all"
              >
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center space-x-2">
                    <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center text-white font-bold">
                      {account.name.charAt(0).toUpperCase()}
                    </div>
                    <div>
                      <h3 className="font-semibold text-gray-900">{account.name}</h3>
                      <span className="text-xs px-2 py-0.5 bg-gray-100 text-gray-600 rounded-full">{account.currency}</span>
                    </div>
                  </div>
                  <button
                    onClick={() => setDeleteConfirm({ id: account.id, name: account.name })}
                    className="text-gray-400 hover:text-red-600 transition-colors p-1"
                    title="Delete account"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
                {account.institution && (
                  <p className="text-sm text-gray-500 mb-3 flex items-center">
                    <span className="mr-1">🏛️</span>
                    {account.institution}
                  </p>
                )}
                <div className="border-t border-gray-200 pt-3 mt-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-500">Current Balance</span>
                    <span className="text-xl font-bold text-gray-900">
                      <SensitiveValue
                        value={`${account.currency} ${(account.current_balance || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`}
                        sensitiveMode={sensitiveMode}
                      />
                    </span>
                  </div>
                  {account.converted_balance !== undefined && account.converted_balance !== null && (
                    <div className="flex items-center justify-between mt-1.5">
                      <span className="text-xs text-gray-400">
                        {account.conversion_rate_age}
                      </span>
                      <span className="text-sm text-gray-500">
                        <SensitiveValue
                          value={`≈ ${userCurrency} ${(account.converted_balance || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`}
                          sensitiveMode={sensitiveMode}
                        />
                      </span>
                    </div>
                  )}
                  <div className="flex items-center justify-between mt-2">
                    <span className="text-xs text-gray-400">
                      Created {formatDateTime(account.created_at)}
                    </span>
                    <button
                      onClick={() => setSelectedAccountId(account.id)}
                      className="text-blue-600 hover:text-blue-700 text-sm font-medium"
                    >
                      View →
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {showCreateModal && (
        <CreateAccountModal
          onClose={() => setShowCreateModal(false)}
          onCreated={() => {
            setShowCreateModal(false)
            fetchData()
          }}
        />
      )}

      {selectedAccountId && (
        <AccountDetailsView
          accountId={selectedAccountId}
          onClose={() => setSelectedAccountId(null)}
        />
      )}

      {/* Delete Confirmation Dialog */}
      {deleteConfirm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
            <div className="p-6">
              <div className="flex items-center mb-4">
                <div className="w-12 h-12 rounded-full bg-red-100 flex items-center justify-center mr-4">
                  <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">Delete Bank Account</h3>
                  <p className="text-sm text-gray-500 mt-1">This action cannot be undone</p>
                </div>
              </div>
              <div className="mb-6">
                <p className="text-gray-700">
                  Are you sure you want to delete <strong className="text-gray-900">"{deleteConfirm.name}"</strong>?
                </p>
                <p className="text-sm text-red-600 mt-2">
                  ⚠️ All transactions associated with this account will also be deleted.
                </p>
              </div>
              <div className="flex gap-3">
                <button
                  onClick={() => setDeleteConfirm(null)}
                  disabled={deleting}
                  className="flex-1 px-4 py-2 bg-gray-100 text-gray-900 rounded-lg hover:bg-gray-200 font-medium disabled:opacity-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleDelete}
                  disabled={deleting}
                  className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 font-medium disabled:opacity-50 transition-colors"
                >
                  {deleting ? 'Deleting...' : 'Delete Account'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
