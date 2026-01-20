import React, { useEffect, useState } from 'react'
import axios from 'axios'
import { getCsrfToken } from '../utils/csrf'
import { useTranslate } from '../hooks/useLanguage'
import { dateToInputFormat, inputDateToISO } from '../utils/format'
import DateInput from './DateInput'
import { X, Zap } from 'lucide-react'

export default function RulesManager({ darkMode = false }) {
  const t = useTranslate()
  const [rules, setRules] = useState([])
  const [categories, setCategories] = useState([])
  const [loading, setLoading] = useState(true)
  const [applying, setApplying] = useState(false)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [editRule, setEditRule] = useState(null) // holds rule object to edit
  const [showGenerateModal, setShowGenerateModal] = useState(false)
  const [generateLoading, setGenerateLoading] = useState(false)
  const [generateTaskId, setGenerateTaskId] = useState(null)
  const [generateError, setGenerateError] = useState(null)
  const [generateResult, setGenerateResult] = useState(null)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = () => {
    setLoading(true)
    Promise.all([
      axios.get('/api/banking/rules/').catch(() => ({ data: [] })),
      axios.get('/api/banking/categories/').catch(() => ({ data: [] }))
    ]).then(([rulesRes, catsRes]) => {
      setRules(rulesRes.data.results || rulesRes.data || [])
      setCategories(catsRes.data.results || catsRes.data || [])
      setLoading(false)
    })
  }

  const applyRules = async () => {
    setApplying(true)
    try {
      await axios.post('/api/banking/transactions/apply-rules/')
      alert(t('rules.rulesAppliedSuccess'))
    } catch (err) {
      alert(t('rules.errorApplying') + ' ' + (err.response?.data?.message || err.message))
    } finally {
      setApplying(false)
    }
  }

  const toggleRule = async (ruleId, currentActive) => {
    try {
      await axios.patch(`/api/banking/rules/${ruleId}/`, { active: !currentActive }, {
        headers: { 'X-CSRFToken': getCsrfToken() }
      })
      loadData()
    } catch (err) {
      alert(t('rules.errorUpdating'))
    }
  }

  const deleteRule = async (ruleId) => {
    if (!confirm(t('rules.deleteConfirm'))) return
    try {
      await axios.delete(`/api/banking/rules/${ruleId}/`, {
        headers: { 'X-CSRFToken': getCsrfToken() }
      })
      loadData()
    } catch (err) {
      alert(t('rules.errorDeleting'))
    }
  }

  const startRuleGeneration = async () => {
    setGenerateLoading(true)
    setGenerateError(null)
    setGenerateResult(null)
    try {
      const response = await axios.post('/api/banking/rules/generate/', {}, {
        headers: { 'X-CSRFToken': getCsrfToken() }
      })
      const taskId = response.data.task_id
      setGenerateTaskId(taskId)

      // Poll for task completion
      let completed = false
      let attempts = 0
      const maxAttempts = 300  // 5 minutes with 1 second polling

      while (!completed && attempts < maxAttempts) {
        attempts++

        try {
          // Check task status using generic endpoint
          const statusResponse = await axios.get(`/api/task-status/${taskId}`, {
            headers: { 'X-CSRFToken': getCsrfToken() }
          })

          const taskStatus = statusResponse.data.status

          if (taskStatus === 'SUCCESS') {
            // Task completed successfully, reload rules
            await loadData()
            completed = true
            const result = statusResponse.data.result
            setGenerateResult({
              message: t('rules.generateModal.success', { count: result.created_count }),
              data: result
            })
            // DO NOT auto-close - user should manually close modal
          } else if (taskStatus === 'FAILURE') {
            // Task failed
            setGenerateError(statusResponse.data.error || t('rules.generateModal.generationError'))
            completed = true
          } else if (taskStatus === 'PENDING' || taskStatus === 'PROGRESS') {
            // Still processing - wait and retry
            await new Promise(resolve => setTimeout(resolve, 1000))
          }
        } catch (err) {
          setGenerateError(t('rules.generateModal.generationError') + ': ' + (err.response?.data?.message || err.message))
          completed = true
        }
      }

      if (!completed) {
        setGenerateError('Request timeout after 5 minutes')
      }
    } catch (err) {
      setGenerateError(t('rules.generateModal.generationError') + ': ' + (err.response?.data?.message || err.message))
    } finally {
      setGenerateLoading(false)
    }
  }

  // ESC key handler for modal
  useEffect(() => {
    const handleEscKey = (e) => {
      if (e.key === 'Escape' && showGenerateModal) {
        setShowGenerateModal(false)
        // Reset all modal state when closing via ESC
        setGenerateLoading(false)
        setGenerateTaskId(null)
        setGenerateError(null)
        setGenerateResult(null)
      }
    }
    if (showGenerateModal) {
      document.addEventListener('keydown', handleEscKey)
      return () => {
        document.removeEventListener('keydown', handleEscKey)
      }
    }
  }, [showGenerateModal])

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">{t('rules.title')}</h2>
        <div className="flex gap-3">
          <button
            onClick={() => setShowCreateModal(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium"
          >
            {t('rules.createRule')}
          </button>
          <button
            onClick={() => setShowGenerateModal(true)}
            className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 font-medium flex items-center gap-2"
          >
            <Zap size={18} />
            {t('rules.generateFromCategories')}
          </button>
          <button
            onClick={applyRules}
            disabled={applying}
            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 font-medium"
          >
            {applying ? t('rules.applying') : t('rules.applyRulesNow')}
          </button>
        </div>
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-sm text-blue-700">
        <strong>{t('rules.howRulesWork')}</strong> {t('rules.howRulesDescription')}
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      ) : rules.length === 0 ? (
        <div className="bg-white rounded-lg border border-gray-200 p-8 text-center">
          <p className="text-gray-500 mb-4">{t('rules.noRulesEmpty')}</p>
          <button
            onClick={() => setShowCreateModal(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            {t('rules.createRule')}
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          {rules.map(rule => {
            const category = categories.find(c => c.id === rule.category)
            return (
              <div key={rule.id} className="bg-white rounded-lg border border-gray-200 p-4 shadow-sm">
                {/* ...existing code... */}
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      <h3 className="font-semibold text-gray-900">{rule.name}</h3>
                      <span className="text-xs px-2 py-1 bg-gray-100 text-gray-600 rounded">
                        Priority: {rule.priority}
                      </span>
                      {category && (
                        <span
                          className="text-xs px-2 py-1 rounded text-white"
                          style={{ backgroundColor: category.color || '#3b82f6' }}
                        >
                          → {category.name}
                        </span>
                      )}
                    </div>
                    <div className="text-sm text-gray-600">
                      <strong>Conditions:</strong>
                      {rule.conditions?.description_contains && (
                        <span className="ml-2">Description contains "{rule.conditions.description_contains}"</span>
                      )}
                      {rule.conditions?.amount_min && (
                        <span className="ml-2">Amount ≥ ${rule.conditions.amount_min}</span>
                      )}
                      {rule.conditions?.amount_max && (
                        <span className="ml-2">Amount ≤ ${rule.conditions.amount_max}</span>
                      )}
                      {rule.conditions?.type && (
                        <span className="ml-2">Type: {rule.conditions.type}</span>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => toggleRule(rule.id, rule.active)}
                      className={`px-3 py-1 rounded text-sm font-medium ${
                        rule.active
                          ? 'bg-green-100 text-green-700'
                          : 'bg-gray-100 text-gray-600'
                      }`}
                    >
                      {rule.active ? 'Active' : 'Inactive'}
                    </button>
                    <button
                      onClick={() => setEditRule(rule)}
                      className="px-3 py-1 rounded text-sm font-medium bg-yellow-100 text-yellow-800 hover:bg-yellow-200"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => deleteRule(rule.id)}
                      className="p-2 text-red-600 hover:bg-red-50 rounded"
                    >
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </button>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* Create Rule Modal */}
      {showCreateModal && (
        <CreateRuleModal
          categories={categories}
          onClose={() => setShowCreateModal(false)}
          onSuccess={() => {
            setShowCreateModal(false)
            loadData()
          }}
        />
      )}

      {/* Edit Rule Modal */}
      {editRule && (
        <EditRuleModal
          rule={editRule}
          categories={categories}
          onClose={() => setEditRule(null)}
          onSuccess={() => { setEditRule(null); loadData() }}
        />
      )}

      {/* Generate Rules Modal */}
      {showGenerateModal && (
        <GenerateRulesModal
          onClose={() => {
            setShowGenerateModal(false)
            // Reset all modal state
            setGenerateLoading(false)
            setGenerateTaskId(null)
            setGenerateError(null)
            setGenerateResult(null)
          }}
          onGenerate={startRuleGeneration}
          loading={generateLoading}
          error={generateError}
          result={generateResult}
        />
      )}
    </div>
  )
}

function GenerateRulesModal({ onClose, onGenerate, loading, error, result }) {
  const t = useTranslate()

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-xl font-bold text-gray-900">{t('rules.generateModal.title')}</h3>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 text-2xl leading-none"
          >
            ×
          </button>
        </div>

        <p className="text-gray-600 text-sm">
          {t('rules.generateModal.description')}
        </p>

        {!loading && !error && !result && (
          <div className="py-4">
            <button
              onClick={onGenerate}
              className="w-full px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 font-medium flex items-center justify-center gap-2"
            >
              <Zap size={18} />
              {t('rules.generateFromCategories')}
            </button>
          </div>
        )}

        {loading && (
          <div className="space-y-3 py-4">
            <div className="flex items-center space-x-3">
              <div className="animate-spin rounded-full h-5 w-5 border-2 border-purple-600 border-t-transparent"></div>
              <span className="text-gray-700 text-sm">{t('rules.generateModal.analyzing')}</span>
            </div>
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-sm text-red-700">
            {error}
          </div>
        )}

        {result && (
          <div className="space-y-3 py-4">
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <p className="text-sm text-green-700 font-medium">{result.message}</p>
            </div>
            <div className="flex gap-2">
              <button
                onClick={onClose}
                className="flex-1 px-4 py-2 bg-gray-100 text-gray-900 rounded-lg hover:bg-gray-200 font-medium"
              >
                {t('rules.generateModal.close')}
              </button>
            </div>
          </div>
        )}

        {!loading && !result && (
          <div className="flex justify-end">
            <button
              onClick={onClose}
              className="px-4 py-2 bg-gray-100 text-gray-900 rounded-lg hover:bg-gray-200 font-medium"
            >
              {t('rules.generateModal.close')}
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

function CreateRuleModal({ categories, onClose, onSuccess }) {
  const [form, setForm] = useState({
    name: '',
    category: categories[0]?.id || '',
    priority: 100,
    active: true,
    // Conditions
    description_contains: '',
    amount_min: '',
    amount_max: '',
    date_from: '',
    date_to: '',
    type: '',
  })
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)

  // ESC key handler
  useEffect(() => {
    const handleEsc = (e) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', handleEsc)
    return () => window.removeEventListener('keydown', handleEsc)
  }, [onClose])

  const handleSubmit = async (e) => {
    e.preventDefault()

    if (!form.name.trim() || !form.category) {
      setError('Name and category are required')
      return
    }

    setSubmitting(true)
    setError(null)

    // Build conditions object (only include non-empty values)
    const conditions = {}
    if (form.description_contains) conditions.description_contains = form.description_contains
    if (form.amount_min) conditions.amount_min = parseFloat(form.amount_min)
    if (form.amount_max) conditions.amount_max = parseFloat(form.amount_max)
    if (form.date_from) conditions.date_from = form.date_from
    if (form.date_to) conditions.date_to = form.date_to
    if (form.type) conditions.type = form.type

    const payload = {
      name: form.name.trim(),
      category: parseInt(form.category),
      priority: parseInt(form.priority),
      active: form.active,
      conditions: conditions
    }

    try {
      await axios.post('/api/banking/rules/', payload, {
        headers: { 'X-CSRFToken': getCsrfToken() }
      })
      onSuccess()
    } catch (err) {
      setError(err.response?.data?.message || err.message || 'Failed to create rule')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
          <h3 className="text-xl font-bold text-gray-900">Create New Rule</h3>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
            <X size={24} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {/* Rule Name */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Rule Name <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              placeholder="e.g., Netflix Subscription"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>

          {/* Category and Priority */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Target Category <span className="text-red-500">*</span>
              </label>
              <select
                value={form.category}
                onChange={(e) => setForm({ ...form, category: e.target.value })}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              >
                {categories.map(cat => (
                  <option key={cat.id} value={cat.id}>{cat.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Priority (lower = higher)
              </label>
              <input
                type="number"
                value={form.priority}
                onChange={(e) => setForm({ ...form, priority: e.target.value })}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                min="1"
              />
            </div>
          </div>

          {/* Conditions Section */}
          <div className="border-t border-gray-200 pt-4 mt-4">
            <h4 className="text-sm font-semibold text-gray-900 mb-3">Conditions (All must match)</h4>

            {/* Description Contains */}
            <div className="mb-3">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Description Contains
              </label>
              <input
                type="text"
                value={form.description_contains}
                onChange={(e) => setForm({ ...form, description_contains: e.target.value })}
                placeholder="e.g., netflix, starbucks"
                className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <p className="text-xs text-gray-500 mt-1">Case-insensitive substring match</p>
            </div>

            {/* Amount Range */}
            <div className="grid grid-cols-2 gap-4 mb-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Amount Min
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={form.amount_min}
                  onChange={(e) => setForm({ ...form, amount_min: e.target.value })}
                  placeholder="e.g., -100 or 0"
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Amount Max
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={form.amount_max}
                  onChange={(e) => setForm({ ...form, amount_max: e.target.value })}
                  placeholder="e.g., 0 or 100"
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            {/* Date Range */}
            <div className="grid grid-cols-2 gap-4 mb-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Date From
                </label>
                <input
                  type="text"
                  value={dateToInputFormat(form.date_from)}
                  onChange={(e) => setForm({ ...form, date_from: inputDateToISO(e.target.value) })}
                  placeholder="MM/DD/YYYY"
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  title="Enter date in your preferred format"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Date To
                </label>
                <input
                  type="text"
                  value={dateToInputFormat(form.date_to)}
                  onChange={(e) => setForm({ ...form, date_to: inputDateToISO(e.target.value) })}
                  placeholder="MM/DD/YYYY"
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  title="Enter date in your preferred format"
                />
              </div>
            </div>

            {/* Transaction Type */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Transaction Type
              </label>
              <select
                value={form.type}
                onChange={(e) => setForm({ ...form, type: e.target.value })}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Any</option>
                <option value="income">Income</option>
                <option value="expense">Expense</option>
                <option value="transfer">Transfer</option>
              </select>
            </div>
          </div>

          {/* Active Toggle */}
          <div className="flex items-center">
            <input
              type="checkbox"
              id="active"
              checked={form.active}
              onChange={(e) => setForm({ ...form, active: e.target.checked })}
              className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
            />
            <label htmlFor="active" className="ml-2 text-sm text-gray-700">
              Active (apply immediately to new transactions)
            </label>
          </div>

          {/* Error Message */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700">
              {error}
            </div>
          )}

          {/* Buttons */}
          <div className="flex gap-3 pt-4 border-t border-gray-200">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 bg-gray-100 text-gray-900 rounded-lg hover:bg-gray-200 font-medium"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 font-medium"
            >
              {submitting ? 'Creating...' : 'Create Rule'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

function EditRuleModal({ rule, categories, onClose, onSuccess }) {
  const [form, setForm] = useState({
    name: rule.name || '',
    category: rule.category || categories[0]?.id || '',
    priority: rule.priority || 100,
    active: !!rule.active,
    // Conditions
    description_contains: rule.conditions?.description_contains || '',
    amount_min: rule.conditions?.amount_min ?? '',
    amount_max: rule.conditions?.amount_max ?? '',
    date_from: rule.conditions?.date_from || '',
    date_to: rule.conditions?.date_to || '',
    type: rule.conditions?.type || '',
  })
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

    if (!form.name.trim() || !form.category) {
      setError('Name and category are required')
      return
    }

    setSubmitting(true)
    setError(null)

    const conditions = {}
    if (form.description_contains) conditions.description_contains = form.description_contains
    if (form.amount_min !== '' && form.amount_min !== null) conditions.amount_min = parseFloat(form.amount_min)
    if (form.amount_max !== '' && form.amount_max !== null) conditions.amount_max = parseFloat(form.amount_max)
    if (form.date_from) conditions.date_from = form.date_from
    if (form.date_to) conditions.date_to = form.date_to
    if (form.type) conditions.type = form.type

    const payload = {
      name: form.name.trim(),
      category: parseInt(form.category),
      priority: parseInt(form.priority),
      active: form.active,
      conditions: conditions
    }

    try {
      await axios.patch(`/api/banking/rules/${rule.id}/`, payload, {
        headers: { 'X-CSRFToken': getCsrfToken() }
      })
      onSuccess()
    } catch (err) {
      setError(err.response?.data?.message || err.message || 'Failed to update rule')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
          <h3 className="text-xl font-bold text-gray-900">Edit Rule</h3>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
            <X size={24} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {/* Rule Name */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Rule Name <span className="text-red-500">*</span></label>
            <input
              type="text"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>

          {/* Category and Priority */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Target Category <span className="text-red-500">*</span></label>
              <select
                value={form.category}
                onChange={(e) => setForm({ ...form, category: e.target.value })}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              >
                {categories.map(cat => (
                  <option key={cat.id} value={cat.id}>{cat.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Priority (lower = higher)</label>
              <input
                type="number"
                value={form.priority}
                onChange={(e) => setForm({ ...form, priority: e.target.value })}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                min="1"
              />
            </div>
          </div>

          {/* Conditions Section */}
          <div className="border-t border-gray-200 pt-4 mt-4">
            <h4 className="text-sm font-semibold text-gray-900 mb-3">Conditions (All must match)</h4>

            <div className="mb-3">
              <label className="block text-sm font-medium text-gray-700 mb-1">Description Contains</label>
              <input
                type="text"
                value={form.description_contains}
                onChange={(e) => setForm({ ...form, description_contains: e.target.value })}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <p className="text-xs text-gray-500 mt-1">Case-insensitive substring match</p>
            </div>

            <div className="grid grid-cols-2 gap-4 mb-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Amount Min</label>
                <input
                  type="number"
                  step="0.01"
                  value={form.amount_min}
                  onChange={(e) => setForm({ ...form, amount_min: e.target.value })}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Amount Max</label>
                <input
                  type="number"
                  step="0.01"
                  value={form.amount_max}
                  onChange={(e) => setForm({ ...form, amount_max: e.target.value })}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4 mb-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Date From</label>
                <DateInput
                  value={form.date_from}
                  onChange={(isoDate) => setForm({ ...form, date_from: isoDate })}
                  title="Start date for rule"
                  showPickerButton={true}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Date To</label>
                <DateInput
                  value={form.date_to}
                  onChange={(isoDate) => setForm({ ...form, date_to: isoDate })}
                  title="End date for rule"
                  showPickerButton={true}
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Transaction Type</label>
              <select
                value={form.type}
                onChange={(e) => setForm({ ...form, type: e.target.value })}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Any</option>
                <option value="income">Income</option>
                <option value="expense">Expense</option>
                <option value="transfer">Transfer</option>
              </select>
            </div>
          </div>

          <div className="flex items-center">
            <input
              type="checkbox"
              checked={form.active}
              onChange={(e) => setForm({ ...form, active: e.target.checked })}
              className="mr-2"
            />
            <span className="text-sm text-gray-700">Active</span>
          </div>

          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 bg-gray-100 text-gray-900 rounded-lg hover:bg-gray-200 font-medium"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 font-medium"
            >
              {submitting ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
