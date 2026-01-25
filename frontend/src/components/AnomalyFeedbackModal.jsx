/**
 * Anomaly Feedback Modal Component
 * Allows users to provide feedback on detected anomalies
 * Feedback is used to improve detection algorithms and generate rules
 */

import { useState } from 'react'
import AnomalyFeedbackService from '../services/AnomalyFeedbackService'
import { getSeverityColor } from '../utils/anomalyUtils'
import useTranslate from '../hooks/useTranslate'

const AnomalyFeedbackModal = ({ anomaly, onClose, onFeedbackSubmitted }) => {
  const t = useTranslate()
  const [feedbackType, setFeedbackType] = useState(null)
  const [notes, setNotes] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(false)

  const handleSubmit = async () => {
    if (!feedbackType) {
      setError(t('anomalies.selectFeedbackType', 'Please select feedback type'))
      return
    }

    setLoading(true)
    setError(null)

    try {
      await AnomalyFeedbackService.submitFeedback(
        anomaly.id,
        feedbackType,
        notes
      )
      setSuccess(true)
      if (onFeedbackSubmitted) {
        onFeedbackSubmitted(feedbackType)
      }
      setTimeout(() => {
        onClose()
      }, 1500)
    } catch (err) {
      setError(t('anomalies.feedbackError', 'Error submitting feedback'))
      console.error('Feedback submission error:', err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-lg w-full max-w-md p-6">
        {success ? (
          // Success State
          <div className="text-center">
            <div className="text-4xl mb-3">✅</div>
            <h3 className="text-lg font-bold text-gray-900 mb-2">
              {t('anomalies.thankYouForFeedback', 'Thank you for your feedback!')}
            </h3>
            <p className="text-gray-600 text-sm">
              {t('anomalies.feedbackHelps', 'Your feedback helps improve anomaly detection')}
            </p>
          </div>
        ) : (
          // Feedback Form
          <>
            {/* Header */}
            <div className="mb-4">
              <h3 className="text-lg font-bold text-gray-900 mb-2">
                {t('anomalies.feedbackTitle', 'Is this anomaly correct?')}
              </h3>
              <p className="text-sm text-gray-600">
                {anomaly.title}
              </p>
            </div>

            {/* Error Message */}
            {error && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
                {error}
              </div>
            )}

            {/* Feedback Options */}
            <div className="space-y-3 mb-4">
              {/* Confirmed Option */}
              <button
                onClick={() => setFeedbackType('confirmed')}
                className={`w-full p-4 border-2 rounded-lg text-left transition-all ${
                  feedbackType === 'confirmed'
                    ? 'border-green-500 bg-green-50'
                    : 'border-gray-200 bg-white hover:border-green-300'
                }`}
              >
                <div className="flex items-start gap-3">
                  <div className="text-2xl">✅</div>
                  <div>
                    <p className="font-semibold text-gray-900">
                      {t('anomalies.confirmed', 'This is a real anomaly')}
                    </p>
                    <p className="text-xs text-gray-600 mt-1">
                      {t('anomalies.confirmedHelp', 'The detected anomaly is accurate and helpful')}
                    </p>
                  </div>
                </div>
              </button>

              {/* False Positive Option */}
              <button
                onClick={() => setFeedbackType('false_positive')}
                className={`w-full p-4 border-2 rounded-lg text-left transition-all ${
                  feedbackType === 'false_positive'
                    ? 'border-red-500 bg-red-50'
                    : 'border-gray-200 bg-white hover:border-red-300'
                }`}
              >
                <div className="flex items-start gap-3">
                  <div className="text-2xl">❌</div>
                  <div>
                    <p className="font-semibold text-gray-900">
                      {t('anomalies.falsePositive', 'This is a false alarm')}
                    </p>
                    <p className="text-xs text-gray-600 mt-1">
                      {t('anomalies.falsePositiveHelp', 'This is not actually an anomaly')}
                    </p>
                  </div>
                </div>
              </button>
            </div>

            {/* Notes */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                {t('anomalies.additionalNotes', 'Additional notes (optional)')}
              </label>
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder={t('anomalies.notesPlaceholder', 'Help us understand why...')}
                className="w-full border border-gray-300 rounded px-3 py-2 text-sm resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                rows="3"
              />
            </div>

            {/* Actions */}
            <div className="flex gap-3">
              <button
                onClick={onClose}
                className="flex-1 px-4 py-2 bg-gray-200 text-gray-900 rounded-lg hover:bg-gray-300 font-medium text-sm transition"
              >
                {t('anomalies.cancel', 'Cancel')}
              </button>
              <button
                onClick={handleSubmit}
                disabled={!feedbackType || loading}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium text-sm transition flex items-center justify-center gap-2"
              >
                {loading && (
                  <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full" />
                )}
                {t('anomalies.submitFeedback', 'Submit Feedback')}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}

export default AnomalyFeedbackModal

