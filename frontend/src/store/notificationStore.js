import { create } from 'zustand'

export const useNotificationStore = create((set, get) => ({
  notifications: [],
  unreadCount: 0,

  setNotifications: (notifications) => set({
    notifications,
    unreadCount: notifications.filter(n => !n.read).length,
  }),
  markAsRead: (notifId) => set((state) => {
    const updated = state.notifications.map(n =>
      n.notif_id === notifId ? { ...n, read: true } : n
    )
    return {
      notifications: updated,
      unreadCount: updated.filter(n => !n.read).length,
    }
  }),
  clearAll: () => set({ notifications: [], unreadCount: 0 }),
}))
