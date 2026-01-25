/**
 * Anomaly AI Explanations Service
 * Integrates with Ollama to generate AI-powered explanations for anomalies
 */

import axios from 'axios'

class AnomalyAIService {
  /**
   * Generate an AI explanation for an anomaly
   * @param {object} anomaly - The anomaly object
   * @returns {Promise<string>} - The AI-generated explanation
   */
  static async generateExplanation(anomaly) {
    try {
      const response = await axios.post('/api/banking/anomalies/generate-explanation/', {
        anomaly_id: anomaly.id,
        anomaly_type: anomaly.anomaly_type,
        title: anomaly.title,
        description: anomaly.description,
        context_data: anomaly.context_data,
      })
      return response.data.explanation
    } catch (error) {
      console.error('Error generating AI explanation:', error)
      throw error
    }
  }

  /**
   * Generate recommendations for an anomaly
   * @param {object} anomaly - The anomaly object
   * @returns {Promise<string[]>} - Array of recommendations
   */
  static async generateRecommendations(anomaly) {
    try {
      const response = await axios.post('/api/banking/anomalies/generate-recommendations/', {
        anomaly_id: anomaly.id,
        anomaly_type: anomaly.anomaly_type,
        context_data: anomaly.context_data,
      })
      return response.data.recommendations
    } catch (error) {
      console.error('Error generating recommendations:', error)
      throw error
    }
  }

  /**
   * Get an explanation from cache or generate new one
   * @param {object} anomaly - The anomaly object
   * @returns {Promise<string>} - Explanation
   */
  static async getExplanation(anomaly) {
    // Check if we have a cached explanation
    const cacheKey = `anomaly_explanation_${anomaly.id}`
    const cached = localStorage.getItem(cacheKey)
    if (cached) {
      return cached
    }

    // Generate new explanation
    const explanation = await this.generateExplanation(anomaly)

    // Cache it for 24 hours
    localStorage.setItem(cacheKey, explanation)
    setTimeout(() => localStorage.removeItem(cacheKey), 24 * 60 * 60 * 1000)

    return explanation
  }
}

export default AnomalyAIService

