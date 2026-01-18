import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { useTranslate } from '../hooks/useLanguage'
import { formatDate, formatCurrency, getCurrencySymbol } from '../utils/format'

/**
 * RecurringTransactionsView
 * Displays detected recurring transactions with summary, list, pagination and filters
 *
 * Uses backend pagination to handle large datasets efficiently.
 */
export default function RecurringTransactionsView() {
  const t = useTranslate()
  const [summary, setSummary] = useState(null)
  const [recurring, setRecurring] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selectedAccount, setSelectedAccount] = useState(null)
  const [accounts, setAccounts] = useState([])
  const [currentPage, setCurrentPage] = useState(1)
  const itemsPerPage = 25
  const [totalCount, setTotalCount] = useState(0)
  const [filters, setFilters] = useState({
    frequency: '',
    is_active: true,
    search: ''
  })
  const [showDetectModal, setShowDetectModal] = useState(false)
  const [detecting, setDetecting] = useState(false)
  const [selectedRecurring, setSelectedRecurring] = useState(null)
  const [linkedTransactions, setLinkedTransactions] = useState([])
  const [loadingLinked, setLoadingLinked] = useState(false)

  // Fetch accounts list
  useEffect(() => {
    fetchAccounts()
  }, [])

  // Fetch recurring data when account, filters, or page changes
  useEffect(() => {
    if (selectedAccount) {
      fetchRecurringData()
    }
  }, [selectedAccount, filters, currentPage])

  const fetchAccounts = async () => {
    try {
      const res = await axios.get('/api/banking/accounts/')
      setAccounts(res.data.results || res.data)
      if (res.data.results?.length > 0 || res.data.length > 0) {
        const first = (res.data.results || res.data)[0]
        setSelectedAccount(first.id)
      }
    } catch (err) {
      console.error('Failed to load accounts:', err)
      setError('Failed to load bank accounts')
    }
  }

  const fetchRecurringData = async () => {
    setLoading(true)
    try {
      // Fetch summary
      const summaryRes = await axios.get(
        `/api/banking/recurring/summary/?account_id=${selectedAccount}`
      )
      setSummary(summaryRes.data)

      // Fetch list with pagination and filters
      const params = new URLSearchParams()
      params.append('account_id', selectedAccount)
      params.append('page', String(currentPage))
      params.append('page_size', String(itemsPerPage))
      params.append('is_active', String(filters.is_active))

      if (filters.frequency) {
        params.append('frequency', filters.frequency)
      }

      // Add search filter if provided (search in description and merchant_name)
      if (filters.search) {
        params.append('search', filters.search)
      }

      const listRes = await axios.get(`/api/banking/recurring/?${params.toString()}`)
      const data = listRes.data
      setRecurring(data.results || data)
      setTotalCount(data.count || (data.results?.length || 0))
      setError(null)
    } catch (err) {
      console.error('Failed to load recurring data:', err)
      setError('Failed to load recurring transactions')
    } finally {
      setLoading(false)
    }
  }

  const triggerDetection = async () => {
    setDetecting(true)
    try {
      await axios.post(`/api/banking/recurring/detect/?account_id=${selectedAccount}&days_back=${365 * 5}`)
      setShowDetectModal(false)
      // Wait a moment then refresh
      setTimeout(() => {
        setCurrentPage(1)
        fetchRecurringData()
      }, 2000)
    } catch (err) {
      console.error('Detection failed:', err)
      setError('Failed to trigger detection')
    } finally {
      setDetecting(false)
    }
  }

  const toggleIgnore = async (id, isIgnored) => {
    try {
      const endpoint = isIgnored ? 'unignore' : 'ignore'
      await axios.post(`/api/banking/recurring/${id}/${endpoint}/`)
      fetchRecurringData()
    } catch (err) {
      console.error('Failed to toggle ignore:', err)
    }
  }

  const fetchLinkedTransactions = async (recurringId) => {
    setLoadingLinked(true)
    try {
      const res = await axios.get(`/api/banking/recurring/${recurringId}/linked_transactions/`)
      setLinkedTransactions(res.data.transactions || [])
      setSelectedRecurring(res.data)
    } catch (err) {
      console.error('Failed to load linked transactions:', err)
      setError('Failed to load linked transactions')
    } finally {
      setLoadingLinked(false)
    }
  }

  const closeLinkedModal = () => {
    setSelectedRecurring(null)
    setLinkedTransactions([])
  }

  const totalPages = Math.max(1, Math.ceil(totalCount / itemsPerPage))
  const canPrev = currentPage > 1
  const canNext = currentPage < totalPages

  if (!selectedAccount) {
    return (
      <div className="p-6 text-center">
        <p className="text-gray-500">{t('recurring.noAccounts')}</p>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">{t('recurring.title')}</h1>
          <p className="text-gray-500">{t('recurring.description')}</p>
        </div>
        <button
          onClick={() => setShowDetectModal(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          🔍 {t('recurring.detectButton')}
        </button>
      </div>

      {/* Account Selector */}
      <div className="bg-white rounded-lg border border-gray-200 p-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          {t('recurring.selectAccount')}
        </label>
        <select
          value={selectedAccount}
          onChange={(e) => setSelectedAccount(parseInt(e.target.value))}
          className="w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          {accounts.map(acc => (
            <option key={acc.id} value={acc.id}>
              {acc.name} ({acc.currency})
            </option>
          ))}
        </select>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
          {error}
        </div>
      )}

      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <SummaryCard
            title={t('recurring.totalSubscriptions')}
            value={summary.total_count}
            icon="📊"
          />
          <SummaryCard
            title={t('recurring.activeSubscriptions')}
            value={summary.active_count}
            icon="✅"
          />
          <SummaryCard
            title={t('recurring.monthlyRecurring')}
            value={formatCurrency(summary.monthly_recurring_cost, summary.account_currency)}
            icon="📅"
            highlight
          />
          <SummaryCard
            title={t('recurring.yearlyRecurring')}
            value={formatCurrency(summary.yearly_recurring_cost, summary.account_currency)}
            icon="📈"
            highlight
          />
        </div>
      )}

      {/* Overdue Alert */}
      {summary && summary.overdue_count > 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <span className="text-2xl">⚠️</span>
            <div>
              <h3 className="font-semibold text-yellow-900">
                {t('recurring.overdueAlert', { count: summary.overdue_count })}
              </h3>
              <p className="text-sm text-yellow-800">
                {t('recurring.overdueDescription')}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="bg-white rounded-lg border border-gray-200 p-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {t('recurring.filterFrequency')}
            </label>
            <select
              value={filters.frequency}
              onChange={(e) => {
                setFilters({...filters, frequency: e.target.value})
                setCurrentPage(1)
              }}
              className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
            >
              <option value="">{t('recurring.allFrequencies')}</option>
              <option value="weekly">{t('recurring.weekly')}</option>
              <option value="bi-weekly">{t('recurring.biWeekly')}</option>
              <option value="monthly">{t('recurring.monthly')}</option>
              <option value="quarterly">{t('recurring.quarterly')}</option>
              <option value="yearly">{t('recurring.yearly')}</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {t('recurring.filterStatus')}
            </label>
            <select
              value={filters.is_active ? 'active' : 'all'}
              onChange={(e) => {
                setFilters({...filters, is_active: e.target.value === 'active'})
                setCurrentPage(1)
              }}
              className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
            >
              <option value="all">{t('recurring.allStatus')}</option>
              <option value="active">{t('recurring.activeOnly')}</option>
            </select>
          </div>

          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {t('recurring.search')}
            </label>
            <input
              type="text"
              placeholder={t('recurring.searchPlaceholder')}
              value={filters.search}
              onChange={(e) => {
                setFilters({...filters, search: e.target.value})
                setCurrentPage(1)
              }}
              className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
            />
          </div>
        </div>
      </div>

      {/* Frequency Breakdown */}
      {summary && (
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <h3 className="font-semibold text-gray-900 mb-4">{t('recurring.byFrequency')}</h3>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            {Object.entries(summary.by_frequency).map(([freq, data]) => (
              <div key={freq} className="text-center p-3 bg-gray-50 rounded">
                <div className="text-2xl mb-1">
                  {freq === 'weekly' && '📅'}
                  {freq === 'bi-weekly' && '📅📅'}
                  {freq === 'monthly' && '📆'}
                  {freq === 'quarterly' && '📊'}
                  {freq === 'yearly' && '📈'}
                </div>
                <div className="text-sm font-medium text-gray-900">
                  {t(`recurring.${freq}`)} ({data.count})
                </div>
                <div className="text-xs text-gray-500">
                  {getCurrencySymbol(summary.account_currency)} {data.total_amount}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recurring Transactions List */}
      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="font-semibold text-gray-900">
            {t('recurring.transactionsList')} ({totalCount})
          </h3>
        </div>

        {loading ? (
          <div className="p-8 text-center">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        ) : recurring.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            {t('recurring.noRecurring')}
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700">
                      {t('recurring.merchant')}
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700">
                      {t('recurring.frequency')}
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700">
                      {t('recurring.amount')}
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700">
                      {t('recurring.nextPayment')}
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700">
                      {t('recurring.confidence')}
                    </th>
                    <th className="px-6 py-3 text-center text-xs font-semibold text-gray-700">
                      {t('recurring.actions')}
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {recurring.map((txn) => (
                    <RecurringTransactionRow
                      key={txn.id}
                      transaction={txn}
                      currency={txn.account_currency}
                      onToggleIgnore={toggleIgnore}
                      onViewLinked={fetchLinkedTransactions}
                    />
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination Controls */}
            {totalPages > 1 && (
              <div className="px-6 py-4 border-t border-gray-200 flex items-center justify-between">
                <div className="text-sm text-gray-600">
                  {t('transactions.page')} <strong>{currentPage}</strong> {t('transactions.of')} <strong>{totalPages}</strong> ({totalCount} {t('transactions.items')})
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => setCurrentPage(1)}
                    disabled={!canPrev}
                    className="px-3 py-2 bg-gray-100 text-gray-700 rounded disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-200"
                    title={t('transactions.firstPage')}
                  >
                    ⏮
                  </button>
                  <button
                    onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                    disabled={!canPrev}
                    className="px-3 py-2 bg-gray-100 text-gray-700 rounded disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-200"
                  >
                    ← {t('transactions.previous')}
                  </button>
                  <button
                    onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                    disabled={!canNext}
                    className="px-3 py-2 bg-gray-100 text-gray-700 rounded disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-200"
                  >
                    {t('transactions.next')} →
                  </button>
                  <button
                    onClick={() => setCurrentPage(totalPages)}
                    disabled={!canNext}
                    className="px-3 py-2 bg-gray-100 text-gray-700 rounded disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-200"
                    title={t('transactions.lastPage')}
                  >
                    ⏭
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>

      {/* Detect Modal */}
      {showDetectModal && (
        <DetectModal
          onClose={() => setShowDetectModal(false)}
          onDetect={triggerDetection}
          detecting={detecting}
        />
      )}

      {/* Linked Transactions Modal */}
      {selectedRecurring && (
        <LinkedTransactionsModal
          recurring={selectedRecurring}
          transactions={linkedTransactions}
          loading={loadingLinked}
          onClose={closeLinkedModal}
        />
      )}
    </div>
  )
}

function SummaryCard({ title, value, icon, highlight }) {
  return (
    <div className={`rounded-lg p-6 ${highlight ? 'bg-blue-50 border border-blue-200' : 'bg-white border border-gray-200'}`}>
      <div className="text-3xl mb-2">{icon}</div>
      <p className="text-sm text-gray-600 mb-1">{title}</p>
      <p className={`text-2xl font-bold ${highlight ? 'text-blue-600' : 'text-gray-900'}`}>
        {value}
      </p>
    </div>
  )
}

function RecurringTransactionRow({ transaction, currency, onToggleIgnore, onViewLinked }) {
  const t = useTranslate()
  const [showNotes, setShowNotes] = useState(false)
  const [notes, setNotes] = useState(transaction.user_notes)

  const getFrequencyEmoji = (freq) => {
    switch(freq) {
      case 'weekly': return '📅'
      case 'bi-weekly': return '📅📅'
      case 'monthly': return '📆'
      case 'quarterly': return '📊'
      case 'yearly': return '📈'
      default: return '💳'
    }
  }

  const getConfidenceColor = (score) => {
    if (score >= 0.9) return 'bg-green-100 text-green-700'
    if (score >= 0.75) return 'bg-blue-100 text-blue-700'
    if (score >= 0.6) return 'bg-yellow-100 text-yellow-700'
    return 'bg-gray-100 text-gray-700'
  }

  return (
    <tr className="border-b border-gray-100 hover:bg-gray-50">
      <td className="px-6 py-4">
        <div>
          <div className="font-medium text-gray-900">{transaction.display_name}</div>
          <div className="text-xs text-gray-500">{transaction.description}</div>
        </div>
      </td>
      <td className="px-6 py-4 whitespace-nowrap">
        <div className="flex items-center gap-2">
          <span>{getFrequencyEmoji(transaction.frequency)}</span>
          <span className="text-sm font-medium text-gray-700">
            {t(`recurring.${transaction.frequency}`)}
          </span>
        </div>
      </td>
      <td className="px-6 py-4 whitespace-nowrap">
        <div className="text-sm font-medium text-gray-900">{formatCurrency(transaction.amount, currency)}</div>
        <div className="text-xs text-gray-500">{formatCurrency(transaction.monthly_cost, currency)}/mo</div>
      </td>
      <td className="px-6 py-4 whitespace-nowrap">
        <div className={`text-sm font-medium ${transaction.is_overdue ? 'text-red-600' : 'text-gray-900'}`}>
          {formatDate(transaction.next_expected_date)}
        </div>
        <div className={`text-xs ${transaction.is_overdue ? 'text-red-500' : 'text-gray-500'}`}>
          {transaction.is_overdue ? '⚠️ Overdue' : `${transaction.days_until_next} days`}
        </div>
      </td>
      <td className="px-6 py-4 whitespace-nowrap">
        <div className={`inline-block px-3 py-1 rounded-full text-xs font-medium ${getConfidenceColor(transaction.confidence_score)}`}>
          {(transaction.confidence_score * 100).toFixed(0)}%
        </div>
      </td>
      <td className="px-6 py-4 text-center whitespace-nowrap">
        <div className="flex items-center justify-center gap-2">
          <button
            onClick={() => onViewLinked(transaction.id)}
            className="px-2 py-1 text-xs bg-purple-100 text-purple-700 rounded hover:bg-purple-200"
            title="View linked transactions"
          >
            🔗
          </button>
          <button
            onClick={() => onToggleIgnore(transaction.id, transaction.is_ignored)}
            className={`px-2 py-1 text-xs rounded ${
              transaction.is_ignored
                ? 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                : 'bg-blue-100 text-blue-700 hover:bg-blue-200'
            }`}
            title={transaction.is_ignored ? 'Unignore' : 'Ignore'}
          >
            {transaction.is_ignored ? '🔄' : '🚫'}
          </button>
          <button
            onClick={() => setShowNotes(!showNotes)}
            className="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
            title="Add note"
          >
            📝
          </button>
        </div>
        {showNotes && (
          <div className="mt-2 p-2 bg-gray-50 rounded text-left">
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Add a note..."
              className="w-full text-xs border border-gray-300 rounded p-2"
              rows="2"
            />
          </div>
        )}
      </td>
    </tr>
  )
}

function DetectModal({ onClose, onDetect, detecting }) {
  const t = useTranslate()

  return (
    <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-lg w-full max-w-md p-6">
        <h3 className="text-lg font-bold text-gray-900 mb-4">
          🔍 {t('recurring.detectRecurring')}
        </h3>

        <p className="text-gray-600 mb-6">
          {t('recurring.detectDescription')}
        </p>

        <div className="space-y-4 mb-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {t('recurring.lookBackDays')}
            </label>
            <div className="text-sm text-gray-500">
              1825 {t('recurring.days')} (5 {t('recurring.years')})
            </div>
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded p-3 text-sm text-blue-800">
            ℹ️ This detector analyzes 5 years of transaction history to identify recurring patterns including yearly subscriptions and annual fees.
          </div>
        </div>

        <div className="flex gap-3">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2 bg-gray-100 text-gray-900 rounded-lg hover:bg-gray-200 font-medium text-sm"
          >
            {t('recurring.cancel')}
          </button>
          <button
            onClick={onDetect}
            disabled={detecting}
            className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 font-medium text-sm flex items-center justify-center gap-2"
          >
            {detecting && <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></div>}
            {detecting ? t('recurring.detecting') : t('recurring.startDetection')}
          </button>
        </div>
      </div>
    </div>
  )
}

function LinkedTransactionsModal({ recurring, transactions, loading, onClose }) {
  const t = useTranslate()

  return (
    <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-lg w-full max-w-4xl max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <div>
            <h3 className="text-lg font-bold text-gray-900">
              🔗 {t('recurring.linkedTransactions')}
            </h3>
            <p className="text-sm text-gray-600 mt-1">
              {recurring.recurring_description} ({recurring.recurring_frequency})
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            ✕
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {loading ? (
            <div className="flex justify-center items-center h-32">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          ) : transactions.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              {t('recurring.noLinkedTransactions')}
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700">
                      {t('transactions.date')}
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700">
                      {t('transactions.description')}
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700">
                      {t('transactions.reference')}
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-semibold text-gray-700">
                      {t('transactions.amount')}
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700">
                      {t('transactions.category')}
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {transactions.map((txn) => (
                    <tr key={txn.id} className="border-b border-gray-100 hover:bg-gray-50">
                      <td className="px-4 py-3 whitespace-nowrap text-sm">
                        {formatDate(txn.date)}
                      </td>
                      <td className="px-4 py-3 text-sm max-w-xs truncate">
                        {txn.description}
                      </td>
                      <td className="px-4 py-3 text-sm max-w-xs truncate text-gray-600">
                        {txn.reference}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-right font-medium">
                        <span className={txn.amount >= 0 ? 'text-green-600' : 'text-red-600'}>
                          {txn.amount >= 0 ? '+' : ''}{txn.amount} {txn.account_currency}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-sm">
                        {txn.category_name ? (
                          <span
                            className="inline-block px-2 py-1 rounded-full text-xs font-medium text-white"
                            style={{ backgroundColor: txn.category_color || '#666' }}
                          >
                            {txn.category_name}
                          </span>
                        ) : (
                          <span className="text-gray-400">-</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-200 flex items-center justify-between bg-gray-50">
          <div className="text-sm text-gray-600">
            {t('recurring.total')}: <strong>{transactions.length}</strong> {t('recurring.transactions')}
          </div>
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-300 text-gray-900 rounded-lg hover:bg-gray-400 font-medium text-sm"
          >
            {t('recurring.close')}
          </button>
        </div>
      </div>
    </div>
  )
}
