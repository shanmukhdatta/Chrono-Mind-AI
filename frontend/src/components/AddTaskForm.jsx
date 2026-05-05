import React, { useState, useEffect } from 'react'
import { X, Plus, Edit3, Calendar, Clock, Star, Repeat } from 'lucide-react'
import { useTasks } from '../hooks/useTasks'
import { Button } from './ui/Button'
import { Spinner } from './ui/Spinner'

const RECURRENCE_OPTIONS = [
  { value: 'none', label: 'No repeat' },
  { value: 'daily', label: 'Every day' },
  { value: 'weekly', label: 'Every week' },
  { value: 'mon,wed,fri', label: 'Mon, Wed, Fri' },
  { value: 'tue,thu', label: 'Tue, Thu' },
  { value: 'mon,tue,wed,thu,fri', label: 'Weekdays' },
]

export function AddTaskForm({ isOpen, onClose, initialData = null, prefillDate = null, prefillStartTime = null }) {
  const { createTask, updateTaskById } = useTasks()
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [errors, setErrors] = useState({})

  const today = new Date().toISOString().split('T')[0]
  const defaultDate = prefillDate || today

  const [form, setForm] = useState({
    title: '',
    date: defaultDate,
    start_time: prefillStartTime || '09:00',
    end_time: '10:00',
    importance: 'important',
    recurrence: 'none',
  })

  useEffect(() => {
    if (isOpen) {
      if (initialData) {
        setForm({
          title: initialData.title || '',
          date: initialData.date || defaultDate,
          start_time: initialData.start_time || '09:00',
          end_time: initialData.end_time || '10:00',
          importance: initialData.importance || 'important',
          recurrence: initialData.recurrence || 'none',
        })
      } else {
        setForm({
          title: '',
          date: prefillDate || defaultDate,
          start_time: prefillStartTime || '09:00',
          end_time: prefillStartTime ? addHour(prefillStartTime) : '10:00',
          importance: 'important',
          recurrence: 'none',
        })
      }
      setErrors({})
    }
  }, [isOpen, initialData, prefillDate, prefillStartTime])

  function addHour(time) {
    const [h, m] = time.split(':').map(Number)
    return `${String((h + 1) % 24).padStart(2, '0')}:${String(m).padStart(2, '0')}`
  }

  const validate = () => {
    const errs = {}
    if (!form.title.trim()) errs.title = 'Title is required'
    if (!form.date) errs.date = 'Date is required'
    if (!form.start_time) errs.start_time = 'Start time is required'
    if (!form.end_time) errs.end_time = 'End time is required'
    if (form.end_time <= form.start_time) errs.end_time = 'End time must be after start time'
    const dur = calcDuration()
    if (dur < 15) errs.end_time = 'Duration must be at least 15 minutes'
    return errs
  }

  const calcDuration = () => {
    if (!form.start_time || !form.end_time) return 0
    const [sh, sm] = form.start_time.split(':').map(Number)
    const [eh, em] = form.end_time.split(':').map(Number)
    return (eh * 60 + em) - (sh * 60 + sm)
  }

  const handleChange = (field, value) => {
    setForm(prev => ({ ...prev, [field]: value }))
    if (errors[field]) setErrors(prev => ({ ...prev, [field]: null }))
  }

  const handleSubmit = async () => {
    const errs = validate()
    if (Object.keys(errs).length > 0) {
      setErrors(errs)
      return
    }

    setIsSubmitting(true)
    try {
      let result
      if (initialData) {
        result = await updateTaskById(initialData.task_id, form)
      } else {
        result = await createTask(form)
      }
      if (result) {
        onClose()
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  if (!isOpen) return null

  const duration = calcDuration()

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-dark/30 backdrop-blur-sm" onClick={onClose} />

      {/* Modal */}
      <div className="relative bg-white rounded-2xl shadow-2xl w-full max-w-md animate-fade-in">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-gray-100">
          <div className="flex items-center gap-2">
            {initialData ? <Edit3 className="w-5 h-5 text-peach" /> : <Plus className="w-5 h-5 text-peach" />}
            <h2 className="font-semibold text-dark">{initialData ? 'Edit Task' : 'Add New Task'}</h2>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-gray-100 rounded-xl transition-colors">
            <X className="w-5 h-5 text-dark-muted" />
          </button>
        </div>

        <div className="p-5 space-y-4">
          {/* Title */}
          <div>
            <label className="text-xs font-semibold text-dark-muted uppercase tracking-wide block mb-1.5">Task Title</label>
            <input
              type="text"
              value={form.title}
              onChange={e => handleChange('title', e.target.value)}
              placeholder="e.g. Fluid Mechanics Revision"
              maxLength={120}
              className={`input-field ${errors.title ? 'border-red-400 focus:ring-red-400/30' : ''}`}
              autoFocus
            />
            {errors.title && <p className="text-xs text-red-500 mt-1">{errors.title}</p>}
          </div>

          {/* Date */}
          <div>
            <label className="text-xs font-semibold text-dark-muted uppercase tracking-wide block mb-1.5">
              <Calendar className="w-3 h-3 inline mr-1" />Date
            </label>
            <input
              type="date"
              value={form.date}
              onChange={e => handleChange('date', e.target.value)}
              className={`input-field ${errors.date ? 'border-red-400' : ''}`}
            />
            {errors.date && <p className="text-xs text-red-500 mt-1">{errors.date}</p>}
          </div>

          {/* Time */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs font-semibold text-dark-muted uppercase tracking-wide block mb-1.5">
                <Clock className="w-3 h-3 inline mr-1" />Start
              </label>
              <input
                type="time"
                value={form.start_time}
                onChange={e => handleChange('start_time', e.target.value)}
                className={`input-field ${errors.start_time ? 'border-red-400' : ''}`}
              />
            </div>
            <div>
              <label className="text-xs font-semibold text-dark-muted uppercase tracking-wide block mb-1.5">
                <Clock className="w-3 h-3 inline mr-1" />End
              </label>
              <input
                type="time"
                value={form.end_time}
                onChange={e => handleChange('end_time', e.target.value)}
                className={`input-field ${errors.end_time ? 'border-red-400' : ''}`}
              />
              {errors.end_time && <p className="text-xs text-red-500 mt-1">{errors.end_time}</p>}
            </div>
          </div>

          {duration > 0 && (
            <p className="text-xs text-dark-muted">
              Duration: <span className={`font-semibold ${duration < 15 ? 'text-red-500' : 'text-peach-dark'}`}>{duration} minutes</span>
            </p>
          )}

          {/* Importance */}
          <div>
            <label className="text-xs font-semibold text-dark-muted uppercase tracking-wide block mb-1.5">
              <Star className="w-3 h-3 inline mr-1" />Priority
            </label>
            <div className="grid grid-cols-2 gap-2">
              {[
                { value: 'important', label: '⭐ Important', desc: 'Will be rescheduled if missed' },
                { value: 'not_important', label: '○ Optional', desc: 'Will be deleted if missed' },
              ].map(opt => (
                <button
                  key={opt.value}
                  onClick={() => handleChange('importance', opt.value)}
                  className={`p-3 rounded-xl border-2 text-left transition-all ${
                    form.importance === opt.value
                      ? opt.value === 'important' ? 'border-peach bg-peach/10' : 'border-gray-400 bg-gray-100'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <p className="text-sm font-medium text-dark">{opt.label}</p>
                  <p className="text-[10px] text-dark-muted mt-0.5">{opt.desc}</p>
                </button>
              ))}
            </div>
          </div>

          {/* Recurrence */}
          <div>
            <label className="text-xs font-semibold text-dark-muted uppercase tracking-wide block mb-1.5">
              <Repeat className="w-3 h-3 inline mr-1" />Repeat
            </label>
            <select
              value={form.recurrence}
              onChange={e => handleChange('recurrence', e.target.value)}
              className="input-field"
            >
              {RECURRENCE_OPTIONS.map(opt => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Footer */}
        <div className="flex gap-3 p-5 border-t border-gray-100">
          <Button variant="ghost" onClick={onClose} className="flex-1">Cancel</Button>
          <Button onClick={handleSubmit} disabled={isSubmitting} className="flex-1">
            {isSubmitting ? <Spinner size="sm" /> : (initialData ? 'Save Changes' : 'Add Task')}
          </Button>
        </div>
      </div>
    </div>
  )
}
