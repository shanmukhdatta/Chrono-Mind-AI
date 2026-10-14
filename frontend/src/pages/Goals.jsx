import React, { useCallback, useEffect, useState } from 'react'
import { Target, Plus, Trash2, CheckCircle2, Circle, RefreshCw } from 'lucide-react'
import toast from 'react-hot-toast'
import api from '../lib/api'
import { useAuthStore } from '../store/authStore'

function errorMessage(error) {
  const detail = error.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (error.response?.status === 503) return 'The PostgreSQL V2 service is not configured yet. Ask the administrator to enable it.'
  return error.message || 'Request failed'
}

export default function Goals() {
  const user = useAuthStore(state => state.user)
  const demo = user?.uid === 'demo'
  const [goals, setGoals] = useState([])
  const [tasks, setTasks] = useState([])
  const [loading, setLoading] = useState(!demo)
  const [working, setWorking] = useState(false)
  const [error, setError] = useState('')
  const [selectedId, setSelectedId] = useState(null)
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [targetDate, setTargetDate] = useState('')
  const [taskTitle, setTaskTitle] = useState('')
  const [duration, setDuration] = useState(30)
  const [adding, setAdding] = useState(false)

  const refresh = useCallback(async () => {
    if (demo) return
    try {
      const [goalsResponse, tasksResponse] = await Promise.all([
        api.get('/api/v2/goals'), api.get('/api/v2/tasks')
      ])
      setGoals(goalsResponse.data)
      setTasks(tasksResponse.data)
      setError('')
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setLoading(false)
    }
  }, [demo])

  useEffect(() => { refresh() }, [refresh])

  const selected = goals.find(goal => goal.id === selectedId) || null
  const linkedTasks = tasks.filter(task => task.goal_id === selectedId)

  const clearEditor = () => {
    setSelectedId(null)
    setTitle('')
    setDescription('')
    setTargetDate('')
  }

  const openEditor = (goal) => {
    setSelectedId(goal.id)
    setTitle(goal.title)
    setDescription(goal.description || '')
    setTargetDate(goal.target_date || '')
    setAdding(false)
  }

  const execute = async (action, success) => {
    setWorking(true)
    try {
      await action()
      toast.success(success)
      await refresh()
    } catch (err) {
      const msg = errorMessage(err)
      setError(msg)
      toast.error(msg)
    } finally {
      setWorking(false)
    }
  }

  const saveGoal = async (event) => {
    event.preventDefault()
    if (!title.trim()) return
    const payload = { title: title.trim(), description: description.trim(), target_date: targetDate || null }
    await execute(async () => {
      if (selectedId) {
        await api.patch('/api/v2/goals/' + selectedId, payload)
      } else {
        const response = await api.post('/api/v2/goals', payload)
        setSelectedId(response.data.id)
      }
    }, selectedId ? 'Goal updated' : 'Goal created')
  }

  const changeStatus = (nextStatus) => execute(
    () => api.patch('/api/v2/goals/' + selectedId, { status: nextStatus }),
    'Goal status updated'
  )

  const removeGoal = async () => {
    if (!selectedId || !window.confirm('Delete this goal? Linked tasks will be kept.')) return
    await execute(async () => {
      await api.delete('/api/v2/goals/' + selectedId)
      clearEditor()
    }, 'Goal deleted. Tasks are preserved.')
  }

  const addTask = async (event) => {
    event.preventDefault()
    if (!selectedId || !taskTitle.trim()) return
    await execute(async () => {
      await api.post('/api/v2/tasks', {
        title: taskTitle.trim(), duration_minutes: Number(duration), goal_id: selectedId
      })
      setTaskTitle('')
    }, 'Task added to goal')
  }

  const toggleTask = (task) => execute(
    () => api.patch('/api/v2/tasks/' + task.id, {
      version: task.version,
      status: task.status === 'completed' ? 'pending' : 'completed'
    }),
    'Task updated'
  )

  if (demo) return (
    <section className="max-w-3xl p-6 rounded-2xl border bg-white">
      <h1 className="text-2xl font-bold text-dark">Goals</h1>
      <p className="mt-3 text-dark-muted">Goals require a signed-in account and PostgreSQL storage. Demo mode does not pretend to save changes.</p>
    </section>
  )

  return (
    <div className="max-w-6xl mx-auto space-y-5">
      <header className="flex items-center justify-between gap-3">
        <div>
          <p className="text-sm text-peach-dark font-semibold">Plan with purpose</p>
          <h1 className="text-3xl font-bold text-dark">Goals</h1>
          <p className="text-sm text-dark-muted mt-1">Connect tasks to meaningful outcomes.</p>
        </div>
        <button type="button" onClick={refresh} aria-label="Refresh goals" className="p-3 bg-white border rounded-xl">
          <RefreshCw className="h-5 w-5" />
        </button>
      </header>

      {error && <div role="alert" className="rounded-xl bg-red-50 border border-red-200 p-4 text-sm text-red-800">{error}</div>}
      {loading ? <p className="text-dark-muted">Loading your goals...</p> : (
        <div className="grid gap-5 lg:grid-cols-[1fr_1.25fr]">
          <section className="bg-white rounded-2xl border border-gray-100 p-5 shadow-sm space-y-3">
            <div className="flex justify-between items-center">
              <h2 className="text-lg font-semibold">Your goals ({goals.length})</h2>
              <button type="button" onClick={() => { clearEditor(); setAdding(true) }}
                className="flex gap-1 items-center rounded-lg bg-peach text-white py-2 px-3 text-sm">
                <Plus className="w-4 h-4" /> New
              </button>
            </div>
            {goals.length === 0 && <p className="py-8 text-sm text-dark-muted">No goals yet. Create one to start planning.</p>}
            <div className="space-y-2">
              {goals.map(goal => {
                const count = tasks.filter(task => task.goal_id === goal.id).length
                return (
                  <button key={goal.id} type="button" onClick={() => { openEditor(goal); setAdding(false) }}
                    className={`w-full text-left p-4 rounded-xl border transition-colors ${selectedId === goal.id ? 'border-peach bg-peach/5' : 'border-gray-100 hover:bg-gray-50'}`}>
                    <div className="flex justify-between gap-3">
                      <div className="flex gap-2 min-w-0">
                        <Target className="w-5 h-5 text-peach shrink-0" />
                        <span className="font-semibold text-dark truncate">{goal.title}</span>
                      </div>
                      <span className="text-xs capitalize text-dark-muted">{goal.status}</span>
                    </div>
                    <p className="text-xs text-dark-muted mt-2">
                      {count} linked {count === 1 ? 'task' : 'tasks'}{goal.target_date ? ` · Due ${goal.target_date}` : ''}
                    </p>
                  </button>
                )
              })}
            </div>
          </section>

          <section className="bg-white rounded-2xl border border-gray-100 p-5 shadow-sm">
            {selected || adding ? (
              <div className="space-y-6">
                <form onSubmit={saveGoal} className="space-y-3">
                  <h2 className="font-semibold text-lg">{selected ? 'Edit goal' : 'Create goal'}</h2>
                  <label className="block text-sm font-medium">Goal title
                    <input className="input-field mt-1" maxLength={160} required value={title}
                      onChange={e => setTitle(e.target.value)} placeholder="Prepare for placements" />
                  </label>
                  <label className="block text-sm font-medium">Description
                    <textarea className="input-field mt-1" maxLength={4000} rows={3} value={description}
                      onChange={e => setDescription(e.target.value)} placeholder="What does success look like?" />
                  </label>
                  <label className="block text-sm font-medium">Target date (optional)
                    <input type="date" className="input-field mt-1" value={targetDate}
                      onChange={e => setTargetDate(e.target.value)} />
                  </label>
                  <button disabled={working} className="btn-primary disabled:opacity-50" type="submit">
                    {selected ? 'Save changes' : 'Create goal'}
                  </button>
                </form>
                {selected && (
                  <>
                    <div className="flex flex-wrap items-center gap-2 border-t pt-4">
                      <span className="text-sm text-dark-muted mr-1">Status:</span>
                      {['active', 'paused', 'completed', 'archived'].map(status => (
                        <button key={status} disabled={working || selected.status === status}
                          onClick={() => changeStatus(status)} type="button"
                          className={`rounded-lg px-3 py-2 capitalize text-xs border ${selected.status === status ? 'bg-peach/15 text-peach-dark border-peach' : 'bg-white'}`}>
                          {status}
                        </button>
                      ))}
                      <button aria-label="Delete goal" type="button" disabled={working}
                        onClick={removeGoal} className="ml-auto text-red-600 p-2 hover:bg-red-50 rounded-lg">
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                    <div className="space-y-3">
                      <h3 className="font-semibold">Linked tasks ({linkedTasks.length})</h3>
                      {linkedTasks.map(task => (
                        <button type="button" disabled={working} onClick={() => toggleTask(task)} key={task.id}
                          className="w-full border rounded-xl text-left px-4 py-3 flex items-center gap-3 hover:bg-gray-50">
                          {task.status === 'completed'
                            ? <CheckCircle2 className="w-5 h-5 text-green-600" />
                            : <Circle className="w-5 h-5 text-gray-400" />}
                          <span className={task.status === 'completed' ? 'line-through text-dark-muted' : ''}>{task.title}</span>
                          <span className="ml-auto text-xs text-dark-muted">{task.duration_minutes} min</span>
                        </button>
                      ))}
                      <form onSubmit={addTask} className="flex flex-col sm:flex-row gap-2">
                        <input aria-label="New task title" className="input-field flex-1" required maxLength={160}
                          placeholder="Add a task..." value={taskTitle} onChange={e => setTaskTitle(e.target.value)} />
                        <input aria-label="Duration in minutes" className="input-field sm:w-24" type="number"
                          min="1" max="1440" value={duration} onChange={e => setDuration(e.target.value)} />
                        <button type="submit" disabled={working} className="btn-primary">Add task</button>
                      </form>
                    </div>
                  </>
                )}
              </div>
            ) : (
              <div className="flex flex-col gap-2 items-center justify-center text-center py-20">
                <Target className="w-10 h-10 text-peach" />
                <h2 className="font-semibold">Select a goal</h2>
                <p className="text-dark-muted text-sm">Select a goal to edit it and organize its tasks.</p>
              </div>
            )}
          </section>
        </div>
      )}
    </div>
  )
}
