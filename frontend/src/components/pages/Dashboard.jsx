import { useEffect } from 'react'
import { motion } from 'framer-motion'
import {
  CheckCircle2, Zap, Target, Flame, Calendar, Clock,
  TrendingUp, BookOpen, Plus
} from 'lucide-react'
import { format } from 'date-fns'
import { useNavigate } from 'react-router-dom'
import { useDashboardStore, useTaskStore, useAuthStore } from '../../store'
import { GlassCard, RevealOnScroll, CountUp, GlassBadge, CATEGORY_COLORS, MagneticButton } from '../ui'

function ProgressRing({ percent = 0, size = 90, stroke = 7 }) {
  const r = (size - stroke * 2) / 2
  const circ = 2 * Math.PI * r
  const offset = circ - (percent / 100) * circ
  return (
    <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
      <circle cx={size / 2} cy={size / 2} r={r} fill="none"
        stroke="rgba(244,162,97,0.15)" strokeWidth={stroke} />
      <motion.circle
        cx={size / 2} cy={size / 2} r={r} fill="none"
        stroke="url(#peach-grad)" strokeWidth={stroke}
        strokeLinecap="round"
        strokeDasharray={circ}
        initial={{ strokeDashoffset: circ }}
        animate={{ strokeDashoffset: offset }}
        transition={{ duration: 1.5, ease: [0.22, 1, 0.36, 1], delay: 0.4 }}
      />
      <defs>
        <linearGradient id="peach-grad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#F4A261" />
          <stop offset="100%" stopColor="#E76F51" />
        </linearGradient>
      </defs>
    </svg>
  )
}

function TaskRow({ task, onComplete, index = 0 }) {
  const color = CATEGORY_COLORS[task.category] || '#F4A261'
  const isCompleted = task.status === 'completed'
  return (
    <motion.div
      className="flex items-center gap-3 py-3 relative z-10"
      style={{ borderBottom: '1px solid rgba(244,162,97,0.08)' }}
      layout
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 20, height: 0 }}
      transition={{ delay: index * 0.1 }}
    >
      <motion.button
        className="w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0 z-10 relative bg-[#0a0a14]"
        style={{
          border: isCompleted ? 'none' : `2px solid ${color}66`,
          background: isCompleted ? color : '#0a0a14',
        }}
        whileTap={{ scale: 0.8 }}
        onClick={() => !isCompleted && onComplete(task.id)}
      >
        {isCompleted && <CheckCircle2 size={13} color="white" />}
      </motion.button>

      <div className="flex-1 min-w-0">
        <p className={`text-sm font-medium truncate ${isCompleted ? 'line-through opacity-50' : ''}`}
          style={{ color: 'var(--text-1)' }}>
          {task.title}
        </p>
        {task.start_time && (
          <p className="text-xs mt-0.5" style={{ color: 'var(--text-3)' }}>
            {task.start_time} – {task.end_time}
          </p>
        )}
      </div>

      <GlassBadge color={color}>{task.category}</GlassBadge>
      {task.ai_placed && (
        <span className="text-xs px-2 py-0.5 rounded-full" style={{ background: 'rgba(42,157,143,0.12)', color: '#2A9D8F' }}>
          AI
        </span>
      )}
    </motion.div>
  )
}

