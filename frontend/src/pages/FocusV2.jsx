import React, { useCallback, useEffect, useState } from 'react'
import { Clock3, Play, Square, CheckCircle2, RefreshCw, ShieldCheck, BarChart3 } from 'lucide-react'
import toast from 'react-hot-toast'
import api from '../lib/api'
import { useAuthStore } from '../store/authStore'
import { focusClock, formatFocusMinutes } from '../lib/focusV2'

function errorText(error) {
  if (typeof error?.response?.data?.detail === 'string') return error.response.data.detail
  if (error?.response?.status === 503) return 'The PostgreSQL focus service is not configured yet.'
  return error.message || 'Focus service is unavailable'
}

export default function FocusV2() {
  const demo = useAuthStore(s => s.user?.uid === 'demo')
  const [sessions, setSessions] = useState([])
  const [tasks, setTasks] = useState([])
  const [insights, setInsights] = useState(null)
  const [consent, setConsent] = useState(false)
  const [taskId, setTaskId] = useState('')
  const [minutes, setMinutes] = useState(25)
  const [clock, setClock] = useState(Date.now())
  const [busy, setBusy] = useState(false)
  const [loading, setLoading] = useState(!demo)
  const [error, setError] = useState('')

  useEffect(() => {
    const id = window.setInterval(() => setClock(Date.now()), 1000)
    return () => window.clearInterval(id)
  }, [])

  const refresh = useCallback(async () => {
    if (demo) return
    try {
      const results = await Promise.all([
        api.get('/api/v2/focus/sessions'),
        api.get('/api/v2/focus/insights'),
        api.get('/api/v2/focus/consent'),
        api.get('/api/v2/tasks', { params: { status: 'pending' } }),
      ])
      setSessions(results[0].data)
      setInsights(results[1].data)
      setConsent(results[2].data.enabled)
      setTasks(results[3].data)
      setError('')
    } catch (err) {
      setError(errorText(err))
    } finally {
      setLoading(false)
    }
  }, [demo])

  useEffect(() => { refresh() }, [refresh])

  const act = async (operation, success) => {
    setBusy(true)
    setError('')
    try {
      await operation()
      toast.success(success)
      await refresh()
    } catch (err) {
      const msg = errorText(err)
      setError(msg)
      toast.error(msg)
    } finally {
      setBusy(false)
    }
  }

  const begin = () => act(
    () => api.post('/api/v2/focus/sessions', {
      task_id: taskId || null, planned_minutes: Number(minutes)
    }), 'Focus session started'
  )

  const end = (id, outcome) => act(
    () => api.post('/api/v2/focus/sessions/' + id + '/finish', { outcome }),
    outcome === 'completed' ? 'Session completed' : 'Session ended'
  )

  const toggleConsent = event => {
    const enabled = event.target.checked
    act(
      () => api.put('/api/v2/focus/consent', { enabled }),
      enabled ? 'Behavior insights enabled' : 'Behavior insights disabled and history cleared'
    )
  }

  const active = sessions.find(session => session.status === 'active')
  const display = focusClock(active, clock)
  const finished = sessions.filter(session => session.status === 'completed')

  return (
    <div className="max-w-5xl mx-auto space-y-5">
      <header>
        <p className="text-sm text-peach-dark font-semibold">Stay focused, at your own pace</p>
        <h1 className="text-3xl font-bold text-dark">Focus Studio</h1>
        <p className="text-sm text-dark-muted mt-2">
          Session timing is recorded by the server. Closing or refreshing this page does not reset an active session.
        </p>
      </header>
      {demo && <div className="rounded-xl border bg-white p-5">Sign in to use persistent focus tracking. Demo mode does not invent completed sessions.</div>}
      {error && <div role="alert" className="rounded-xl border border-red-200 bg-red-50 p-4 text-red-800 text-sm">{error}</div>}
      {!demo && (loading ? <p>Loading focus records...</p> : (
        <>
          <div className="grid lg:grid-cols-[1.2fr_1fr] gap-5">
            <section className="rounded-2xl bg-white border p-6 space-y-5">
              <h2 className="font-semibold text-lg flex items-center gap-2"><Clock3 className="w-5 h-5 text-peach"/> Focus timer</h2>
              <div className="text-center py-4">
                <p className="text-6xl font-bold tabular-nums">{active ? display.label : String(minutes).padStart(2, '0') + ':00'}</p>
                <p className="text-sm text-dark-muted mt-3">{active ? 'Session in progress' : 'Ready to begin'}</p>
              </div>
              {!active ? (
                <div className="space-y-4">
                  <label className="block text-sm font-medium">Session duration
                    <select className="input-field mt-1" value={minutes} onChange={e => setMinutes(Number(e.target.value))}>
                      {[10, 15, 25, 30, 45, 60, 90, 120].map(value => <option key={value} value={value}>{value} minutes</option>)}
                    </select>
                  </label>
                  <label className="block text-sm font-medium">Task (optional)
                    <select className="input-field mt-1" value={taskId} onChange={e => setTaskId(e.target.value)}>
                      <option value="">General focus</option>
                      {tasks.map(task => <option key={task.id} value={task.id}>{task.title}</option>)}
                    </select>
                  </label>
                  <button type="button" disabled={busy} onClick={begin} className="btn-primary flex items-center justify-center gap-2 w-full">
                    <Play className="w-4 h-4" /> Begin focus
                  </button>
                </div>
              ) : (
                <div className="flex flex-col sm:flex-row gap-2">
                  <button type="button" disabled={busy} onClick={() => end(active.id, 'completed')}
                    className="btn-primary flex flex-1 gap-2 items-center justify-center">
                    <CheckCircle2 className="w-4 h-4" /> Complete session
                  </button>
                  <button type="button" disabled={busy} onClick={() => end(active.id, 'abandoned')}
                    className="border rounded-xl px-4 py-3 flex gap-2 items-center justify-center">
                    <Square className="w-4 h-4" /> End early
                  </button>
                </div>
              )}
            </section>
            <section className="rounded-2xl bg-white border p-6 space-y-5">
              <h2 className="font-semibold text-lg flex items-center gap-2"><BarChart3 className="w-5 h-5 text-peach"/> Your focus history</h2>
              <div className="grid grid-cols-2 gap-3">
                <div className="rounded-xl bg-peach/10 p-4">
                  <p className="text-3xl font-bold">{insights?.completed_sessions ?? 0}</p>
                  <p className="text-sm text-dark-muted">Completed sessions</p>
                </div>
                <div className="rounded-xl bg-peach/10 p-4">
                  <p className="text-3xl font-bold">{insights?.completed_minutes ?? 0}</p>
                  <p className="text-sm text-dark-muted">Recorded minutes</p>
                </div>
              </div>
              <label className="flex gap-3 items-start text-sm">
                <input type="checkbox" className="mt-1 accent-peach" checked={consent} disabled={busy}
                  onChange={toggleConsent}/>
                <span><strong>Enable behavioral insights</strong>
                  <span className="block text-dark-muted mt-1">Optional. Records only session start-hour and duration. Turning it off deletes those behavior signals.</span>
                </span>
              </label>
              <div className="rounded-xl border p-4 text-sm">
                <div className="flex items-center gap-2 font-semibold"><ShieldCheck className="w-4 h-4 text-peach"/> Personalization</div>
                {insights?.preferred_hour != null
                  ? <p className="mt-2">Your most consistently practiced hour starts at {String(insights.preferred_hour).padStart(2, '0')}:00.</p>
                  : <p className="mt-2 text-dark-muted">{insights?.reason || 'No behavior suggestion yet.'}</p>}
                {consent && <p className="mt-2 text-xs text-dark-muted">{insights?.sample_size || 0} opted-in completed sessions available.</p>}
              </div>
            </section>
          </div>
          <section className="rounded-2xl bg-white border p-5 space-y-3">
            <div className="flex justify-between items-center gap-2">
              <h2 className="font-semibold">Recent sessions</h2>
              <button type="button" aria-label="Refresh focus sessions" onClick={refresh} className="p-2 hover:bg-gray-50 rounded-lg"><RefreshCw className="w-4 h-4"/></button>
            </div>
            {sessions.length === 0 && <p className="text-sm text-dark-muted py-5">No focus sessions yet.</p>}
            {sessions.slice(0, 20).map(session => (
              <div key={session.id} className="flex justify-between items-center gap-3 border-t pt-3">
                <div className="min-w-0">
                  <p className="text-sm font-medium capitalize">{session.status}</p>
                  <p className="text-xs text-dark-muted">{new Date(session.started_at).toLocaleString()}</p>
                </div>
                <p className="text-sm text-dark-muted">{formatFocusMinutes(session.actual_seconds)} recorded min</p>
              </div>
            ))}
          </section>
        </>
      ))}
    </div>
  )
}
