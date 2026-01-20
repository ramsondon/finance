import React, { useEffect, useState } from 'react'
import axios from 'axios'
import { getCsrfToken } from '../utils/csrf'
import { useTranslate } from '../hooks/useLanguage'
import { Folder, Zap, X, Check, AlertCircle } from 'lucide-react'

export default function CategoriesManager({ darkMode = false }) {
  const t = useTranslate()
  const [categories, setCategories] = useState([])
  const [loading, setLoading] = useState(true)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [editingCategory, setEditingCategory] = useState(null)
  const [showAIGenerationModal, setShowAIGenerationModal] = useState(false)
  const [aiGenerationLoading, setAIGenerationLoading] = useState(false)
  const [aiGenerationTaskId, setAIGenerationTaskId] = useState(null)
  const [aiGenerationResult, setAIGenerationResult] = useState(null)
  const [aiGenerationError, setAIGenerationError] = useState(null)

  // Pagination using backend links
  const [nextUrl, setNextUrl] = useState(null)
  const [previousUrl, setPreviousUrl] = useState(null)
  const [currentUrl, setCurrentUrl] = useState('/api/banking/categories/')
  const [totalCount, setTotalCount] = useState(0)

  // Filters and sorting
  const [searchQuery, setSearchQuery] = useState('')
  const [sortBy, setSortBy] = useState('name')
  const [sortOrder, setSortOrder] = useState('asc')

  useEffect(() => {
    // Reset to first page when search/sort changes
    setCurrentUrl('/api/banking/categories/')
    loadCategories('/api/banking/categories/')
  }, [searchQuery, sortBy, sortOrder])

  useEffect(() => {
    loadCategories(currentUrl)
  }, [currentUrl])

  // Listen for ESC key to close AI generation modal
  useEffect(() => {
    const handleEscKey = (event) => {
      if (event.key === 'Escape' && showAIGenerationModal) {
        closeAIGenerationModal()
      }
    }

    // Only add listener when modal is open
    if (showAIGenerationModal) {
      document.addEventListener('keydown', handleEscKey)
      return () => {
        document.removeEventListener('keydown', handleEscKey)
      }
    }
  }, [showAIGenerationModal])

  const loadCategories = async (url) => {
    setLoading(true)
    // Default to base endpoint if no URL provided
    const apiUrl = url || '/api/banking/categories/'
    try {
      // Only add params if using base endpoint (not pagination links)
      const isBaseEndpoint = apiUrl === '/api/banking/categories/' || !apiUrl.includes('?')
      const params = isBaseEndpoint ? {
        search: searchQuery,
        ordering: sortOrder === 'desc' ? `-${sortBy}` : sortBy
      } : undefined

      const response = await axios.get(apiUrl, params ? { params } : {})
      const data = response.data

      // Handle paginated response from backend
      if (data.results) {
        setCategories(data.results)
        setNextUrl(data.next || null)
        setPreviousUrl(data.previous || null)
        setTotalCount(data.count || 0)
      } else if (Array.isArray(data)) {
        // Fallback for non-paginated response
        setCategories(data)
        setNextUrl(null)
        setPreviousUrl(null)
        setTotalCount(data.length)
      } else {
        setCategories([])
        setNextUrl(null)
        setPreviousUrl(null)
        setTotalCount(0)
      }
    } catch (err) {
      console.error('Error loading categories:', err)
      setCategories([])
      setNextUrl(null)
      setPreviousUrl(null)
      setTotalCount(0)
    } finally {
      setLoading(false)
    }
  }

  const deleteCategory = async (categoryId) => {
    if (!confirm(t('categories.deleteConfirm'))) return
    try {
      await axios.delete(`/api/banking/categories/${categoryId}/`, {
        headers: { 'X-CSRFToken': getCsrfToken() }
      })
      loadCategories(currentUrl)
    } catch (err) {
      alert('Error deleting category: ' + (err.response?.data?.message || err.message))
    }
  }

  const handleSort = (field) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')
    } else {
      setSortBy(field)
      setSortOrder('asc')
    }
    setCurrentUrl('/api/banking/categories/')
  }

  const startAIGeneration = async () => {
    setAIGenerationLoading(true)
    setAIGenerationError(null)
    setAIGenerationResult(null)
    try {
      const response = await axios.post('/api/ai/generate-categories',
        { auto_approve: true },
        { headers: { 'X-CSRFToken': getCsrfToken() } }
      )
      const taskId = response.data.task_id
      setAIGenerationTaskId(taskId)

      // Poll for task completion
      let completed = false
      let attempts = 0
      const maxAttempts = 300  // 5 minutes with 1 second polling

      while (!completed && attempts < maxAttempts) {
        attempts++

        try {
          // Check task status - using generic endpoint
          const statusResponse = await axios.get(`/api/task-status/${taskId}`, {
            headers: { 'X-CSRFToken': getCsrfToken() }
          })

          const taskStatus = statusResponse.data.status

          if (taskStatus === 'SUCCESS') {
            // Task completed successfully, reload categories
            await loadCategories(currentUrl)
            completed = true

            // Show success message
            setAIGenerationResult({
              message: t('aiCategoryGeneration.generationComplete') || 'Categories generated successfully!',
              taskId: taskId
            })
          } else if (taskStatus === 'FAILURE') {
            // Task failed
            setAIGenerationError(
              statusResponse.data.error || t('categories.aiGenerationFailed')
            )
            completed = true
          } else if (taskStatus === 'PENDING' || taskStatus === 'PROGRESS') {
            // Still processing, wait a bit before checking again
            await new Promise(resolve => setTimeout(resolve, 1000))
          }
        } catch (err) {
          // Network error or other issue, retry after delay
          console.warn('Error checking task status:', err)
          await new Promise(resolve => setTimeout(resolve, 1000))
        }
      }

      if (!completed && attempts >= maxAttempts) {
        setAIGenerationError('Task took too long to complete. Please try again.')
      }

      setAIGenerationLoading(false)

      // Auto-close modal after 3 seconds if successful
      if (completed && !setAIGenerationError) {
        setTimeout(() => {
          closeAIGenerationModal()
        }, 3000)
      }
    } catch (err) {
      console.error('Error starting AI generation:', err)
      setAIGenerationError(
        err.response?.data?.error || t('categories.aiGenerationFailed')
      )
      setAIGenerationLoading(false)
    }
  }

  const closeAIGenerationModal = () => {
    setShowAIGenerationModal(false)
    setAIGenerationLoading(false)
    setAIGenerationTaskId(null)
    setAIGenerationResult(null)
    setAIGenerationError(null)
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">{t('categories.title')}</h2>
          <p className="text-gray-500 text-sm mt-1">{t('categories.description')}</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setShowAIGenerationModal(true)}
            disabled={aiGenerationLoading}
            className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 font-medium disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {aiGenerationLoading ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                {t('categories.generating')}
              </>
            ) : (
              <>
                <Zap size={18} />
                {t('categories.generateWithAI')}
              </>
            )}
          </button>
          <button
            onClick={() => setShowCreateModal(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium"
          >
            {t('categories.createCategory')}
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg border border-gray-200 p-4">
        <div className="flex items-center gap-4">
          <div className="flex-1">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder={t('categories.searchPlaceholder')}
              className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <span>{t('categories.sortBy')}</span>
            <select
              value={sortBy}
              onChange={(e) => {
                setSortBy(e.target.value)
                setCurrentUrl('/api/banking/categories/')
              }}
              className="border border-gray-300 rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="name">{t('categories.name')}</option>
              <option value="color">{t('categories.color')}</option>
            </select>
            <button
              onClick={() => {
                setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')
                setCurrentUrl('/api/banking/categories/')
              }}
              className="p-1 hover:bg-gray-100 rounded"
              title={sortOrder === 'asc' ? 'Ascending' : 'Descending'}
            >
              {sortOrder === 'asc' ? t('categories.ascending') : t('categories.descending')}
            </button>
          </div>
        </div>
      </div>

      {/* Categories List */}
      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      ) : categories.length === 0 ? (
        <div className="bg-white rounded-lg border border-gray-200 p-8 text-center">
          <Folder size={64} className="mx-auto text-gray-400 mb-4" />
          <p className="text-gray-500 mb-4">
            {searchQuery ? t('categories.noCategoriesSearch') : t('categories.noCategoriesEmpty')}
          </p>
          {!searchQuery && (
            <button
              onClick={() => setShowCreateModal(true)}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              {t('categories.createCategory')}
            </button>
          )}
        </div>
      ) : (
        <>
          {/* Table */}
          <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th
                    className="text-left py-3 px-4 text-xs font-semibold text-gray-700 cursor-pointer hover:bg-gray-100"
                    onClick={() => handleSort('name')}
                  >
                    <div className="flex items-center gap-2">
                      {t('categories.name')}
                      {sortBy === 'name' && (
                        <span className="text-blue-600">{sortOrder === 'asc' ? '↑' : '↓'}</span>
                      )}
                    </div>
                  </th>
                  <th
                    className="text-left py-3 px-4 text-xs font-semibold text-gray-700 cursor-pointer hover:bg-gray-100"
                    onClick={() => handleSort('color')}
                  >
                    <div className="flex items-center gap-2">
                      {t('categories.color')}
                      {sortBy === 'color' && (
                        <span className="text-blue-600">{sortOrder === 'asc' ? '↑' : '↓'}</span>
                      )}
                    </div>
                  </th>
                  <th className="text-right py-3 px-4 text-xs font-semibold text-gray-700">
                    {t('categories.actions')}
                  </th>
                </tr>
              </thead>
              <tbody>
                {categories.map(category => (
                  <tr key={category.id} className="border-b border-gray-100 hover:bg-gray-50">
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-2">
                        <div
                          className="w-4 h-4 rounded-full border border-gray-300"
                          style={{ backgroundColor: category.color }}
                        ></div>
                        <span className="font-medium text-gray-900">{category.name}</span>
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-2">
                        <code className="text-xs bg-gray-100 px-2 py-1 rounded text-gray-700">
                          {category.color}
                        </code>
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => setEditingCategory(category)}
                          className="p-2 text-blue-600 hover:bg-blue-50 rounded"
                          title="Edit"
                        >
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                          </svg>
                        </button>
                        <button
                          onClick={() => deleteCategory(category.id)}
                          className="p-2 text-red-600 hover:bg-red-50 rounded"
                          title="Delete"
                        >
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                          </svg>
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {(nextUrl || previousUrl) && (
            <div className="flex items-center justify-between bg-white rounded-lg border border-gray-200 px-4 py-3">
              <div className="text-sm text-gray-600">
                {t('categories.total', { count: totalCount })} {totalCount === 1 ? t('categories.category') : t('categories.categories')}
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => previousUrl && setCurrentUrl(previousUrl)}
                  disabled={!previousUrl}
                  className="px-3 py-1 border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
                >
                  {t('transactions.previousPage')}
                </button>
                <button
                  onClick={() => nextUrl && setCurrentUrl(nextUrl)}
                  disabled={!nextUrl}
                  className="px-3 py-1 border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
                >
                  {t('transactions.nextPage')}
                </button>
              </div>
            </div>
          )}
        </>
      )}

      {/* Create Modal */}
      {showCreateModal && (
        <CategoryModal
          onClose={() => setShowCreateModal(false)}
          onSuccess={() => {
            setShowCreateModal(false)
            loadCategories()
          }}
        />
      )}

      {/* Edit Modal */}
      {editingCategory && (
        <CategoryModal
          category={editingCategory}
          onClose={() => setEditingCategory(null)}
          onSuccess={() => {
            setEditingCategory(null)
            loadCategories()
          }}
        />
      )}

      {/* AI Category Generation Modal */}
      {showAIGenerationModal && (
        <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-md">
            <div className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between rounded-t-lg">
              <h3 className="text-xl font-bold text-gray-900 flex items-center gap-2">
                <Zap size={24} className="text-yellow-500" />
                {t('aiCategoryGeneration.title')}
              </h3>
              <button
                onClick={closeAIGenerationModal}
                disabled={aiGenerationLoading}
                className="text-gray-500 hover:text-gray-700 disabled:opacity-50"
              >
                <X size={24} />
              </button>
            </div>

            <div className="p-6 space-y-4">
              {/* Description */}
              <p className="text-gray-600 text-sm">
                {t('aiCategoryGeneration.description')}
              </p>

              {/* Result or Loading State */}
              {aiGenerationLoading && !aiGenerationResult ? (
                <div className="space-y-4">
                  <div className="flex items-center justify-center py-6">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
                  </div>
                  <p className="text-center text-gray-600 text-sm">
                    {t('aiCategoryGeneration.analyzing')}
                  </p>
                </div>
              ) : aiGenerationResult ? (
                <div className="bg-green-50 border border-green-200 rounded-lg p-4 space-y-2">
                  <p className="text-green-800 font-medium flex items-center gap-2">
                    <Check size={18} className="text-green-600" />
                    {t('aiCategoryGeneration.generationComplete')}
                  </p>
                  <p className="text-green-700 text-sm">
                    {aiGenerationResult.message}
                  </p>
                </div>
              ) : aiGenerationError ? (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4 space-y-2">
                  <p className="text-red-800 font-medium flex items-center gap-2">
                    <AlertCircle size={18} className="text-red-600" />
                    {t('aiCategoryGeneration.generationError')}
                  </p>
                  <p className="text-red-700 text-sm">
                    {aiGenerationError}
                  </p>
                </div>
              ) : null}

              {/* Buttons */}
              <div className="flex gap-3 pt-4 border-t border-gray-200">
                {!aiGenerationResult && !aiGenerationError ? (
                  <>
                    <button
                      type="button"
                      onClick={closeAIGenerationModal}
                      disabled={aiGenerationLoading}
                      className="flex-1 px-4 py-2 bg-gray-100 text-gray-900 rounded-lg hover:bg-gray-200 font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {t('common.cancel')}
                    </button>
                    <button
                      type="button"
                      onClick={startAIGeneration}
                      disabled={aiGenerationLoading}
                      className="flex-1 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium flex items-center justify-center gap-2"
                    >
                      {aiGenerationLoading ? (
                        <>
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                          {t('categories.generating')}
                        </>
                      ) : (
                        t('aiCategoryGeneration.startGeneration')
                      )}
                    </button>
                  </>
                ) : (
                  <button
                    type="button"
                    onClick={closeAIGenerationModal}
                    className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium"
                  >
                    {t('common.close')}
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function CategoryModal({ category, onClose, onSuccess }) {
  const isEdit = !!category
  const t = useTranslate()
  const [form, setForm] = useState({
    name: category?.name || '',
    color: category?.color || '#3b82f6'
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

  // Predefined color palette
  const colorPalette = [
    '#ef4444', '#f97316', '#f59e0b', '#eab308', '#84cc16',
    '#22c55e', '#10b981', '#14b8a6', '#06b6d4', '#0ea5e9',
    '#3b82f6', '#6366f1', '#8b5cf6', '#a855f7', '#d946ef',
    '#ec4899', '#f43f5e', '#64748b', '#6b7280', '#000000'
  ]

  const handleSubmit = async (e) => {
    e.preventDefault()

    if (!form.name.trim()) {
      setError('Category name is required')
      return
    }

    setSubmitting(true)
    setError(null)

    const payload = {
      name: form.name.trim(),
      color: form.color
    }

    try {
      if (isEdit) {
        await axios.patch(`/api/banking/categories/${category.id}/`, payload, {
          headers: { 'X-CSRFToken': getCsrfToken() }
        })
      } else {
        await axios.post('/api/banking/categories/', payload, {
          headers: { 'X-CSRFToken': getCsrfToken() }
        })
      }
      onSuccess()
    } catch (err) {
      // Handle validation errors (e.g., duplicate category)
      if (err.response?.data) {
        const data = err.response.data

        // Check for field-specific errors (from serializer validation)
        if (data.name && Array.isArray(data.name)) {
          // Check if it's a duplicate error
          if (data.name[0].includes('already exists')) {
            setError(t('categories.duplicateError') || 'A category with this name already exists.')
          } else {
            setError(data.name[0])
          }
        } else if (typeof data === 'string') {
          // General error message
          setError(data)
        } else if (data.detail) {
          setError(data.detail)
        } else {
          setError(t('categories.failedToSave') || `Failed to ${isEdit ? 'update' : 'create'} category`)
        }
      } else {
        setError(err.message || `Failed to ${isEdit ? 'update' : 'create'} category`)
      }
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md">
        <div className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between rounded-t-lg">
          <h3 className="text-xl font-bold text-gray-900">
            {isEdit ? 'Edit Category' : 'Create New Category'}
          </h3>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
            <X size={24} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {/* Category Name */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Category Name <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              placeholder="e.g., Groceries, Entertainment"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
              autoFocus
            />
          </div>

          {/* Color Picker */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Color
            </label>
            <div className="flex items-center gap-3 mb-3">
              <div
                className="w-12 h-12 rounded-lg border-2 border-gray-300 shadow-sm"
                style={{ backgroundColor: form.color }}
              ></div>
              <input
                type="text"
                value={form.color}
                onChange={(e) => setForm({ ...form, color: e.target.value })}
                placeholder="#3b82f6"
                className="flex-1 border border-gray-300 rounded-lg px-3 py-2 font-mono text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div className="grid grid-cols-10 gap-2">
              {colorPalette.map(color => (
                <button
                  key={color}
                  type="button"
                  onClick={() => setForm({ ...form, color })}
                  className={`w-8 h-8 rounded-lg border-2 ${
                    form.color === color ? 'border-gray-900 scale-110' : 'border-gray-300'
                  } transition-transform hover:scale-110`}
                  style={{ backgroundColor: color }}
                  title={color}
                ></button>
              ))}
            </div>
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
              disabled={submitting}
              className="flex-1 px-4 py-2 bg-gray-100 text-gray-900 rounded-lg hover:bg-gray-200 font-medium disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 font-medium"
            >
              {submitting ? (isEdit ? 'Updating...' : 'Creating...') : (isEdit ? 'Update' : 'Create')}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

