export function unreadNotifications(notifications) {
  return (notifications || []).filter(n => !n.read_at)
}

export function notificationLabel(notification) {
  if (!notification) return ''
  if (notification.kind === 'overdue') return 'Overdue'
  if (notification.kind === 'due_today') return 'Due soon'
  return 'Notification'
}
