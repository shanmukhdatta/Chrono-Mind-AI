import { useCallback } from 'react'
import { useNotificationStore } from '../store/notificationStore'
import api from '../lib/api'

export function useNotifications() {
  const { setNotifications, markAsRead } = useNotificationStore()

  const fetchNotifications = useCallback(async () => {
    try {
      const response = await api.get('/api/notifications')
      if (response.data.success) {
        setNotifications(response.data.data)
      }
    } catch (error) {
      console.error('fetchNotifications error:', error)
    }
  }, [setNotifications])

  const markNotificationRead = useCallback(async (notifId) => {
    try {
      markAsRead(notifId) // optimistic update
      await api.patch(`/api/notifications/${notifId}/read`)
    } catch (error) {
      console.error('markNotificationRead error:', error)
    }
  }, [markAsRead])

  const clearReadNotifications = useCallback(async () => {
    try {
      await api.delete('/api/notifications/clear')
      await fetchNotifications()
    } catch (error) {
      console.error('clearReadNotifications error:', error)
    }
  }, [fetchNotifications])

  return { fetchNotifications, markNotificationRead, clearReadNotifications }
}
