/**
 * Anomaly Alert Banner Component
 * Displays at the top of the dashboard for critical/warning anomalies
 * Allows quick dismissal and navigation to details
 */

import { useEffect, useState } from 'react'
import useAnomalies from '../hooks/useAnomalies'
import { getSeverityColor, getSeverityBgColor, getSeverityTextColor } from '../utils/anomalyUtils'
import useTranslate from '../hooks/useTranslate'

const AnomalyAlertBanner = ({ onViewAll }) => {
  const { anomalies, dismissAnomaly, stats } = useAnomalies()
  const t = useTranslate()
  const [visibleAnomalies, setVisibleAnomalies] = useState([])

  // Filter for critical/warning anomalies that haven't been dismissed
  useEffect(() => {
    const filtered = anomalies
      .filter(a => !a.is_dismissed && ['critical', 'warning'].includes(a.severity))
      .slice(0, 3) // Show up to 3
    setVisibleAnomalies(filtered)
  }, [anomalies])

  if (visibleAnomalies.length === 0) {
    return null
  }

  const criticalCount = stats?.critical_count || 0
  const warningCount = stats?.warning_count || 0
  const totalAlert = criticalCount + warningCount

  return (
    <div className="mb-4 space-y-2">
      {/* Main banner */}
      <div
        style={{
          backgroundColor: getSeverityBgColor('critical'),
          borderLeft: `4px solid ${getSeverityColor('critical')}`,
        }}
        className="p-4 rounded-lg flex items-start justify-between"
      >
        <div className="flex items-start gap-3">
          <span className="text-2xl">🚨</span>
          <div>
            <h3
              style={{ color: getSeverityTextColor('critical') }}
              className="font-semibold"
            >
              {t('anomalies.alertTitle', 'Anomalies detected')}
            </h3>
            <p className="text-sm mt-1">
              {totalAlert} {totalAlert === 1 ? 'anomaly' : 'anomalies'} require attention
              ({criticalCount} critical, {warningCount} warning)
            </p>
          </div>
        </div>
        <div className="flex gap-2">
          <button
            onClick={onViewAll}
            className="px-3 py-1 bg-white rounded text-sm font-medium hover:bg-gray-100 transition"
            style={{ color: getSeverityColor('critical') }}
          >
            {t('anomalies.viewAll', 'View All')}
          </button>
          <button
            onClick={() => {
              // Dismiss all visible anomalies
              visibleAnomalies.forEach(a => dismissAnomaly(a.id))
            }}
            className="px-3 py-1 rounded text-sm font-medium text-white hover:opacity-90 transition"
            style={{ backgroundColor: getSeverityColor('critical') }}
          >
            {t('anomalies.dismiss', 'Dismiss')}
          </button>
        </div>
      </div>

      {/* Individual anomaly cards */}
      {visibleAnomalies.map(anomaly => (
        <div
          key={anomaly.id}
          style={{
            backgroundColor: getSeverityBgColor(anomaly.severity),
            borderLeft: `4px solid ${getSeverityColor(anomaly.severity)}`,
          }}
          className="p-3 rounded-lg flex items-center justify-between"
        >
          <div>
            <p
              style={{ color: getSeverityTextColor(anomaly.severity) }}
              className="font-medium text-sm"
            >
              {anomaly.title}
            </p>
            {anomaly.anomaly_score && (
              <p className="text-xs opacity-75 mt-1">
                Confidence: {Math.round(parseFloat(anomaly.anomaly_score))}%
              </p>
            )}
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => onViewAll()}
              className="text-xs px-2 py-1 rounded hover:bg-gray-200 transition"
            >
              {t('anomalies.details', 'Details')}
            </button>
            <button
              onClick={() => dismissAnomaly(anomaly.id)}
              className="text-xs px-2 py-1 rounded hover:bg-gray-200 transition"
            >
              ✕
            </button>
          </div>
        </div>
      ))}
    </div>
  )
}

export default AnomalyAlertBanner

