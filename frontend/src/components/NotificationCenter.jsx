/**
export default NotificationCenter

}
  )
    </div>
      )}
        </div>
          )}
            </div>
              </button>
                {t('notifications.close', 'Close')}
              >
                className="flex-1 px-3 py-1.5 text-sm font-medium bg-gray-200 text-gray-800 rounded hover:bg-gray-300 transition"
                onClick={() => setIsOpen(false)}
              <button
              </button>
                {t('notifications.markRead', 'Mark all read')}
              >
                className="flex-1 px-3 py-1.5 text-sm font-medium bg-blue-500 text-white rounded hover:bg-blue-600 transition"
                }}
                  setIsOpen(false)
                  unreadNotifications.forEach(n => markAsRead(n.id))
                onClick={() => {
              <button
            <div className="p-3 border-t border-gray-200 flex gap-2">
          {unreadNotifications.length > 0 && (
          {/* Footer */}

          </div>
            )}
              ))
                </div>
                  </div>
                    </div>
                      )}
                        </span>
                          📱
                        <span title={t('notifications.pushSent', 'Push sent')} className="text-xs">
                      {notification.is_notified_via_push && (
                      )}
                        </span>
                          📧
                        <span title={t('notifications.emailSent', 'Email sent')} className="text-xs">
                      {notification.is_notified_via_email && (
                    <div className="flex items-center gap-1 flex-shrink-0 ml-2">
                    {/* Quick Actions */}

                    </div>
                      </p>
                        {new Date(notification.created_at).toLocaleDateString()}
                      <p className="text-xs text-gray-400 mt-1">
                      </p>
                        {notification.anomaly?.description}
                      <p className="text-xs text-gray-500 mt-1">
                      </p>
                        {notification.anomaly?.title}
                      <p className="font-medium text-sm text-gray-900">
                    <div className="flex-1 min-w-0">
                    {/* Content */}

                    />
                      }}
                        backgroundColor: getSeverityColor(notification.anomaly?.severity),
                      style={{
                      className="w-2 h-2 rounded-full mt-1.5 flex-shrink-0"
                    <div
                    {/* Severity Indicator */}
                  <div className="flex items-start gap-3">
                >
                  onClick={() => handleNotificationClick(notification)}
                  className="p-3 border-b border-gray-100 hover:bg-gray-50 transition cursor-pointer"
                  key={notification.id}
                <div
              unreadNotifications.map(notification => (
            ) : (
              </div>
                {t('notifications.empty', 'No new notifications')}
              <div className="p-4 text-center text-gray-500">
            {unreadNotifications.length === 0 ? (
          <div className="max-h-96 overflow-y-auto">
          {/* Notifications List */}

          </div>
            </button>
              ✕
            >
              className="text-gray-400 hover:text-gray-600"
              onClick={() => setIsOpen(false)}
            <button
            <h3 className="font-semibold">{t('notifications.title', 'Notifications')}</h3>
          <div className="p-4 border-b border-gray-200 flex items-center justify-between">
          {/* Header */}
        <div className="absolute right-0 mt-2 w-80 bg-white rounded-lg shadow-lg z-50 border border-gray-200">
      {isOpen && (
      {/* Dropdown Panel */}

      </button>
        )}
          </span>
            {unreadCount > 9 ? '9+' : unreadCount}
          <span className="absolute top-0 right-0 bg-red-500 text-white text-xs font-bold rounded-full w-5 h-5 flex items-center justify-center">
        {unreadCount > 0 && (
        <span className="text-xl">🔔</span>
      >
        title={t('notifications.title', 'Notifications')}
        className="relative p-2 hover:bg-gray-100 rounded-lg transition"
        onClick={() => setIsOpen(!isOpen)}
      <button
      {/* Notification Bell Button */}
    <div className="relative">
  return (

  }
    }
      onAnomalyClick(notification.anomaly)
    if (onAnomalyClick) {
    markAsRead(notification.id)
  const handleNotificationClick = (notification) => {

  const unreadNotifications = notifications?.filter(n => !n.is_read) || []

  }, [notifications])
    setUnreadCount(count)
    const count = notifications?.filter(n => !n.is_read).length || 0
  useEffect(() => {

  const [unreadCount, setUnreadCount] = useState(0)
  const [isOpen, setIsOpen] = useState(false)
  const t = useTranslate()
  const { notifications, markAsRead, dismissAnomaly } = useAnomalies()
const NotificationCenter = ({ onAnomalyClick }) => {

import useTranslate from '../hooks/useTranslate'
import { getSeverityColor } from '../utils/anomalyUtils'
import useAnomalies from '../hooks/useAnomalies'
import { useEffect, useState } from 'react'

 */
 * Shows unread notifications with quick actions
 * Displays anomaly notifications in a dropdown widget
 * Notification Center Component

