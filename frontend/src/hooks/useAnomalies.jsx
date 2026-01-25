/**
 * Custom hook for managing anomalies
 * Handles fetching, filtering, and dismissing anomalies
 */

import { useState, useCallback, useEffect } from 'react'
import axios from 'axios'

const useAnomalies = () => {
  const [anomalies, setAnomalies] = useState([])
  const [loading, setLoading] = useState(false)
  const [filters, setFilters] = useState({
    severity: 'all',
    type: 'all',
    dateFrom: null,
    dateTo: null,
    isDismissed: false,
    accountId: null,
  })
  const [selectedAnomaly, setSelectedAnomaly] = useState(null)
  const [stats, setStats] = useState(null)

  // Fetch anomalies with filters
  const fetchAnomalies = useCallback(async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()

      if (filters.severity !== 'all') {
        params.append('severity', filters.severity)
      }
      if (filters.type !== 'all') {
        params.append('anomaly_type', filters.type)
      }
      if (filters.isDismissed) {
        params.append('is_dismissed', 'true')
      }
      if (filters.accountId) {
        params.append('account_id', filters.accountId)
      }

      const response = await axios.get(`/api/banking/anomalies/?${params.toString()}`)
      setAnomalies(response.data.results || response.data)
    } catch (err) {
      console.error('Failed to fetch anomalies:', err)
    } finally {
      setLoading(false)
    }
  }, [filters])

  // Fetch anomaly statistics
  const fetchStats = useCallback(async () => {
    try {
      const response = await axios.get('/api/banking/anomalies/stats/')
      setStats(response.data)
    } catch (err) {
      console.error('Failed to fetch anomaly stats:', err)
    }
  }, [])

  // Dismiss individual anomaly
  const dismissAnomaly = useCallback(async (anomalyId) => {
    try {
      await axios.post(`/api/banking/anomalies/${anomalyId}/dismiss/`)
      setAnomalies(anomalies.filter(a => a.id !== anomalyId))
      if (selectedAnomaly?.id === anomalyId) {
        setSelectedAnomaly(null)
      }
      // Refresh stats
      await fetchStats()
    } catch (err) {
      console.error('Failed to dismiss anomaly:', err)
    }
  }, [anomalies, selectedAnomaly, fetchStats])

  // Provide feedback on anomaly
  const provideFeedback = useCallback(async (anomalyId, feedbackType, reason = '') => {
    try {
      await axios.post(`/api/banking/anomalies/${anomalyId}/feedback/`, {
        feedback_type: feedbackType,
        reason: reason,
      })
      // Refresh anomalies
      await fetchAnomalies()
      await fetchStats()
    } catch (err) {
      console.error('Failed to provide feedback:', err)
    }
  }, [fetchAnomalies, fetchStats])

  // Auto-refresh on interval (every 30 seconds)
  useEffect(() => {
    fetchAnomalies()
    fetchStats()
    const interval = setInterval(() => {
      fetchAnomalies()
      fetchStats()
    }, 30000)
    return () => clearInterval(interval)
  }, [fetchAnomalies, fetchStats])

  return {
    anomalies,
    loading,
    filters,
    setFilters,
    selectedAnomaly,
    setSelectedAnomaly,
    dismissAnomaly,
    provideFeedback,
    fetchAnomalies,
    stats,
    fetchStats,
  }
}

export default useAnomalies

