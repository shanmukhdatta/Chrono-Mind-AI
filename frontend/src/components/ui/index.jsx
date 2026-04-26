import { motion, useMotionValue, useSpring, useTransform, AnimatePresence } from 'framer-motion'
import { useRef, useState } from 'react'
import { X, ChevronDown, Check } from 'lucide-react'

// ─── Scroll reveal wrapper ─────────────────────────────────────────
export function RevealOnScroll({ children, delay = 0, className = '' }) {
  return (
    <motion.div
      className={className}
      initial={{ opacity: 0, y: 40 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: '-80px' }}
      transition={{ duration: 0.7, delay, ease: [0.22, 1, 0.36, 1] }}
    >
      {children}
    </motion.div>
  )
}

// ─── Glass Card with 3D tilt ──────────────────────────────────────
export function GlassCard({ children, className = '', onClick, style = {} }) {
  const ref = useRef(null)
  const rotateX = useMotionValue(0)
  const rotateY = useMotionValue(0)
  const rxSpring = useSpring(rotateX, { stiffness: 200, damping: 20 })
  const rySpring = useSpring(rotateY, { stiffness: 200, damping: 20 })

  const handleMouseMove = (e) => {
    const rect = ref.current?.getBoundingClientRect()
    if (!rect) return
    const cx = rect.left + rect.width / 2
    const cy = rect.top + rect.height / 2
    const dx = (e.clientX - cx) / (rect.width / 2)
    const dy = (e.clientY - cy) / (rect.height / 2)
    rotateX.set(-dy * 8)
    rotateY.set(dx * 8)
  }

  const handleMouseLeave = () => {
    rotateX.set(0)
    rotateY.set(0)
  }

  return (
    <motion.div
      ref={ref}
      className={`glass ${className}`}
      style={{ rotateX: rxSpring, rotateY: rySpring, transformPerspective: 1000, ...style }}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      onClick={onClick}
      whileHover={{ y: -2 }}
    >
      {children}
    </motion.div>
  )
}

// ─── Magnetic Button ──────────────────────────────────────────────
export function MagneticButton({ children, className = '', onClick, type = 'button', disabled = false }) {
  const ref = useRef(null)
  const x = useMotionValue(0)
  const y = useMotionValue(0)
  const xSpring = useSpring(x, { stiffness: 200, damping: 20 })
  const ySpring = useSpring(y, { stiffness: 200, damping: 20 })

  const handleMouseMove = (e) => {
    const rect = ref.current?.getBoundingClientRect()
    if (!rect) return
    const cx = rect.left + rect.width / 2
    const cy = rect.top + rect.height / 2
    x.set((e.clientX - cx) * 0.3)
    y.set((e.clientY - cy) * 0.3)
  }

  const handleMouseLeave = () => { x.set(0); y.set(0) }

  return (
    <motion.button
      ref={ref}
      type={type}
      className={className}
      style={{ x: xSpring, y: ySpring }}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      onClick={onClick}
      whileHover={{ scale: 1.04 }}
      whileTap={{ scale: 0.96 }}
      disabled={disabled}
    >
      {children}
    </motion.button>
  )
}

// ─── Word-by-word text reveal ─────────────────────────────────────
export function WordReveal({ text, className = '', delay = 0 }) {
  const words = text.split(' ')
  return (
    <span className={className} aria-label={text}>
      {words.map((word, i) => (
        <motion.span
          key={i}
          className="inline-block"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5, delay: delay + i * 0.07, ease: [0.22, 1, 0.36, 1] }}
          style={{ marginRight: '0.28em' }}
        >
          {word}
        </motion.span>
      ))}
    </span>
  )
}

// ─── Animated counter ─────────────────────────────────────────────
export function CountUp({ to, suffix = '', className = '', duration = 1.5 }) {
  const [value, setValue] = useState(0)
  const [started, setStarted] = useState(false)

  return (
    <motion.span
      className={className}
      onViewportEnter={() => {
        if (started) return
        setStarted(true)
        let start = 0
        const step = to / (duration * 60)
        const timer = setInterval(() => {
          start = Math.min(start + step, to)
          setValue(Math.round(start))
          if (start >= to) clearInterval(timer)
        }, 1000 / 60)
      }}
    >
      {value}{suffix}
    </motion.span>
  )
}

// ─── Stat Card ────────────────────────────────────────────────────
export function StatCard({ icon: Icon, label, value, suffix = '', color = '#F4A261', delay = 0 }) {
  return (
    <RevealOnScroll delay={delay}>
      <GlassCard className="p-6">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center"
            style={{ background: `${color}22` }}>
            <Icon size={20} style={{ color }} />
          </div>
          <span className="text-sm font-medium" style={{ color: 'var(--text-2)' }}>{label}</span>
        </div>
        <div className="text-3xl font-bold" style={{ fontFamily: 'Inter', color: 'var(--text-1)' }}>
          <CountUp to={typeof value === 'number' ? value : 0} suffix={suffix} />
          {typeof value === 'string' ? value : ''}
        </div>
      </GlassCard>
    </RevealOnScroll>
  )
}

// ─── Glass Badge / Pill ───────────────────────────────────────────
export function GlassBadge({ children, color = '#F4A261' }) {
  return (
    <span
      className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold"
      style={{
        background: `${color}22`,
        color,
        border: `1px solid ${color}44`,
      }}
    >
      {children}
    </span>
  )
}

// ─── Skeleton loader ──────────────────────────────────────────────
export function SkeletonBlock({ className = '' }) {
  return (
    <div className={`relative overflow-hidden rounded-xl ${className}`}
      style={{ background: 'rgba(255,255,255,0.2)' }}>
      <div className="absolute inset-0 shimmer" />
    </div>
  )
}

