import React, { useCallback, useEffect, useState } from 'react'
import { Bell, BellOff, CheckCheck, RefreshCw, CalendarClock } from 'lucide-react'
import { Link } from 'react-router-dom'
import toast from 'react-hot-toast'
import api from '../lib/api'
import { useAuthStore } from '../store/authStore'
import { notificationLabel, unreadNotifications } from '../lib/notificationsV2'

function explainError(error) {
  if (typeof error.response?.data?.detail === 'string') return error.response.data.detail
  if (error.response?.status === 503) return 'PostgreSQL notification storage is not configured.'
  return error.message || 'Could not access notifications'
}

export default function NotificationsV2() {
  const demo = useAuthStore(s => s.user?.uid === 'demo')
  const [notifications, setNotifications] = useState([])
  const [unreadOnly, setUnreadOnly] = useState(false)
  const [loading, setLoading] = useState(!demo)
  const [working, setWorking] = useState(false)
  const [error, setError] = useState('')

  const refresh = useCallback(async () => {
    if (demo) return
    setLoading(true)
    try {
      const response = await api.get('/api/v2/notifications', { params: { limit: 100 } })
      setNotifications(response.data)
      setError('')
    } catch (err) {
      setError(explainError(err))
    } finally {
      setLoading(false)
    }
  }, [demo])

  useEffect(() => { refresh() }, [refresh])

  const mutate = async (operation, message) => {
    setWorking(true)
    try {
      await operation()
      await refresh()
      toast.success(message)
    } catch (err) {
      const detail = explainError(err)
      setError(detail)
      toast.error(detail)
    } finally {
      setWorking(false)
    }
  }

  const unread = unreadNotifications(notifications)
  const visible = unreadOnly ? unread : notifications

  return (
    <div className="max-w-4xl mx-auto space-y-5">
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-peach-dark text-sm font-semibold">Deadline awareness</p>
          <h1 className="text-3xl font-bold text-dark">Notifications</h1>
          <p className="text-sm text-dark-muted mt-2">Real reminders generated from your task deadlines and saved to PostgreSQL.</p>
        </div>
        <button type="button" onClick={refresh} disabled={demo || working}
          className="bg-white border rounded-xl p-3" aria-label="Reload notifications">
          <RefreshCw className="w-5 h-5"/>
        </button>
      </header>
      <p className="text-sm text-dark-muted rounded-xl bg-white border p-4">
        These are in-app notifications. Your administrator must enable the scheduled notification worker;
        this page does not deliver email, SMS or mobile push alerts.
      </p>
      {demo && <p className="rounded-xl border bg-white p-4">Sign in to access your own notifications. Demo mode does not invent reminders.</p>}
      {error && <p role="alert" className="bg-red-50 border border-red-200 text-red-800 rounded-xl p-4 text-sm">{error}</p>}
      {!demo && <>
        <section className="bg-white rounded-2xl border p-4 flex flex-wrap justify-between gap-3 items-center">
          <label className="flex gap-2 items-center text-sm">
            <input type="checkbox" className="accent-peach" checked={unreadOnly}
              onChange={event => setUnreadOnly(event.target.checked)} /> Unread only
          </label>
          <div className="flex gap-3 items-center">
            <span className="text-sm text-dark-muted">{unread.length} unread</span>
            <button type="button" disabled={working || unread.length === 0}
              onClick={() => mutate(() => api.post('/api/v2/notifications/mark-all-read'), 'All notifications marked read')}
              className="flex gap-2 items-center text-sm border rounded-xl px-3 py-2 disabled:opacity-50">
              <CheckCheck className="w-4 h-4"/> Mark all read
            </button>
          </div>
        </section>
        <section className="bg-white border rounded-2xl p-5 space-y-3">
          {loading && <p className="text-sm text-dark-muted">Loading notifications...</p>}
          {!loading && visible.length === 0 && (
            <div className="text-center py-12 space-y-2">
              <BellOff className="w-9 h-9 mx-auto text-peach"/>
              <p className="font-semibold">Nothing to review</p>
              <p className="text-sm text-dark-muted">New reminders will appear after the scheduled worker runs.</p>
            </div>
          )}
          {!loading && visible.map(item => (
            <div key={item.id} className={`flex gap-3 justify-between rounded-xl p-4 border ${item.read_at ? 'bg-gray-50 border-gray-100' : 'border-peach/50'}`}>
              <Bell className="w-5 h-5 shrink-0 text-peach mt-1"/>
              <div className="flex-1 min-w-0">
                <p className="text-xs font-semibold uppercase text-peach-dark">{notificationLabel(item)}</p>
                <p className="font-medium mt-1">{item.message}</p>
                <p className="text-xs text-dark-muted mt-1">{new Date(item.created_at).toLocaleString()}</p>
              </div>
              {!item.read_at && (
                <button type="button" disabled={working} onClick={() =>
                  mutate(() => api.post('/api/v2/notifications/' + item.id + '/read'), 'Notification marked read')}
                  className="self-start border rounded-lg px-3 py-2 text-xs disabled:opacity-50">Mark read</button>
              )}
            </div>
          ))}
        </section>
        <Link to="/tasks-v2" className="inline-flex text-sm text-peach-dark gap-2 items-center underline">
          <CalendarClock className="w-4 h-4"/> Manage task deadlines
        </Link>
      </>}
    </div>
  )
}
