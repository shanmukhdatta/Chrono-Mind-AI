import React, { useState, useEffect } from 'react'
import { startOfWeek, addDays, format, parseISO } from 'date-fns'
import { AddTaskForm } from './AddTaskForm'
import api from '../lib/api'

export function CalendarWeek({ date, onTaskClick, onDayClick }) {
  const [weekTasks, setWeekTasks] = useState({})
  const [showAddModal, setShowAddModal] = useState(false)
  const [prefillSlot, setPrefillSlot] = useState(null)

  const weekStart = startOfWeek(parseISO(date), { weekStartsOn: 1 })
  const days = Array.from({ length: 7 }, (_, i) => addDays(weekStart, i))
  const hours = Array.from({ length: 14 }, (_, i) => i + 8) // 08-21

  useEffect(() => {
    const fetchAll = async () => {
      const result = {}
      await Promise.all(
        days.map(async (day) => {
          const dateStr = format(day, 'yyyy-MM-dd')
          try {
            const res = await api.get('/api/tasks', { params: { date: dateStr } })
            result[dateStr] = res.data.success ? res.data.data : []
          } catch { result[dateStr] = [] }
        })
      )
      setWeekTasks(result)
    }
    fetchAll()
  }, [date])

  const getTaskColor = (task) => {
    if (task.completed) return 'bg-green-100 text-green-800 border-green-200'
    if (task.rescheduled) return 'bg-blue-100 text-blue-800 border-blue-200'
    if (task.importance === 'important') return 'bg-peach/20 text-dark border-peach/30'
    return 'bg-gray-100 text-dark-muted border-gray-200'
  }

  const today = format(new Date(), 'yyyy-MM-dd')

  return (
    <div className="h-full flex flex-col overflow-hidden">
      {/* Day headers */}
      <div className="grid grid-cols-8 border-b border-gray-100 flex-shrink-0 bg-white">
        <div className="w-16 border-r border-gray-100" />
        {days.map((day, i) => {
          const ds = format(day, 'yyyy-MM-dd')
          const isToday = ds === today
          return (
            <button
              key={i}
              onClick={() => onDayClick && onDayClick(ds)}
              className={`py-3 text-center border-l border-gray-100 hover:bg-peach/5 transition-colors ${isToday ? 'bg-peach/10' : ''}`}
            >
              <p className="text-xs text-dark-muted">{format(day, 'EEE')}</p>
              <p className={`text-base font-bold mt-1 w-8 h-8 rounded-full flex items-center justify-center mx-auto ${isToday ? 'bg-peach text-white' : 'text-dark'}`}>
                {format(day, 'd')}
              </p>
            </button>
          )
        })}
      </div>

      {/* Time grid */}
      <div className="flex-1 overflow-y-auto">
        {hours.map(hour => (
          <div key={hour} className="grid grid-cols-8 border-b border-gray-50 min-h-[56px]">
            <div className="px-3 py-1 text-xs text-dark-muted font-medium border-r border-gray-100 bg-white flex-shrink-0">
              {`${String(hour).padStart(2, '0')}:00`}
            </div>
            {days.map((day, di) => {
              const ds = format(day, 'yyyy-MM-dd')
              const dayTasks = (weekTasks[ds] || []).filter(t => {
                const [h] = t.start_time.split(':').map(Number)
                return h === hour
              })
              return (
                <div
                  key={di}
                  onClick={() => {
                    setPrefillSlot({ date: ds, startTime: `${String(hour).padStart(2, '0')}:00` })
                    setShowAddModal(true)
                  }}
                  className="border-l border-gray-100 p-1 hover:bg-peach/5 cursor-pointer transition-colors min-h-[56px]"
                >
                  {dayTasks.map(task => (
                    <div
                      key={task.task_id}
                      onClick={(e) => { e.stopPropagation(); onTaskClick && onTaskClick(task) }}
                      className={`text-[10px] px-1.5 py-1 rounded border mb-1 cursor-pointer hover:opacity-80 transition-opacity truncate ${getTaskColor(task)}`}
                      title={`${task.title} (${task.start_time}–${task.end_time})`}
                    >
                      {task.title}
                    </div>
                  ))}
                </div>
              )
            })}
          </div>
        ))}
      </div>

      <AddTaskForm
        isOpen={showAddModal}
        onClose={() => { setShowAddModal(false); setPrefillSlot(null) }}
        prefillDate={prefillSlot?.date}
        prefillStartTime={prefillSlot?.startTime}
      />
    </div>
  )
}
