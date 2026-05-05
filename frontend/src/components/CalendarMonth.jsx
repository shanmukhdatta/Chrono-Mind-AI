import React, { useState, useEffect } from 'react'
import { startOfMonth, endOfMonth, startOfWeek, addDays, format, isSameMonth, parseISO } from 'date-fns'
import api from '../lib/api'

export function CalendarMonth({ date, onDayClick }) {
  const [monthTasks, setMonthTasks] = useState({})

  const monthStart = startOfMonth(parseISO(date))
  const monthEnd = endOfMonth(parseISO(date))
  const gridStart = startOfWeek(monthStart, { weekStartsOn: 1 })

  const days = []
  let cursor = gridStart
  while (cursor <= monthEnd || days.length % 7 !== 0) {
    days.push(new Date(cursor))
    cursor = addDays(cursor, 1)
    if (days.length > 42) break
  }

  useEffect(() => {
    const fetchMonthTasks = async () => {
      try {
        const res = await api.get('/api/tasks', {
          params: {
            date_from: format(monthStart, 'yyyy-MM-dd'),
            date_to: format(monthEnd, 'yyyy-MM-dd')
          }
        })
        if (res.data.success) {
          const byDate = {}
          res.data.data.forEach(t => {
            if (!byDate[t.date]) byDate[t.date] = []
            byDate[t.date].push(t)
          })
          setMonthTasks(byDate)
        }
      } catch (e) { console.error('CalendarMonth fetch error:', e) }
    }
    fetchMonthTasks()
  }, [date])

  const today = format(new Date(), 'yyyy-MM-dd')
  const dayHeaders = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

  return (
    <div className="h-full flex flex-col">
      <div className="grid grid-cols-7 border-b border-gray-100">
        {dayHeaders.map(d => (
          <div key={d} className="py-2 text-center text-xs font-semibold text-dark-muted">{d}</div>
        ))}
      </div>
      <div className="flex-1 grid grid-cols-7 auto-rows-fr gap-px bg-gray-100 overflow-hidden">
        {days.map((day, i) => {
          const dateStr = format(day, 'yyyy-MM-dd')
          const isThisMonth = isSameMonth(day, monthStart)
          const isToday = dateStr === today
          const dayTasks = monthTasks[dateStr] || []
          const completedCount = dayTasks.filter(t => t.completed).length

          return (
            <button
              key={i}
              onClick={() => onDayClick && onDayClick(dateStr)}
              className={`bg-white p-2 text-left hover:bg-peach/5 transition-colors flex flex-col ${!isThisMonth ? 'opacity-40' : ''}`}
            >
              <span className={`text-sm font-semibold w-7 h-7 flex items-center justify-center rounded-full mb-1 ${isToday ? 'bg-peach text-white' : 'text-dark'}`}>
                {format(day, 'd')}
              </span>
              <div className="space-y-0.5 overflow-hidden flex-1">
                {dayTasks.slice(0, 3).map(task => (
                  <div key={task.task_id} className={`text-[9px] px-1.5 py-0.5 rounded truncate ${task.completed ? 'bg-green-100 text-green-700' : task.importance === 'important' ? 'bg-peach/20 text-peach-dark' : 'bg-gray-100 text-dark-muted'}`}>
                    {task.title}
                  </div>
                ))}
                {dayTasks.length > 3 && <p className="text-[9px] text-dark-muted pl-1">+{dayTasks.length - 3} more</p>}
              </div>
              {dayTasks.length > 0 && (
                <p className="text-[9px] text-green-600 font-medium mt-1">{completedCount}/{dayTasks.length} done</p>
              )}
            </button>
          )
        })}
      </div>
    </div>
  )
}
