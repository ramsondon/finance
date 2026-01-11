import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { getCsrfToken } from '../utils/csrf'

export default function CreateAccountModal({ onClose, onCreated }) {
  const [form, setForm] = useState({
    name: '',
    institution: '',
    iban: '',
    currency: 'USD',
    opening_balance: '', // keep as string for Decimal precision on backend
    opening_balance_date: '', // optional reference date
  })
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)
  const [currencies, setCurrencies] = useState(["USD", "EUR", "GBP", "CHF", "JPY"]) // fallback

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
    let mounted = true
    // Try fetching currencies from backend. Expected shape: { currencies: ["USD", "EUR", ...] }
    axios.get('/api/banking/currencies').then(res => {
      if (!mounted) return
      const list = res.data?.currencies || res.data || []
      if (Array.isArray(list) && list.length) {
        setCurrencies(list)
        // If current currency not in list, default to first
        if (!list.includes(form.currency)) {
          setForm(prev => ({ ...prev, currency: list[0] }))
        }
      }
    }).catch(() => {
      // Ignore and keep fallback
    })
    return () => { mounted = false }
  }, [])

  const handleChange = (e) => {
    const { name, value } = e.target
    setForm(prev => ({ ...prev, [name]: value }))
  }

  // Simple Decimal validation: optional, but if present must be a valid decimal with up to 2 places
  const isValidDecimal = (v) => {
    if (v === '' || v === null || v === undefined) return true
    return /^-?\d{0,15}(\.\d{1,2})?$/.test(String(v))
  }

  const isFormValid = () => {
    return (
      form.name.trim().length > 0 &&
      form.currency &&
      isValidDecimal(form.opening_balance)
    )
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!isFormValid()) return
    setSubmitting(true)
    setError(null)
    try {
      // Preserve Decimal precision by sending as string; backend should use DecimalField
      const payload = {
        name: form.name.trim(),
        institution: form.institution.trim(),
        iban: form.iban.trim(),
        currency: form.currency,
        opening_balance: form.opening_balance === '' ? '0' : String(form.opening_balance),
        opening_balance_date: form.opening_balance_date || null,
      }

      const csrfToken = getCsrfToken()
      const resp = await axios.post('/api/banking/accounts/', payload, {
        headers: {
          'X-CSRFToken': csrfToken,
        }
      })
      setSuccess('Account created successfully')
      // Tiny delay to show toast then notify parent
      setTimeout(() => {
        setSuccess(null)
        onCreated?.(resp.data)
      }, 800)
    } catch (err) {
      const msg = err?.response?.data?.detail || err?.message || 'Failed to create account'
      setError(msg)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-lg w-full max-w-md border border-gray-200">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Create Bank Account</h3>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">✕</button>
        </div>
        <form onSubmit={handleSubmit} className="px-6 py-4 space-y-4">
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 rounded p-3 text-sm">
              {error}
            </div>
          )}
          {success && (
            <div className="bg-green-50 border border-green-200 text-green-700 rounded p-3 text-sm">
              {success}
            </div>
          )}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Account Name</label>
            <input
              type="text"
              name="name"
              value={form.name}
              onChange={handleChange}
              placeholder="e.g., Checking, Savings"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Institution</label>
            <input
              type="text"
              name="institution"
              value={form.institution}
              onChange={handleChange}
              placeholder="e.g., Bank of America"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">IBAN</label>
            <input
              type="text"
              name="iban"
              value={form.iban}
              onChange={handleChange}
              placeholder="e.g., DE89370400440532013000"
              maxLength="34"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Currency</label>
              <select
                name="currency"
                value={form.currency}
                onChange={handleChange}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              >
                {currencies.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Opening Balance</label>
              <input
                type="text"
                inputMode="decimal"
                name="opening_balance"
                value={form.opening_balance}
                onChange={handleChange}
                placeholder="0.00"
                className={`w-full border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 ${
                  isValidDecimal(form.opening_balance)
                    ? 'border-gray-300 focus:ring-blue-500'
                    : 'border-red-300 focus:ring-red-500'
                }`}
              />
              {!isValidDecimal(form.opening_balance) && (
                <p className="text-xs text-red-600 mt-1">Please enter a valid amount (up to 2 decimal places).</p>
              )}
            </div>
          </div>

          {/* Opening Balance Date - Optional */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Opening Balance Reference Date (Optional)
            </label>
            <input
              type="date"
              name="opening_balance_date"
              value={form.opening_balance_date}
              onChange={handleChange}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <p className="text-xs text-gray-500 mt-1">
              💡 Set a reference date when you know your account balance. Leave empty if you have complete transaction history.
            </p>
            <p className="text-xs text-gray-400 mt-1">
              Example: If you know your balance was €5,000 two weeks ago, enter that date. Then import transactions from that date onward.
            </p>
          </div>

          <div className="flex items-center justify-end space-x-3 pt-2">
            <button type="button" onClick={onClose} className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-800 rounded-lg">Cancel</button>
            <button type="submit" disabled={submitting || !isFormValid()} className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50">
              {submitting ? 'Creating…' : 'Create Account'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
