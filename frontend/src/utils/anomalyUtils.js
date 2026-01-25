/**
 * Utility functions for anomaly display
 */

export const ANOMALY_TYPES = {
  UNUSUAL_AMOUNT: 'unusual_amount',
  UNUSUAL_TIMING: 'unusual_timing',
  DUPLICATE_PATTERN: 'duplicate_pattern',
  MISSING_RECURRING: 'missing_recurring',
  CHANGED_RECURRING: 'changed_recurring',
  SPENDING_SPIKE: 'spending_spike',
  NEW_MERCHANT: 'new_merchant',
  ACCOUNT_INACTIVE: 'account_inactive',
  MULTIPLE_FAILURES: 'multiple_failures',
}

export const SEVERITY_LEVELS = {
  INFO: 'info',
  WARNING: 'warning',
  CRITICAL: 'critical',
}

export const getSeverityColor = (severity) => {
  switch (severity) {
    case SEVERITY_LEVELS.CRITICAL:
      return '#dc2626' // red-600
    case SEVERITY_LEVELS.WARNING:
      return '#f59e0b' // amber-500
    case SEVERITY_LEVELS.INFO:
      return '#3b82f6' // blue-500
    default:
      return '#6b7280' // gray-500
  }
}

export const getSeverityBgColor = (severity) => {
  switch (severity) {
    case SEVERITY_LEVELS.CRITICAL:
      return '#fee2e2' // red-100
    case SEVERITY_LEVELS.WARNING:
      return '#fef3c7' // amber-100
    case SEVERITY_LEVELS.INFO:
      return '#dbeafe' // blue-100
    default:
      return '#f3f4f6' // gray-100
  }
}

export const getSeverityTextColor = (severity) => {
  switch (severity) {
    case SEVERITY_LEVELS.CRITICAL:
      return '#991b1b' // red-900
    case SEVERITY_LEVELS.WARNING:
      return '#b45309' // amber-900
    case SEVERITY_LEVELS.INFO:
      return '#1e40af' // blue-900
    default:
      return '#374151' // gray-700
  }
}

export const getAnomalyIcon = (anomalyType) => {
  switch (anomalyType) {
    case ANOMALY_TYPES.UNUSUAL_AMOUNT:
      return '💰'
    case ANOMALY_TYPES.UNUSUAL_TIMING:
      return '⏰'
    case ANOMALY_TYPES.DUPLICATE_PATTERN:
      return '🔄'
    case ANOMALY_TYPES.MISSING_RECURRING:
      return '⚠️'
    case ANOMALY_TYPES.CHANGED_RECURRING:
      return '📊'
    case ANOMALY_TYPES.SPENDING_SPIKE:
      return '📈'
    case ANOMALY_TYPES.NEW_MERCHANT:
      return '🏪'
    case ANOMALY_TYPES.ACCOUNT_INACTIVE:
      return '😴'
    case ANOMALY_TYPES.MULTIPLE_FAILURES:
      return '❌'
    default:
      return 'ℹ️'
  }
}

export const getAnomalyTypeName = (type) => {
  const names = {
    unusual_amount: 'Unusual Amount',
    unusual_timing: 'Unusual Timing',
    duplicate_pattern: 'Duplicate Pattern',
    missing_recurring: 'Missing Recurring',
    changed_recurring: 'Changed Amount/Frequency',
    spending_spike: 'Spending Spike',
    new_merchant: 'New Merchant',
    account_inactive: 'Account Inactive',
    multiple_failures: 'Multiple Failures',
  }
  return names[type] || type
}

export const formatAnomalyScore = (score) => {
  const numScore = typeof score === 'string' ? parseFloat(score) : score
  return `${Math.round(numScore)}%`
}

export const formatDeviation = (deviation) => {
  const numDev = typeof deviation === 'string' ? parseFloat(deviation) : deviation
  if (numDev > 0) {
    return `+${numDev.toFixed(0)}%`
  }
  return `${numDev.toFixed(0)}%`
}

export const getRecommendedAction = (anomaly) => {
  switch (anomaly.anomaly_type) {
    case ANOMALY_TYPES.UNUSUAL_AMOUNT:
      return 'Check if this transaction is correct'
    case ANOMALY_TYPES.DUPLICATE_PATTERN:
      return 'Verify if this is a duplicate'
    case ANOMALY_TYPES.MISSING_RECURRING:
      return 'Check if the subscription was cancelled'
    case ANOMALY_TYPES.CHANGED_RECURRING:
      return 'Review the recurring pattern'
    case ANOMALY_TYPES.SPENDING_SPIKE:
      return 'Review your spending this month'
    case ANOMALY_TYPES.NEW_MERCHANT:
      return 'Add a category for this merchant'
    case ANOMALY_TYPES.ACCOUNT_INACTIVE:
      return 'Consider archiving inactive accounts'
    default:
      return 'Review and take action'
  }
}

export const shouldShowAnomalyBadge = (anomaly, preferences) => {
  // Show badge if:
  // 1. Not dismissed
  // 2. Severity matches user preferences
  if (anomaly.is_dismissed) {
    return false
  }

  const severityMap = {
    critical: preferences?.notify_on_critical ?? true,
    warning: preferences?.notify_on_warning ?? false,
    info: preferences?.notify_on_info ?? false,
  }

  return severityMap[anomaly.severity] ?? false
}

