/**
 * Anomalies View Component
 * Dedicated page for viewing and managing anomalies
 * Includes filtering, statistics, and detailed views
 */

import { useState } from 'react'
import useAnomalies from '../hooks/useAnomalies'
import useTranslate from '../hooks/useTranslate'
import {
  getSeverityColor,
  getSeverityBgColor,
  getSeverityTextColor,
  getAnomalyIcon,
  getAnomalyTypeName,
  formatAnomalyScore,
  formatDeviation,
  getRecommendedAction,
} from '../utils/anomalyUtils'

const AnomaliesView = () => {
  const {
    anomalies,
    loading,
    filters,
    setFilters,
    selectedAnomaly,
    setSelectedAnomaly,
    dismissAnomaly,
    provideFeedback,
    stats,
  } = useAnomalies()

  const t = useTranslate()
  const [selectedId, setSelectedId] = useState(null)

  const anomalyTypes = [
    { value: 'all', label: t('anomalies.typeAll', 'All Types') },
    { value: 'unusual_amount', label: 'Unusual Amount' },
    { value: 'spending_spike', label: 'Spending Spike' },
    { value: 'missing_recurring', label: 'Missing Recurring' },
    { value: 'changed_recurring', label: 'Changed Amount' },
    { value: 'new_merchant', label: 'New Merchant' },
    { value: 'duplicate_pattern', label: 'Duplicate Pattern' },
    { value: 'account_inactive', label: 'Account Inactive' },
  ]

  const severityOptions = [
    { value: 'all', label: t('anomalies.severityAll', 'All Severities') },
    { value: 'critical', label: '🔴 Critical' },
    { value: 'warning', label: '🟡 Warning' },
    { value: 'info', label: '🔵 Info' },
  ]

  const filteredAnomalies = anomalies.filter(a => {
    if (filters.isDismissed !== 'all' && a.is_dismissed !== (filters.isDismissed === 'dismissed')) {
      return false
    }
    return true
  })

  // Group by severity
  const bySeverity = {
    critical: filteredAnomalies.filter(a => a.severity === 'critical'),
    warning: filteredAnomalies.filter(a => a.severity === 'warning'),
    info: filteredAnomalies.filter(a => a.severity === 'info'),
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2">{t('anomalies.title', 'Anomalies')}</h1>
        <p className="text-gray-600">
          {t('anomalies.subtitle', 'Review and manage unusual patterns in your financial data')}
        </p>
      </div>

      {/* Statistics */}
      {stats && (
        <div className="grid grid-cols-4 gap-4 mb-6">
          <div className="bg-white p-4 rounded-lg shadow">
            <div className="text-2xl font-bold text-gray-900">{stats.total_anomalies}</div>
            <div className="text-sm text-gray-600">{t('anomalies.total', 'Total Anomalies')}</div>
          </div>
          <div className="bg-red-50 p-4 rounded-lg shadow border-l-4 border-red-600">
            <div className="text-2xl font-bold text-red-600">{stats.critical_count}</div>
            <div className="text-sm text-red-700">{t('anomalies.critical', 'Critical')}</div>
          </div>
          <div className="bg-yellow-50 p-4 rounded-lg shadow border-l-4 border-yellow-500">
            <div className="text-2xl font-bold text-yellow-600">{stats.warning_count}</div>
            <div className="text-sm text-yellow-700">{t('anomalies.warning', 'Warning')}</div>
          </div>
          <div className="bg-blue-50 p-4 rounded-lg shadow border-l-4 border-blue-500">
            <div className="text-2xl font-bold text-blue-600">{stats.info_count}</div>
            <div className="text-sm text-blue-700">{t('anomalies.info', 'Info')}</div>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="bg-white p-4 rounded-lg shadow mb-6">
        <div className="grid grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium mb-1">
              {t('anomalies.filterSeverity', 'Severity')}
            </label>
            <select
              value={filters.severity}
              onChange={(e) => setFilters({ ...filters, severity: e.target.value })}
              className="w-full p-2 border border-gray-300 rounded"
            >
              {severityOptions.map(opt => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">
              {t('anomalies.filterType', 'Type')}
            </label>
            <select
              value={filters.type}
              onChange={(e) => setFilters({ ...filters, type: e.target.value })}
              className="w-full p-2 border border-gray-300 rounded"
            >
              {anomalyTypes.map(opt => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">
              {t('anomalies.filterStatus', 'Status')}
            </label>
            <select
              value={filters.isDismissed}
              onChange={(e) => setFilters({ ...filters, isDismissed: e.target.value })}
              className="w-full p-2 border border-gray-300 rounded"
            >
              <option value="all">{t('anomalies.statusAll', 'All')}</option>
              <option value="active">{t('anomalies.statusActive', 'Active')}</option>
              <option value="dismissed">{t('anomalies.statusDismissed', 'Dismissed')}</option>
            </select>
          </div>
        </div>
      </div>

      {/* Anomalies by Severity */}
      {['critical', 'warning', 'info'].map(severity => {
        const anomalysForSeverity = bySeverity[severity]
        if (anomalysForSeverity.length === 0) return null

        return (
          <div key={severity} className="mb-6">
            <h2 className="text-lg font-semibold mb-3 flex items-center gap-2">
              <span
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: getSeverityColor(severity) }}
              ></span>
              {severity === 'critical' && '🔴 Critical'}
              {severity === 'warning' && '🟡 Warning'}
              {severity === 'info' && '🔵 Info'}
              <span className="text-gray-600 text-sm">({anomalysForSeverity.length})</span>
            </h2>

            <div className="space-y-2">
              {anomalysForSeverity.map(anomaly => (
                <div
                  key={anomaly.id}
                  className="bg-white p-4 rounded-lg shadow border-l-4 cursor-pointer hover:shadow-lg transition"
                  style={{ borderColor: getSeverityColor(severity) }}
                  onClick={() => setSelectedId(anomaly.id)}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="text-2xl">{getAnomalyIcon(anomaly.anomaly_type)}</span>
                        <div>
                          <h3 className="font-semibold">{anomaly.title}</h3>
                          <p className="text-sm text-gray-600 mt-1">{anomaly.description}</p>
                        </div>
                      </div>
                      <div className="mt-2 flex gap-4 text-sm">
                        {anomaly.anomaly_score && (
                          <span className="text-gray-600">
                            Confidence: <strong>{formatAnomalyScore(anomaly.anomaly_score)}</strong>
                          </span>
                        )}
                        {anomaly.deviation_percent && (
                          <span className="text-gray-600">
                            Deviation: <strong>{formatDeviation(anomaly.deviation_percent)}</strong>
                          </span>
                        )}
                      </div>
                    </div>

                    <div className="flex gap-2">
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          setSelectedId(anomaly.id)
                        }}
                        className="px-3 py-1 text-sm rounded bg-blue-100 text-blue-700 hover:bg-blue-200 transition"
                      >
                        {t('anomalies.details', 'Details')}
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          dismissAnomaly(anomaly.id)
                        }}
                        className="px-3 py-1 text-sm rounded bg-gray-200 text-gray-700 hover:bg-gray-300 transition"
                      >
                        {t('anomalies.dismiss', 'Dismiss')}
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )
      })}

      {filteredAnomalies.length === 0 && (
        <div className="bg-white p-8 rounded-lg shadow text-center">
          <p className="text-gray-500">
            {t('anomalies.noAnomalies', 'No anomalies detected')}
          </p>
        </div>
      )}

      {/* Detail Modal */}
      {selectedId && (
        <AnomalyDetailModal
          anomaly={anomalies.find(a => a.id === selectedId)}
          onClose={() => setSelectedId(null)}
          onDismiss={() => {
            dismissAnomaly(selectedId)
            setSelectedId(null)
          }}
          onFeedback={provideFeedback}
        />
      )}
    </div>
  )
}

// Detail Modal Component
const AnomalyDetailModal = ({ anomaly, onClose, onDismiss, onFeedback }) => {
  const t = useTranslate()
  const [feedback, setFeedback] = useState('')

  if (!anomaly) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div
          style={{ backgroundColor: getSeverityBgColor(anomaly.severity) }}
          className="p-6 border-b-4"
          style={{ borderColor: getSeverityColor(anomaly.severity) }}
        >
          <div className="flex items-start justify-between">
            <div className="flex items-start gap-3">
              <span className="text-4xl">{getAnomalyIcon(anomaly.anomaly_type)}</span>
              <div>
                <h2 className="text-2xl font-bold">{anomaly.title}</h2>
                <p className="text-sm text-gray-600 mt-1">
                  {getAnomalyTypeName(anomaly.anomaly_type)} • {new Date(anomaly.created_at).toLocaleDateString()}
                </p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="text-2xl text-gray-500 hover:text-gray-700"
            >
              ✕
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Description */}
          <div>
            <h3 className="font-semibold mb-2">{t('anomalies.description', 'Description')}</h3>
            <p className="text-gray-700">{anomaly.description}</p>
          </div>

          {/* Reason */}
          <div>
            <h3 className="font-semibold mb-2">{t('anomalies.reason', 'Why This Was Flagged')}</h3>
            <p className="text-gray-700">{anomaly.reason}</p>
          </div>

          {/* Metrics */}
          {(anomaly.anomaly_score || anomaly.expected_value || anomaly.actual_value) && (
            <div className="bg-gray-50 p-4 rounded-lg">
              <h3 className="font-semibold mb-3">{t('anomalies.metrics', 'Metrics')}</h3>
              <div className="grid grid-cols-2 gap-4 text-sm">
                {anomaly.anomaly_score && (
                  <div>
                    <span className="text-gray-600">Confidence Score</span>
                    <div className="font-semibold text-lg">{formatAnomalyScore(anomaly.anomaly_score)}</div>
                  </div>
                )}
                {anomaly.expected_value && (
                  <div>
                    <span className="text-gray-600">Expected</span>
                    <div className="font-semibold">{anomaly.expected_value}</div>
                  </div>
                )}
                {anomaly.actual_value && (
                  <div>
                    <span className="text-gray-600">Actual</span>
                    <div className="font-semibold">{anomaly.actual_value}</div>
                  </div>
                )}
                {anomaly.deviation_percent && (
                  <div>
                    <span className="text-gray-600">Deviation</span>
                    <div className="font-semibold text-red-600">{formatDeviation(anomaly.deviation_percent)}</div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Recommended Action */}
          <div className="bg-blue-50 p-4 rounded-lg border-l-4 border-blue-500">
            <h3 className="font-semibold mb-1 text-blue-900">{t('anomalies.recommendedAction', 'Recommended Action')}</h3>
            <p className="text-blue-800">{getRecommendedAction(anomaly)}</p>
          </div>

          {/* Feedback */}
          <div>
            <h3 className="font-semibold mb-3">{t('anomalies.yourFeedback', 'Your Feedback')}</h3>
            <div className="space-y-2">
              <button
                onClick={() => onFeedback(anomaly.id, 'false_positive', 'This is not an anomaly')}
                className="w-full p-2 border border-gray-300 rounded hover:bg-gray-50 transition text-left"
              >
                ✗ {t('anomalies.falsePositive', 'This is a false positive')}
              </button>
              <button
                onClick={() => onFeedback(anomaly.id, 'confirmed', 'This anomaly is real')}
                className="w-full p-2 border border-gray-300 rounded hover:bg-gray-50 transition text-left"
              >
                ✓ {t('anomalies.confirmed', 'I confirm this anomaly')}
              </button>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-6 border-t bg-gray-50 flex gap-3 justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded border border-gray-300 hover:bg-gray-100 transition"
          >
            {t('common.cancel', 'Cancel')}
          </button>
          <button
            onClick={onDismiss}
            className="px-4 py-2 rounded bg-gray-700 text-white hover:bg-gray-800 transition"
          >
            {t('anomalies.dismiss', 'Dismiss')}
          </button>
        </div>
      </div>
    </div>
  )
}

export default AnomaliesView

