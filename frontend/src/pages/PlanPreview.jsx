import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { CalendarDays, Clock3, RefreshCw, AlertTriangle, ShieldCheck } from 'lucide-react'
import api from '../lib/api'
import { useAuthStore } from '../store/authStore'
import { summarizePlan, formatPlanInstant } from '../lib/planPreview'

function describeError(error) {
  if (typeof error.response?.data?.detail === 'string') return error.response.data.detail
  if (error.response?.status === 503) return 'PostgreSQL V2 is not configured. Existing calendar data is unaffected.'
  return error.message || 'Could not compute a schedule.'
}

export default function PlanPreview() {
  const demo = useAuthStore(s => s.user?.uid === 'demo')
  const navigate = useNavigate()
  const [days, setDays] = useState(7)
  const [preview, setPreview] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const generate = async () => {
    setBusy(true)
    setError('')
    setPreview(null)
    try {
      const response = await api.get('/api/v2/planning/preview', { params: { days } })
      setPreview(response.data)
    } catch (err) {
      setError(describeError(err))
    } finally {
      setBusy(false)
    }
  }

  const requestApproval = async () => {
    setBusy(true)
    setError('')
    try {
      const response = await api.post('/api/v2/plans', { days })
      navigate('/approvals?planId=' + encodeURIComponent(response.data.id))
    } catch (err) {
      setError(describeError(err))
    } finally {
      setBusy(false)
    }
  }

  const summary = summarizePlan(preview)

  return (
    <div className="max-w-5xl mx-auto space-y-5">
      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
        <div>
          <p className="text-peach-dark text-sm font-semibold">Scheduling engine</p>
          <h1 className="text-3xl font-bold text-dark">Plan Preview</h1>
          <p className="text-sm text-dark-muted mt-2">
            Review conflict-aware suggestions before any changes are made.
          </p>
        </div>
      </div>

      <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 flex gap-3">
        <ShieldCheck className="w-5 h-5 text-amber-700 shrink-0 mt-0.5" />
        <div>
          <p className="text-amber-900 font-semibold text-sm">Read-only preview</p>
          <p className="text-amber-900/90 text-sm mt-1">
            Previews do not change your calendar. You may create a durable proposal, review it, and explicitly approve it.
          </p>
        </div>
      </div>

      {demo && (
        <div role="alert" className="bg-white rounded-xl p-5 border">
          Sign in to use real task and preference data. Demo mode does not simulate saved planning results.
        </div>
      )}

      {!demo && (
        <section className="flex flex-col sm:flex-row sm:items-end gap-3 p-4 bg-white border border-gray-100 shadow-sm rounded-2xl">
          <label className="text-sm font-semibold">Plan for
            <select className="input-field mt-1" value={days} onChange={e => setDays(Number(e.target.value))}>
              <option value={3}>Next 3 days</option>
              <option value={7}>Next 7 days</option>
              <option value={14}>Next 14 days</option>
            </select>
          </label>
          <button className="btn-primary flex gap-2 items-center justify-center" type="button" disabled={busy}
            onClick={generate}>
            <RefreshCw className="w-4 h-4" /> {busy ? 'Calculating...' : 'Generate preview'}
          </button>
        </section>
      )}

      {error && <p role="alert" className="p-4 rounded-xl border bg-red-50 border-red-200 text-red-700 text-sm">{error}</p>}

      {preview && (
        <div className="space-y-5">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {[
              ['Proposed sessions', summary.sessions],
              ['Planned minutes', summary.plannedMinutes],
              ['Remaining minutes', summary.remainingMinutes]
            ].map(([label, value]) => (
              <div key={label} className="bg-white p-5 rounded-xl border border-gray-100 shadow-sm">
                <p className="text-sm text-dark-muted">{label}</p>
                <p className="text-3xl font-bold mt-2 text-dark">{value}</p>
              </div>
            ))}
          </div>
          <section className="bg-white border border-gray-100 rounded-2xl p-5 space-y-3">
            <h2 className="text-lg font-semibold flex gap-2 items-center">
              <CalendarDays className="w-5 h-5 text-peach" /> Suggested work blocks
            </h2>
            {preview.blocks.length === 0 && (
              <p className="text-dark-muted text-sm py-4">No new sessions fit this period. Try a longer planning horizon or update task priorities and working hours.</p>
            )}
            {[...preview.blocks].sort((a,b) => a.starts_at.localeCompare(b.starts_at)).map((block, index) => (
              <div key={block.task_id + block.starts_at + index} className="border rounded-xl px-4 py-3 flex flex-col sm:flex-row sm:justify-between gap-2">
                <div>
                  <p className="font-semibold text-dark">{block.title}</p>
                  <p className="text-sm text-dark-muted">{formatPlanInstant(block.starts_at, preview.timezone)} – {formatPlanInstant(block.ends_at, preview.timezone)}</p>
                </div>
                <span className="inline-flex items-center text-sm gap-1 text-peach-dark">
                  <Clock3 className="w-4 h-4" /> {block.duration_minutes} min
                </span>
              </div>
            ))}
          </section>
          {preview.unscheduled.length > 0 && (
            <section className="p-5 border border-amber-200 bg-amber-50 rounded-2xl space-y-3">
              <h2 className="font-semibold text-amber-900 flex items-center gap-2">
                <AlertTriangle className="w-5 h-5" /> Unscheduled work
              </h2>
              {preview.unscheduled.map(task => (
                <div key={task.task_id} className="text-sm border-t border-amber-200 pt-3">
                  <p className="font-semibold">{task.title} — {task.remaining_minutes} minutes remaining</p>
                  <p className="text-amber-900/80 mt-1">{task.reason}</p>
                </div>
              ))}
            </section>
          )}
          {preview.blocks.length > 0 && (
            <button type="button" disabled={busy} onClick={requestApproval} className="btn-primary">
              {busy ? 'Creating approval request...' : 'Review and approve this plan'}
            </button>
          )}
          <p className="text-xs text-dark-muted">
            Generated at {formatPlanInstant(preview.generated_at, preview.timezone)}. All suggestions are provisional and may become stale when tasks change.
          </p>
        </div>
      )}
    </div>
  )
}