// ─── Loading Spinner ──────────────────────────────────────────────
export function Spinner({ size = 24, color = 'var(--peach)' }) {
  return (
    <motion.div
      style={{
        width: size, height: size,
        border: `2px solid ${color}33`,
        borderTopColor: color,
        borderRadius: '50%',
      }}
      animate={{ rotate: 360 }}
      transition={{ duration: 0.8, repeat: Infinity, ease: 'linear' }}
    />
  )
}

// ─── Toggle Switch ─────────────────────────────────────────────────
export function Toggle({ checked, onChange, label }) {
  return (
    <label className="flex items-center gap-3 cursor-none select-none">
      <motion.div
        className="relative"
        style={{ width: 50, height: 28 }}
        onClick={() => onChange(!checked)}
        whileTap={{ scale: 0.96 }}
      >
        <motion.div
          className="absolute inset-0 rounded-full"
          animate={{ background: checked ? 'linear-gradient(135deg, #F4A261, #E76F51)' : 'rgba(255,255,255,0.25)' }}
          transition={{ duration: 0.3 }}
          style={{ border: '1px solid rgba(255,255,255,0.4)', backdropFilter: 'blur(8px)' }}
        />
        <motion.div
          className="absolute top-1"
          style={{
            width: 20, height: 20,
            background: 'white',
            borderRadius: '50%',
            boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
            left: 4,
          }}
          animate={{ x: checked ? 22 : 0 }}
          transition={{ type: 'spring', stiffness: 500, damping: 35 }}
        />
      </motion.div>
      {label && <span className="text-sm font-medium" style={{ color: 'var(--text-2)' }}>{label}</span>}
    </label>
  )
}

// ─── Category color map ───────────────────────────────────────────
export const CATEGORY_COLORS = {
  study: '#2A9D8F',
  assignment: '#E76F51',
  project: '#E9C46A',
  personal: '#F4A261',
  health: '#52B788',
  exercise: '#52B788',
  reading: '#8B5CF6',
  other: '#8B8FA8',
}

export const CATEGORY_LABELS = {
  study: 'Study',
  assignment: 'Assignment',
  project: 'Project',
  personal: 'Personal',
  health: 'Health',
  exercise: 'Exercise',
  reading: 'Reading',
  other: 'Other',
}

// ─── Glass Modal ──────────────────────────────────────────────────
export function GlassModal({ isOpen, onClose, children, title }) {
  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            className="fixed inset-0 z-[100]"
            style={{ background: 'rgba(10,10,20,0.35)', backdropFilter: 'blur(10px)' }}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3 }}
            onClick={onClose}
          />
          {/* Panel */}
          <motion.div
            className="fixed inset-0 z-[101] flex items-center justify-center p-4"
            initial={{ opacity: 0, scale: 0.94, y: 40 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.94, y: 20 }}
            transition={{ type: 'spring', stiffness: 350, damping: 30 }}
          >
            <div className="glass w-full max-w-lg p-8 relative" style={{ borderRadius: 28 }}>
              <motion.button
                className="absolute top-5 right-5 w-8 h-8 glass rounded-full flex items-center justify-center"
                whileHover={{ rotate: 90, background: 'rgba(231,111,81,0.15)' }}
                onClick={onClose}
              >
                <X size={14} style={{ color: 'var(--text-2)' }} />
              </motion.button>
              {title && <h3 className="text-lg font-bold mb-5" style={{ fontFamily: 'Inter' }}>{title}</h3>}
              {children}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}

// ─── Glass Select Dropdown ────────────────────────────────────────
export function GlassSelect({ options, value, onChange, placeholder }) {
  const [open, setOpen] = useState(false)
  return (
    <div className="relative">
      <motion.button
        className="glass w-full px-4 py-3 rounded-2xl flex items-center justify-between text-sm"
        style={{ color: 'var(--text-1)' }}
        onClick={() => setOpen(!open)}
        whileTap={{ scale: 0.99 }}
      >
        <span>{options.find(o => o.value === value)?.label || placeholder}</span>
        <motion.div animate={{ rotate: open ? 180 : 0 }} transition={{ duration: 0.2 }}>
          <ChevronDown size={16} style={{ color: 'var(--text-3)' }} />
        </motion.div>
      </motion.button>
      <AnimatePresence>
        {open && (
          <motion.div
            className="absolute top-full mt-2 left-0 right-0 glass z-50 overflow-hidden"
            style={{ borderRadius: 16 }}
            initial={{ scaleY: 0.8, opacity: 0, transformOrigin: 'top center' }}
            animate={{ scaleY: 1, opacity: 1 }}
            exit={{ scaleY: 0.8, opacity: 0 }}
            transition={{ duration: 0.25, ease: [0.22,1,0.36,1] }}
          >
            {options.map(opt => (
              <motion.button
                key={opt.value}
                className="w-full px-4 py-3 text-sm text-left flex items-center justify-between"
                style={{
                  color: value === opt.value ? 'var(--teal)' : 'var(--text-1)',
                  borderLeft: value === opt.value ? '3px solid var(--peach)' : '3px solid transparent',
                }}
                whileHover={{ background: 'rgba(244,162,97,0.08)' }}
                onClick={() => { onChange(opt.value); setOpen(false) }}
              >
                {opt.label}
                {value === opt.value && (
                  <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }}>
                    <Check size={14} style={{ color: 'var(--teal)' }} />
                  </motion.div>
                )}
              </motion.button>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
