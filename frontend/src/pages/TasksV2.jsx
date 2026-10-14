import React, { useCallback, useEffect, useState } from 'react'
import {
  ListTodo, Plus, CheckCircle2, Clock3, Pencil, Archive, RefreshCw,
  Layers, GitFork, Trash2, ChevronDown, ChevronUp, Link as LinkIcon
} from 'lucide-react'
import toast from 'react-hot-toast'
import api from '../lib/api'
import { useAuthStore } from '../store/authStore'
import { isoToDateTimeLocal, taskPayload } from '../lib/tasksV2'

const empty = () => ({
  title: '', description: '', importance: 'important', duration_minutes: 30,
  deadline_at: '', goal_id: '', splittable: true,
})

function message(err) {
  if (typeof err.response?.data?.detail === 'string') return err.response.data.detail
  if (err.response?.status === 503) return 'V2 PostgreSQL is not configured. Your Firestore tasks remain untouched.'
  if (err.response?.status === 409) return err.response.data?.detail || 'Task changed elsewhere. Refresh it before editing.'
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

  // Decomposition state
  const [decomposeTask, setDecomposeTask] = useState(null)
  const [numSubtasks, setNumSubtasks] = useState(3)
  const [promptHint, setPromptHint] = useState('')
  const [decompositionPreview, setDecompositionPreview] = useState(null)
  const [decomposing, setDecomposing] = useState(false)
  const [expandedParents, setExpandedParents] = useState({})

  // Dependency modal state
  const [dependencyTask, setDependencyTask] = useState(null)
  const [taskDependencies, setTaskDependencies] = useState([])
  const [selectedPrereq, setSelectedPrereq] = useState('')
  const [loadingDeps, setLoadingDeps] = useState(false)

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

  const edit = (item) => {
    setEditing(item)
    setForm({
      title: item.title,
      description: item.description || '',
      duration_minutes: item.duration_minutes,
      splittable: item.splittable,
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

  const save = async (event) => {
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
      await api.patch('/api/v2/tasks/' + task.id, { version: task.version, status })
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

  // Decomposition actions
  const openDecomposition = (task) => {
    setDecomposeTask(task)
    setNumSubtasks(3)
    setPromptHint('')
    setDecompositionPreview(null)
  }

  const previewDecomposition = async () => {
    if (!decomposeTask) return
    setDecomposing(true)
    try {
      const resp = await api.post(`/api/v2/tasks/${decomposeTask.id}/decompose`, {
        num_subtasks: numSubtasks,
        prompt_hint: promptHint || null,
        apply: false,
      })
      setDecompositionPreview(resp.data)
    } catch (err) {
      toast.error(message(err))
    } finally {
      setDecomposing(false)
    }
  }

  const applyDecomposition = async () => {
    if (!decomposeTask) return
    setDecomposing(true)
    try {
      await api.post(`/api/v2/tasks/${decomposeTask.id}/decompose`, {
        num_subtasks: numSubtasks,
        prompt_hint: promptHint || null,
        apply: true,
      })
      toast.success('Subtasks and sequential dependencies created!')
      setDecomposeTask(null)
      setDecompositionPreview(null)
      await refresh()
    } catch (err) {
      toast.error(message(err))
    } finally {
      setDecomposing(false)
    }
  }

  // Dependency actions
  const openDependencies = async (task) => {
    setDependencyTask(task)
    setSelectedPrereq('')
    setLoadingDeps(true)
    try {
      const resp = await api.get(`/api/v2/tasks/${task.id}/dependencies`)
      setTaskDependencies(resp.data)
    } catch (err) {
      toast.error(message(err))
    } finally {
      setLoadingDeps(false)
    }
  }

  const addDependency = async () => {
    if (!dependencyTask || !selectedPrereq) return
    try {
      await api.post(`/api/v2/tasks/${dependencyTask.id}/dependencies`, {
        depends_on_id: selectedPrereq,
      })
      toast.success('Prerequisite dependency added!')
      setSelectedPrereq('')
      const resp = await api.get(`/api/v2/tasks/${dependencyTask.id}/dependencies`)
      setTaskDependencies(resp.data)
      await refresh()
    } catch (err) {
      toast.error(message(err))
    }
  }

  const toggleParentExpand = (taskId) => {
    setExpandedParents(prev => ({ ...prev, [taskId]: !prev[taskId] }))
  }

  // Filter tasks
  const items = tasks.filter(task => filter === 'all' || task.status === filter)
  const goalName = id => goals.find(goal => goal.id === id)?.title

  // Map subtasks to parents
  const subtasksByParent = {}
  tasks.forEach(t => {
    if (t.parent_task_id) {
      subtasksByParent[t.parent_task_id] = subtasksByParent[t.parent_task_id] || []
      subtasksByParent[t.parent_task_id].push(t)
    }
  })

  return (
    <div className="max-w-6xl mx-auto space-y-5">
      <header className="flex flex-col sm:flex-row justify-between gap-3">
        <div>
          <p className="text-peach-dark text-sm font-semibold tracking-wide">Structured PostgreSQL Tasks</p>
          <h1 className="text-3xl font-bold text-dark">Tasks Hub V2</h1>
          <p className="text-sm text-dark-muted mt-2">
            Effort estimation, deadlines, goals, task decomposition, and dependency scheduling.
          </p>
        </div>
        <button type="button" className="btn-primary flex gap-2 items-center justify-center self-start" disabled={demo} onClick={add}>
          <Plus className="w-4 h-4" /> Add Task
        </button>
      </header>

      {demo && <p className="bg-white border rounded-xl p-4">Sign in for real PostgreSQL task storage. Demo mode does not save tasks.</p>}
      {error && <p role="alert" className="bg-red-50 border border-red-200 rounded-xl p-4 text-sm text-red-800">{error}</p>}

      {!demo && (
        <>
          <section className="bg-white border rounded-2xl p-4 flex flex-wrap gap-2 items-center justify-between shadow-sm">
            <div className="flex gap-1">
              {['pending', 'completed', 'archived', 'all'].map(status => (
                <button
                  type="button"
                  key={status}
                  onClick={() => setFilter(status)}
                  className={`px-3 py-2 rounded-lg capitalize text-sm font-medium transition-colors ${
                    filter === status ? 'bg-peach/15 text-peach-dark font-semibold' : 'text-dark-muted hover:bg-gray-50'
                  }`}
                >
                  {status}
                </button>
              ))}
            </div>
            <button type="button" onClick={refresh} aria-label="Refresh tasks" className="p-2 hover:bg-gray-50 rounded-lg text-dark-muted">
              <RefreshCw className="w-5 h-5" />
            </button>
          </section>

          {editor && (
            <form className="rounded-2xl p-5 border bg-white space-y-4 shadow-sm" onSubmit={save}>
              <h2 className="font-semibold text-lg">{editing ? 'Edit Task' : 'New Task'}</h2>
              <label className="block text-sm font-medium">Title
                <input className="input-field mt-1" maxLength={160} required value={form.title} onChange={e => updateField('title', e.target.value)} />
              </label>
              <label className="block text-sm font-medium">Description
                <textarea rows={2} className="input-field mt-1" maxLength={4000} value={form.description} onChange={e => updateField('description', e.target.value)} />
              </label>
              <div className="grid sm:grid-cols-2 gap-4">
                <label className="block text-sm font-medium">Expected Effort (minutes)
                  <input type="number" min="1" max="1440" className="input-field mt-1" required value={form.duration_minutes}
                    onChange={e => updateField('duration_minutes', e.target.value)} />
                </label>
                <label className="block text-sm font-medium">Importance
                  <select className="input-field mt-1" value={form.importance} onChange={e => updateField('importance', e.target.value)}>
                    <option value="important">Important</option>
                    <option value="not_important">Optional (never silently deleted)</option>
                  </select>
                </label>
                <label className="block text-sm font-medium">Deadline (optional)
                  <input type="datetime-local" className="input-field mt-1" value={form.deadline_at}
                    onChange={e => updateField('deadline_at', e.target.value)} />
                </label>
                <label className="block text-sm font-medium">Linked Goal (optional)
                  <select className="input-field mt-1" value={form.goal_id} onChange={e => updateField('goal_id', e.target.value)}>
                    <option value="">No linked goal</option>
                    {goals.map(goal => <option key={goal.id} value={goal.id}>{goal.title}</option>)}
                  </select>
                </label>
              </div>
              <label className="flex items-center gap-2 text-sm font-medium">
                <input type="checkbox" checked={Boolean(form.splittable)}
                  onChange={e => updateField('splittable', e.target.checked)} />
                Allow this task to be split into shorter focus sessions
              </label>
              <div className="flex gap-3 pt-2">
                <button className="btn-primary" type="submit" disabled={busy}>{busy ? 'Saving...' : 'Save Task'}</button>
                <button type="button" className="border rounded-xl px-4 py-2 hover:bg-gray-50" onClick={() => setEditor(false)}>Cancel</button>
              </div>
            </form>
          )}

          <section className="bg-white rounded-2xl border p-5 space-y-3 shadow-sm">
            <h2 className="font-semibold text-lg flex gap-2 items-center">
              <ListTodo className="w-5 h-5 text-peach" />
              {filter === 'all' ? 'All Tasks' : filter.charAt(0).toUpperCase() + filter.slice(1)} ({items.length})
            </h2>
            {loading && <p className="text-sm text-dark-muted py-6">Loading tasks...</p>}
            {!loading && items.length === 0 && <p className="text-sm text-dark-muted py-12 text-center">No matching tasks yet.</p>}

            {!loading && items.map(task => {
              const subtaskList = subtasksByParent[task.id] || []
              const hasSubtasks = subtaskList.length > 0
              const isExpanded = expandedParents[task.id]

              return (
                <div key={task.id} className="rounded-xl border border-gray-100 p-4 space-y-3 transition-colors hover:border-gray-200">
                  <div className="flex flex-col sm:flex-row gap-3 sm:items-center justify-between">
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <p className={`font-semibold text-base ${task.status === 'completed' ? 'line-through text-dark-muted' : 'text-dark'}`}>
                          {task.title}
                        </p>
                        {task.parent_task_id && (
                          <span className="text-[10px] bg-purple-50 text-purple-700 border border-purple-200 font-semibold px-2 py-0.5 rounded-full">
                            Subtask
                          </span>
                        )}
                        {hasSubtasks && (
                          <button
                            type="button"
                            onClick={() => toggleParentExpand(task.id)}
                            className="text-[11px] bg-peach/10 text-peach-dark font-semibold px-2 py-0.5 rounded-full flex items-center gap-1 hover:bg-peach/20"
                          >
                            <Layers className="w-3 h-3" /> {subtaskList.length} Subtasks
                            {isExpanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                          </button>
                        )}
                      </div>
                      {task.description && <p className="text-sm text-dark-muted mt-1">{task.description}</p>}
                      <p className="text-xs text-dark-muted mt-2 flex flex-wrap gap-2 items-center">
                        <span className="flex gap-1 items-center font-medium"><Clock3 className="w-3 h-3 text-peach" /> {task.duration_minutes} min</span>
                        <span className="px-1.5 py-0.5 rounded bg-gray-100 text-[11px]">{task.importance === 'important' ? 'Important' : 'Optional'}</span>
                        {task.deadline_at && (
                          <span className="text-blue-700 font-medium">Due {new Date(task.deadline_at).toLocaleString()}</span>
                        )}
                        {task.goal_id && <span className="text-purple-700 font-medium">Goal: {goalName(task.goal_id) || 'Active'}</span>}
                      </p>
                    </div>

                    <div className="flex flex-wrap gap-1.5 shrink-0 items-center">
                      {/* Decompose Button for pending tasks */}
                      {task.status === 'pending' && task.duration_minutes >= 20 && (
                        <button
                          type="button"
                          onClick={() => openDecomposition(task)}
                          title="Decompose task into subtasks"
                          className="px-2.5 py-1.5 rounded-lg border border-purple-200 bg-purple-50 text-purple-700 hover:bg-purple-100 text-xs font-semibold flex items-center gap-1"
                        >
                          <Layers className="w-3.5 h-3.5" /> Decompose
                        </button>
                      )}

                      {/* Dependencies button */}
                      {task.status === 'pending' && (
                        <button
                          type="button"
                          onClick={() => openDependencies(task)}
                          title="Manage prerequisites and dependencies"
                          className="px-2.5 py-1.5 rounded-lg border border-gray-200 hover:bg-gray-50 text-xs font-semibold flex items-center gap-1 text-dark-muted"
                        >
                          <GitFork className="w-3.5 h-3.5" /> Prereqs
                        </button>
                      )}

                      <button
                        type="button"
                        aria-label={'Edit ' + task.title}
                        disabled={busy}
                        onClick={() => edit(task)}
                        className="rounded-lg border p-2 hover:bg-gray-50 text-dark-muted"
                      >
                        <Pencil className="w-4 h-4" />
                      </button>

                      {task.status !== 'completed' && task.status !== 'archived' && (
                        <button
                          type="button"
                          disabled={busy}
                          onClick={() => changeStatus(task, 'completed')}
                          className="rounded-lg border border-green-200 p-2 text-green-700 hover:bg-green-50"
                          aria-label={'Complete ' + task.title}
                        >
                          <CheckCircle2 className="w-4 h-4" />
                        </button>
                      )}

                      {task.status === 'completed' && (
                        <button
                          type="button"
                          disabled={busy}
                          onClick={() => changeStatus(task, 'pending')}
                          className="border rounded-lg px-3 py-2 text-xs font-semibold hover:bg-gray-50"
                        >
                          Reopen
                        </button>
                      )}

                      {task.status !== 'archived' && (
                        <button
                          type="button"
                          disabled={busy}
                          onClick={() => changeStatus(task, 'archived')}
                          className="border rounded-lg p-2 text-dark-muted hover:bg-gray-50"
                          aria-label={'Archive ' + task.title}
                        >
                          <Archive className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                  </div>

                  {/* Expanded Subtasks List */}
                  {hasSubtasks && isExpanded && (
                    <div className="pl-4 pt-2 border-t border-gray-100 space-y-2 bg-gray-50/50 p-3 rounded-xl">
                      <p className="text-xs font-bold uppercase tracking-wider text-dark-muted">Sequential Subtasks:</p>
                      {subtaskList.map((sub, idx) => (
                        <div key={sub.id} className="flex items-center justify-between text-xs bg-white p-2.5 rounded-lg border border-gray-100">
                          <div className="flex items-center gap-2">
                            <span className="w-4 h-4 rounded-full bg-peach/20 text-peach-dark flex items-center justify-center font-bold text-[10px]">
                              {idx + 1}
                            </span>
                            <span className={`font-medium ${sub.status === 'completed' ? 'line-through text-dark-muted' : 'text-dark'}`}>
                              {sub.title}
                            </span>
                            <span className="text-dark-muted">({sub.duration_minutes} min)</span>
                          </div>
                          <span className={`text-[10px] font-semibold px-2 py-0.5 rounded capitalize ${
                            sub.status === 'completed' ? 'bg-green-50 text-green-700' : 'bg-amber-50 text-amber-700'
                          }`}>
                            {sub.status}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )
            })}
          </section>
        </>
      )}

      {/* Semantic Task Decomposition Modal */}
      {decomposeTask && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-gray-100 space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs font-bold uppercase tracking-wider text-peach-dark">Semantic Decomposition</p>
                <h2 className="text-xl font-bold text-dark mt-0.5">Break Down Task</h2>
                <p className="text-xs text-dark-muted mt-1">
                  Decomposing: <strong className="text-dark">{decomposeTask.title}</strong> ({decomposeTask.duration_minutes} min)
                </p>
              </div>
              <button
                type="button"
                onClick={() => setDecomposeTask(null)}
                className="text-dark-muted hover:text-dark text-lg font-bold"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3 bg-gray-50 p-4 rounded-xl border border-gray-100">
              <div className="grid grid-cols-2 gap-3">
                <label className="block text-xs font-semibold text-dark">
                  Target Subtasks
                  <select
                    value={numSubtasks}
                    onChange={(e) => setNumSubtasks(Number(e.target.value))}
                    className="w-full mt-1 px-3 py-1.5 border rounded-lg bg-white text-xs"
                  >
                    <option value={2}>2 Subtasks</option>
                    <option value={3}>3 Subtasks (Recommended)</option>
                    <option value={4}>4 Subtasks</option>
                    <option value={5}>5 Subtasks</option>
                  </select>
                </label>
                <label className="block text-xs font-semibold text-dark">
                  Focus Hint (Optional)
                  <input
                    type="text"
                    value={promptHint}
                    onChange={(e) => setPromptHint(e.target.value)}
                    placeholder="e.g. Focus on slides & rehearsal"
                    className="w-full mt-1 px-3 py-1.5 border rounded-lg bg-white text-xs"
                  />
                </label>
              </div>

              <button
                type="button"
                onClick={previewDecomposition}
                disabled={decomposing}
                className="w-full py-2 bg-purple-600 text-white rounded-lg text-xs font-semibold hover:bg-purple-700 transition-colors"
              >
                {decomposing ? 'Generating Decomposition...' : 'Generate Proposed Subtasks'}
              </button>
            </div>

            {decompositionPreview && (
              <div className="space-y-3 pt-2">
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-dark">Proposed Subtasks & Dependencies</h3>
                  <span className="text-[11px] text-purple-700 font-semibold bg-purple-50 px-2 py-0.5 rounded">
                    Sequential Workflow
                  </span>
                </div>
                <div className="space-y-2">
                  {decompositionPreview.subtasks.map((st, i) => (
                    <div key={i} className="p-3 bg-white border border-gray-200 rounded-xl space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-xs text-dark">
                          Step {i + 1}: {st.title}
                        </span>
                        <span className="text-[11px] font-bold text-peach-dark">{st.duration_minutes} min</span>
                      </div>
                      {st.description && <p className="text-[11px] text-dark-muted">{st.description}</p>}
                      {i > 0 && (
                        <p className="text-[10px] text-purple-600 font-medium">
                          ↳ Depends on Step {i}
                        </p>
                      )}
                    </div>
                  ))}
                </div>

                <div className="flex gap-2 pt-2">
                  <button
                    type="button"
                    onClick={() => setDecomposeTask(null)}
                    className="flex-1 py-2.5 border rounded-xl text-xs font-medium hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                  <button
                    type="button"
                    onClick={applyDecomposition}
                    disabled={decomposing}
                    className="flex-1 py-2.5 bg-peach text-white rounded-xl text-xs font-bold hover:bg-peach-dark shadow-sm"
                  >
                    {decomposing ? 'Creating...' : 'Apply Decomposition & Save'}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Task Dependencies Modal */}
      {dependencyTask && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-gray-100 space-y-4">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs font-bold uppercase tracking-wider text-peach-dark">Prerequisites & Blockers</p>
                <h2 className="text-lg font-bold text-dark mt-0.5">Task Dependencies</h2>
                <p className="text-xs text-dark-muted">Task: <strong>{dependencyTask.title}</strong></p>
              </div>
              <button
                type="button"
                onClick={() => setDependencyTask(null)}
                className="text-dark-muted hover:text-dark text-lg font-bold"
              >
                ✕
              </button>
            </div>

            <div className="space-y-2">
              <h3 className="text-xs font-semibold text-dark">Current Prerequisites:</h3>
              {loadingDeps && <p className="text-xs text-dark-muted">Loading dependencies...</p>}
              {!loadingDeps && taskDependencies.length === 0 && (
                <p className="text-xs text-dark-muted py-3 bg-gray-50 rounded-lg text-center">
                  No prerequisites. This task can be scheduled anytime.
                </p>
              )}
              {!loadingDeps && taskDependencies.map(dep => (
                <div key={dep.depends_on_id} className="p-2.5 rounded-lg border flex items-center justify-between text-xs">
                  <div>
                    <p className="font-semibold text-dark">{dep.title}</p>
                    <p className="text-[10px] text-dark-muted capitalize">Status: {dep.status}</p>
                  </div>
                  <span className={`text-[10px] px-2 py-0.5 rounded font-bold ${
                    dep.status === 'completed' ? 'bg-green-100 text-green-800' : 'bg-amber-100 text-amber-800'
                  }`}>
                    {dep.status === 'completed' ? 'Satisfied' : 'Blocking'}
                  </span>
                </div>
              ))}
            </div>

            <div className="pt-2 border-t space-y-2">
              <label className="block text-xs font-semibold text-dark">
                Add Prerequisite (Task that must be completed first)
                <select
                  value={selectedPrereq}
                  onChange={(e) => setSelectedPrereq(e.target.value)}
                  className="w-full mt-1 px-3 py-2 border rounded-xl text-xs bg-white"
                >
                  <option value="">Select a task...</option>
                  {tasks
                    .filter(t => t.id !== dependencyTask.id && t.status === 'pending')
                    .map(t => (
                      <option key={t.id} value={t.id}>{t.title} ({t.duration_minutes}m)</option>
                    ))}
                </select>
              </label>
              <div className="flex gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setDependencyTask(null)}
                  className="flex-1 py-2 border rounded-xl text-xs font-medium hover:bg-gray-50"
                >
                  Close
                </button>
                <button
                  type="button"
                  onClick={addDependency}
                  disabled={!selectedPrereq}
                  className="flex-1 py-2 bg-peach text-white rounded-xl text-xs font-bold hover:bg-peach-dark disabled:opacity-50"
                >
                  Add Prerequisite
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
