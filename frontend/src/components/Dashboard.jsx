import React, { useEffect, useState } from 'react'
import axios from 'axios'
import { getCsrfToken } from '../utils/csrf'
import { SensitiveValue, useSensitiveModeListener } from '../utils/sensitive'
import CreateAccountModal from './CreateAccountModal'
import AccountDetailsView from './AccountDetailsView'
import { useTranslate } from '../hooks/useLanguage'
import { formatDateTime, getFormatPreferences, getCurrencySymbol, formatNumber } from '../utils/format'
import { Pie, Bar } from 'react-chartjs-2'
import { Chart as ChartJS, ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement, Title } from 'chart.js'
import { TrendingUp, TrendingDown, DollarSign, Plus, AlertCircle, Trash2, Wallet, ArrowUpDown, RotateCw, Building } from 'lucide-react'
ChartJS.register(ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement, Title)

export default function Dashboard({ darkMode = false }) {
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
  const [dashboardPeriod, setDashboardPeriod] = useState('current_month')
  const [selectedAccountFilter, setSelectedAccountFilter] = useState('all')
  const [filtersLoading, setFiltersLoading] = useState(false)
  const [userCurrency, setUserCurrency] = useState(getFormatPreferences().currencyCode)
  const sensitiveMode = useSensitiveModeListener()
  const [spendingTrend, setSpendingTrend] = useState(null)
  const [cashFlow, setCashFlow] = useState(null)
  const [recurringTransactions, setRecurringTransactions] = useState(null)
  const [monthlyIncomeExpense, setMonthlyIncomeExpense] = useState(null)

  const fetchData = (period = dashboardPeriod, accountId = selectedAccountFilter) => {
    setLoading(true)
    const accountParam = accountId !== 'all' ? `&account_id=${accountId}` : ''
    Promise.all([
      axios.get(`/api/analytics/overview?period=${period}${accountParam}`).catch(() => ({ data: { total_balance: 0, income_expense_breakdown: { income: 0, expense: 0 }, monthly_trends: [], income_change_percent: null, expense_change_percent: null } })),
      axios.get('/api/banking/accounts/').catch(() => ({ data: { results: [] } })),
      axios.get(`/api/analytics/category-expense/?period=${period}${accountParam}`).catch(() => ({ data: { labels: [], values: [] } })),
      axios.get(`/api/analytics/spending-trend/?period=${period}${accountParam}`).catch(() => ({ data: { current_period_expense: 0, previous_period_expense: 0, trend_percent: 0, daily_average: 0, forecast_month_end: 0, days_in_period: 0, days_elapsed: 0, is_trending_up: false } })),
      axios.get(`/api/analytics/cash-flow/?period=${period}${accountParam}`).catch(() => ({ data: { income: 0, expense: 0, net_flow: 0, savings_rate: 0, burn_rate: 0, balance_change: 0 } })),
      axios.get('/api/banking/recurring/summary/').catch(() => ({ data: { total_count: 0, active_count: 0, monthly_recurring_cost: 0, yearly_recurring_cost: 0, by_frequency: {}, top_recurring: [], overdue_count: 0 } })),
      axios.get(`/api/analytics/monthly-income-expense/${accountId !== 'all' ? `?account_id=${accountId}` : ''}`).catch(() => ({ data: { months: [], income: [], expense: [], currency: 'USD' } }))
    ]).then(([overviewRes, accountsRes, catRes, trendRes, cashFlowRes, recurringRes, monthlyRes]) => {
      setOverview(overviewRes.data)
      setAccounts(accountsRes.data.results || accountsRes.data || [])
      setCategoryBreakdown(catRes.data || { labels: [], values: [] })
      setSpendingTrend(trendRes.data)
      setCashFlow(cashFlowRes.data)
      setRecurringTransactions(recurringRes.data)
      setMonthlyIncomeExpense(monthlyRes.data)
      setLoading(false)
    }).catch(err => {
      setError(err.message)
      setLoading(false)
    })
  }

  const handleFilterChange = (newPeriod, newAccount = selectedAccountFilter) => {
    setDashboardPeriod(newPeriod)
    setSelectedAccountFilter(newAccount)
    setFiltersLoading(true)
    const accountParam = newAccount !== 'all' ? `&account_id=${newAccount}` : ''
    Promise.all([
      axios.get(`/api/analytics/overview?period=${newPeriod}${accountParam}`),
      axios.get(`/api/analytics/category-expense/?period=${newPeriod}${accountParam}`),
      axios.get(`/api/analytics/spending-trend/?period=${newPeriod}${accountParam}`),
      axios.get(`/api/analytics/cash-flow/?period=${newPeriod}${accountParam}`),
      axios.get(`/api/analytics/monthly-income-expense/${newAccount !== 'all' ? `?account_id=${newAccount}` : ''}`)
    ]).then(([overviewRes, catRes, trendRes, cashFlowRes, monthlyRes]) => {
      setOverview(overviewRes.data)
      setCategoryBreakdown(catRes.data || { labels: [], values: [] })
      setSpendingTrend(trendRes.data)
      setCashFlow(cashFlowRes.data)
      setMonthlyIncomeExpense(monthlyRes.data)
    }).catch(err => {
      console.error('Failed to fetch data:', err)
    }).finally(() => {
      setFiltersLoading(false)
    })
  }

  const handleAccountFilterChange = (newAccount) => {
    handleFilterChange(dashboardPeriod, newAccount)
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
          <AlertCircle size={32} className="text-red-500 mr-3" />
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
      {/* Dashboard Filters */}
      <div className={`${darkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'} rounded-lg shadow-sm p-4 border`}>
        <div className="flex flex-wrap items-center gap-4">
          {/* Period Label & Dropdown */}
          <div className="flex items-center gap-2">
            <label htmlFor="dashboard-period" className={`text-sm font-medium ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>
              {t('dashboard.periodSelector')}:
            </label>
            <select
              id="dashboard-period"
              value={dashboardPeriod}
              onChange={(e) => handleFilterChange(e.target.value)}
              disabled={filtersLoading}
              className={`px-3 py-2 border rounded-lg text-sm font-medium focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 ${darkMode ? 'bg-gray-700 border-gray-600 text-white hover:border-gray-500' : 'bg-white border-gray-300 text-gray-900 hover:border-gray-400'}`}
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

          {/* Quick Period Buttons */}
          <div className="flex items-center gap-1 border-l border-gray-200 pl-4">
            <button
              onClick={() => handleFilterChange('current_month')}
              disabled={filtersLoading}
              className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                dashboardPeriod === 'current_month'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              } disabled:opacity-50`}
            >
              {t('dashboard.quickThisMonth')}
            </button>
            <button
              onClick={() => handleFilterChange('last_month')}
              disabled={filtersLoading}
              className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                dashboardPeriod === 'last_month'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              } disabled:opacity-50`}
            >
              {t('dashboard.quickLastMonth')}
            </button>
            <button
              onClick={() => handleFilterChange('current_year')}
              disabled={filtersLoading}
              className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                dashboardPeriod === 'current_year'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              } disabled:opacity-50`}
            >
              {t('dashboard.quickYTD')}
            </button>
          </div>

          {/* Account Filter */}
          <div className="flex items-center gap-2 border-l border-gray-200 pl-4">
            <label htmlFor="account-filter" className="text-sm font-medium text-gray-700">
              {t('dashboard.accountFilter')}:
            </label>
            <select
              id="account-filter"
              value={selectedAccountFilter}
              onChange={(e) => handleAccountFilterChange(e.target.value)}
              disabled={filtersLoading}
              className={`px-3 py-2 border rounded-lg text-sm font-medium focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 ${darkMode ? 'bg-gray-700 border-gray-600 text-white hover:border-gray-500' : 'bg-white border-gray-300 text-gray-900 hover:border-gray-400'}`}
            >
              <option value="all">{t('dashboard.allAccounts')}</option>
              {accounts.map(acc => (
                <option key={acc.id} value={acc.id}>{acc.name}</option>
              ))}
            </select>
          </div>

          {/* Loading indicator */}
          {filtersLoading && (
            <div className="ml-auto">
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
            </div>
          )}
        </div>
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Total Balance Card */}
        <div className="bg-blue-600 rounded-lg p-6 text-white shadow-sm">
          <div className="flex items-center justify-between mb-3">
            <div className="text-blue-100 text-sm font-medium uppercase tracking-wider">{t('dashboard.totalBalance')}</div>
            <Wallet size={36} className="text-blue-200" />
          </div>
          <div className="text-4xl font-bold mb-2">
            <SensitiveValue
              value={`${getCurrencySymbol(overview?.total_balance_currency || 'USD')} ${formatNumber(overview?.total_balance || 0)}`}
              sensitiveMode={sensitiveMode}
            />
          </div>
          <div className="flex items-center text-blue-100 text-sm">
            <span className="mr-2">↗</span>
            <span>{selectedAccountFilter === 'all' ? t('dashboard.allAccountsCombined') : accounts.find(a => a.id === parseInt(selectedAccountFilter))?.name || ''}</span>
          </div>
        </div>

        {/* Income Card */}
        <div className="bg-green-600 rounded-lg p-6 text-white shadow-sm relative">
          {filtersLoading && (
            <div className="absolute inset-0 bg-green-600/80 rounded-lg flex items-center justify-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white"></div>
            </div>
          )}
          <div className="flex items-center justify-between mb-3">
            <div className="text-green-100 text-sm font-medium uppercase tracking-wider">{t('dashboard.income')}</div>
            <TrendingUp size={36} className="text-green-200" />
          </div>
          <div className="text-4xl font-bold mb-2">
            <SensitiveValue
              value={`${getCurrencySymbol(overview?.total_balance_currency || 'USD')} ${formatNumber(overview?.income_expense_breakdown?.income || 0)}`}
              sensitiveMode={sensitiveMode}
            />
          </div>
          <div className="flex items-center text-sm">
            {overview?.income_change_percent !== null && overview?.income_change_percent !== undefined ? (
              <>
                <span className={`mr-2 px-2 py-0.5 rounded ${
                  overview.income_change_percent >= 0 
                    ? 'bg-white/20 text-white' 
                    : 'bg-red-100 text-red-800'
                }`}>
                  {overview.income_change_percent >= 0 ? '+' : ''}{overview.income_change_percent.toFixed(1)}%
                </span>
                <span className="text-green-100">{t('dashboard.vsPreviousPeriod')}</span>
              </>
            ) : (
              <span className="text-green-100">{t('dashboard.periodAllTime')}</span>
            )}
          </div>
        </div>

        {/* Expenses Card */}
        <div className="bg-red-600 rounded-lg p-6 text-white shadow-sm relative">
          {filtersLoading && (
            <div className="absolute inset-0 bg-red-600/80 rounded-lg flex items-center justify-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white"></div>
            </div>
          )}
          <div className="flex items-center justify-between mb-3">
            <div className="text-red-100 text-sm font-medium uppercase tracking-wider">{t('dashboard.expenses')}</div>
            <TrendingDown size={36} className="text-red-200" />
          </div>
          <div className="text-4xl font-bold mb-2">
            <SensitiveValue
              value={`${getCurrencySymbol(overview?.total_balance_currency || 'USD')} ${formatNumber(overview?.income_expense_breakdown?.expense || 0)}`}
              sensitiveMode={sensitiveMode}
            />
          </div>
          <div className="flex items-center text-sm">
            {overview?.expense_change_percent !== null && overview?.expense_change_percent !== undefined ? (
              <>
                <span className={`mr-2 px-2 py-0.5 rounded ${
                  overview.expense_change_percent <= 0 
                    ? 'bg-green-100 text-green-800' 
                    : 'bg-white/20 text-white'
                }`}>
                  {overview.expense_change_percent >= 0 ? '+' : ''}{overview.expense_change_percent.toFixed(1)}%
                </span>
                <span className="text-red-100">{t('dashboard.vsPreviousPeriod')}</span>
              </>
            ) : (
              <span className="text-red-100">{t('dashboard.periodAllTime')}</span>
            )}
          </div>
        </div>
      </div>

      {/* Charts Grid - Expenses by Category and Monthly Income vs Expenses */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Expense by Category - Pie Chart */}
        <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-bold text-gray-900">{t('dashboard.expensesByCategory')}</h3>
          </div>
          {categoryBreakdown.values.length > 0 ? (
            <>
              {filtersLoading && (
                <div className="flex items-center justify-center" style={{ height: '300px' }}>
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
                </div>
              )}
              {!filtersLoading && (
                <div style={{ height: '300px' }}>
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
                      responsive: true,
                      maintainAspectRatio: false,
                      plugins: {
                        legend: { display: false },
                        tooltip: { callbacks: { label: (ctx) => `${ctx.label}: ${formatNumber(ctx.raw)}` } }
                      }
                    }}
                  />
                </div>
              )}

              {/* Category Breakdown List - Inside Pie Chart Card */}
              <div className="mt-6 border-t border-gray-200 pt-6">
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
                          value={formatNumber(item.value)}
                          sensitiveMode={sensitiveMode}
                        />
                      </span>
                    </li>
                  ))}
                </ul>
                <p className="text-xs text-gray-500 mt-2">Tip: Click a category to view all matching transactions.</p>
              </div>
            </>
          ) : (
            <div className="text-gray-500 flex items-center justify-center h-64">No expense data available.</div>
          )}
        </div>

        {/* Monthly Income vs Expenses - Bar Chart */}
        <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-bold text-gray-900">{t('dashboard.monthlyIncomeVsExpenses')}</h3>
          </div>
          {filtersLoading && (
            <div className="flex items-center justify-center" style={{ height: '300px' }}>
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            </div>
          )}
          {!filtersLoading && monthlyIncomeExpense && monthlyIncomeExpense.months && monthlyIncomeExpense.months.length > 0 ? (
            <div style={{ height: '300px' }}>
              <Bar
                data={{
                  labels: monthlyIncomeExpense.months,
                  datasets: [
                    {
                      label: t('dashboard.income'),
                      data: monthlyIncomeExpense.income,
                      backgroundColor: '#10b981',
                      borderColor: '#059669',
                      borderWidth: 1,
                    },
                    {
                      label: t('dashboard.expenses'),
                      data: monthlyIncomeExpense.expense,
                      backgroundColor: '#ef4444',
                      borderColor: '#dc2626',
                      borderWidth: 1,
                    }
                  ]
                }}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  plugins: {
                    legend: {
                      display: true,
                      position: 'top',
                      labels: { usePointStyle: true }
                    },
                    tooltip: {
                      callbacks: {
                        label: (ctx) => `${ctx.dataset.label}: ${getCurrencySymbol(monthlyIncomeExpense.currency)} ${formatNumber(ctx.raw)}`
                      }
                    }
                  },
                  scales: {
                    y: {
                      beginAtZero: true,
                      ticks: {
                        callback: (value) => `${getCurrencySymbol(monthlyIncomeExpense.currency)} ${formatNumber(value)}`
                      }
                    }
                  }
                }}
              />
            </div>
          ) : !filtersLoading ? (
            <div className="text-gray-500 flex items-center justify-center h-64">{t('dashboard.noDataAvailable')}</div>
          ) : null}
        </div>
      </div>

      {/* Spending Trend Widget */}
      {spendingTrend && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold text-gray-900">{t('dashboard.spendingTrend')}</h3>
              {spendingTrend.is_trending_up ?
                <TrendingUp size={28} className="text-red-500" /> :
                <TrendingDown size={28} className="text-green-500" />
              }
            </div>

            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">{t('dashboard.currentSpending')}</p>
                  <p className="text-2xl font-bold text-gray-900">
                    <SensitiveValue
                      value={`${getCurrencySymbol(overview?.total_balance_currency || 'USD')} ${formatNumber(spendingTrend.current_period_expense)}`}
                      sensitiveMode={sensitiveMode}
                    />
                  </p>
                </div>
                <div className={`px-3 py-1 rounded-full text-sm font-semibold ${spendingTrend.is_trending_up ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'}`}>
                  {spendingTrend.trend_percent >= 0 ? '+' : ''}{spendingTrend.trend_percent.toFixed(1)}%
                </div>
              </div>

              <div className="bg-gray-50 rounded-lg p-4">
                <p className="text-sm text-gray-500">{t('dashboard.dailyAverage')}</p>
                <p className="text-xl font-bold text-gray-900">
                  <SensitiveValue
                    value={`${getCurrencySymbol(overview?.total_balance_currency || 'USD')} ${formatNumber(spendingTrend.daily_average)}`}
                    sensitiveMode={sensitiveMode}
                  />
                </p>
                <p className="text-xs text-gray-500 mt-1">{spendingTrend.days_elapsed} of {spendingTrend.days_in_period} days</p>
              </div>

              <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
                <p className="text-sm text-gray-500">{t('dashboard.forecastedTotal')}</p>
                <p className="text-xl font-bold text-blue-900">
                  <SensitiveValue
                    value={`${getCurrencySymbol(overview?.total_balance_currency || 'USD')} ${formatNumber(spendingTrend.forecast_month_end)}`}
                    sensitiveMode={sensitiveMode}
                  />
                </p>
              </div>
            </div>
          </div>

          {cashFlow && (
            <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-bold text-gray-900">{t('dashboard.cashFlow')}</h3>
                <ArrowUpDown size={28} className="text-blue-500" />
              </div>

              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-green-50 rounded-lg p-3">
                    <p className="text-xs text-gray-500">{t('dashboard.income')}</p>
                    <p className="text-lg font-bold text-green-900">
                      <SensitiveValue
                        value={`${getCurrencySymbol(overview?.total_balance_currency || 'USD')} ${formatNumber(cashFlow.income)}`}
                        sensitiveMode={sensitiveMode}
                      />
                    </p>
                  </div>
                  <div className="bg-red-50 rounded-lg p-3">
                    <p className="text-xs text-gray-500">{t('dashboard.expenses')}</p>
                    <p className="text-lg font-bold text-red-900">
                      <SensitiveValue
                        value={`${getCurrencySymbol(overview?.total_balance_currency || 'USD')} ${formatNumber(cashFlow.expense)}`}
                        sensitiveMode={sensitiveMode}
                      />
                    </p>
                  </div>
                </div>

                <div className={`rounded-lg p-4 ${cashFlow.net_flow >= 0 ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
                  <p className="text-sm text-gray-500">{t('dashboard.netFlow')}</p>
                  <p className={`text-xl font-bold ${cashFlow.net_flow >= 0 ? 'text-green-900' : 'text-red-900'}`}>
                    <SensitiveValue
                      value={`${getCurrencySymbol(overview?.total_balance_currency || 'USD')} ${formatNumber(cashFlow.net_flow)}`}
                      sensitiveMode={sensitiveMode}
                    />
                  </p>
                </div>

                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <p className="text-sm text-gray-500">{t('dashboard.savingsRate')}</p>
                    <p className={`text-lg font-bold ${cashFlow.savings_rate >= 20 ? 'text-green-600' : cashFlow.savings_rate >= 0 ? 'text-blue-600' : 'text-red-600'}`}>
                      {cashFlow.savings_rate.toFixed(1)}%
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {recurringTransactions && recurringTransactions.total_count > 0 && (
        <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-bold text-gray-900">{t('dashboard.recurringTransactions')}</h3>
            <RotateCw size={28} className="text-blue-500" />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
              <p className="text-sm text-gray-500">{t('dashboard.activeSubscriptions')}</p>
              <p className="text-3xl font-bold text-blue-900">{recurringTransactions.active_count}</p>
              <p className="text-xs text-blue-700 mt-1">of {recurringTransactions.total_count} total</p>
            </div>

            <div className="bg-green-50 rounded-lg p-4 border border-green-200">
              <p className="text-sm text-gray-500">{t('dashboard.monthlyRecurringCost')}</p>
              <p className="text-2xl font-bold text-green-900">
                <SensitiveValue
                  value={`${getCurrencySymbol(overview?.total_balance_currency || 'USD')} ${formatNumber(parseFloat(recurringTransactions.monthly_recurring_cost))}`}
                  sensitiveMode={sensitiveMode}
                />
              </p>
            </div>

            <div className="bg-purple-50 rounded-lg p-4 border border-purple-200">
              <p className="text-sm text-gray-500">{t('dashboard.yearlyRecurringCost')}</p>
              <p className="text-2xl font-bold text-purple-900">
                <SensitiveValue
                  value={`${getCurrencySymbol(overview?.total_balance_currency || 'USD')} ${formatNumber(parseFloat(recurringTransactions.yearly_recurring_cost))}`}
                  sensitiveMode={sensitiveMode}
                />
              </p>
            </div>

            {recurringTransactions.overdue_count > 0 && (
              <div className="bg-red-50 rounded-lg p-4 border border-red-200">
                <p className="text-sm text-gray-500">{t('dashboard.overdueSubscriptions')}</p>
                <p className="text-3xl font-bold text-red-900">{recurringTransactions.overdue_count}</p>
                <p className="text-xs text-red-700 mt-1">Need attention</p>
              </div>
            )}
          </div>
        </div>
      )}

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
            <Building size={64} className="mx-auto text-gray-400 mb-4" />
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
                    <Trash2 size={20} />
                  </button>
                </div>
                {account.institution && (
                  <p className="text-sm text-gray-500 mb-3 flex items-center">
                    <Building size={14} className="mr-1 text-gray-400" />
                    {account.institution}
                  </p>
                )}
                <div className="border-t border-gray-200 pt-3 mt-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-500">Current Balance</span>
                    <span className="text-xl font-bold text-gray-900">
                      <SensitiveValue
                        value={`${account.currency} ${formatNumber(account.current_balance || 0)}`}
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
                          value={`≈ ${userCurrency} ${formatNumber(account.converted_balance || 0)}`}
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
                <div className="flex items-start gap-2 mt-2 text-sm text-red-600 bg-red-50 p-2 rounded">
                  <AlertCircle size={18} className="text-red-600 flex-shrink-0 mt-0.5" />
                  <p>All transactions associated with this account will also be deleted.</p>
                </div>
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
