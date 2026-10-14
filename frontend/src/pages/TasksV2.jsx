import React, { useCallback, useEffect, useState } from 'react'
import { ListTodo, Plus, CheckCircle2, Clock3, Pencil, Archive, RefreshCw } from 'lucide-react'
import toast from 'react-hot-toast'
import api from '../lib/api'
import { useAuthStore } from '../store/authStore'
import { isoToDateTimeLocal, taskPayload } from '../lib/tasksV2'

const empty = () => ({
  title: '', description: '', importance: 'important', duration_minutes: 30,
  deadline_at: '', goal_id: '',
})

function message(err) {
  if (typeof err.response?.data?.detail === 'string') return err.response.data.detail
  if (err.response?.status === 503) return 'V2 PostgreSQL is not configured. Your Firestore tasks remain untouched.'
  if (err.response?.status === 409) return 'Task changed elsewhere. Refresh it before editing.'
  return err.message || 'Unable to save task'
}

export default function TasksV2() {
  const demo = useAuthStore(state => state.user?.uid === 'demo')
  const [tasks, setTasks] = useState([])
  const [goals, setGoals] = useState([])
  const [filter, setFilter] = useState('pending')
  const [editor, setEditor] = useState(false)
  const [editing, setEditing] = useState(null)
  const [form, setForm] = useState(empty)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(!demo)
  const [busy, setBusy] = useState(false)

  const refresh = useCallback(async () => {
    if (demo) return
    setLoading(true)
    try {
      const [taskResponse, goalResponse] = await Promise.all([
        api.get('/api/v2/tasks', { params: { status: 'all' } }),
        api.get('/api/v2/goals'),
      ])
      setTasks(taskResponse.data)
      setGoals(goalResponse.data)
      setError('')
    } catch (err) {
      setError(message(err))
    } finally {
      setLoading(false)
    }
  }, [demo])

  useEffect(() => { refresh() }, [refresh])

  const edit = item => {
    setEditing(item)
    setForm({
      title: item.title,
      description: item.description || '',
      duration_minutes: item.duration_minutes,
      importance: item.importance,
      deadline_at: isoToDateTimeLocal(item.deadline_at),
      goal_id: item.goal_id || '',
    })
    setEditor(true)
  }

  const add = () => {
    setEditing(null)
    setForm(empty())
    setEditor(true)
  }

  const updateField = (key, value) => setForm(values => ({ ...values, [key]: value }))

  const save = async event => {
    event.preventDefault()
    setBusy(true)
    setError('')
    try {
      const payload = taskPayload(form)
      if (editing) {
        await api.patch('/api/v2/tasks/' + editing.id, { ...payload, version: editing.version })
        toast.success('Task updated')
      } else {
        const response = await api.post('/api/v2/tasks', payload)
        if (response.status !== 201) throw new Error('Save not confirmed')
        toast.success('Task saved')
      }
      setEditor(false)
      await refresh()
    } catch (err) {
      const note = message(err)
      setError(note)
      toast.error(note)
    } finally {
      setBusy(false)
    }
  }

  const changeStatus = async (task, status) => {
    setBusy(true)
    setError('')
    try {
      await api.patch('/api/v2/tasks/' + task.id, {version: task.version, status})
      await refresh()
      toast.success(status === 'completed' ? 'Task completed' : status === 'archived' ? 'Task archived' : 'Task reopened')
    } catch (err) {
      const note = message(err)
      setError(note)
      toast.error(note)
    } finally {
      setBusy(false)
    }
  }

  const items = tasks.filter(task => filter === 'all' || task.status === filter)
  const goalName = id => goals.find(goal => goal.id === id)?.title

  return (
    <div className="max-w-6xl mx-auto space-y-5">
      <header className="flex flex-col sm:flex-row justify-between gap-3">
        <div>
          <p className="text-peach-dark text-sm font-semibold">Structured PostgreSQL tasks</p>
          <h1 className="text-3xl font-bold text-dark">My tasks</h1>
          <p className="text-sm text-dark-muted mt-2">Set realistic effort estimates, deadlines and linked goals.</p>
        </div>
        <button type="button" className="btn-primary flex gap-2 items-center justify-center" disabled={demo} onClick={add}>
          <Plus className="w-4 h-4" /> Add task
        </button>
      </header>
      {demo && <p className="bg-white border rounded-xl p-4">Sign in for real PostgreSQL task storage. Demo mode does not save tasks.</p>}
      {error && <p role="alert" className="bg-red-50 border border-red-200 rounded-xl p-4 text-sm text-red-800">{error}</p>}
      {!demo && (
        <>
          <section className="bg-white border rounded-2xl p-4 flex flex-wrap gap-2 items-center justify-between">
            <div className="flex gap-1">
              {['pending', 'completed', 'archived', 'all'].map(status => (
                <button type="button" key={status} onClick={() => setFilter(status)}
                  className={`px-3 py-2 rounded-lg capitalize text-sm ${filter === status ? 'bg-peach/15 text-peach-dark font-semibold' : 'text-dark-muted hover:bg-gray-50'}`}>{status}</button>
              ))}
            </div>
            <button type="button" onClick={refresh} aria-label="Refresh tasks" className="p-2 hover:bg-gray-50 rounded-lg">
              <RefreshCw className="w-5 h-5" />
            </button>
          </section>
          {editor && (
            <form className="rounded-2xl p-5 border bg-white space-y-4" onSubmit={save}>
              <h2 className="font-semibold text-lg">{editing ? 'Edit task' : 'New task'}</h2>
              <label className="block text-sm font-medium">Title
                <input className="input-field mt-1" maxLength={160} required value={form.title} onChange={e => updateField('title',e.target.value)} />
              </label>
              <label className="block text-sm font-medium">Description
                <textarea rows={2} className="input-field mt-1" maxLength={4000} value={form.description} onChange={e => updateField('description',e.target.value)} />
              </label>
              <div className="grid sm:grid-cols-2 gap-4">
                <label className="block text-sm font-medium">Expected effort (minutes)
                  <input type="number" min="1" max="1440" className="input-field mt-1" required value={form.duration_minutes}
                    onChange={e => updateField('duration_minutes',e.target.value)} />
                </label>
                <label className="block text-sm font-medium">Importance
                  <select className="input-field mt-1" value={form.importance} onChange={e => updateField('importance',e.target.value)}>
                    <option value="important">Important</option><option value="not_important">Optional (never silently deleted)</option>
                  </select>
                </label>
                <label className="block text-sm font-medium">Deadline (optional)
                  <input type="datetime-local" className="input-field mt-1" value={form.deadline_at}
                    onChange={e => updateField('deadline_at',e.target.value)} />
                </label>
                <label className="block text-sm font-medium">Goal (optional)
                  <select className="input-field mt-1" value={form.goal_id} onChange={e => updateField('goal_id',e.target.value)}>
                    <option value="">No linked goal</option>
                    {goals.map(goal => <option key={goal.id} value={goal.id}>{goal.title}</option>)}
                  </select>
                </label>
              </div>
              <div className="flex gap-3">
                <button className="btn-primary" type="submit" disabled={busy}>{busy ? 'Saving...' : 'Save task'}</button>
                <button type="button" className="border rounded-xl px-4 py-2" onClick={() => setEditor(false)}>Cancel</button>
              </div>
            </form>
          )}
          <section className="bg-white rounded-2xl border p-5 space-y-2">
            <h2 className="font-semibold text-lg flex gap-2 items-center">
              <ListTodo className="w-5 h-5 text-peach" />
              {filter === 'all' ? 'All tasks' : filter.charAt(0).toUpperCase() + filter.slice(1)} ({items.length})
            </h2>
            {loading && <p className="text-sm text-dark-muted py-6">Loading tasks...</p>}
            {!loading && items.length === 0 && <p className="text-sm text-dark-muted py-12 text-center">No matching tasks yet.</p>}
            {!loading && items.map(task => (
              <div key={task.id} className="rounded-xl border p-4 flex flex-col sm:flex-row gap-3 sm:items-center justify-between">
                <div className="min-w-0">
                  <p className={`font-semibold ${task.status === 'completed' ? 'line-through text-dark-muted' : 'text-dark'}`}>{task.title}</p>
                  {task.description && <p className="text-sm text-dark-muted mt-1">{task.description}</p>}
                  <p className="text-xs text-dark-muted mt-2 flex flex-wrap gap-2 items-center">
                    <span className="flex gap-1 items-center"><Clock3 className="w-3 h-3" /> {task.duration_minutes} min</span>
                    <span>{task.importance === 'important' ? 'Important' : 'Optional'}</span>
                    {task.deadline_at && <span>Due {new Date(task.deadline_at).toLocaleString()}</span>}
                    {task.goal_id && <span>Goal: {goalName(task.goal_id) || 'Archived goal'}</span>}
                  </p>
                </div>
                <div className="flex flex-wrap gap-2 shrink-0">
                  <button type="button" aria-label={'Edit '+task.title} disabled={busy} onClick={() => edit(task)}
                    className="rounded-lg border p-2 hover:bg-gray-50"><Pencil className="w-4 h-4" /></button>
                  {task.status !== 'completed' && task.status !== 'archived' && (
                    <button type="button" disabled={busy} onClick={() => changeStatus(task,'completed')}
                      className="rounded-lg border p-2 text-green-700 hover:bg-green-50" aria-label={'Complete '+task.title}>
                      <CheckCircle2 className="w-4 h-4" />
                    </button>
                  )}
                  {task.status === 'completed' && (
                    <button type="button" disabled={busy} onClick={() => changeStatus(task,'pending')} className="border rounded-lg px-3 py-2 text-sm">Reopen</button>
                  )}
                  {task.status !== 'archived' && (
                    <button type="button" disabled={busy} onClick={() => changeStatus(task,'archived')}
                      className="border rounded-lg p-2 text-dark-muted hover:bg-gray-50" aria-label={'Archive '+task.title}>
                      <Archive className="w-4 h-4" />
                    </button>
                  )}
                </div>
              </div>
            ))}
          </section>
        </>
      )}
    </div>
  )
}
