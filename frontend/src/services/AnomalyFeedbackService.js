/**
 * Anomaly Feedback Service
 * Handles user feedback on anomalies and converts feedback to rules
 */

import axios from 'axios'
import { getCsrfToken } from '../utils/csrf'

class AnomalyFeedbackService {
  /**
   * Submit feedback on an anomaly
   * @param {number} anomalyId - ID of the anomaly
   * @param {string} feedbackType - 'confirmed' or 'false_positive'
   * @param {string} notes - Optional user notes
   * @returns {Promise}
   */
  static async submitFeedback(anomalyId, feedbackType, notes = '') {
    try {
      const response = await axios.post(
        `/api/banking/anomalies/${anomalyId}/feedback/`,
        {
          feedback_type: feedbackType,
          notes: notes,
        },
        {
          headers: {
            'X-CSRFToken': getCsrfToken(),
          },
        }
      )
      return response.data
    } catch (error) {
      console.error('Error submitting anomaly feedback:', error)
      throw error
    }
  }

  /**
   * Get feedback statistics for a user
   * @returns {Promise}
   */
  static async getFeedbackStats() {
    try {
      const response = await axios.get('/api/banking/anomalies/feedback/stats/')
      return response.data
    } catch (error) {
      console.error('Error getting feedback stats:', error)
      throw error
    }
  }

  /**
   * Get false positives (for improving detection)
   * @returns {Promise}
   */
  static async getFalsePositives() {
    try {
      const response = await axios.get('/api/banking/anomalies/?feedback=false_positive')
      return response.data
    } catch (error) {
      console.error('Error getting false positives:', error)
      throw error
    }
  }

  /**
   * Convert feedback to a rule
   * @param {number} anomalyId - ID of the anomaly
   * @param {string} ruleType - Type of rule to create
   * @returns {Promise}
   */
  static async createRuleFromFeedback(anomalyId, ruleType) {
    try {
      const response = await axios.post(
        `/api/banking/anomalies/${anomalyId}/create-rule/`,
        {
          rule_type: ruleType,
        },
        {
          headers: {
            'X-CSRFToken': getCsrfToken(),
          },
        }
      )
      return response.data
    } catch (error) {
      console.error('Error creating rule from feedback:', error)
      throw error
    }
  }

  /**
   * Get feedback trends (which anomalies are mostly false positives)
   * @returns {Promise}
   */
  static async getFeedbackTrends() {
    try {
      const response = await axios.get('/api/banking/anomalies/feedback/trends/')
      return response.data
    } catch (error) {
      console.error('Error getting feedback trends:', error)
      throw error
    }
  }
}

export default AnomalyFeedbackService

