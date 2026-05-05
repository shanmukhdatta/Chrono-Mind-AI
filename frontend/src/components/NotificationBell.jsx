import React, { useState, useRef, useEffect } from 'react'
import { Bell, X, RefreshCw, CheckCheck } from 'lucide-react'
import { useNotificationStore } from '../store/notificationStore'
import { useNotifications } from '../hooks/useNotifications'
import { format, parseISO } from 'date-fns'

export function NotificationBell() {
  const { notifications, unreadCount } = useNotificationStore()
  const { markNotificationRead, clearReadNotifications } = useNotifications()
  const [isOpen, setIsOpen] = useState(false)
  const panelRef = useRef(null)

  useEffect(() => {
    function handleClickOutside(e) {
      if (panelRef.current && !panelRef.current.contains(e.target)) {
        setIsOpen(false)
      }
    }
    if (isOpen) document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [isOpen])

  const getNotifStyle = (type) => {
    if (type === 'tasks_rescheduled') return 'bg-blue-50 border-blue-200 text-blue-700'
    if (type === 'tasks_deleted') return 'bg-amber-50 border-amber-200 text-amber-700'
    return 'bg-gray-50 border-gray-200 text-dark'
  }

  return (
    <div className="relative" ref={panelRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 rounded-xl hover:bg-gray-100 transition-colors"
        aria-label="Notifications"
      >
        <Bell className="w-5 h-5 text-dark-muted" />
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 w-5 h-5 bg-peach text-white text-[10px] font-bold rounded-full flex items-center justify-center">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>

      {isOpen && (
        <div className="absolute right-0 top-full mt-2 w-80 bg-white border border-gray-100 rounded-2xl shadow-card z-50 overflow-hidden animate-fade-in">
          <div className="flex items-center justify-between p-4 border-b border-gray-100">
            <h3 className="font-semibold text-dark text-sm">Notifications</h3>
            <div className="flex items-center gap-2">
              {notifications.some(n => n.read) && (
                <button
                  onClick={clearReadNotifications}
                  className="text-xs text-dark-muted hover:text-dark flex items-center gap-1"
                >
                  <RefreshCw className="w-3 h-3" /> Clear read
                </button>
              )}
              <button onClick={() => setIsOpen(false)} className="p-1 hover:bg-gray-100 rounded-lg">
                <X className="w-4 h-4 text-dark-muted" />
              </button>
            </div>
          </div>

          <div className="max-h-80 overflow-y-auto">
            {notifications.length === 0 ? (
              <div className="py-8 text-center">
                <CheckCheck className="w-8 h-8 text-peach/40 mx-auto mb-2" />
                <p className="text-sm text-dark-muted">All caught up!</p>
              </div>
            ) : (
              notifications.map((notif) => (
                <div
                  key={notif.notif_id}
                  onClick={() => !notif.read && markNotificationRead(notif.notif_id)}
                  className={`p-4 border-b border-gray-50 cursor-pointer hover:bg-gray-50 transition-colors ${notif.read ? 'opacity-60' : ''}`}
                >
                  <div className={`text-xs px-2 py-1 rounded-lg border inline-block mb-2 ${getNotifStyle(notif.type)}`}>
                    {notif.type === 'tasks_rescheduled' ? '📅 Rescheduled' : '🗑 Cleared'}
                  </div>
                  <p className="text-sm text-dark leading-relaxed">{notif.message}</p>
                  {notif.created_at && (
                    <p className="text-xs text-dark-muted mt-1">
                      {format(new Date(notif.created_at._seconds ? notif.created_at._seconds * 1000 : notif.created_at), 'PPp')}
                    </p>
                  )}
                  {!notif.read && (
                    <span className="text-[10px] text-peach font-medium">tap to mark read</span>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  )
}
