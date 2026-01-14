import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { SensitiveValue, useSensitiveModeListener } from '../utils/sensitive'
import { useTranslate } from '../hooks/useLanguage'
import { formatDate, formatDateTime, dateToInputFormat, inputDateToISO } from '../utils/format'
import DateInput from './DateInput'
import { Line } from 'react-chartjs-2'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js'

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
)

export default function AccountDetailsView({ accountId, onClose }) {
  const t = useTranslate()
  // Account data
  const [account, setAccount] = useState(null)

  // Transaction pagination state
  const [transactions, setTransactions] = useState([])
  const [totalCount, setTotalCount] = useState(0)
  const [currentPage, setCurrentPage] = useState(1)
  const itemsPerPage = 25

  // Filter state
  const [searchQuery, setSearchQuery] = useState('')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')

  // Sensitive mode state - use custom hook for instant updates
  const sensitiveMode = useSensitiveModeListener()
  const [sortBy, setSortBy] = useState('date')
  const [sortOrder, setSortOrder] = useState('desc')

  // Loading states
  const [accountLoading, setAccountLoading] = useState(true)
  const [transactionsLoading, setTransactionsLoading] = useState(false)
  const [chartLoading, setChartLoading] = useState(false)

  // Chart data state
  const [chartDates, setChartDates] = useState([])
  const [chartBalances, setChartBalances] = useState([])

  // Fetch account details
  const fetchAccountDetails = async () => {
    if (!accountId) return

    setAccountLoading(true)
    try {
      const res = await axios.get(`/api/banking/accounts/${accountId}/`)
      setAccount(res.data)
      console.log('Loaded account:', res.data)
    } catch (e) {
      console.error('Failed to load account:', e)
      setAccount(null)
    } finally {
      setAccountLoading(false)
    }
  }

  // ESC key handler
  useEffect(() => {
    const handleEsc = (e) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', handleEsc)
    return () => window.removeEventListener('keydown', handleEsc)
  }, [onClose])

  // Fetch transactions for current page
  const fetchTransactions = async (page = 1) => {
    if (!account?.id) return

    setTransactionsLoading(true)
    try {
      const params = {
        account: account.id,
        page: page,
        page_size: itemsPerPage,
        ordering: sortOrder === 'desc' ? `-${sortBy}` : sortBy,
      }
      if (searchQuery) params.search = searchQuery
      if (dateFrom) params.date__gte = dateFrom
      if (dateTo) params.date__lte = dateTo

      console.log('Fetching transactions with params:', params)
      const res = await axios.get('/api/banking/transactions/', { params })
      const data = res.data
      const results = data.results || []
      const count = data.count || 0

      setTransactions(results)
      setTotalCount(count)
      console.log(`Loaded page ${page}: ${results.length} transactions, total: ${count}`)
    } catch (e) {
      console.error('Failed to load transactions:', e)
      setTransactions([])
      setTotalCount(0)
    } finally {
      setTransactionsLoading(false)
    }
  }

  // Fetch timeseries data for chart
  const fetchChartData = async () => {
    if (!account?.id) return

    setChartLoading(true)
    try {
      const params = {}
      if (dateFrom) params.date__gte = dateFrom
      if (dateTo) params.date__lte = dateTo

      console.log('Fetching chart data with params:', params)
      const res = await axios.get(`/api/analytics/accounts/${account.id}/balance-timeseries/`, { params })
      const data = res.data

      setChartDates(data.dates || [])
      setChartBalances(data.balances || [])
      console.log(`Loaded chart data: ${data.count} data points`)
    } catch (e) {
      console.error('Failed to load chart data:', e)
      setChartDates([])
      setChartBalances([])
    } finally {
      setChartLoading(false)
    }
  }

  // Load initial page when account changes
  useEffect(() => {
    if (accountId) {
      console.log('Account ID changed, loading account details:', accountId)
      fetchAccountDetails()
    }
  }, [accountId])

  // Load transactions and chart when account is loaded
  useEffect(() => {
    if (account?.id) {
      console.log('Account loaded, loading initial data for account:', account.id)
      setCurrentPage(1)
      fetchTransactions(1)
      fetchChartData()
    }
  }, [account?.id])

  // Load new page when page changes
  useEffect(() => {
    if (account?.id && currentPage >= 1) {
      console.log('Page changed to:', currentPage)
      fetchTransactions(currentPage)
    }
  }, [currentPage, account?.id])

  // Reload on filter changes
  useEffect(() => {
    if (account?.id) {
      console.log('Filters changed, reloading data')
      setCurrentPage(1)
      fetchTransactions(1)
      fetchChartData()
    }
  }, [searchQuery, dateFrom, dateTo, sortBy, sortOrder, account?.id])

  // Helper functions for transaction type display
  const getTypeColor = (type) => {
    switch(type) {
      case 'income': return 'bg-green-100 text-green-700 border-green-200'
      case 'expense': return 'bg-red-100 text-red-700 border-red-200'
      case 'transfer': return 'bg-blue-100 text-blue-700 border-blue-200'
      default: return 'bg-gray-100 text-gray-700 border-gray-200'
    }
  }

  const getTypeIcon = (type) => {
    switch(type) {
      case 'income': return '📈'
      case 'expense': return '📉'
      case 'transfer': return '↔️'
      default: return '💳'
    }
  }

  // Apply filters
  const applyFilters = () => {
    console.log('Applying filters')
    setCurrentPage(1)
  }

  // Build chart labels - only show first day of month
  const buildChartLabels = () => {
    return chartDates.map((dateStr) => {
      const date = new Date(dateStr)
      // Only show label if it's the first day of the month
      if (date.getDate() === 1) {
        return formatDate(dateStr)
      }
      return ''
    })
  }

  // Pagination helpers
  const totalPages = Math.max(1, Math.ceil(totalCount / itemsPerPage))
  const canPrev = currentPage > 1
  const canNext = currentPage < totalPages

  if (!accountId) {
    return null
  }

  if (accountLoading) {
    return (
      <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-8">
          <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-blue-600 mx-auto"></div>
        </div>
      </div>
    )
  }

  if (!account) {
    return (
      <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-8 text-center">
          <p className="text-red-600">{t('accountDetails.failedToLoadAccount')}</p>
          <button onClick={onClose} className="mt-4 px-4 py-2 bg-blue-600 text-white rounded">{t('common.close')}</button>
        </div>
      </div>
    )
  }

  return (
    <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50 overflow-y-auto p-4">
      <div className="bg-white rounded-lg shadow-lg w-full max-w-6xl max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between z-10">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">{account.name}</h2>
            <p className="text-sm text-gray-500">{account.institution}</p>
            {account.iban && <p className="text-xs text-gray-400 font-mono">IBAN: {account.iban}</p>}
          </div>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700 text-2xl">✕</button>
        </div>

        {/* Filters */}
        <div className="px-6 py-4 border-b border-gray-100 bg-gray-50">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
            <input
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter') applyFilters() }}
              placeholder={t('transactions.searchPlaceholder')}
              className="border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <DateInput
              value={dateFrom}
              onChange={(isoDate) => setDateFrom(isoDate)}
              title="Start date for filter"
              showPickerButton={true}
            />
            <DateInput
              value={dateTo}
              onChange={(isoDate) => setDateTo(isoDate)}
              title="End date for filter"
              showPickerButton={true}
            />
            <div className="flex gap-2">
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="border border-gray-300 rounded px-3 py-2 flex-1 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="date">{t('transactions.date')}</option>
                <option value="amount">{t('transactions.amount')}</option>
              </select>
              <button
                onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
                className="border border-gray-300 rounded px-3 py-2 hover:bg-gray-100"
              >{sortOrder === 'asc' ? '↑' : '↓'}</button>
            </div>
          </div>
        </div>

        {/* Balance Chart */}
        <div className="px-6 py-6 border-b border-gray-200">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">{t('accountDetails.balanceOverTime')}</h3>
            {chartLoading && <span className="text-xs text-gray-500">{t('accountDetails.loadingChart')}</span>}
          </div>
          <div className="bg-gray-50 p-4 rounded-lg" style={{ height: '300px' }}>
            {chartDates.length > 0 ? (
              <Line
                data={{
                  labels: buildChartLabels(),
                  datasets: [{
                    label: t('accountDetails.balance'),
                    data: chartBalances,
                    borderColor: '#2563eb',
                    backgroundColor: 'rgba(37, 99, 235, 0.1)',
                    fill: true,
                    tension: 0.4,
                    pointRadius: 0,
                    pointHoverRadius: 6,
                  }]
                }}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  plugins: {
                    legend: { display: true }
                  },
                  scales: {
                    y: {
                      ticks: {
                        callback: (v) => `${account.currency} ${Number(v).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
                      }
                    }
                  }
                }}
              />
            ) : chartLoading ? (
              <div className="h-full flex items-center justify-center text-gray-500">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              </div>
            ) : (
              <div className="h-full flex items-center justify-center text-gray-500">{t('accountDetails.noDataAvailable')}</div>
            )}
          </div>
        </div>

        {/* Transactions Table */}
        <div className="px-6 py-4">
          {transactionsLoading && transactions.length === 0 ? (
            <div className="flex items-center justify-center h-40">
              <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600"></div>
            </div>
          ) : (
            <div className="bg-white rounded-lg border border-gray-200 overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    <th className="text-left py-3 px-4 text-xs font-semibold text-gray-700">{t('transactions.date')}</th>
                    <th className="text-left py-3 px-4 text-xs font-semibold text-gray-700">{t('transactions.fieldReference')}</th>
                    <th className="text-right py-3 px-4 text-xs font-semibold text-gray-700">{t('transactions.amount')}</th>
                    <th className="text-left py-3 px-4 text-xs font-semibold text-gray-700">{t('transactions.type')}</th>
                    <th className="text-left py-3 px-4 text-xs font-semibold text-gray-700">{t('transactions.category')}</th>
                  </tr>
                </thead>
                <tbody>
                  {transactions.length > 0 ? (
                    transactions.map(tx => (
                      <tr key={tx.id} className="border-b border-gray-100 hover:bg-gray-50">
                        <td className="py-3 px-4 whitespace-nowrap">{formatDate(tx.date)}</td>
                        <td className="py-3 px-4 text-sm max-w-xs truncate" title={tx.description || '-'}>
                          {tx.reference || '-'}
                        </td>
                        <td className="py-3 px-4 text-right font-medium whitespace-nowrap">
                          <span style={{ color: parseFloat(tx.amount) >= 0 ? '#10b981' : '#ef4444' }}>
                            <SensitiveValue
                              value={`${Number((typeof tx.amount === 'string' ? parseFloat(tx.amount) : tx.amount) || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ${account.currency}`}
                              sensitiveMode={sensitiveMode}
                            />
                          </span>
                        </td>
                        <td className="py-3 px-4 text-sm whitespace-nowrap">
                          <span className={`inline-flex items-center px-3 py-1 text-xs font-semibold rounded-full border ${getTypeColor(tx.type)}`}>
                            {/*<span className="mr-1">{getTypeIcon(tx.type)}</span>*/}
                            {t(`transactions.${tx.type}`)}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-sm whitespace-nowrap">{tx.category_name || tx.category || '-'}</td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan="5" className="py-8 text-center text-gray-500">{t('transactions.noTransactionsFound')}</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}

          {/* Pagination */}
          <div className="flex items-center justify-between bg-white rounded-lg border border-gray-200 px-4 py-3 mt-3">
            <div className="text-sm text-gray-600">
              {t('transactions.pageOf', { current: currentPage, total: totalPages, count: totalCount })}
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => canPrev && setCurrentPage(p => Math.max(1, p - 1))}
                disabled={!canPrev}
                className="px-3 py-1 border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
              >{t('transactions.previousPage')}</button>
              <button
                onClick={() => canNext && setCurrentPage(p => Math.min(totalPages, p + 1))}
                disabled={!canNext}
                className="px-3 py-1 border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
              >{t('transactions.nextPage')}</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
