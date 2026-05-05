import React, { useState, useEffect, useRef } from 'react'
import { format, parseISO, addDays, subDays } from 'date-fns'
import { Plus, Search, Sun, ChevronLeft, ChevronRight } from 'lucide-react'
import { useTasks } from '../hooks/useTasks'
import { useTaskStore } from '../store/taskStore'
import { useNotifications } from '../hooks/useNotifications'
import { useNotificationStore } from '../store/notificationStore'
import { useAuth } from '../hooks/useAuth'
import { useAuthStore } from '../store/authStore'
import { AddTaskForm } from '../components/AddTaskForm'
import { TaskCard } from '../components/TaskCard'
import { RescheduleBanner } from '../components/RescheduleBanner'
import { Button } from '../components/ui/Button'
import { Spinner } from '../components/ui/Spinner'
import api from '../lib/api'

function DemoBanner() {
  const { user } = useAuthStore()
  const { signIn } = useAuth()
  if (user?.uid !== 'demo') return null
  return (
    <div className="bg-amber-100 border border-amber-300 rounded-xl p-3 mb-4 flex items-center justify-between shadow-sm">
      <p className="text-amber-900 text-sm font-medium">⚠️ Demo Mode — tasks are not saved. Sign in to keep your data.</p>
      <Button size="sm" onClick={signIn} className="bg-amber-500 hover:bg-amber-600 border-none text-white shadow-none">Sign In</Button>
    </div>
  )
}