export default function Dashboard() {
  const { stats, fetchStats } = useDashboardStore()
  const { tasks, fetchTasks, completeTask } = useTaskStore()
  const { user } = useAuthStore()
  const navigate = useNavigate()
  const today = format(new Date(), 'yyyy-MM-dd')
  const todayDisplay = format(new Date(), 'EEEE, MMMM d')

  useEffect(() => {
    fetchStats()
    fetchTasks(today)
  }, [])

  const todayTasks = tasks.filter((t) => t.scheduled_date === today)
  const completedToday = todayTasks.filter((t) => t.status === 'completed').length
  const completionPct = todayTasks.length > 0 ? Math.round((completedToday / todayTasks.length) * 100) : 0

  const STAT_CARDS = [
    { icon: Zap, label: 'Slots Found This Week', value: stats?.slots_found_this_week ?? 0, color: '#F4A261' },
    { icon: Target, label: 'AI Scheduled Tasks', value: stats?.tasks_ai_scheduled ?? 0, color: '#2A9D8F' },
    { icon: TrendingUp, label: 'Completion Rate', value: stats?.completion_rate ?? 0, suffix: '%', color: '#E9C46A' },
    { icon: Flame, label: 'Day Streak', value: stats?.streak_days ?? 0, suffix: ' days', color: '#E76F51' },
  ]

  return (
    <div className="min-h-screen p-6 md:p-8">
      {/* Header */}
      <RevealOnScroll>
        <div className="mb-8 flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-bold mb-1" style={{ fontFamily: 'Inter', color: 'var(--text-1)' }}>
              Good {new Date().getHours() < 12 ? 'morning' : new Date().getHours() < 18 ? 'afternoon' : 'evening'},{' '}
              <span className="text-gradient-peach">{user?.name?.split(' ')[0]} 👋</span>
            </h1>
            <p style={{ color: 'var(--text-2)' }}>{todayDisplay} · Let's make today count.</p>
          </div>
          <MagneticButton
            className="btn-primary flex items-center gap-2"
            onClick={() => navigate('/assistant')}
          >
            <Plus size={16} /> Add Task
          </MagneticButton>
        </div>
      </RevealOnScroll>

      {/* Stats Row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {STAT_CARDS.map((card, i) => (
          <RevealOnScroll key={card.label} delay={i * 0.08}>
            <GlassCard className="p-5">
              <div className="flex items-center gap-3 mb-3">
                <div className="w-9 h-9 rounded-xl flex items-center justify-center"
                  style={{ background: `${card.color}22` }}>
                  <card.icon size={18} style={{ color: card.color }} />
                </div>
                <span className="text-xs font-medium leading-tight" style={{ color: 'var(--text-2)' }}>{card.label}</span>
              </div>
              <div className="text-2xl font-bold" style={{ fontFamily: 'Inter' }}>
                <CountUp to={card.value} suffix={card.suffix || ''} />
              </div>
            </GlassCard>
          </RevealOnScroll>
        ))}
      </div>

      {/* Main Grid */}
      <div className="grid lg:grid-cols-3 gap-6">
        {/* Today's Tasks */}
        <RevealOnScroll className="lg:col-span-2">
          <GlassCard className="p-6">
            <div className="flex items-center justify-between mb-5">
              <div>
                <h2 className="text-lg font-bold" style={{ fontFamily: 'Inter', color: 'var(--text-1)' }}>
                  Today's Tasks
                </h2>
                <p className="text-sm" style={{ color: 'var(--text-2)' }}>
                  {completedToday}/{todayTasks.length} completed
                </p>
              </div>
              <button
                className="text-sm font-medium"
                style={{ color: 'var(--deep-peach)' }}
                onClick={() => navigate('/calendar')}
              >
                View calendar →
              </button>
            </div>

            {todayTasks.length === 0 ? (
              <motion.div
                className="text-center py-12"
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.5 }}
              >
                <Calendar size={40} style={{ color: 'var(--text-3)', margin: '0 auto 12px' }} />
                <p style={{ color: 'var(--text-2)' }}>No tasks scheduled today</p>
                <p className="text-sm mt-1" style={{ color: 'var(--text-3)' }}>
                  Ask the AI assistant to plan your day
                </p>
                <MagneticButton
                  className="btn-primary mt-4 text-sm"
                  onClick={() => navigate('/assistant')}
                >
                  Plan with AI ✨
                </MagneticButton>
              </motion.div>
            ) : (
              <div className="relative">
                <div className="absolute top-4 bottom-4 w-[1.5px] rounded-full z-0" style={{ left: '9.5px', background: 'linear-gradient(to bottom, rgba(244,162,97,0.6), transparent)' }} />
                {todayTasks.map((task, i) => (
                  <TaskRow key={task.id} task={task} index={i} onComplete={completeTask} />
                ))}
              </div>
            )}
          </GlassCard>
        </RevealOnScroll>

        {/* Completion Ring + Quick Stats */}
        <div className="flex flex-col gap-5">
          <RevealOnScroll delay={0.1}>
            <GlassCard className="p-6 text-center">
              <h3 className="text-base font-semibold mb-4" style={{ fontFamily: 'Inter', color: 'var(--text-1)' }}>
                Today's Progress
              </h3>
              <div className="relative inline-block">
                <ProgressRing percent={completionPct} size={110} stroke={8} />
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <span className="text-2xl font-bold" style={{ fontFamily: 'Inter', color: 'var(--text-1)' }}>
                    {completionPct}%
                  </span>
                  <span className="text-xs" style={{ color: 'var(--text-3)' }}>done</span>
                </div>
              </div>
              <p className="text-sm mt-3" style={{ color: 'var(--text-2)' }}>
                {completedToday} of {todayTasks.length} tasks
              </p>
            </GlassCard>
          </RevealOnScroll>

          <RevealOnScroll delay={0.2}>
            <GlassCard className="p-5">
              <div className="flex items-center gap-2 mb-3">
                <Clock size={16} style={{ color: 'var(--peach)' }} />
                <h3 className="text-sm font-semibold" style={{ fontFamily: 'Inter', color: 'var(--text-1)' }}>
                  Quick Actions
                </h3>
              </div>
              <div className="flex flex-col gap-2">
                {[
                  { label: '📚 Schedule study time', action: () => navigate('/assistant') },
                  { label: '📅 View full calendar', action: () => navigate('/calendar') },
                  { label: '🤖 Ask AI assistant', action: () => navigate('/assistant') },
                ].map((item) => (
                  <motion.button
                    key={item.label}
                    className="text-left text-sm px-3 py-2.5 rounded-xl"
                    style={{
                      background: 'rgba(244,162,97,0.08)',
                      color: 'var(--text-1)',
                      border: '1px solid rgba(244,162,97,0.15)',
                    }}
                    whileHover={{ background: 'rgba(244,162,97,0.15)', x: 3 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={item.action}
                  >
                    {item.label}
                  </motion.button>
                ))}
              </div>
            </GlassCard>
          </RevealOnScroll>
        </div>
      </div>
    </div>
  )
}
