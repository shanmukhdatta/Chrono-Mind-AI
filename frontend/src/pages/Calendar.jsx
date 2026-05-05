import React, { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { format, parseISO, addDays, subDays, addMonths, subMonths, addWeeks, subWeeks } from 'date-fns'
import { Plus, ChevronLeft, ChevronRight } from 'lucide-react'
import { useTaskStore } from '../store/taskStore'
import { useTasks } from '../hooks/useTasks'
import { useUiStore } from '../store/uiStore'
import { CalendarDay } from '../components/CalendarDay'
import { CalendarWeek } from '../components/CalendarWeek'
import { CalendarMonth } from '../components/CalendarMonth'
import { AddTaskForm } from '../components/AddTaskForm'
import { Button } from '../components/ui/Button'

export default function Calendar() {
  const [searchParams, setSearchParams] = useSearchParams()
  const { tasks, selectedDate, setSelectedDate } = useTaskStore()
  const { fetchTasks } = useTasks()
  const { calendarView, setCalendarView } = useUiStore()
  const [showAddModal, setShowAddModal] = useState(false)
  const [editingTask, setEditingTask] = useState(null)
  const [prefillSlot, setPrefillSlot] = useState(null)

  // Sync date with URL param
  useEffect(() => {
    const dateParam = searchParams.get('date')
    if (dateParam) setSelectedDate(dateParam)
  }, [])

  // Fetch day tasks whenever date changes (day view only — week/month fetch their own)
  useEffect(() => {
    if (calendarView === 'day') fetchTasks(selectedDate)
  }, [selectedDate, calendarView])

  const handleTaskClick = (task) => {
    setEditingTask(task)
    setPrefillSlot(null)
    setShowAddModal(true)
  }

  const handleSlotClick = (date, startTime) => {
    setEditingTask(null)
    setPrefillSlot({ date, startTime })
    setShowAddModal(true)
  }

  const handleDayClick = (dateStr) => {
    setSelectedDate(dateStr)
    setSearchParams({ date: dateStr })
    setCalendarView('day')
  }

  const handleCloseModal = () => {
    setShowAddModal(false)
    setEditingTask(null)
    setPrefillSlot(null)
    if (calendarView === 'day') fetchTasks(selectedDate)
  }

  const navigate = (dir) => {
    const d = parseISO(selectedDate)
    let newDate
    if (calendarView === 'day') newDate = dir > 0 ? addDays(d, 1) : subDays(d, 1)
    else if (calendarView === 'week') newDate = dir > 0 ? addWeeks(d, 1) : subWeeks(d, 1)
    else newDate = dir > 0 ? addMonths(d, 1) : subMonths(d, 1)
    const newStr = format(newDate, 'yyyy-MM-dd')
    setSelectedDate(newStr)
    setSearchParams({ date: newStr })
  }

  const navLabel = () => {
    const d = parseISO(selectedDate)
    if (calendarView === 'day') return format(d, 'EEEE, d MMMM yyyy')
    if (calendarView === 'week') return `Week of ${format(d, 'd MMM yyyy')}`
    return format(d, 'MMMM yyyy')
  }

  const today = format(new Date(), 'yyyy-MM-dd')
  const views = [{ key: 'day', label: 'Day' }, { key: 'week', label: 'Week' }, { key: 'month', label: 'Month' }]

  return (
    <div className="h-full flex flex-col gap-4">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 flex-shrink-0">
        <div className="flex items-center gap-2">
          <button onClick={() => navigate(-1)} className="p-2 hover:bg-gray-100 rounded-xl transition-colors">
            <ChevronLeft className="w-5 h-5 text-dark-muted" />
          </button>
          <div className="min-w-[220px] text-center">
            <p className="font-semibold text-dark text-sm">{navLabel()}</p>
            {selectedDate !== today && (
              <button
                onClick={() => { setSelectedDate(today); setSearchParams({ date: today }); setCalendarView('day') }}
                className="text-xs text-peach hover:underline"
              >Today</button>
            )}
          </div>
          <button onClick={() => navigate(1)} className="p-2 hover:bg-gray-100 rounded-xl transition-colors">
            <ChevronRight className="w-5 h-5 text-dark-muted" />
          </button>
        </div>

        <div className="flex items-center gap-2">
          <div className="flex bg-gray-100 rounded-xl p-1">
            {views.map(v => (
              <button
                key={v.key}
                onClick={() => setCalendarView(v.key)}
                className={`px-3 py-1.5 text-sm font-medium rounded-lg transition-all ${
                  calendarView === v.key ? 'bg-white text-dark shadow-sm' : 'text-dark-muted hover:text-dark'
                }`}
              >{v.label}</button>
            ))}
          </div>
          <Button onClick={() => { setEditingTask(null); setPrefillSlot({ date: selectedDate }); setShowAddModal(true) }}>
            <Plus className="w-4 h-4 mr-1" /> Add
          </Button>
        </div>
      </div>

      {/* Calendar Body */}
      <div className="flex-1 bg-white rounded-xl border border-gray-100 overflow-hidden shadow-sm min-h-0">
        {calendarView === 'day' && (
          <CalendarDay
            date={selectedDate}
            tasks={tasks}
            onTaskClick={handleTaskClick}
            onSlotClick={handleSlotClick}
          />
        )}
        {calendarView === 'week' && (
          <CalendarWeek
            date={selectedDate}
            onTaskClick={handleTaskClick}
            onDayClick={handleDayClick}
          />
        )}
        {calendarView === 'month' && (
          <CalendarMonth
            date={selectedDate}
            onDayClick={handleDayClick}
          />
        )}
      </div>

      <AddTaskForm
        isOpen={showAddModal}
        onClose={handleCloseModal}
        initialData={editingTask}
        prefillDate={prefillSlot?.date}
        prefillStartTime={prefillSlot?.startTime}
      />
    </div>
  )
}
