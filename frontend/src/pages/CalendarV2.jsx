import React, { useCallback, useEffect, useState } from 'react'
import { addDays, format, parseISO } from 'date-fns'
import { CalendarDays, ChevronLeft, ChevronRight, Plus, Pencil, Trash2, RefreshCw } from 'lucide-react'
import toast from 'react-hot-toast'
import api from '../lib/api'
import { useAuthStore } from '../store/authStore'
import { calendarDayWindow, localEventPayload } from '../lib/calendarV2'

function msg(error) {
  if (typeof error.response?.data?.detail === 'string') return error.response.data.detail
  if (error.response?.status === 503) return 'V2 PostgreSQL is not configured yet.'
  return error.message || 'Request failed'
}

const today = () => format(new Date(), 'yyyy-MM-dd')
const hour = instant => format(new Date(instant), 'HH:mm')

export default function CalendarV2() {
  const demo = useAuthStore(s => s.user?.uid === 'demo')
  const [day, setDay] = useState(today)
  const [events, setEvents] = useState([])
  const [blocks, setBlocks] = useState([])
  const [loading, setLoading] = useState(!demo)
  const [working, setWorking] = useState(false)
  const [error, setError] = useState('')
  const [editingId, setEditingId] = useState(null)
  const [showEditor, setShowEditor] = useState(false)
  const [title, setTitle] = useState('')
  const [start, setStart] = useState('09:00')
  const [end, setEnd] = useState('10:00')

  const refresh = useCallback(async () => {
    if (demo) return
    setLoading(true)
    try {
      const response = await api.get('/api/v2/calendar', { params: calendarDayWindow(day) })
      setEvents(response.data.fixed_events)
      setBlocks(response.data.task_blocks)
      setError('')
    } catch (err) {
      setError(msg(err))
    } finally {
      setLoading(false)
    }
  }, [day, demo])

  useEffect(() => { refresh() }, [refresh])

  const changeDay = amount => setDay(format(addDays(parseISO(day), amount), 'yyyy-MM-dd'))

  const beginNew = () => {
    setEditingId(null)
    setTitle('')
    setStart('09:00')
    setEnd('10:00')
    setShowEditor(true)
  }

  const beginEdit = event => {
    setEditingId(event.id)
    setTitle(event.title)
    setStart(hour(event.starts_at))
    setEnd(hour(event.ends_at))
    setShowEditor(true)
  }

  const save = async event => {
    event.preventDefault()
    setWorking(true)
    try {
      const payload = localEventPayload(day, title, start, end)
      if (editingId) {
        await api.put('/api/v2/fixed-events/' + editingId, payload)
      } else {
        await api.post('/api/v2/fixed-events', payload)
      }
      setShowEditor(false)
      await refresh()
      toast.success('Fixed commitment saved')
    } catch (err) {
      const message = msg(err)
      setError(message)
      toast.error(message)
    } finally {
      setWorking(false)
    }
  }

  const remove = async event => {
    if (!window.confirm('Delete this fixed commitment?')) return
    setWorking(true)
    try {
      await api.delete('/api/v2/fixed-events/' + event.id)
      await refresh()
      toast.success('Commitment removed')
    } catch (err) {
      const message = msg(err)
      setError(message)
      toast.error(message)
    } finally {
      setWorking(false)
    }
  }

  const all = [
    ...events.map(event => ({ ...event, kind: 'fixed' })),
    ...blocks.map(block => ({ ...block, kind: 'task' })),
  ].sort((a,b) => a.starts_at.localeCompare(b.starts_at))

  return (
    <div className="max-w-5xl mx-auto space-y-5">
      <header className="flex flex-col sm:flex-row justify-between gap-4">
        <div>
          <p className="text-sm font-semibold text-peach-dark">PostgreSQL-backed calendar</p>
          <h1 className="text-3xl font-bold text-dark">V2 Calendar</h1>
          <p className="text-sm text-dark-muted mt-2">Times are entered and displayed in your device timezone. Existing V1 Firestore calendar remains separate until migration.</p>
        </div>
        <button type="button" disabled={demo} onClick={beginNew} className="btn-primary flex gap-2 items-center justify-center">
          <Plus className="w-4 h-4" /> Add commitment
        </button>
      </header>
      {demo && <p role="alert" className="rounded-xl bg-white border p-4">Sign in to use the real V2 calendar. Demo mode cannot persist events.</p>}
      {error && <p role="alert" className="bg-red-50 border border-red-200 text-red-800 rounded-xl p-4">{error}</p>}
      {!demo && (
        <>
          <section className="bg-white rounded-2xl border p-4 flex flex-wrap items-center justify-between gap-2">
            <div className="flex gap-2 items-center">
              <button type="button" onClick={() => changeDay(-1)} aria-label="Previous day" className="p-2 hover:bg-gray-100 rounded-lg"><ChevronLeft className="w-5 h-5" /></button>
              <p className="font-semibold min-w-[180px] text-center">{format(parseISO(day), 'EEEE, d MMM yyyy')}</p>
              <button type="button" onClick={() => changeDay(1)} aria-label="Next day" className="p-2 hover:bg-gray-100 rounded-lg"><ChevronRight className="w-5 h-5" /></button>
              <button type="button" className="ml-2 text-sm text-peach-dark underline" onClick={() => setDay(today())}>Today</button>
            </div>
            <button type="button" aria-label="Reload calendar" onClick={refresh} className="p-2 hover:bg-gray-100 rounded-lg"><RefreshCw className="w-5 h-5" /></button>
          </section>
          {showEditor && (
            <form onSubmit={save} className="bg-white rounded-2xl border p-5 space-y-3">
              <h2 className="font-semibold">{editingId ? 'Edit commitment' : 'Add fixed commitment'}</h2>
              <label className="block text-sm">Title
                <input required maxLength={160} className="input-field mt-1" value={title}
                  onChange={event => setTitle(event.target.value)} placeholder="Class, exam, or appointment" />
              </label>
              <div className="flex gap-3 flex-wrap">
                <label className="text-sm">Start <input required type="time" className="input-field mt-1" value={start} onChange={e=>setStart(e.target.value)}/></label>
                <label className="text-sm">End <input required type="time" className="input-field mt-1" value={end} onChange={e=>setEnd(e.target.value)}/></label>
              </div>
              <div className="flex gap-3">
                <button disabled={working} type="submit" className="btn-primary">Save commitment</button>
                <button type="button" onClick={() => setShowEditor(false)} className="px-4 py-2 border rounded-xl">Cancel</button>
              </div>
            </form>
          )}
          <section className="rounded-2xl border bg-white p-5 space-y-3">
            <h2 className="font-semibold flex gap-2 items-center"><CalendarDays className="w-5 h-5 text-peach" /> Your schedule</h2>
            {loading && <p className="text-sm text-dark-muted">Loading calendar...</p>}
            {!loading && all.length === 0 && <p className="text-sm text-dark-muted py-10 text-center">Nothing scheduled for this day.</p>}
            {!loading && all.map(item => (
              <div key={item.kind+item.id} className="flex gap-3 justify-between items-center rounded-xl border p-4">
                <div className="min-w-0">
                  <p className="font-semibold text-dark truncate">{item.title}</p>
                  <p className="text-sm text-dark-muted mt-1">{hour(item.starts_at)} – {hour(item.ends_at)} · {item.kind === 'fixed' ? 'Fixed commitment' : 'Scheduled task'}</p>
                </div>
                {item.kind === 'fixed' && (
                  <div className="flex gap-1 shrink-0">
                    <button aria-label={'Edit '+item.title} onClick={() => beginEdit(item)} className="p-2 hover:bg-gray-100 rounded-lg"><Pencil className="w-4 h-4" /></button>
                    <button aria-label={'Delete '+item.title} disabled={working} onClick={() => remove(item)} className="p-2 text-red-600 hover:bg-red-50 rounded-lg"><Trash2 className="w-4 h-4" /></button>
                  </div>
                )}
              </div>
            ))}
          </section>
        </>
      )}
    </div>
  )
}
