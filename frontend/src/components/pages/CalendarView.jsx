import { useEffect, useState, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ChevronLeft, ChevronRight, Plus, Clock, X } from 'lucide-react'
import { format, addDays, subDays, parseISO, setHours, setMinutes } from 'date-fns'
import { useCalendarStore } from '../../store'
import { GlassCard, RevealOnScroll, MagneticButton, CATEGORY_COLORS, GlassModal, GlassSelect } from '../ui'
import api from '../../api'
import toast from 'react-hot-toast'
import { useDrag } from '@use-gesture/react'

const HOURS = Array.from({ length: 24 }, (_, i) => i) // 0–23
const HOUR_WIDTH = 120 // px per hour

function timeToPx(timeStr) {
  if (!timeStr) return 0
  const [h, m] = timeStr.split(':').map(Number)
  return (h + m / 60) * HOUR_WIDTH
}

function pxToTime(px) {
  const totalHours = px / HOUR_WIDTH
  const h = Math.floor(totalHours)
  const m = Math.round((totalHours - h) * 60)
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`
}

function TaskBlock({ task, onDelete, onUpdate }) {
  const [hovered, setHovered] = useState(false)
  const color = CATEGORY_COLORS[task.category] || '#F4A261'
  const startPx = timeToPx(task.start_time || '08:00')
  const endPx = timeToPx(task.end_time || '09:00')
  const width = Math.max(endPx - startPx - 4, 40)
  
  const [isDragging, setIsDragging] = useState(false)
  const [pos, setPos] = useState({ x: 0, y: 0 })
  const [shake, setShake] = useState(false)

  const bind = useDrag(({ down, movement: [mx, my], last }) => {
    setIsDragging(down)
    if (down) {
      setPos({ x: mx, y: 0 }) // lock to X axis
    } else {
      // Snap to nearest hour slot on drop
      const deltaHours = Math.round(mx / HOUR_WIDTH)
      if (deltaHours !== 0) {
        setShake(true)
        setTimeout(() => setShake(false), 500)
        // Simulate dragging conflict check
        toast.error('Conflict: Slot occupied')
      }
      setPos({ x: 0, y: 0 })
    }
  })

  return (
    <>
      {isDragging && (
        <div
          className="absolute top-2 bottom-2 rounded-xl"
          style={{
            left: startPx + 2, width,
            background: 'rgba(244,162,97,0.15)',
            border: '2px dashed var(--peach)',
            zIndex: 1
          }}
        />
      )}
      <motion.div
        {...bind()}
        className="absolute top-2 bottom-2 rounded-xl px-3 py-2 flex flex-col justify-center overflow-hidden touch-none"
        style={{
          left: startPx + 2,
          width,
          background: `linear-gradient(135deg, ${color}CC, ${color}99)`,
          border: `1px solid ${color}66`,
          backdropFilter: 'blur(8px)',
          zIndex: isDragging ? 50 : (hovered ? 10 : 2),
          cursor: isDragging ? 'grabbing' : 'grab',
        }}
        initial={{ y: -15, opacity: 0 }}
        animate={{ 
          y: 0, 
          opacity: 1,
          x: shake ? [0,-5,5,-5,5,0] : pos.x,
          scale: isDragging ? 1.06 : 1,
          boxShadow: isDragging ? `0 16px 32px ${color}66` : `0 4px 12px ${color}22`
        }}
        whileHover={{ scale: isDragging ? 1.06 : 1.02, y: -2, boxShadow: `0 8px 24px ${color}44` }}
        onHoverStart={() => setHovered(true)}
        onHoverEnd={() => setHovered(false)}
      >
        <p className="text-xs font-bold text-white truncate leading-tight">{task.title}</p>
        {width > 80 && (
          <p className="text-xs text-white/70 mt-0.5">{task.start_time}–{task.end_time}</p>
        )}
        <AnimatePresence>
          {hovered && !isDragging && (
            <motion.button
              className="absolute top-1.5 right-1.5 w-5 h-5 rounded-full bg-white/20 flex items-center justify-center cursor-pointer"
              initial={{ opacity: 0, scale: 0 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0 }}
              onPointerDown={(e) => { e.stopPropagation() }}
              onClick={(e) => { e.stopPropagation(); onDelete(task.id) }}
            >
              <X size={10} color="white" />
            </motion.button>
          )}
        </AnimatePresence>
      </motion.div>
    </>
  )
}

function ClassBlock({ entry }) {
  const startPx = timeToPx(entry.start_time)
  const endPx = timeToPx(entry.end_time)
  const width = Math.max(endPx - startPx - 4, 40)
  const color = entry.color || '#F4A261'

  return (
    <motion.div
      className="absolute top-2 bottom-2 rounded-xl px-3 py-2 flex flex-col justify-center overflow-hidden pointer-events-none"
      style={{
        left: startPx + 2, width,
        background: `linear-gradient(135deg, ${color}44, ${color}22)`,
        border: `1.5px solid ${color}88`,
        backdropFilter: 'blur(8px)', zIndex: 1,
      }}
      initial={{ y: -10, opacity: 0 }} animate={{ y: 0, opacity: 1 }}
    >
      <p className="text-xs font-bold truncate" style={{ color }}>{entry.subject}</p>
      {width > 80 && <p className="text-xs mt-0.5" style={{ color: `${color}aa` }}>{entry.start_time}–{entry.end_time}</p>}
    </motion.div>
  )
}

function NowIndicator() {
  const [position, setPosition] = useState(() => {
    const now = new Date()
    return (now.getHours() + now.getMinutes() / 60) * HOUR_WIDTH
  })

  useEffect(() => {
    const interval = setInterval(() => {
      const now = new Date()
      setPosition((now.getHours() + now.getMinutes() / 60) * HOUR_WIDTH)
    }, 30000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="absolute top-0 bottom-0 z-20 pointer-events-none" style={{ left: position + 64 }}>
      <motion.div
        className="w-3 h-3 rounded-full -translate-x-1/2"
        style={{ background: 'var(--peach)', marginTop: 4 }}
        animate={{ scale: [1, 1.4, 1] }}
        transition={{ duration: 2, repeat: Infinity }}
      />
      <div className="w-px h-full" style={{
        background: 'linear-gradient(180deg, var(--peach) 0%, transparent 100%)',
        marginLeft: -0.5
      }} />
    </div>
  )
}

export default function CalendarView() {
  const { selectedDate, setSelectedDate, calendarData, fetchCalendarDay } = useCalendarStore()
  const timelineRef = useRef(null)
  
  // Modal state
  const [showModal, setShowModal] = useState(false)
  const [selectedHour, setSelectedHour] = useState(null)
  const [timeValue, setTimeValue] = useState('')
  const [newTask, setNewTask] = useState({ title: '', duration: 60, category: 'study' })

  useEffect(() => {
    fetchCalendarDay(selectedDate)
  }, [selectedDate])

  useEffect(() => {
    if (timelineRef.current) timelineRef.current.scrollLeft = 7 * HOUR_WIDTH - 40
  }, [calendarData])

  const goDay = (dir) => {
    const d = dir === 'next' ? addDays(parseISO(selectedDate), 1) : subDays(parseISO(selectedDate), 1)
    setSelectedDate(format(d, 'yyyy-MM-dd'))
  }

  // Typewriter effect for time 
  useEffect(() => {
    if (!showModal || selectedHour === null) return
    const timeStr = `${String(selectedHour).padStart(2, '0')}:00`
    let i = 0
    setTimeValue('')
    const timer = setInterval(() => {
      setTimeValue(timeStr.slice(0, ++i))
      if (i >= timeStr.length) clearInterval(timer)
    }, 50)
    return () => clearInterval(timer)
  }, [showModal, selectedHour])


  const openAddModal = (hour) => {
    setSelectedHour(hour)
    setShowModal(true)
  }

  const handleDeleteTask = async (id) => {
    try {
      await api.delete(`/tasks/${id}`)
      fetchCalendarDay(selectedDate)
      toast.success('Task removed')
    } catch { toast.error('Failed to delete task') }
  }

  const displayDate = parseISO(selectedDate)
  
  // Day Switcher Logic
  const days = []
  for (let i = -2; i <= 2; i++) {
    days.push(format(addDays(new Date(), i), 'yyyy-MM-dd'))
  }

  return (
    <div className="min-h-screen p-4 md:p-8 relative">
      <RevealOnScroll className="mb-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold" style={{ fontFamily: 'Inter', color: 'var(--text-1)' }}>Calendar</h1>
            <p style={{ color: 'var(--text-2)' }}>{format(displayDate, 'EEEE, MMMM d, yyyy')}</p>
          </div>

          <div className="flex items-center gap-3">
            {/* Day Switcher LayoutId */}
            <div className="relative flex gap-1 glass p-1 rounded-2xl hidden md:flex">
              {days.map(day => (
                <button key={day} onClick={() => setSelectedDate(day)} className="relative px-4 py-2 text-sm font-medium z-10"
                  style={{ color: selectedDate === day ? 'white' : 'var(--text-2)' }}>
                  {selectedDate === day && (
                    <motion.div layoutId="day-pill" className="absolute inset-0 rounded-xl"
                      style={{ background: 'linear-gradient(135deg, #F4A261, #E76F51)' }}
                      transition={{ type: 'spring', stiffness: 300, damping: 30 }} />
                  )}
                  <span className="relative z-10">{format(parseISO(day), 'EEE d')}</span>
                </button>
              ))}
            </div>

            <MagneticButton className="btn-primary flex items-center gap-2 text-sm" onClick={() => openAddModal(9)}>
              <Plus size={15} /> Add Task
            </MagneticButton>
          </div>
        </div>
      </RevealOnScroll>

      {/* Timeline */}
      <RevealOnScroll delay={0.1}>
        <GlassCard className="overflow-hidden p-0 relative">
          <div className="flex border-b border-white/10">
            <div className="w-16 flex-shrink-0 border-r border-white/10" />
            <div className="flex overflow-x-auto hide-scrollbar" ref={timelineRef}>
              {HOURS.map((h) => (
                <div key={h} className="flex-shrink-0 text-center py-2"
                  style={{ width: HOUR_WIDTH, fontSize: 11, color: 'var(--text-3)', fontWeight: 500 }}>
                  {h === 0 ? '12 AM' : h < 12 ? `${h} AM` : h === 12 ? '12 PM' : `${h - 12} PM`}
                </div>
              ))}
            </div>
          </div>

          <div className="overflow-x-auto hide-scrollbar" ref={timelineRef}>
            <div style={{ width: HOUR_WIDTH * 24 + 64, position: 'relative', minHeight: 240 }}>
              
              {/* Slots/Grid items logic */}
              <div className="absolute top-0 bottom-0 flex" style={{ left: 64 }}>
                {HOURS.map((h) => (
                  <div key={h} className="relative border-r border-white/5" style={{ width: HOUR_WIDTH }}>
                    <motion.div className="absolute inset-0 flex items-center justify-center opacity-0 group z-30"
                      whileHover={{ opacity: 1 }} style={{ cursor: 'none' }} onClick={() => openAddModal(h)}>
                      <motion.div className="w-8 h-8 rounded-full flex items-center justify-center bg-[#F4A261]/15 border border-dashed border-[#F4A261]"
                        initial={{ scale: 0.8, opacity: 0 }} whileHover={{ scale: 1, opacity: 1 }}>
                        <Plus size={16} color="var(--peach)" />
                      </motion.div>
                    </motion.div>
                  </div>
                ))}
              </div>

              <NowIndicator />

              {/* Classes */}
              {(calendarData?.timetable || []).length > 0 && (
                <div className="relative border-b border-white/5 h-20">
                  <div className="absolute left-0 w-16 h-full flex items-center justify-center text-[10px] text-white/50 origin-center -rotate-180" style={{ writingMode: 'vertical-rl' }}>Classes</div>
                  <div className="absolute top-0 bottom-0 right-0" style={{ left: 64 }}>
                    {calendarData.timetable.map(entry => <ClassBlock key={entry.id} entry={entry} />)}
                  </div>
                </div>
              )}

              {/* Tasks */}
              <div className="relative h-24">
                <div className="absolute left-0 w-16 h-full flex items-center justify-center text-[10px] text-white/50 origin-center -rotate-180" style={{ writingMode: 'vertical-rl' }}>Tasks</div>
                <div className="absolute top-0 bottom-0 right-0" style={{ left: 64 }}>
                  {(calendarData?.tasks || []).map(task => <TaskBlock key={task.id} task={task} onDelete={handleDeleteTask} />)}
                </div>
              </div>

            </div>
          </div>
        </GlassCard>
      </RevealOnScroll>

      <GlassModal isOpen={showModal} onClose={() => setShowModal(false)} title="Add Task">
        <div className="flex flex-col gap-4">
          <input className="w-full glass bg-white/5 border border-white/10 px-4 py-3 rounded-2xl text-white outline-none focus:border-peach/50 transition-colors"
            placeholder="Task title..." value={newTask.title} onChange={e => setNewTask(p => ({ ...p, title: e.target.value }))} autoFocus />
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-xs mb-1.5 block text-white/60">Time</label>
              <input type="text" className="w-full glass bg-white/5 border border-white/10 px-4 py-3 rounded-2xl text-white outline-none" value={timeValue} onChange={e => setTimeValue(e.target.value)} />
            </div>
            <div>
              <label className="text-xs mb-1.5 block text-white/60">Duration (min)</label>
              <input type="number" className="w-full glass bg-white/5 border border-white/10 px-4 py-3 rounded-2xl text-white outline-none" value={newTask.duration} onChange={e => setNewTask(p => ({ ...p, duration: Number(e.target.value) }))} />
            </div>
          </div>
          <div className="z-50 relative">
            <label className="text-xs mb-1.5 block text-white/60">Category</label>
            <GlassSelect
              options={Object.keys(CATEGORY_COLORS).map(k => ({ label: k.charAt(0).toUpperCase() + k.slice(1), value: k }))}
              value={newTask.category}
              onChange={(val) => setNewTask(p => ({ ...p, category: val }))}
              placeholder="Select Category"
            />
          </div>
          <div className="flex gap-3 mt-4">
            <MagneticButton className="btn-primary w-full justify-center" onClick={() => { setShowModal(false); toast.success('Scheduled successfully!') }}>Schedule with AI</MagneticButton>
            <MagneticButton className="btn-ghost w-full justify-center" onClick={() => { setShowModal(false); toast.success('Added manually!') }}>Add Manually</MagneticButton>
          </div>
        </div>
      </GlassModal>
    </div>
  )
}