export default function Dashboard() {
  const { tasks, selectedDate, setSelectedDate, isLoading } = useTaskStore()
  const { fetchTasks } = useTasks()
  const { notifications } = useNotificationStore()
  const { fetchNotifications } = useNotifications()

  const [showAddModal, setShowAddModal] = useState(false)
  const [editingTask, setEditingTask] = useState(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [briefing, setBriefing] = useState(null)

  const tasksLoadedRef = useRef(false)
  const briefingFiredRef = useRef(false)

  // Fetch tasks whenever selected date changes
  useEffect(() => {
    tasksLoadedRef.current = false
    briefingFiredRef.current = false
    fetchTasks(selectedDate).then(() => {
      tasksLoadedRef.current = true
    })
  }, [selectedDate])

  // Fetch notifications once on mount
  useEffect(() => {
    fetchNotifications()
  }, [])

  // Daily briefing — fires only once today, only after tasks actually loaded
  useEffect(() => {
    if (briefingFiredRef.current) return
    const today = new Date().toISOString().split('T')[0]
    if (selectedDate !== today) return
    if (isLoading) return
    if (!tasksLoadedRef.current) return
    if (tasks.length === 0) return
    // Only attempt if tasks are for today
    const lastDate = localStorage.getItem('last_briefing_date')
    if (lastDate === today) return

    briefingFiredRef.current = true
    const taskCount = tasks.length
    api.post('/api/assistant/chat', {
      message: `Give me a short 2-sentence morning briefing for my day. I have ${taskCount} tasks scheduled today (${today}).`,
      conversation_history: []
    }).then(res => {
      if (res.data.success) {
        const reply = res.data.data.reply
        // Strip any JSON action block from the reply before showing
        const clean = reply.replace(/\{[^{}]*"action"[^{}]*\}/g, '').trim()
        if (clean.length > 20) {
          setBriefing(clean)
          localStorage.setItem('last_briefing_date', today)
        }
      }
    }).catch(() => {})
  }, [isLoading, tasks.length, selectedDate])

  const shiftDay = (dir) => {
    const d = parseISO(selectedDate)
    setSelectedDate(format(dir > 0 ? addDays(d, 1) : subDays(d, 1), 'yyyy-MM-dd'))
  }

  const goToday = () => setSelectedDate(new Date().toISOString().split('T')[0])
  const isToday = selectedDate === new Date().toISOString().split('T')[0]

  const filtered = tasks.filter(t =>
    t.title.toLowerCase().includes(searchQuery.toLowerCase())
  )
  const rescheduled = filtered.filter(t => t.rescheduled)
  const regular = filtered.filter(t => !t.rescheduled)
  const doneCount = filtered.filter(t => t.completed).length
  const pendingCount = filtered.filter(t => !t.completed).length

  const handleEdit = (task) => { setEditingTask(task); setShowAddModal(true) }
  const handleClose = () => { setShowAddModal(false); setEditingTask(null) }

  return (
    <div className="space-y-5 max-w-3xl">
      <DemoBanner />

      {/* Daily briefing */}
      {briefing && isToday && (
        <div className="bg-gradient-to-r from-amber-50 to-orange-50 border border-amber-200 rounded-xl p-4 flex items-start gap-3 animate-fade-in">
          <Sun className="w-5 h-5 text-amber-500 mt-0.5 flex-shrink-0" />
          <div className="flex-1">
            <p className="text-sm font-semibold text-amber-900 mb-0.5">Good morning ☀️</p>
            <p className="text-sm text-amber-800 leading-relaxed">{briefing}</p>
          </div>
          <button onClick={() => setBriefing(null)} className="text-amber-400 hover:text-amber-600 text-xl leading-none flex-shrink-0">×</button>
        </div>
      )}

      {/* Reschedule banner */}
      <RescheduleBanner
        notifications={notifications}
        onViewTasks={() => document.getElementById('rescheduled-section')?.scrollIntoView({ behavior: 'smooth' })}
      />

      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-dark">Dashboard</h1>
          <p className="text-dark-muted text-sm mt-0.5">
            {doneCount} done · {pendingCount} pending
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-dark-muted pointer-events-none" />
            <input
              type="text"
              placeholder="Search tasks…"
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              className="pl-9 pr-4 py-2.5 bg-white border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-peach/30 w-40"
            />
          </div>
          <Button onClick={() => { setEditingTask(null); setShowAddModal(true) }}>
            <Plus className="w-4 h-4 mr-1" /> Add Task
          </Button>
        </div>
      </div>

      {/* Date Navigator */}
      <div className="flex items-center justify-between bg-white rounded-xl p-3 border border-gray-100 shadow-sm">
        <button onClick={() => shiftDay(-1)} className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
          <ChevronLeft className="w-5 h-5 text-dark-muted" />
        </button>
        <div className="text-center">
          <p className="font-semibold text-dark text-sm">
            {format(parseISO(selectedDate), 'EEEE, d MMMM yyyy')}
          </p>
          {isToday
            ? <p className="text-xs text-green-500 font-medium mt-0.5">Today</p>
            : <button onClick={goToday} className="text-xs text-peach hover:underline mt-0.5">Back to today</button>
          }
        </div>
        <button onClick={() => shiftDay(1)} className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
          <ChevronRight className="w-5 h-5 text-dark-muted" />
        </button>
      </div>

      {/* Progress bar */}
      {filtered.length > 0 && (
        <div>
          <div className="flex justify-between text-xs text-dark-muted mb-1">
            <span>Progress</span>
            <span>{doneCount}/{filtered.length} tasks</span>
          </div>
          <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-peach to-peach-dark rounded-full transition-all duration-500"
              style={{ width: `${filtered.length > 0 ? (doneCount / filtered.length) * 100 : 0}%` }}
            />
          </div>
        </div>
      )}

      {/* Task List */}
      {isLoading ? (
        <div className="flex justify-center py-16"><Spinner size="lg" /></div>
      ) : filtered.length === 0 ? (
        <div className="text-center py-16 bg-white rounded-xl border-2 border-dashed border-gray-200">
          <div className="w-16 h-16 bg-peach/10 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <Plus className="w-8 h-8 text-peach" />
          </div>
          <h3 className="font-semibold text-dark mb-2">No tasks for this day</h3>
          <p className="text-dark-muted text-sm mb-4">Add tasks manually or use the AI assistant below</p>
          <Button variant="outline" onClick={() => setShowAddModal(true)}>Create First Task</Button>
        </div>
      ) : (
        <div className="space-y-5">
          {/* Rescheduled section */}
          {rescheduled.length > 0 && (
            <div id="rescheduled-section" className="scroll-mt-4">
              <div className="flex items-center gap-2 mb-2">
                <span className="w-2 h-2 bg-blue-500 rounded-full" />
                <h3 className="text-sm font-semibold text-blue-600">
                  Rescheduled from Previous Days ({rescheduled.length})
                </h3>
              </div>
              <div className="space-y-2">
                {rescheduled.map(task => (
                  <TaskCard key={task.task_id} task={task} onEdit={handleEdit} />
                ))}
              </div>
            </div>
          )}

          {/* Today's tasks */}
          {regular.length > 0 && (
            <div>
              {rescheduled.length > 0 && (
                <div className="flex items-center gap-2 mb-2">
                  <span className="w-2 h-2 bg-peach rounded-full" />
                  <h3 className="text-sm font-semibold text-dark-muted">
                    Today's Tasks ({regular.length})
                  </h3>
                </div>
              )}
              <div className="space-y-2">
                {regular.map(task => (
                  <TaskCard key={task.task_id} task={task} onEdit={handleEdit} />
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      <AddTaskForm
        isOpen={showAddModal}
        onClose={handleClose}
        initialData={editingTask}
        prefillDate={selectedDate}
      />
    </div>
  )
}
