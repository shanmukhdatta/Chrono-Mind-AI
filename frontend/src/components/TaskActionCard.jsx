import React from 'react'
import { CheckCircle2, Calendar, Clock, Star } from 'lucide-react'
import { format, parseISO } from 'date-fns'

export function TaskActionCard({ task }) {
  if (!task || !task.task_id) return null

  return (
    <div className="mt-2 p-3 bg-peach/10 border border-peach/25 rounded-xl animate-fade-in">
      <div className="flex items-center gap-2 mb-2">
        <CheckCircle2 className="w-4 h-4 text-green-500 flex-shrink-0" />
        <p className="text-xs font-semibold text-peach-dark">Task scheduled!</p>
      </div>
      <p className="text-sm font-medium text-dark mb-2 truncate">{task.title}</p>
      <div className="space-y-1">
        <div className="flex items-center gap-2 text-xs text-dark-muted">
          <Calendar className="w-3 h-3 text-peach" />
          <span>{task.date ? format(parseISO(task.date), 'EEE, d MMM') : ''}</span>
        </div>
        <div className="flex items-center gap-2 text-xs text-dark-muted">
          <Clock className="w-3 h-3 text-peach" />
          <span>{task.start_time} – {task.end_time} ({task.duration_minutes}m)</span>
        </div>
        <div className="flex items-center gap-2 text-xs text-dark-muted">
          <Star className="w-3 h-3 text-peach" />
          <span className="capitalize">{task.importance === 'important' ? '⭐ Important' : '○ Optional'}</span>
        </div>
      </div>
    </div>
  )
}
