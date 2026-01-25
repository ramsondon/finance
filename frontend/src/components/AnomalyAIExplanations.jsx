/**
 * Anomaly AI Explanations Component
 * Displays AI-generated explanations and recommendations for anomalies
 */

import { useState, useEffect } from 'react'
import AnomalyAIService from '../services/AnomalyAIService'
import useTranslate from '../hooks/useTranslate'

const AnomalyAIExplanations = ({ anomaly, className = '' }) => {
  const t = useTranslate()
  const [explanation, setExplanation] = useState(null)
  const [recommendations, setRecommendations] = useState([])
  const [loading, setLoading] = useState(false)
  const [showAI, setShowAI] = useState(false)
  const [error, setError] = useState(null)

  const loadExplanation = async () => {
    if (loading) return

    setLoading(true)
    setError(null)

    try {
      const exp = await AnomalyAIService.getExplanation(anomaly)
      setExplanation(exp)
    } catch (err) {
      setError(t('anomalies.aiError', 'Could not generate explanation'))
      console.error('AI explanation error:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (showAI && !explanation && !loading) {
      loadExplanation()
    }
  }, [showAI])

  if (!showAI) {
    return (
      <button
        onClick={() => setShowAI(true)}
        className="text-sm text-blue-600 hover:text-blue-700 font-medium flex items-center gap-1 mt-2"
      >
        <span>🤖</span>
        {t('anomalies.getAIExplanation', 'Get AI explanation')}
      </button>
    )
  }

  return (
    <div className={`mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <h4 className="font-semibold text-gray-900 flex items-center gap-2">
          <span>🤖</span>
          {t('anomalies.aiInsight', 'AI Insight')}
        </h4>
        <button
          onClick={() => setShowAI(false)}
          className="text-gray-400 hover:text-gray-600"
        >
          ✕
        </button>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="flex items-center justify-center py-4">
          <div className="animate-spin h-5 w-5 border-2 border-blue-600 border-t-transparent rounded-full" />
          <span className="ml-2 text-sm text-gray-600">
            {t('anomalies.generatingExplanation', 'Generating explanation...')}
          </span>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
          {error}
        </div>
      )}

      {/* Explanation */}
      {explanation && !loading && (
        <>
          <div className="text-sm text-gray-700 leading-relaxed mb-4">
            {explanation}
          </div>

          {/* Recommendations */}
          {recommendations && recommendations.length > 0 && (
            <div className="mt-3 pt-3 border-t border-blue-200">
              <p className="text-sm font-semibold text-gray-900 mb-2">
                💡 {t('anomalies.recommendations', 'Recommendations')}
              </p>
              <ul className="space-y-1">
                {recommendations.map((rec, idx) => (
                  <li key={idx} className="text-sm text-gray-700 flex gap-2">
                    <span className="text-blue-600">•</span>
                    <span>{rec}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Disclaimer */}
          <p className="text-xs text-gray-500 mt-3">
            {t('anomalies.aiDisclaimer', 'AI-generated content. Please verify with actual data.')}
          </p>
        </>
      )}
    </div>
  )
}

export default AnomalyAIExplanations

