import React, { useState, useRef, useEffect } from 'react'
import { format } from 'date-fns'

export function CalendarDay({ date, tasks, onTaskClick, onSlotClick }) {
  const [currentTime, setCurrentTime] = useState(new Date())
  const timelineRef = useRef(null)
  const rowHeight = 64
  const totalHeight = 24 * rowHeight

  useEffect(() => {
    const interval = setInterval(() => setCurrentTime(new Date()), 60000)
    // Scroll to current hour on mount
    if (timelineRef.current) {
      const hour = new Date().getHours()
      timelineRef.current.scrollTop = Math.max(0, hour * rowHeight - 200)
    }
    return () => clearInterval(interval)
  }, [])

  const getTaskStyle = (task) => {
    const [sh, sm] = task.start_time.split(':').map(Number)
    const [eh, em] = task.end_time.split(':').map(Number)
    const startMin = sh * 60 + sm
    const duration = (eh * 60 + em) - startMin
    return {
      top: `${(startMin / 1440) * totalHeight}px`,
      height: `${Math.max((duration / 1440) * totalHeight, 24)}px`,
    }
  }

  const getTaskColor = (task) => {
    if (task.completed) return 'bg-green-100 border-green-300 text-green-800'
    if (task.rescheduled) return 'bg-blue-50 border-blue-300 text-blue-800'
    if (task.importance === 'important') return 'bg-peach/20 border-peach/50 text-dark'
    return 'bg-gray-100 border-gray-300 text-dark-muted'
  }

  const handleTimelineClick = (e) => {
    if (e.target.closest('[data-task]')) return
    if (!timelineRef.current) return
    const rect = timelineRef.current.getBoundingClientRect()
    const y = e.clientY - rect.top + timelineRef.current.scrollTop
    const minute = Math.floor((y / totalHeight) * 1440)
    const hour = Math.floor(minute / 60)
    const min = Math.floor((minute % 60) / 15) * 15
    const timeStr = `${String(hour).padStart(2, '0')}:${String(min).padStart(2, '0')}`
    onSlotClick && onSlotClick(date, timeStr)
  }

  const currentTimeTop = () => {
    const mins = currentTime.getHours() * 60 + currentTime.getMinutes()
    return (mins / 1440) * totalHeight
  }

  const today = new Date().toISOString().split('T')[0]
  const isToday = date === today

  return (
    <div className="h-full flex flex-col overflow-hidden">
      <div className="flex-1 overflow-y-auto" ref={timelineRef}>
        <div
          className="relative cursor-pointer select-none"
          style={{ height: `${totalHeight}px` }}
          onClick={handleTimelineClick}
        >
          {/* Hour rows */}
          {Array.from({ length: 24 }, (_, h) => (
            <div
              key={h}
              className="absolute w-full border-b border-gray-100 flex"
              style={{ top: `${h * rowHeight}px`, height: `${rowHeight}px` }}
            >
              <div className="w-16 flex-shrink-0 text-xs text-dark-muted font-medium px-3 pt-2 border-r border-gray-100 bg-white">
                {format(new Date(2000, 0, 1, h, 0), 'h a')}
              </div>
              <div className={`flex-1 ${h % 2 === 0 ? 'bg-white' : 'bg-gray-50/30'} hover:bg-peach/5 transition-colors`} />
            </div>
          ))}

          {/* Current time indicator */}
          {isToday && (
            <div
              className="absolute w-full z-20 pointer-events-none"
              style={{ top: `${currentTimeTop()}px` }}
            >
              <div className="flex items-center">
                <div className="w-16 flex-shrink-0" />
                <div className="w-3 h-3 bg-red-500 rounded-full -ml-1.5 flex-shrink-0" />
                <div className="flex-1 h-0.5 bg-red-400" />
              </div>
            </div>
          )}

          {/* Tasks */}
          {tasks.map(task => (
            <div
              key={task.task_id}
              data-task="true"
              className={`absolute left-16 right-2 rounded-xl border px-3 py-2 cursor-pointer hover:shadow-md hover:scale-[1.01] transition-all z-10 ${getTaskColor(task)}`}
              style={getTaskStyle(task)}
              onClick={(e) => { e.stopPropagation(); onTaskClick && onTaskClick(task) }}
            >
              <p className="text-xs font-semibold truncate leading-tight">{task.title}</p>
              <p className="text-[10px] opacity-70 mt-0.5">{task.start_time} – {task.end_time}</p>
              {task.rescheduled && <span className="text-[9px] text-blue-600">↻ rescheduled</span>}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
