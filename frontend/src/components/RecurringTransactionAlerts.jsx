/**
 * Recurring Transaction Alerts Component
 * Displays anomalies related to recurring transactions
 * Shows missing payments and pattern changes
 */

import { useEffect, useState } from 'react'
import useAnomalies from '../hooks/useAnomalies'
import { getSeverityColor, getSeverityBgColor } from '../utils/anomalyUtils'
import useTranslate from '../hooks/useTranslate'

const RecurringTransactionAlerts = ({ recurringTransaction, onAnomalyClick }) => {
  const { anomalies } = useAnomalies()
  const t = useTranslate()
  const [relatedAnomalies, setRelatedAnomalies] = useState([])

  useEffect(() => {
    if (!recurringTransaction) return

    // Find anomalies related to this recurring transaction
    const related = anomalies?.filter(a => {
      // Match on type: missing_recurring or changed_recurring
      const isRecurringAnomaly = [
        'missing_recurring',
        'changed_recurring',
      ].includes(a.anomaly_type)

      if (!isRecurringAnomaly) return false

      // Match on description/context mentioning the recurring transaction
      const transactionName =
        recurringTransaction.name || recurringTransaction.description || ''
      const anomalyText =
        `${a.title} ${a.description}`.toLowerCase()
      const transactionText = transactionName.toLowerCase()

      return transactionText && anomalyText.includes(transactionText)
    }) || []

    setRelatedAnomalies(related)
  }, [anomalies, recurringTransaction])

  if (relatedAnomalies.length === 0) {
    return null
  }

  return (
    <div className="mt-3 space-y-2">
      {relatedAnomalies.map(anomaly => (
        <div
          key={anomaly.id}
          style={{
            backgroundColor: getSeverityBgColor(anomaly.severity),
            borderLeft: `3px solid ${getSeverityColor(anomaly.severity)}`,
          }}
          className="p-3 rounded cursor-pointer hover:shadow-md transition"
          onClick={() => onAnomalyClick?.(anomaly)}
        >
          <div className="flex items-start gap-2">
            <span className="text-sm">
              {anomaly.severity === 'critical' && '🔴'}
              {anomaly.severity === 'warning' && '🟡'}
              {anomaly.severity === 'info' && '🔵'}
            </span>
            <div className="flex-1">
              <p className="font-medium text-sm">{anomaly.title}</p>
              <p className="text-xs opacity-75 mt-1">{anomaly.description}</p>
              {anomaly.anomaly_score && (
                <p className="text-xs opacity-50 mt-1">
                  {t('anomalies.confidence', 'Confidence')}: {Math.round(parseFloat(anomaly.anomaly_score))}%
                </p>
              )}
            </div>
            <button
              onClick={e => {
                e.stopPropagation()
                onAnomalyClick?.(anomaly)
              }}
              className="text-xs font-medium px-2 py-1 rounded hover:opacity-80"
              style={{
                backgroundColor: getSeverityColor(anomaly.severity),
                color: 'white',
              }}
            >
              {t('anomalies.view', 'View')}
            </button>
          </div>
        </div>
      ))}
    </div>
  )
}

export default RecurringTransactionAlerts

