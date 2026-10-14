import React, { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { LayoutDashboard, Target, ListTodo, CalendarDays, Sparkles, ClipboardCheck, Clock3, AlertTriangle, RefreshCw } from 'lucide-react'
import api from '../lib/api'
import { useAuthStore } from '../store/authStore'
import { completionBars } from '../lib/dashboardV2'

function errorText(error) {
  if (typeof error.response?.data?.detail === 'string') return error.response.data.detail
  if (error.response?.status === 503) return 'V2 PostgreSQL is not configured; legacy Firestore tasks are unaffected.'
  return error.message || 'Could not load dashboard'
}

const links = [
  { path: '/tasks-v2', label: 'Manage tasks', icon: ListTodo },
  { path: '/goals', label: 'Manage goals', icon: Target },
  { path: '/calendar-v2', label: 'My calendar', icon: CalendarDays },
  { path: '/planning', label: 'Build a plan', icon: Sparkles },
  { path: '/approvals', label: 'Review approvals', icon: ClipboardCheck },
]

export default function DashboardV2() {
  const demo = useAuthStore(s => s.user?.uid === 'demo')
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(!demo)
  const [error, setError] = useState('')

  const refresh = useCallback(async () => {
    if (demo) return
    setLoading(true)
    try {
      const response = await api.get('/api/v2/dashboard')
      setData(response.data)
      setError('')
    } catch (err) {
      setError(errorText(err))
    } finally {
      setLoading(false)
    }
  }, [demo])

  useEffect(() => { refresh() }, [refresh])
  const bars = completionBars(data?.completed_last_seven_days)
  const metrics = data ? [
    { title: 'Pending tasks', value: data.pending_count, icon: ListTodo },
    { title: 'Completed', value: data.completed_count, icon: Target },
    { title: 'Overdue', value: data.overdue_count, icon: AlertTriangle },
    { title: 'Scheduled today', value: data.scheduled_minutes_today + ' min', icon: Clock3 },
    { title: 'Active goals', value: data.active_goals, icon: Sparkles },
    { title: 'Completion rate', value: data.completion_rate + '%', icon: LayoutDashboard },
  ] : []

  return (
    <div className="max-w-6xl mx-auto space-y-5">
      <header className="flex flex-col sm:flex-row justify-between gap-3">
        <div>
          <p className="text-sm font-semibold text-peach-dark">Your plan, at a glance</p>
          <h1 className="text-3xl font-bold text-dark">ChronoMind Dashboard V2</h1>
          <p className="text-sm text-dark-muted mt-2">Real PostgreSQL metrics, transparent priorities, and your next actions.</p>
        </div>
        <button type="button" disabled={demo} aria-label="Refresh dashboard" onClick={refresh} className="self-start p-3 rounded-xl border bg-white">
          <RefreshCw className="w-5 h-5"/>
        </button>
      </header>
      {demo && <p className="rounded-xl border bg-white p-5">Sign in to view your own real V2 dashboard data. No sample stats are presented as real achievements.</p>}
      {error && <p role="alert" className="p-4 border border-red-200 bg-red-50 rounded-xl text-sm text-red-800">{error}</p>}
      {!demo && (
        <>
          {loading && <p className="text-sm text-dark-muted">Loading dashboard...</p>}
          {data && (
            <>
              <div className="grid grid-cols-2 lg:grid-cols-3 gap-3">
                {metrics.map(({title,value,icon:Icon}) => (
                  <div key={title} className="rounded-2xl bg-white border p-5 space-y-3">
                    <Icon className="w-5 h-5 text-peach" />
                    <p className="text-2xl font-bold">{value}</p>
                    <p className="text-sm text-dark-muted">{title}</p>
                  </div>
                ))}
              </div>
              <div className="grid lg:grid-cols-[1.3fr_1fr] gap-5">
                <section className="bg-white rounded-2xl border p-5 space-y-3">
                  <h2 className="font-semibold text-lg">Top priorities</h2>
                  <p className="text-sm text-dark-muted">Scores combine importance, due dates, and active goals. Scores are rules, not predictions.</p>
                  {data.top_priorities.length === 0 && <p className="text-dark-muted text-sm py-6">No pending tasks. Add one to begin.</p>}
                  {data.top_priorities.map(task => (
                    <div key={task.id} className="border rounded-xl p-4 flex gap-3 items-start justify-between">
                      <div>
                        <p className="font-semibold">{task.title}</p>
                        <p className="text-xs text-dark-muted mt-1">{task.priority_reasons.join(' · ')}</p>
                        <p className="text-xs text-dark-muted mt-1">
                          {task.duration_minutes} min
                          {task.deadline_at ? ' · Due ' + new Date(task.deadline_at).toLocaleString() : ''}
                        </p>
                      </div>
                      <span className="bg-peach/10 text-peach-dark rounded-lg p-2 text-sm font-bold shrink-0">
                        {task.priority_score}
                      </span>
                    </div>
                  ))}
                </section>
                <div className="space-y-5">
                  <section className="bg-white rounded-2xl border p-5 space-y-3">
                    <h2 className="font-semibold text-lg">Recent completions</h2>
                    <p className="text-sm text-dark-muted">Completed tasks per day · past 7 days</p>
                    <div className="flex items-end justify-between gap-2 h-36 pt-2">
                      {bars.map(bar => (
                        <div key={bar.date} className="flex flex-col items-center gap-2 flex-1 h-full justify-end" title={bar.date + ': ' + bar.completed + ' tasks'}>
                          <span className="text-xs text-dark-muted">{bar.completed}</span>
                          <div className="rounded-t-lg bg-peach w-full max-w-10" style={{ height: bar.heightPercent + '%', minHeight:'3px' }} />
                          <span className="text-[10px] text-dark-muted">{bar.label}</span>
                        </div>
                      ))}
                    </div>
                  </section>
                  <section className="bg-white rounded-2xl border p-5 space-y-3">
                    <h2 className="font-semibold text-lg">Quick actions</h2>
                    {links.map(({path,label,icon:Icon}) => (
                      <Link to={path} key={path} className="border rounded-xl px-4 py-3 flex gap-2 items-center text-sm hover:border-peach">
                        <Icon className="w-4 h-4 text-peach-dark"/>{label}
                      </Link>
                    ))}
                  </section>
                </div>
              </div>
              <p className="text-xs text-dark-muted">
                Data updated for {data.today} ({data.timezone}). V1 Firestore records are not combined until verified migration.
              </p>
            </>
          )}
        </>
      )}
    </div>
  )
}
