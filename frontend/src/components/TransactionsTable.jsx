import React, { useEffect, useState } from 'react'
import axios from 'axios'

export default function TransactionsTable() {
  const [transactions, setTransactions] = useState([])
  const [loading, setLoading] = useState(true)
  const [filters, setFilters] = useState({ search: '', type: '' })

  useEffect(() => {
    loadTransactions()
  }, [filters])

  const loadTransactions = () => {
    setLoading(true)
    const params = new URLSearchParams()
    if (filters.search) params.append('search', filters.search)
    if (filters.type) params.append('type', filters.type)

    axios.get(`/api/banking/transactions/?${params}`)
      .then(res => {
        setTransactions(res.data.results || res.data || [])
        setLoading(false)
      })
      .catch(() => {
        setTransactions([])
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

  return (
    <div className="space-y-6">
      {/* Filters Card */}
      <div className="bg-white rounded-2xl shadow-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Filters</h3>
          <button
            onClick={loadTransactions}
            className="px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors font-medium text-sm"
          >
            🔄 Refresh
          </button>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Search</label>
            <div className="relative">
              <span className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400">🔍</span>
              <input
                type="text"
                value={filters.search}
                onChange={(e) => setFilters({...filters, search: e.target.value})}
                placeholder="Search descriptions..."
                className="w-full pl-10 pr-4 py-2.5 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all"
              />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Type</label>
            <select
              value={filters.type}
              onChange={(e) => setFilters({...filters, type: e.target.value})}
              className="w-full px-4 py-2.5 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all"
            >
              <option value="">All Types</option>
              <option value="income">📈 Income</option>
              <option value="expense">📉 Expense</option>
              <option value="transfer">↔️ Transfer</option>
            </select>
          </div>
        </div>
      </div>

      {/* Transactions Table */}
      <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200 bg-gradient-to-r from-gray-50 to-white">
          <h3 className="text-lg font-semibold text-gray-900">Transactions</h3>
          <p className="text-sm text-gray-500 mt-1">
            {transactions.length} {transactions.length === 1 ? 'transaction' : 'transactions'} found
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
        ) : transactions.length === 0 ? (
          <div className="text-center py-20 bg-gradient-to-br from-gray-50 to-white">
            <div className="text-6xl mb-4">💳</div>
            <h3 className="text-xl font-semibold text-gray-700 mb-2">No transactions found</h3>
            <p className="text-gray-500">Import a CSV to get started with transaction tracking</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Date</th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Description</th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Category</th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Type</th>
                  <th className="px-6 py-4 text-right text-xs font-semibold text-gray-600 uppercase tracking-wider">Amount</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-100">
                {transactions.map(tx => (
                  <tr key={tx.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">
                        {new Date(tx.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm text-gray-900 font-medium">{tx.description || '-'}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {tx.category ? (
                        <span className="px-3 py-1 text-xs font-medium bg-purple-100 text-purple-700 rounded-full border border-purple-200">
                          {tx.category}
                        </span>
                      ) : (
                        <span className="text-sm text-gray-400">-</span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex items-center px-3 py-1 text-xs font-semibold rounded-full border ${getTypeColor(tx.type)}`}>
                        <span className="mr-1">{getTypeIcon(tx.type)}</span>
                        {tx.type}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right">
                      <div className={`text-sm font-bold ${
                        tx.type === 'income' ? 'text-green-600' : tx.type === 'expense' ? 'text-red-600' : 'text-gray-900'
                      }`}>
                        {tx.type === 'income' ? '+' : tx.type === 'expense' ? '-' : ''}{tx.account_currency || 'EUR'} {Math.abs(tx.amount).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

