import React, { useEffect, useState } from 'react'
import axios from 'axios'
import { getCsrfToken } from '../utils/csrf'
import { SensitiveValue, useSensitiveModeListener } from '../utils/sensitive'
import { useTranslate } from '../hooks/useLanguage'
import { formatDate, formatDateTime } from '../utils/format'

export default function TransactionsTable() {
  const t = useTranslate()
  const [transactions, setTransactions] = useState([])
  const [loading, setLoading] = useState(true)
  const [totalCount, setTotalCount] = useState(0)
  const [currentPage, setCurrentPage] = useState(1)
  const itemsPerPage = 25
  const [categories, setCategories] = useState([])
  const [filters, setFilters] = useState({ search: '', type: '', category: '', categoryUnknown: false })
  const [editingTransaction, setEditingTransaction] = useState(null)
  const sensitiveMode = useSensitiveModeListener()

  // Load categories for filter dropdown
  useEffect(() => {
    axios.get('/api/banking/categories/', {
      params: { page_size: 1000 }
    })
      .then(res => {
        const results = res.data.results || res.data || []
        setCategories(results)
      })
      .catch((err) => {
        console.error('Error loading categories:', err)
        setCategories([])
      })
  }, [])

  // Initialize from URL hash (supports category filter and "unknown")
  useEffect(() => {
    const applyHash = () => {
      const hash = window.location.hash.replace('#','')
      const params = new URLSearchParams(hash)
      const cat = params.get('category')
      if (cat) {
        if (cat === 'unknown') {
          setFilters((f) => ({ ...f, category: '', categoryUnknown: true }))
        } else {
          setFilters((f) => ({ ...f, category: cat, categoryUnknown: false }))
        }
        setCurrentPage(1)
      }
    }
    applyHash()
    window.addEventListener('hashchange', applyHash)
    return () => window.removeEventListener('hashchange', applyHash)
  }, [])

  useEffect(() => {
    loadTransactions()
  }, [filters, currentPage])

  const loadTransactions = () => {
    setLoading(true)
    const params = new URLSearchParams()
    if (filters.search) params.append('search', filters.search)
    if (filters.type) params.append('type', filters.type)
    if (filters.category && !filters.categoryUnknown) params.append('category', filters.category)
    if (filters.categoryUnknown) params.append('category__isnull', 'true')
    params.append('page', String(currentPage))
    params.append('page_size', String(itemsPerPage))
    params.append('ordering', '-date')

    axios.get(`/api/banking/transactions/?${params.toString()}`)
      .then(res => {
        const data = res.data
        const results = data.results || []
        setTransactions(results)
        setTotalCount(data.count || results.length || 0)
        setLoading(false)
      })
      .catch(() => {
        setTransactions([])
        setTotalCount(0)
        setLoading(false)
      })
  }

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

  const totalPages = Math.max(1, Math.ceil(totalCount / itemsPerPage))
  const canPrev = currentPage > 1
  const canNext = currentPage < totalPages

  return (
    <div className="space-y-6">
      {/* Filters Card */}
      <div className="bg-white rounded-2xl shadow-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">{t('transactions.filters')}</h3>
          <button
            onClick={() => { setCurrentPage(1); loadTransactions() }}
            className="px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors font-medium text-sm"
          >
            🔄 {t('transactions.refresh')}
          </button>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">{t('transactions.search')}</label>
            <div className="relative">
              <span className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400">🔍</span>
              <input
                type="text"
                value={filters.search}
                onChange={(e) => setFilters({...filters, search: e.target.value})}
                placeholder={t('transactions.searchPlaceholder')}
                className="w-full pl-10 pr-4 py-2.5 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all"
              />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">{t('transactions.typeFilter')}</label>
            <select
              value={filters.type}
              onChange={(e) => { setFilters({...filters, type: e.target.value}); setCurrentPage(1) }}
              className="w-full px-4 py-2.5 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all"
            >
              <option value="">{t('transactions.allTypes')}</option>
              <option value="income">{t('transactions.income')}</option>
              <option value="expense">{t('transactions.expense')}</option>
              <option value="transfer">{t('transactions.transfer')}</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">{t('transactions.categoryFilter')}</label>
            <select
              value={filters.categoryUnknown ? 'unknown' : (filters.category || '')}
              onChange={(e) => {
                const val = e.target.value
                if (val === '') {
                  setFilters({...filters, category: '', categoryUnknown: false})
                } else if (val === 'unknown') {
                  setFilters({...filters, category: '', categoryUnknown: true})
                } else {
                  setFilters({...filters, category: val, categoryUnknown: false})
                }
                setCurrentPage(1)
              }}
              className="w-full px-4 py-2.5 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all"
            >
              <option value="">{t('transactions.allCategories')}</option>
              <option value="unknown">{t('transactions.unknown')}</option>
              {categories.map(cat => (
                <option key={cat.id} value={cat.id}>{cat.name}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Transactions Table */}
      <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200 bg-gradient-to-r from-gray-50 to-white">
          <h3 className="text-lg font-semibold text-gray-900">{t('transactions.title')}</h3>
          <p className="text-sm text-gray-500 mt-1">
            {totalCount === 1 ? t('transactions.transactionsFound').replace('{count}', '1') : t('transactions.transactionsFound').replace('{count}', totalCount)}
          </p>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="relative">
              <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-blue-600"></div>
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="w-8 h-8 bg-blue-600 rounded-full opacity-20 animate-pulse"></div>
              </div>
            </div>
          </div>
        ) : totalCount === 0 ? (
          <div className="text-center py-20 bg-gradient-to-br from-gray-50 to-white">
            <div className="text-6xl mb-4">💳</div>
            <h3 className="text-xl font-semibold text-gray-700 mb-2">{t('transactions.noTransactionsFound')}</h3>
            <p className="text-gray-500">{t('transactions.importCSV')}</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">{t('transactions.date')}</th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">{t('transactions.fieldReference')}</th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">{t('transactions.category')}</th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">{t('transactions.type')}</th>
                  <th className="px-6 py-4 text-right text-xs font-semibold text-gray-600 uppercase tracking-wider">{t('transactions.amount')}</th>
                  <th className="px-6 py-4 text-center text-xs font-semibold text-gray-600 uppercase tracking-wider">{t('transactions.actions')}</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-100">
                {transactions.map(tx => (
                  <tr key={tx.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">
                        {formatDate(tx.date)}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm text-gray-900 font-medium truncate max-w-xs" title={tx.description || '-'}>{tx.reference || '-'}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {tx.category_name ? (
                        <span
                          className="px-3 py-1 text-xs font-medium rounded-full border"
                          style={{ borderColor: tx.category_color, color: tx.category_color }}
                          title={tx.category_name}
                        >
                          {tx.category_name}
                        </span>
                      ) : (
                        <span className="text-sm text-gray-400">-</span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex items-center px-3 py-1 text-xs font-semibold rounded-full border ${getTypeColor(tx.type)}`}>
                        {/*<span className="mr-1">{getTypeIcon(tx.type)}</span>*/}
                        {t(`transactions.${tx.type}`)}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right">
                      <div className={`text-sm font-bold ${
                        tx.type === 'income' ? 'text-green-600' : tx.type === 'expense' ? 'text-red-600' : 'text-gray-900'
                      }`}>
                        <SensitiveValue
                          value={`${tx.type === 'income' ? '+' : tx.type === 'expense' ? '-' : ''}${tx.account_currency || 'EUR'} ${Math.abs(tx.amount).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`}
                          sensitiveMode={sensitiveMode}
                        />
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-center">
                      <button
                        onClick={() => setEditingTransaction(tx)}
                        className="px-2 py-1 text-xs font-medium bg-blue-100 text-blue-700 rounded hover:bg-blue-200 transition-colors"
                      >
                        {t('transactions.edit')}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination */}
        <div className="flex items-center justify-between px-6 py-4 border-t border-gray-200 bg-white">
          <div className="text-sm text-gray-600">{t('transactions.pageOf', { current: currentPage, total: totalPages, count: totalCount })}</div>
          <div className="flex gap-2">
            <button
              onClick={() => canPrev && setCurrentPage(p => Math.max(1, p - 1))}
              disabled={!canPrev}
              className="px-3 py-1 border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50"
            >{t('transactions.previousPage')}</button>
            <button
              onClick={() => canNext && setCurrentPage(p => Math.min(totalPages, p + 1))}
              disabled={!canNext}
              className="px-3 py-1 border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50"
            >{t('transactions.nextPage')}</button>
          </div>
        </div>
      </div>

      {/* Edit Transaction Modal */}
      {editingTransaction && (
        <EditTransactionModal
          transaction={editingTransaction}
          categories={categories}
          sensitiveMode={sensitiveMode}
          onClose={() => setEditingTransaction(null)}
          onSuccess={() => {
            setEditingTransaction(null)
            loadTransactions()
          }}
        />
      )}
    </div>
  )
}

function EditTransactionModal({ transaction, categories, onClose, onSuccess, sensitiveMode }) {
  const t = useTranslate()
  const [selectedCategory, setSelectedCategory] = useState(transaction.category || null)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)

  // ESC key handler
  useEffect(() => {
    const handleEsc = (e) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', handleEsc)
    return () => window.removeEventListener('keydown', handleEsc)
  }, [onClose])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSubmitting(true)
    setError(null)

    try {
      await axios.patch(`/api/banking/transactions/${transaction.id}/`,
        { category: selectedCategory },
        { headers: { 'X-CSRFToken': getCsrfToken() } }
      )
      onSuccess()
    } catch (err) {
      setError(err.response?.data?.message || err.message || 'Failed to update transaction')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md">
        <div className="border-b border-gray-200 px-6 py-4 flex items-center justify-between">
          <h3 className="text-lg font-bold text-gray-900">{t('transactionEdit.title')}</h3>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700 text-2xl">✕</button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {/* Transaction Info */}
          <div className="bg-gray-50 rounded-lg p-4 text-sm space-y-3">
            <div>
              <span className="text-gray-600 block mb-1">{t('transactionEdit.date')}</span>
              <span className="font-medium">{formatDate(transaction.date)}</span>
            </div>
            <div>
              <span className="text-gray-600 block mb-1">{t('transactionEdit.description')}</span>
              <span className="font-medium text-gray-900 break-words">{transaction.description || '-'}</span>
            </div>
            <div>
              <span className="text-gray-600 block mb-1">{t('transactionEdit.amount')}</span>
              <span className={`font-medium ${
                transaction.type === 'income' ? 'text-green-600' : transaction.type === 'expense' ? 'text-red-600' : 'text-gray-900'
              }`}>
                <SensitiveValue
                  value={`${transaction.type === 'income' ? '+' : transaction.type === 'expense' ? '-' : ''}${transaction.account_currency || 'EUR'} ${Math.abs(transaction.amount).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`}
                  sensitiveMode={sensitiveMode}
                />
              </span>
            </div>
          </div>

          {/* Category Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {t('transactionEdit.category')}
            </label>
            <select
              value={selectedCategory || ''}
              onChange={(e) => setSelectedCategory(e.target.value ? parseInt(e.target.value) : null)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">{t('transactionEdit.unknownUncategorized')}</option>
              {categories.map(cat => (
                <option key={cat.id} value={cat.id}>{cat.name}</option>
              ))}
            </select>
            <p className="text-xs text-gray-500 mt-1">{t('transactionEdit.selectCategory')}</p>
          </div>

          {/* Error Message */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700">
              {error}
            </div>
          )}

          {/* Buttons */}
          <div className="flex gap-3 pt-2 border-t border-gray-200">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 bg-gray-100 text-gray-900 rounded-lg hover:bg-gray-200 font-medium text-sm"
            >
              {t('transactionEdit.cancel')}
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 font-medium text-sm"
            >
              {submitting ? t('transactionEdit.saving') : t('transactionEdit.saveChanges')}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
