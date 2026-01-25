/**
 * Anomaly Badge Component
 * Displays a small badge on transactions/items showing anomaly status
 * Used inline in transaction lists and recurring transaction views
 */

import { getSeverityColor, getSeverityIcon } from '../utils/anomalyUtils'
import useTranslate from '../hooks/useTranslate'

const AnomalyBadge = ({ anomaly, size = 'sm', onClick }) => {
  const t = useTranslate()

  if (!anomaly) return null

  const sizeClasses = {
    xs: 'px-2 py-0.5 text-xs',
    sm: 'px-3 py-1 text-sm',
    md: 'px-4 py-1.5 text-base',
    lg: 'px-5 py-2 text-lg',
  }

  const severityEmoji = {
    critical: '🔴',
    warning: '🟡',
    info: '🔵',
  }

  return (
    <button
      onClick={onClick}
      title={anomaly.title}
      className={`inline-flex items-center gap-1.5 rounded-full font-medium transition-all hover:shadow-md hover:scale-105 ${sizeClasses[size]}`}
      style={{
        backgroundColor: getSeverityColor(anomaly.severity),
        color: 'white',
        border: `1px solid ${getSeverityColor(anomaly.severity)}`,
        opacity: anomaly.is_dismissed ? 0.5 : 1,
        textDecoration: anomaly.is_dismissed ? 'line-through' : 'none',
      }}
    >
      <span>{severityEmoji[anomaly.severity]}</span>
      <span className="hidden sm:inline">{anomaly.anomaly_type.replace('_', ' ')}</span>
    </button>
  )
}

export default AnomalyBadge

