import React, { useState } from 'react'
import { CheckCircle2, Circle, Edit3, Trash2, Timer, Clock, AlertCircle, RefreshCw } from 'lucide-react'
import { useTasks } from '../hooks/useTasks'
import { useTimerStore } from '../store/timerStore'
import toast from 'react-hot-toast'

export function TaskCard({ task, onEdit }) {
  const { completeTask, deleteTask } = useTasks()
  const { startTimer, activeTimerId } = useTimerStore()
  const [isDeleting, setIsDeleting] = useState(false)

  const handleComplete = async () => {
    if (task.completed) return
    await completeTask(task.task_id)
  }

  const handleDelete = async () => {
    if (!window.confirm(`Delete "${task.title}"?`)) return
    setIsDeleting(true)
    await deleteTask(task.task_id)
  }

  const handleStartTimer = () => {
    if (activeTimerId === task.task_id) {
      toast('Timer already running for this task', { icon: '⏱' })
      return
    }
    startTimer(task.task_id, task.duration_minutes || 60, task.title)
    toast.success(`Timer started for "${task.title}"`)
  }

  const importanceBadge = task.importance === 'important'
    ? 'bg-peach/15 text-peach-dark border border-peach/30'
    : 'bg-gray-100 text-dark-muted border border-gray-200'

  const cardStyle = task.completed
    ? 'border-green-200 bg-green-50/50'
    : task.rescheduled
    ? 'border-blue-200 bg-blue-50/30'
    : 'border-gray-100 bg-white hover:border-peach/30 hover:shadow-peach'

  return (
    <div className={`rounded-xl border p-4 transition-all duration-200 ${cardStyle} ${isDeleting ? 'opacity-50 pointer-events-none' : ''}`}>
      <div className="flex items-start gap-3">
        {/* Checkbox */}
        <button
          onClick={handleComplete}
          disabled={task.completed}
          className="mt-0.5 flex-shrink-0 transition-transform hover:scale-110"
          aria-label={task.completed ? 'Task completed' : 'Mark complete'}
        >
          {task.completed
            ? <CheckCircle2 className="w-5 h-5 text-green-500" />
            : <Circle className="w-5 h-5 text-gray-300 hover:text-peach transition-colors" />
          }
        </button>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-2 mb-1">
            <p className={`font-medium text-sm ${task.completed ? 'line-through text-dark-muted' : 'text-dark'}`}>
              {task.title}
            </p>
            {task.rescheduled && (
              <span className="flex items-center gap-1 text-[10px] bg-blue-100 text-blue-700 rounded-full px-2 py-0.5">
                <RefreshCw className="w-2.5 h-2.5" /> Rescheduled
              </span>
            )}
            {task.recurrence && task.recurrence !== 'none' && (
              <span className="text-[10px] bg-violet-100 text-violet-700 rounded-full px-2 py-0.5">
                🔁 {task.recurrence}
              </span>
            )}
          </div>

          <div className="flex flex-wrap items-center gap-3 text-xs text-dark-muted">
            <span className="flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {task.start_time} – {task.end_time}
            </span>
            <span className="flex items-center gap-1">
              <Timer className="w-3 h-3" />
              {task.duration_minutes}m
            </span>
            <span className={`px-2 py-0.5 rounded-full text-[10px] font-medium ${importanceBadge}`}>
              {task.importance === 'important' ? '⭐ Important' : 'Optional'}
            </span>
          </div>

          {task.rescheduled_from && (
            <p className="text-[10px] text-blue-500 mt-1">Moved from {task.rescheduled_from}</p>
          )}
        </div>

        {/* Actions */}
        <div className="flex items-center gap-1 flex-shrink-0">
          {!task.completed && (
            <button
              onClick={handleStartTimer}
              className={`p-1.5 rounded-lg transition-colors ${activeTimerId === task.task_id ? 'bg-peach text-white' : 'hover:bg-peach/10 text-dark-muted hover:text-peach'}`}
              title="Start Focus Timer"
            >
              <Timer className="w-4 h-4" />
            </button>
          )}
          {!task.completed && (
            <button
              onClick={() => onEdit(task)}
              className="p-1.5 rounded-lg hover:bg-gray-100 text-dark-muted hover:text-dark transition-colors"
              title="Edit task"
            >
              <Edit3 className="w-4 h-4" />
            </button>
          )}
          <button
            onClick={handleDelete}
            className="p-1.5 rounded-lg hover:bg-red-50 text-dark-muted hover:text-red-500 transition-colors"
            title="Delete task"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  )
}
