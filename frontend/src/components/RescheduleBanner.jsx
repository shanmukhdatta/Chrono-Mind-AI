import React from 'react'
import { RefreshCw, ArrowRight } from 'lucide-react'

export function RescheduleBanner({ notifications = [], onViewTasks }) {
  const rescheduleNotifs = notifications.filter(n => n.type === 'tasks_rescheduled' && !n.read)
  if (rescheduleNotifs.length === 0) return null

  const latest = rescheduleNotifs[0]

  return (
    <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-xl p-4 flex items-center gap-3 animate-fade-in">
      <div className="w-9 h-9 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
        <RefreshCw className="w-4 h-4 text-blue-600" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-blue-800">{latest.message}</p>
        <p className="text-xs text-blue-600 mt-0.5">Tap to view rescheduled tasks below</p>
      </div>
      {onViewTasks && (
        <button
          onClick={onViewTasks}
          className="flex items-center gap-1 text-xs font-semibold text-blue-700 hover:text-blue-900 whitespace-nowrap"
        >
          View <ArrowRight className="w-3 h-3" />
        </button>
      )}
    </div>
  )
}
