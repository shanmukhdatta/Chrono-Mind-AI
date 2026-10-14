import React, { useCallback, useEffect, useState } from 'react'
import { Repeat2, Plus, Pause, Play, CalendarPlus, CalendarX2, RefreshCw } from 'lucide-react'
import toast from 'react-hot-toast'
import api from '../lib/api'
import { useAuthStore } from '../store/authStore'
import { recurrencePayload } from '../lib/recurrenceV2'

const weekdays = [
  ['Mon', 0], ['Tue', 1], ['Wed', 2], ['Thu', 3],
  ['Fri', 4], ['Sat', 5], ['Sun', 6],
]

function todayLocal() {
  const local = new Date()
  const yyyy = local.getFullYear()
  return [yyyy, String(local.getMonth() + 1).padStart(2, '0'), String(local.getDate()).padStart(2, '0')].join('-')
}

function errorText(error) {
  if (typeof error.response?.data?.detail === 'string') return error.response.data.detail
  if (error.response?.status === 503) return 'PostgreSQL recurrence storage is not configured.'
  return error.message || 'Recurrence operation failed'
}

export default function RecurrenceV2() {
  const demo = useAuthStore(state => state.user?.uid === 'demo')
  const [series, setSeries] = useState([])
  const [formOpen, setFormOpen] = useState(false)
  const [title, setTitle] = useState('')
  const [frequency, setFrequency] = useState('daily')
  const [selectedDays, setSelectedDays] = useState([0, 2, 4])
  const [duration, setDuration] = useState(30)
  const [importance, setImportance] = useState('important')
  const [timezone, setTimezone] = useState(Intl.DateTimeFormat().resolvedOptions().timeZone || 'Asia/Kolkata')
  const [dueTime, setDueTime] = useState('')
  const [startDate, setStartDate] = useState(todayLocal)
  const [endDate, setEndDate] = useState('')
  const [skipDates, setSkipDates] = useState({})
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(!demo)
  const [working, setWorking] = useState(false)

  const refresh = useCallback(async () => {
    if (demo) return
    setLoading(true)
    try {
      const response = await api.get('/api/v2/recurrence')
      setSeries(response.data)
      setError('')
    } catch (err) {
      setError(errorText(err))
    } finally {
      setLoading(false)
    }
  }, [demo])

  useEffect(() => { refresh() }, [refresh])

  const action = async (operation, success) => {
    setWorking(true)
    setError('')
    try {
      const result = await operation()
      await refresh()
      toast.success(success instanceof Function ? success(result.data) : success)
    } catch (err) {
      const explanation = errorText(err)
      setError(explanation)
      toast.error(explanation)
    } finally {
      setWorking(false)
    }
  }

  const create = event => {
    event.preventDefault()
    const body = recurrencePayload({
      title, frequency, weekdays: selectedDays, duration_minutes: duration, importance,
      timezone, due_time: dueTime, start_date: startDate, end_date: endDate,
    })
    action(
      () => api.post('/api/v2/recurrence', body),
      'Recurring routine created. Generate occurrences to add future tasks.'
    )
    setFormOpen(false)
  }

  const toggleDay = day => {
    setSelectedDays(existing => existing.includes(day)
      ? existing.filter(x => x !== day) : [...existing, day].sort())
  }

  return (
    <div className="max-w-5xl mx-auto space-y-5">
      <header className="flex flex-col sm:flex-row justify-between gap-3">
        <div>
          <p className="text-peach-dark text-sm font-semibold">Build repeatable routines</p>
          <h1 className="text-3xl font-bold text-dark">Recurring tasks</h1>
          <p className="text-sm text-dark-muted mt-2">
            Daily, weekly, or monthly templates generate task occurrences without duplicating existing records.
          </p>
        </div>
        <button type="button" disabled={demo} className="btn-primary flex gap-2 items-center justify-center"
          onClick={() => setFormOpen(open => !open)}>
          <Plus className="w-4 h-4"/> New routine
        </button>
      </header>
      {demo && <p className="rounded-xl bg-white border p-4">Sign in to use persistent recurring tasks.</p>}
      {error && <p role="alert" className="rounded-xl bg-red-50 border border-red-200 text-sm text-red-800 p-4">{error}</p>}
      {!demo && <>
        {formOpen && (
          <form onSubmit={create} className="bg-white rounded-2xl border p-5 space-y-4">
            <h2 className="font-semibold text-lg">Create routine</h2>
            <label className="block text-sm font-medium">Title
              <input className="input-field mt-1" required maxLength={160} value={title}
                onChange={e => setTitle(e.target.value)} placeholder="Morning programming practice"/>
            </label>
            <div className="grid sm:grid-cols-2 gap-4">
              <label className="block text-sm font-medium">Frequency
                <select className="input-field mt-1" value={frequency} onChange={e => setFrequency(e.target.value)}>
                  <option value="daily">Every day</option>
                  <option value="weekly">Selected weekdays</option>
                  <option value="monthly">Monthly</option>
                </select>
              </label>
              <label className="block text-sm font-medium">Duration (minutes)
                <input className="input-field mt-1" type="number" min="1" max="1440" required
                  value={duration} onChange={e => setDuration(e.target.value)}/>
              </label>
            </div>
            {frequency === 'weekly' && (
              <fieldset className="space-y-2">
                <legend className="text-sm font-medium">Weekdays</legend>
                <div className="flex flex-wrap gap-2">
                  {weekdays.map(([label, day]) => (
                    <label key={day} className={`border rounded-xl px-3 py-2 text-sm cursor-pointer ${selectedDays.includes(day) ? 'border-peach bg-peach/10' : ''}`}>
                      <input type="checkbox" className="sr-only" checked={selectedDays.includes(day)}
                        onChange={() => toggleDay(day)}/>{label}
                    </label>
                  ))}
                </div>
              </fieldset>
            )}
            <div className="grid sm:grid-cols-2 gap-4">
              <label className="block text-sm font-medium">Start date
                <input className="input-field mt-1" type="date" required value={startDate}
                  onChange={e => setStartDate(e.target.value)}/>
              </label>
              <label className="block text-sm font-medium">End date (optional)
                <input className="input-field mt-1" type="date" value={endDate}
                  onChange={e => setEndDate(e.target.value)}/>
              </label>
              <label className="block text-sm font-medium">Due time (optional)
                <input className="input-field mt-1" type="time" value={dueTime}
                  onChange={e => setDueTime(e.target.value)}/>
              </label>
              <label className="block text-sm font-medium">Timezone
                <input className="input-field mt-1" required value={timezone} maxLength={64}
                  onChange={e => setTimezone(e.target.value)}/>
              </label>
              <label className="block text-sm font-medium">Importance
                <select className="input-field mt-1" value={importance}
                  onChange={e => setImportance(e.target.value)}>
                  <option value="important">Important</option>
                  <option value="not_important">Optional</option>
                </select>
              </label>
            </div>
            <div className="flex gap-3">
              <button className="btn-primary" disabled={working} type="submit">Create routine</button>
              <button type="button" className="border rounded-xl px-4 py-2" onClick={() => setFormOpen(false)}>Cancel</button>
            </div>
          </form>
        )}
        <section className="rounded-2xl bg-white border p-5 space-y-3">
          <div className="flex justify-between gap-3 items-center">
            <h2 className="font-semibold text-lg">Your routines ({series.length})</h2>
            <button type="button" onClick={refresh} aria-label="Refresh routines" className="p-2 hover:bg-gray-100 rounded-lg">
              <RefreshCw className="w-5 h-5"/>
            </button>
          </div>
          {loading && <p className="text-sm text-dark-muted">Loading recurring tasks...</p>}
          {!loading && series.length === 0 && <p className="text-center text-sm text-dark-muted py-10">No routines yet.</p>}
          {!loading && series.map(item => (
            <div key={item.id} className="border rounded-xl p-4 space-y-3">
              <div className="flex flex-wrap gap-2 justify-between">
                <div>
                  <p className="font-semibold">{item.title}</p>
                  <p className="text-sm text-dark-muted mt-1">
                    {item.frequency === 'daily' ? 'Every day' : 'Weekly · '+item.weekdays.map(d => weekdays[d]?.[0]).join(', ')}
                    {' · '}{item.duration_minutes} min · {item.timezone}
                  </p>
                  <p className="text-xs text-dark-muted mt-1">
                    Starting {item.start_date}{item.end_date ? ' through ' + item.end_date : ''}
                    {item.due_time ? ' · Due at ' + item.due_time.slice(0,5) : ''}
                  </p>
                </div>
                <span className={`self-start text-xs px-2 py-1 border rounded-lg ${item.active ? 'bg-green-50 text-green-700' : 'bg-gray-100 text-dark-muted'}`}>
                  {item.active ? 'Active' : 'Paused'}
                </span>
              </div>
              <div className="flex gap-2 flex-wrap">
                <button type="button" disabled={working || !item.active} onClick={() =>
                  action(() => api.post('/api/v2/recurrence/' + item.id + '/materialize', {}, {params:{days:30}}),
                    result => result.created + ' future tasks generated')}
                  className="border rounded-lg px-3 py-2 text-sm flex items-center gap-2">
                  <CalendarPlus className="w-4 h-4"/> Generate next 30 days
                </button>
                <button type="button" disabled={working} onClick={() =>
                  action(() => api.post('/api/v2/recurrence/' + item.id + '/' + (item.active ? 'pause' : 'resume')),
                    item.active ? 'Routine paused; existing tasks preserved' : 'Routine resumed')}
                  className="border rounded-lg px-3 py-2 text-sm flex items-center gap-2">
                  {item.active ? <Pause className="w-4 h-4"/> : <Play className="w-4 h-4"/>}
                  {item.active ? 'Pause' : 'Resume'}
                </button>
              </div>
              <div className="flex flex-wrap gap-2 items-end border-t pt-3">
                <label className="text-sm">Skip one future date
                  <input className="input-field mt-1" type="date" min={todayLocal()}
                    value={skipDates[item.id] || ''} onChange={event =>
                      setSkipDates(current => ({...current,[item.id]:event.target.value}))}/>
                </label>
                <button type="button" disabled={working || !skipDates[item.id]} onClick={() =>
                  action(() => api.post('/api/v2/recurrence/' + item.id + '/skip', {
                    occurrence_date: skipDates[item.id]
                  }), 'Occurrence skipped; completed tasks remain untouched')}
                  className="border rounded-lg px-3 py-3 text-sm flex items-center gap-2">
                  <CalendarX2 className="w-4 h-4"/> Skip
                </button>
              </div>
            </div>
          ))}
        </section>
        <p className="text-xs text-dark-muted">
          New tasks appear in V2 Tasks after you choose Generate. Automatic horizon extension is not active until a managed background job is deployed.
        </p>
      </>}
    </div>
  )
}
