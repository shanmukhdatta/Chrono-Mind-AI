import React, { useCallback, useEffect, useState } from 'react'
import { addDays, addMonths, format, parseISO, isSameDay } from 'date-fns'
import { CalendarDays, ChevronLeft, ChevronRight, Plus, Pencil, Trash2, RefreshCw, Calendar as CalendarIcon, Clock, CheckCircle2 } from 'lucide-react'
import toast from 'react-hot-toast'
import api from '../lib/api'
import { useAuthStore } from '../store/authStore'
import { calendarDayWindow, calendarWeekWindow, calendarMonthWindow, localEventPayload } from '../lib/calendarV2'

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
  const [viewMode, setViewMode] = useState('day') // 'day' | 'week' | 'month'
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
      let windowParams
      if (viewMode === 'day') {
        windowParams = calendarDayWindow(day)
      } else if (viewMode === 'week') {
        windowParams = calendarWeekWindow(day)
      } else {
        windowParams = calendarMonthWindow(day)
      }
      const response = await api.get('/api/v2/calendar', {
        params: { starts_at: windowParams.starts_at, ends_at: windowParams.ends_at }
      })
      setEvents(response.data.fixed_events || [])
      setBlocks(response.data.task_blocks || [])
      setError('')
    } catch (err) {
      setError(msg(err))
    } finally {
      setLoading(false)
    }
  }, [day, viewMode, demo])

  useEffect(() => { refresh() }, [refresh])

  const navigateDate = (direction) => {
    const current = parseISO(day)
    if (viewMode === 'day') {
      setDay(format(addDays(current, direction), 'yyyy-MM-dd'))
    } else if (viewMode === 'week') {
      setDay(format(addDays(current, direction * 7), 'yyyy-MM-dd'))
    } else {
      setDay(format(addMonths(current, direction), 'yyyy-MM-dd'))
    }
  }

  const beginNew = (initialDay) => {
    setEditingId(null)
    setTitle('')
    setStart('09:00')
    setEnd('10:00')
    if (initialDay) setDay(initialDay)
    setShowEditor(true)
  }

  const beginEdit = (event) => {
    setEditingId(event.id)
    setTitle(event.title)
    setStart(hour(event.starts_at))
    setEnd(hour(event.ends_at))
    setShowEditor(true)
  }

  const save = async (e) => {
    e.preventDefault()
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

  const remove = async (event) => {
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

  // Header Title Formatting
  const currentParsed = parseISO(day)
  let headerTitle = format(currentParsed, 'EEEE, MMMM d, yyyy')
  if (viewMode === 'week') {
    const week = calendarWeekWindow(day)
    const first = parseISO(week.days[0])
    const last = parseISO(week.days[6])
    headerTitle = `${format(first, 'MMM d')} – ${format(last, 'MMM d, yyyy')}`
  } else if (viewMode === 'month') {
    headerTitle = format(currentParsed, 'MMMM yyyy')
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <p className="text-peach-dark text-sm font-semibold tracking-wide">Schedule & Commitments</p>
          <h1 className="text-3xl font-bold text-dark">Calendar V2</h1>
          <p className="text-sm text-dark-muted mt-1">
            Real PostgreSQL commitments, scheduled task sessions, and conflict prevention.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => refresh()}
            disabled={loading}
            className="p-2.5 rounded-xl border border-gray-200 bg-white hover:bg-gray-50 text-dark-muted transition-colors"
            title="Refresh schedule"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
          <button
            type="button"
            onClick={() => beginNew()}
            className="px-4 py-2.5 rounded-xl bg-peach text-white font-medium text-sm flex items-center gap-2 hover:bg-peach-dark transition-colors shadow-sm"
          >
            <Plus className="w-4 h-4" /> New Commitment
          </button>
        </div>
      </div>

      {/* Navigation and View Controls Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 bg-white p-4 rounded-2xl border border-gray-100 shadow-sm">
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => navigateDate(-1)}
            className="p-2 rounded-lg border border-gray-200 hover:bg-gray-50 text-dark"
            aria-label="Previous"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <button
            type="button"
            onClick={() => setDay(today())}
            className="px-3 py-1.5 rounded-lg border border-gray-200 hover:bg-gray-50 text-xs font-semibold text-dark"
          >
            Today
          </button>
          <button
            type="button"
            onClick={() => navigateDate(1)}
            className="p-2 rounded-lg border border-gray-200 hover:bg-gray-50 text-dark"
            aria-label="Next"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
          <span className="text-base font-bold text-dark ml-2">{headerTitle}</span>
        </div>

        {/* View Mode Toggle */}
        <div className="flex items-center bg-gray-100 p-1 rounded-xl">
          {['day', 'week', 'month'].map((mode) => (
            <button
              key={mode}
              type="button"
              onClick={() => setViewMode(mode)}
              className={`px-4 py-1.5 rounded-lg text-xs font-semibold capitalize transition-all ${
                viewMode === mode
                  ? 'bg-white text-dark shadow-sm'
                  : 'text-dark-muted hover:text-dark'
              }`}
            >
              {mode} view
            </button>
          ))}
        </div>
      </div>

      {error && (
        <div role="alert" className="p-4 rounded-xl bg-red-50 border border-red-200 text-sm text-red-800">
          {error}
        </div>
      )}

      {/* Main View Renderer */}
      {viewMode === 'day' && (
        <div className="bg-white rounded-2xl border border-gray-100 p-6 shadow-sm space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-dark">Timeline for {format(currentParsed, 'MMMM d, yyyy')}</h2>
            <div className="flex items-center gap-4 text-xs text-dark-muted">
              <span className="flex items-center gap-1.5">
                <span className="w-3 h-3 rounded-md bg-blue-500"></span> Fixed Event
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-3 h-3 rounded-md bg-peach"></span> Scheduled Task
              </span>
            </div>
          </div>

          <div className="space-y-3">
            {events.length === 0 && blocks.length === 0 ? (
              <div className="text-center py-12 border-2 border-dashed border-gray-100 rounded-xl">
                <CalendarIcon className="w-8 h-8 text-gray-300 mx-auto mb-2" />
                <p className="text-sm font-medium text-dark-muted">No commitments or scheduled sessions for this day.</p>
                <button
                  type="button"
                  onClick={() => beginNew()}
                  className="mt-3 text-peach text-sm font-semibold hover:underline"
                >
                  + Add a fixed commitment
                </button>
              </div>
            ) : (
              <>
                {events.map((event) => (
                  <div
                    key={event.id}
                    className="p-4 rounded-xl border border-blue-100 bg-blue-50/60 flex items-center justify-between gap-3"
                  >
                    <div className="flex items-start gap-3">
                      <div className="p-2 rounded-lg bg-blue-500 text-white mt-0.5">
                        <Clock className="w-4 h-4" />
                      </div>
                      <div>
                        <h3 className="font-semibold text-dark text-sm">{event.title}</h3>
                        <p className="text-xs text-blue-900/80 mt-0.5">
                          {hour(event.starts_at)} – {hour(event.ends_at)} · Fixed Commitment
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-1">
                      <button
                        type="button"
                        onClick={() => beginEdit(event)}
                        className="p-2 rounded-lg hover:bg-white/80 text-dark-muted"
                        title="Edit commitment"
                      >
                        <Pencil className="w-4 h-4" />
                      </button>
                      <button
                        type="button"
                        onClick={() => remove(event)}
                        className="p-2 rounded-lg hover:bg-red-100 text-red-600"
                        title="Delete commitment"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                ))}

                {blocks.map((block) => (
                  <div
                    key={block.id}
                    className="p-4 rounded-xl border border-peach/30 bg-peach/10 flex items-center justify-between gap-3"
                  >
                    <div className="flex items-start gap-3">
                      <div className="p-2 rounded-lg bg-peach text-white mt-0.5">
                        <CheckCircle2 className="w-4 h-4" />
                      </div>
                      <div>
                        <h3 className="font-semibold text-dark text-sm">{block.title}</h3>
                        <p className="text-xs text-peach-dark mt-0.5">
                          {hour(block.starts_at)} – {hour(block.ends_at)} · Scheduled Task Session
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </>
            )}
          </div>
        </div>
      )}

      {viewMode === 'week' && (
        <div className="bg-white rounded-2xl border border-gray-100 p-6 shadow-sm overflow-x-auto">
          <div className="grid grid-cols-7 gap-3 min-w-[760px]">
            {calendarWeekWindow(day).days.map((dStr) => {
              const dDate = parseISO(dStr)
              const isToday = isSameDay(dDate, new Date())
              const isSelected = dStr === day
              const dayEvents = events.filter((e) => isSameDay(parseISO(e.starts_at), dDate))
              const dayBlocks = blocks.filter((b) => isSameDay(parseISO(b.starts_at), dDate))

              return (
                <div
                  key={dStr}
                  className={`border rounded-xl p-3 flex flex-col min-h-[300px] transition-colors ${
                    isSelected ? 'border-peach bg-peach/5' : isToday ? 'border-blue-200 bg-blue-50/20' : 'border-gray-100 bg-gray-50/50'
                  }`}
                >
                  <div className="flex items-center justify-between mb-3 pb-2 border-b border-gray-100">
                    <div>
                      <p className="text-[11px] font-bold uppercase text-dark-muted">{format(dDate, 'EEE')}</p>
                      <p className={`text-base font-bold ${isToday ? 'text-peach-dark' : 'text-dark'}`}>
                        {format(dDate, 'd')}
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={() => {
                        setDay(dStr)
                        setViewMode('day')
                      }}
                      className="text-[10px] text-peach font-semibold hover:underline"
                    >
                      View
                    </button>
                  </div>

                  <div className="space-y-1.5 flex-1">
                    {dayEvents.map((e) => (
                      <div
                        key={e.id}
                        className="p-1.5 rounded-lg bg-blue-100 text-blue-900 border border-blue-200 text-xs truncate"
                        title={`${e.title} (${hour(e.starts_at)}–${hour(e.ends_at)})`}
                      >
                        <p className="font-semibold truncate">{e.title}</p>
                        <p className="text-[10px] text-blue-800">{hour(e.starts_at)}</p>
                      </div>
                    ))}
                    {dayBlocks.map((b) => (
                      <div
                        key={b.id}
                        className="p-1.5 rounded-lg bg-peach/20 text-peach-dark border border-peach/30 text-xs truncate"
                        title={`${b.title} (${hour(b.starts_at)}–${hour(b.ends_at)})`}
                      >
                        <p className="font-semibold truncate">{b.title}</p>
                        <p className="text-[10px]">{hour(b.starts_at)}</p>
                      </div>
                    ))}
                    {dayEvents.length === 0 && dayBlocks.length === 0 && (
                      <div className="h-full flex items-center justify-center text-center">
                        <span className="text-[11px] text-gray-300">Free</span>
                      </div>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {viewMode === 'month' && (
        <div className="bg-white rounded-2xl border border-gray-100 p-6 shadow-sm">
          <div className="grid grid-cols-7 gap-2">
            {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map((dw) => (
              <div key={dw} className="text-center font-bold text-xs uppercase text-dark-muted py-2">
                {dw}
              </div>
            ))}
            {calendarMonthWindow(day).days.map((dStr) => {
              const dDate = parseISO(dStr)
              const isToday = isSameDay(dDate, new Date())
              const isSelected = dStr === day
              const dayEvents = events.filter((e) => isSameDay(parseISO(e.starts_at), dDate))
              const dayBlocks = blocks.filter((b) => isSameDay(parseISO(b.starts_at), dDate))
              const totalItems = dayEvents.length + dayBlocks.length

              return (
                <button
                  key={dStr}
                  type="button"
                  onClick={() => {
                    setDay(dStr)
                    setViewMode('day')
                  }}
                  className={`p-2.5 min-h-[90px] text-left rounded-xl border flex flex-col justify-between transition-all hover:border-peach hover:shadow-sm ${
                    isSelected
                      ? 'border-peach bg-peach/10'
                      : isToday
                      ? 'border-blue-300 bg-blue-50/30'
                      : 'border-gray-100 bg-white'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className={`text-xs font-bold ${isToday ? 'text-peach-dark' : 'text-dark'}`}>
                      {format(dDate, 'd')}
                    </span>
                    {totalItems > 0 && (
                      <span className="text-[10px] font-bold px-1.5 py-0.5 rounded-full bg-peach/20 text-peach-dark">
                        {totalItems}
                      </span>
                    )}
                  </div>
                  <div className="space-y-1 mt-1">
                    {dayEvents.slice(0, 1).map((e) => (
                      <div key={e.id} className="text-[10px] truncate px-1 py-0.5 rounded bg-blue-100 text-blue-800">
                        {e.title}
                      </div>
                    ))}
                    {dayBlocks.slice(0, 1).map((b) => (
                      <div key={b.id} className="text-[10px] truncate px-1 py-0.5 rounded bg-peach/20 text-peach-dark">
                        {b.title}
                      </div>
                    ))}
                    {totalItems > 2 && (
                      <span className="text-[9px] text-dark-muted block">+{totalItems - 2} more</span>
                    )}
                  </div>
                </button>
              )
            })}
          </div>
        </div>
      )}

      {/* Editor Modal */}
      {showEditor && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-gray-100 space-y-4">
            <h2 className="text-xl font-bold text-dark">
              {editingId ? 'Edit Fixed Commitment' : 'Add Fixed Commitment'}
            </h2>
            <form onSubmit={save} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-dark mb-1">Date</label>
                <input
                  type="date"
                  value={day}
                  onChange={(e) => setDay(e.target.value)}
                  className="w-full px-3 py-2 border rounded-xl text-sm"
                  required
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-dark mb-1">Title</label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g. Distributed Systems Lecture"
                  className="w-full px-3 py-2 border rounded-xl text-sm"
                  required
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-dark mb-1">Starts At</label>
                  <input
                    type="time"
                    value={start}
                    onChange={(e) => setStart(e.target.value)}
                    className="w-full px-3 py-2 border rounded-xl text-sm"
                    required
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-dark mb-1">Ends At</label>
                  <input
                    type="time"
                    value={end}
                    onChange={(e) => setEnd(e.target.value)}
                    className="w-full px-3 py-2 border rounded-xl text-sm"
                    required
                  />
                </div>
              </div>
              <div className="flex gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowEditor(false)}
                  className="flex-1 py-2.5 border rounded-xl text-sm font-medium hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={working}
                  className="flex-1 py-2.5 bg-peach text-white rounded-xl text-sm font-medium hover:bg-peach-dark"
                >
                  {working ? 'Saving...' : 'Save Commitment'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
