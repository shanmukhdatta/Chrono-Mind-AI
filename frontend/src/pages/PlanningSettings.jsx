import React, { useCallback, useEffect, useState } from 'react'
import { Clock3, Save, RefreshCw, SlidersHorizontal } from 'lucide-react'
import toast from 'react-hot-toast'
import api from '../lib/api'
import { normalizePlanningPreferences } from '../lib/planningPreferences'
import { useAuthStore } from '../store/authStore'

const defaults = {
  timezone: 'Asia/Kolkata', work_start: '08:00', work_end: '22:00',
  max_daily_minutes: 480, min_break_minutes: 10,
}

function errorText(error) {
  const detail = error?.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (error?.response?.status === 503) return 'V2 PostgreSQL storage is not configured. Your existing tasks are unaffected.'
  return error?.message || 'Unable to save preferences'
}

export default function PlanningSettings() {
  const isDemo = useAuthStore(s => s.user?.uid === 'demo')
  const [form, setForm] = useState(defaults)
  const [loading, setLoading] = useState(!isDemo)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const refresh = useCallback(async () => {
    if (isDemo) return
    setLoading(true)
    try {
      const response = await api.get('/api/v2/preferences')
      const data = response.data
      setForm({
        timezone: data.timezone,
        work_start: data.work_start.slice(0, 5),
        work_end: data.work_end.slice(0, 5),
        max_daily_minutes: data.max_daily_minutes,
        min_break_minutes: data.min_break_minutes,
      })
      setError('')
    } catch (err) {
      setError(errorText(err))
    } finally {
      setLoading(false)
    }
  }, [isDemo])

  useEffect(() => { refresh() }, [refresh])

  const change = (field, value) => setForm(current => ({ ...current, [field]: value }))

  const save = async (event) => {
    event.preventDefault()
    setSaving(true)
    try {
      const normalized = normalizePlanningPreferences(form)
      const response = await api.put('/api/v2/preferences', normalized)
      const data = response.data
      setForm({
        ...data, work_start: data.work_start.slice(0, 5),
        work_end: data.work_end.slice(0, 5),
      })
      setError('')
      toast.success('Planning preferences saved')
    } catch (err) {
      const message = errorText(err)
      setError(message)
      toast.error(message)
    } finally {
      setSaving(false)
    }
  }

  if (isDemo) return (
    <section className="max-w-2xl bg-white border rounded-2xl p-6">
      <h1 className="text-2xl font-bold">Planning preferences</h1>
      <p className="mt-2 text-dark-muted">Sign in to store your planning settings. Demo changes are not persisted.</p>
    </section>
  )

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <header className="flex items-start justify-between gap-3">
        <div>
          <p className="text-peach-dark text-sm font-semibold flex gap-2 items-center">
            <SlidersHorizontal className="w-4 h-4" /> Personalize your planner
          </p>
          <h1 className="text-3xl font-bold text-dark mt-1">Planning preferences</h1>
          <p className="text-dark-muted mt-2 text-sm">Set boundaries that the future scheduling agent must respect.</p>
        </div>
        <button type="button" onClick={refresh} className="p-3 bg-white border rounded-xl" aria-label="Reload preferences">
          <RefreshCw className="w-5 h-5" />
        </button>
      </header>
      {error && <p role="alert" className="bg-red-50 border border-red-200 text-red-800 p-4 rounded-xl text-sm">{error}</p>}
      {loading ? <p>Loading saved preferences...</p> : (
        <form onSubmit={save} className="bg-white border border-gray-100 rounded-2xl shadow-sm p-6 space-y-6">
          <div className="flex items-center gap-2">
            <Clock3 className="w-5 h-5 text-peach" />
            <h2 className="font-semibold">Your working hours</h2>
          </div>
          <label className="block text-sm font-medium">Time zone (IANA name)
            <input className="input-field mt-1" required maxLength={64} list="common-timezones"
              value={form.timezone} onChange={e => change('timezone', e.target.value)} />
            <datalist id="common-timezones">
              <option value="Asia/Kolkata" />
              <option value="UTC" />
              <option value="Europe/London" />
              <option value="America/New_York" />
              <option value="Asia/Singapore" />
            </datalist>
          </label>
          <div className="grid sm:grid-cols-2 gap-4">
            <label className="block text-sm font-medium">Start of work day
              <input required className="input-field mt-1" type="time" value={form.work_start}
                onChange={e => change('work_start', e.target.value)} />
            </label>
            <label className="block text-sm font-medium">End of work day
              <input required className="input-field mt-1" type="time" value={form.work_end}
                onChange={e => change('work_end', e.target.value)} />
            </label>
          </div>
          <div className="grid sm:grid-cols-2 gap-4">
            <label className="block text-sm font-medium">Maximum work minutes per day
              <input required className="input-field mt-1" type="number" min="60" max="960"
                value={form.max_daily_minutes}
                onChange={e => change('max_daily_minutes', e.target.value)} />
            </label>
            <label className="block text-sm font-medium">Minimum break between sessions (minutes)
              <input required className="input-field mt-1" type="number" min="0" max="120"
                value={form.min_break_minutes}
                onChange={e => change('min_break_minutes', e.target.value)} />
            </label>
          </div>
          <p className="text-sm text-dark-muted">
            These limits are persisted in PostgreSQL. The scheduling engine will enforce them when its planning phase is implemented.
          </p>
          <button type="submit" className="btn-primary flex gap-2 items-center" disabled={saving}>
            <Save className="w-4 h-4" /> {saving ? 'Saving...' : 'Save preferences'}
          </button>
        </form>
      )}
    </div>
  )
}
