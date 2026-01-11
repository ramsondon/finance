import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { getCsrfToken } from '../utils/csrf'

export default function ImportModal({ onClose }) {
  const [accounts, setAccounts] = useState([])
  const [selectedAccount, setSelectedAccount] = useState('')
  const [file, setFile] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)

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

  useEffect(() => {
    axios.get('/api/banking/accounts/')
      .then(res => {
        const accts = res.data.results || res.data || []
        setAccounts(accts)
        if (accts.length > 0) setSelectedAccount(accts[0].id)
      })
      .catch(() => setAccounts([]))
  }, [])

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!file || !selectedAccount) return

    setUploading(true)
    setError(null)
    setResult(null)
    setSuccess(null)

    const formData = new FormData()
    formData.append('file', file)
    formData.append('account', selectedAccount)

    try {
      // Use generic import endpoint
      const res = await axios.post('/api/banking/transactions/import-transactions/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
          'X-CSRFToken': getCsrfToken()
        }
      })
      setSuccess(`✅ Successfully imported ${res.data.queued} transactions (${res.data.file_type.toUpperCase()})`)
      setResult(res.data)
      setFile(null)
      setTimeout(() => onClose(), 2500)
    } catch (err) {
      setError(err.response?.data?.message || err.message || 'Import failed')
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-lg w-full max-w-md border border-gray-200">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Import Transactions</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">✕</button>
        </div>
        <div className="p-6">
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Account Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Bank Account
              </label>
              <select
                value={selectedAccount}
                onChange={(e) => setSelectedAccount(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              >
                {accounts.length === 0 ? (
                  <option value="">No accounts available</option>
                ) : (
                  accounts.map(acc => (
                    <option key={acc.id} value={acc.id}>
                      {acc.name} ({acc.currency})
                    </option>
                  ))
                )}
              </select>
            </div>

            {/* File Upload */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                File (CSV or JSON)
              </label>
              <div className="relative">
                <input
                  type="file"
                  accept=".csv,.json"
                  onChange={(e) => setFile(e.target.files[0])}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
              <p className="mt-2 text-xs text-gray-500 space-y-1">
                <div>📄 <strong>CSV Format:</strong> date, amount, description, type, category (optional)</div>
                <div>📋 <strong>JSON Format:</strong> Array of transaction objects with banking fields</div>
              </p>
            </div>

            {/* Success Message */}
            {success && (
              <div className="bg-green-50 border border-green-200 rounded-lg p-3 text-sm text-green-700">
                {success}
              </div>
            )}

            {/* Error Message */}
            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700">
                {error}
              </div>
            )}

            {/* Import Results */}
            {result && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-sm text-blue-700">
                <div className="font-medium mb-1">Import Complete</div>
                <div>✓ Queued {result.queued} transactions</div>
                {result.errors?.length > 0 && (
                  <div className="mt-2 text-red-600">
                    ⚠️ {result.errors.length} rows had errors
                  </div>
                )}
                {result.file_type && (
                  <div className="mt-1 text-xs">Format: {result.file_type.toUpperCase()}</div>
                )}
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex gap-3">
              <button
                type="submit"
                disabled={uploading || !file || !selectedAccount}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium transition-colors"
              >
                {uploading ? '⏳ Importing...' : '📤 Import'}
              </button>
              <button
                type="button"
                onClick={onClose}
                className="flex-1 px-4 py-2 bg-gray-100 text-gray-900 rounded-lg hover:bg-gray-200 font-medium transition-colors"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}

