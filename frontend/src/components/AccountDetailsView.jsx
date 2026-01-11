import React, { useState, useEffect } from 'react'
import axios from 'axios'
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

export default function AccountDetailsView({ account, onClose }) {
  const [transactions, setTransactions] = useState([])
  const [totalCount, setTotalCount] = useState(0)
  const [currentPage, setCurrentPage] = useState(1)
  const itemsPerPage = 25

  const [searchQuery, setSearchQuery] = useState('')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [sortBy, setSortBy] = useState('date')
  const [sortOrder, setSortOrder] = useState('desc')
  const [loading, setLoading] = useState(false)

  // ESC key handler to close modal
  useEffect(() => {
    const handleEsc = (e) => {
      if (e.key === 'Escape') {
        onClose()
      }
    }
    window.addEventListener('keydown', handleEsc)
    return () => window.removeEventListener('keydown', handleEsc)
  }, [onClose])

  // Fetch transactions for this specific account with server-side pagination
  const fetchAccountTransactions = async (page = 1) => {
    if (!account?.id) {
      console.warn('No account ID available')
      return
    }

    setLoading(true)
    try {
      const params = {
        account: account.id,
        page: page,
        page_size: itemsPerPage,
        ordering: sortOrder === 'desc' ? `-${sortBy}` : sortBy,
      }
      if (searchQuery) params.search = searchQuery
      if (dateFrom) params.date_from = dateFrom
      if (dateTo) params.date_to = dateTo

      console.log('Fetching transactions with params:', params)
      const res = await axios.get('/api/banking/transactions/', { params })
      console.log('Transactions response:', res.data)

      const data = res.data
      const results = data.results || []
      const count = data.count || 0

      setTransactions(results)
      setTotalCount(count)
      console.log(`Loaded ${results.length} transactions, total: ${count}`)
    } catch (e) {
      console.error('Failed to load account transactions:', e)
      setTransactions([])
      setTotalCount(0)
    } finally {
      setLoading(false)
    }
  }

  // Fetch when account changes
  useEffect(() => {
    if (account?.id) {
      console.log('Account changed, fetching transactions for account:', account.id)
      setCurrentPage(1)
      fetchAccountTransactions(1)
    }
  }, [account?.id])

  // Fetch when page or filters change
  useEffect(() => {
    if (account?.id && currentPage >= 1) {
      console.log('Page or filters changed, fetching page:', currentPage)
      fetchAccountTransactions(currentPage)
    }
  }, [currentPage, searchQuery, dateFrom, dateTo, sortBy, sortOrder, account?.id])

  // ApplyFilters resets to page 1 and fetches
  const applyFilters = () => {
    console.log('Applying filters')
    setCurrentPage(1)
  }

  // Chart data computed from current page transactions
  const calculateBalanceOverTime = () => {
    if (!transactions.length) return { labels: [], data: [] }

    const sorted = [...transactions].sort((a, b) => new Date(a.date) - new Date(b.date))

    let runningBalance = parseFloat(account?.opening_balance || 0)

    const labels = []
    const data = []
    sorted.forEach(tx => {
      const amt = typeof tx.amount === 'string' ? parseFloat(tx.amount) : tx.amount
      runningBalance += parseFloat(amt || 0)
      labels.push(new Date(tx.date).toLocaleDateString())
      data.push(Number(runningBalance.toFixed(2)))
    })
    return { labels, data }
  }

  const chartData = calculateBalanceOverTime()

  // Pagination controls
  const totalPages = Math.max(1, Math.ceil(totalCount / itemsPerPage))
  const canPrev = currentPage > 1
  const canNext = currentPage < totalPages

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-8">
          <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-blue-600 mx-auto"></div>
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
            <h2 className="text-2xl font-bold text-gray-900">{account?.name}</h2>
            <p className="text-sm text-gray-500">{account?.institution}</p>
            {account?.iban && <p className="text-xs text-gray-400 font-mono">IBAN: {account.iban}</p>}
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
              placeholder="Search description, partner, merchant"
              className="border border-gray-300 rounded px-3 py-2"
            />
            <input
              type="date"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
              className="border border-gray-300 rounded px-3 py-2"
            />
            <input
              type="date"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
              className="border border-gray-300 rounded px-3 py-2"
            />
            <div className="flex gap-2">
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="border border-gray-300 rounded px-3 py-2 flex-1"
              >
                <option value="date">Date</option>
                <option value="amount">Amount</option>
                <option value="description">Description</option>
              </select>
              <button
                onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
                className="border border-gray-300 rounded px-3 py-2"
              >{sortOrder === 'asc' ? '↑' : '↓'}</button>
              <button
                onClick={applyFilters}
                className="bg-blue-600 text-white rounded px-4 py-2"
              >Apply</button>
            </div>
          </div>
        </div>

        {/* Balance Chart */}
        <div className="px-6 py-6 border-b border-gray-200">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Balance Over Time</h3>
            {account?.opening_balance_date && (
              <div className="text-xs bg-blue-50 border border-blue-200 rounded px-2 py-1 text-blue-700">
                Reference: {account.currency} {parseFloat(account.opening_balance).toFixed(2)} on {new Date(account.opening_balance_date).toLocaleDateString()}
              </div>
            )}
          </div>
          <div className="bg-gray-50 p-4 rounded-lg" style={{ height: '300px' }}>
            {chartData.labels.length > 0 ? (
              <Line
                data={{
                  labels: chartData.labels,
                  datasets: [{
                    label: 'Balance',
                    data: chartData.data,
                    borderColor: '#2563eb',
                    backgroundColor: 'rgba(37, 99, 235, 0.1)',
                    fill: true,
                    tension: 0.4,
                  }]}}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  scales: {
                    y: { ticks: { callback: (v) => `${account.currency} ${Number(v).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` } }
                  }
                }}
              />
            ) : (
              <div className="h-full flex items-center justify-center text-gray-500">No data for current filters/page</div>
            )}
          </div>
        </div>

        {/* Transactions Table */}
        <div className="px-6 py-4">
          {loading ? (
            <div className="flex items-center justify-center h-40">
              <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600"></div>
            </div>
          ) : (
            <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
              <table className="w-full">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    <th className="text-left py-3 px-4 text-xs font-semibold text-gray-700">Date</th>
                    <th className="text-left py-3 px-4 text-xs font-semibold text-gray-700">Description</th>
                    <th className="text-right py-3 px-4 text-xs font-semibold text-gray-700">Amount</th>
                    <th className="text-left py-3 px-4 text-xs font-semibold text-gray-700">Type</th>
                    <th className="text-left py-3 px-4 text-xs font-semibold text-gray-700">Category</th>
                  </tr>
                </thead>
                <tbody>
                  {transactions.map(tx => (
                    <tr key={tx.id} className="border-b border-gray-100 hover:bg-gray-50">
                      <td className="py-3 px-4">{new Date(tx.date).toLocaleDateString()}</td>
                      <td className="py-3 px-4">{tx.description || '-'}</td>
                      <td className="py-3 px-4 text-right">{Number((typeof tx.amount === 'string' ? parseFloat(tx.amount) : tx.amount) || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} {account.currency}</td>
                      <td className="py-3 px-4">{tx.type}</td>
                      <td className="py-3 px-4">{tx.category_name || tx.category || '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Pagination */}
          <div className="flex items-center justify-between bg-white rounded-lg border border-gray-200 px-4 py-3 mt-3">
            <div className="text-sm text-gray-600">Page {currentPage} of {totalPages} • {totalCount} transactions</div>
            <div className="flex gap-2">
              <button
                onClick={() => canPrev && setCurrentPage(p => Math.max(1, p - 1))}
                disabled={!canPrev}
                className="px-3 py-1 border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50"
              >← Previous</button>
              <button
                onClick={() => canNext && setCurrentPage(p => Math.min(totalPages, p + 1))}
                disabled={!canNext}
                className="px-3 py-1 border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50"
              >Next →</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
