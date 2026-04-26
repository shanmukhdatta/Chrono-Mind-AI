import { useState, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import { Upload, CheckCircle, Settings2, ArrowRight, Edit3, Check, X, Loader } from 'lucide-react'
import { useAuthStore } from '../../store'
import { GlassCard, MagneticButton, Toggle, Spinner } from '../ui'
import api from '../../api'
import toast from 'react-hot-toast'

const STEP_VARIANTS = {
  enter: (dir) => ({ x: dir > 0 ? 80 : -80, opacity: 0 }),
  center: { x: 0, opacity: 1 },
  exit: (dir) => ({ x: dir > 0 ? -80 : 80, opacity: 0 }),
}

function StepDots({ current, total }) {
  return (
    <div className="flex items-center gap-3 justify-center mb-8">
      {Array.from({ length: total }).map((_, i) => (
        <div key={i} className="flex items-center gap-3">
          <motion.div
            className="rounded-full flex items-center justify-center"
            animate={{
              width: i === current ? 32 : 12,
              height: 12,
              background: i < current
                ? '#2A9D8F'
                : i === current
                  ? 'linear-gradient(135deg, #F4A261, #E76F51)'
                  : 'rgba(255,255,255,0.3)',
            }}
            transition={{ type: 'spring', stiffness: 300, damping: 25 }}
          >
            {i < current && <Check size={7} color="white" />}
          </motion.div>
          {i < total - 1 && (
            <motion.div
              className="h-0.5 rounded-full"
              style={{ width: 40 }}
              animate={{ background: i < current ? '#2A9D8F' : 'rgba(244,162,97,0.2)' }}
              transition={{ duration: 0.5 }}
            />
          )}
        </div>
      ))}
    </div>
  )
}

// ─── Step 1: Upload ────────────────────────────────────────────────
function StepUpload({ onNext }) {
  const [dragging, setDragging] = useState(false)
  const [processing, setProcessing] = useState(false)
  const [result, setResult] = useState(null)
  const fileRef = useRef()

  const processFile = async (file) => {
    if (!file) return
    const allowed = ['image/jpeg', 'image/png', 'image/webp', 'application/pdf']
    if (!allowed.includes(file.type)) { toast.error('Please upload an image or PDF'); return }

    setProcessing(true)
    try {
      const formData = new FormData()
      formData.append('file', file)
      const { data } = await api.post('/timetable/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      setResult(data)
      toast.success(`Extracted ${data.entries.length} classes! ✨`)
    } catch {
      toast.error('OCR failed — you can enter manually on the next step')
      // Proceed with empty entries
      setResult({ entries: [], confidence: 0, message: 'Manual entry required' })
    } finally {
      setProcessing(false)
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setDragging(false)
    const file = e.dataTransfer.files[0]
    processFile(file)
  }

  return (
    <div>
      <h2 className="text-2xl font-bold mb-2 text-center" style={{ fontFamily: 'Inter', color: 'var(--text-1)' }}>
        Upload your timetable
      </h2>
      <p className="text-sm text-center mb-6" style={{ color: 'var(--text-2)' }}>
        Drag & drop your class schedule image. Our AI will extract it automatically.
      </p>

      {!result ? (
        <motion.div
          className="relative rounded-2xl border-2 border-dashed p-12 text-center"
          style={{
            borderColor: dragging ? 'var(--peach)' : 'rgba(244,162,97,0.35)',
            background: dragging ? 'rgba(244,162,97,0.08)' : 'rgba(255,255,255,0.08)',
            transition: 'all 0.25s',
          }}
          onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
          onDragLeave={() => setDragging(false)}
          onDrop={handleDrop}
          onClick={() => fileRef.current?.click()}
          whileHover={{ borderColor: 'rgba(244,162,97,0.6)', background: 'rgba(244,162,97,0.06)' }}
        >
          <input ref={fileRef} type="file" accept="image/*,.pdf" className="hidden"
            onChange={(e) => processFile(e.target.files[0])} />

          {processing ? (
            <div className="flex flex-col items-center gap-3">
              <Spinner size={36} />
              <p className="font-medium" style={{ color: 'var(--text-1)' }}>Scanning your timetable…</p>
              <p className="text-sm" style={{ color: 'var(--text-3)' }}>OCR + AI parsing in progress</p>
            </div>
          ) : (
            <>
              <div className="w-14 h-14 rounded-2xl flex items-center justify-center mx-auto mb-4"
                style={{ background: 'rgba(244,162,97,0.15)' }}>
                <Upload size={24} style={{ color: 'var(--peach)' }} />
              </div>
              <p className="font-semibold mb-1" style={{ color: 'var(--text-1)' }}>
                Drop your timetable here
              </p>
              <p className="text-sm" style={{ color: 'var(--text-3)' }}>JPG, PNG, WebP, or PDF · Click to browse</p>
            </>
          )}
        </motion.div>
      ) : (
        <motion.div
          className="rounded-2xl p-5 text-center"
          style={{ background: 'rgba(42,157,143,0.1)', border: '1.5px solid rgba(42,157,143,0.3)' }}
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
        >
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ type: 'spring', stiffness: 300, delay: 0.1 }}
          >
            <CheckCircle size={36} style={{ color: '#2A9D8F', margin: '0 auto 12px' }} />
          </motion.div>
          <p className="font-semibold" style={{ color: 'var(--text-1)' }}>
            {result.entries.length > 0
              ? `Extracted ${result.entries.length} classes (${Math.round(result.confidence * 100)}% confidence)`
              : 'File uploaded — proceed to manual review'}
          </p>
          <p className="text-sm mt-1" style={{ color: '#2A9D8F' }}>{result.message}</p>
        </motion.div>
      )}

      <div className="flex gap-3 mt-6">
        <MagneticButton
          className="btn-ghost flex-1 text-sm"
          onClick={() => onNext([])}
        >
          Skip — enter manually
        </MagneticButton>
        <MagneticButton
          className="btn-primary flex-1 flex items-center justify-center gap-2 text-sm"
          onClick={() => onNext(result?.entries || [])}
          disabled={processing || !result}
        >
          Review & confirm <ArrowRight size={14} />
        </MagneticButton>
      </div>
    </div>
  )
}

// ─── Step 2: Review OCR table ──────────────────────────────────────
function StepReview({ entries, onNext, onBack }) {
  const [rows, setRows] = useState(entries.length > 0 ? entries : [
    { day_of_week: 'Monday', start_time: '09:00', end_time: '10:00', subject: '', location: '' },
  ])
  const [saving, setSaving] = useState(false)

  const updateRow = (i, field, val) =>
    setRows((prev) => prev.map((r, idx) => idx === i ? { ...r, [field]: val } : r))

  const addRow = () =>
    setRows((p) => [...p, { day_of_week: 'Monday', start_time: '09:00', end_time: '10:00', subject: '', location: '' }])

  const removeRow = (i) => setRows((p) => p.filter((_, idx) => idx !== i))

  const handleSave = async () => {
    const valid = rows.filter((r) => r.subject.trim())
    if (valid.length === 0) { toast.error('Add at least one class'); return }
    setSaving(true)
    try {
      await api.post('/timetable/save', valid)
      toast.success(`Saved ${valid.length} classes!`)
      onNext()
    } catch { toast.error('Failed to save timetable') }
    finally { setSaving(false) }
  }

  const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

  return (
    <div>
      <h2 className="text-2xl font-bold mb-2 text-center" style={{ fontFamily: 'Inter', color: 'var(--text-1)' }}>
        Review your timetable
      </h2>
      <p className="text-sm text-center mb-5" style={{ color: 'var(--text-2)' }}>
        Check the extracted schedule and fix any errors before saving.
      </p>

      <div className="max-h-72 overflow-y-auto flex flex-col gap-2 mb-4">
        <AnimatePresence>
          {rows.map((row, i) => (
            <motion.div
              key={i}
              className="glass rounded-xl p-3 grid grid-cols-5 gap-2 items-center"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, x: -20, height: 0 }}
              transition={{ delay: i * 0.03 }}
            >
              <select className="glass-input text-xs col-span-1" value={row.day_of_week}
                onChange={(e) => updateRow(i, 'day_of_week', e.target.value)}>
                {days.map((d) => <option key={d} value={d}>{d.slice(0, 3)}</option>)}
              </select>
              <input className="glass-input text-xs" type="time" value={row.start_time}
                onChange={(e) => updateRow(i, 'start_time', e.target.value)} />
              <input className="glass-input text-xs" type="time" value={row.end_time}
                onChange={(e) => updateRow(i, 'end_time', e.target.value)} />
              <input className="glass-input text-xs" placeholder="Subject" value={row.subject}
                onChange={(e) => updateRow(i, 'subject', e.target.value)} />
              <div className="flex gap-1">
                <input className="glass-input text-xs flex-1" placeholder="Room" value={row.location || ''}
                  onChange={(e) => updateRow(i, 'location', e.target.value)} />
                <motion.button className="w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0"
                  style={{ background: 'rgba(231,111,81,0.12)' }}
                  whileTap={{ scale: 0.8 }} onClick={() => removeRow(i)}>
                  <X size={12} style={{ color: '#E76F51' }} />
                </motion.button>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>

      <motion.button className="w-full py-2.5 rounded-xl text-sm font-medium mb-4 flex items-center justify-center gap-2"
        style={{ background: 'rgba(244,162,97,0.1)', color: 'var(--peach)', border: '1px dashed rgba(244,162,97,0.35)' }}
        whileHover={{ background: 'rgba(244,162,97,0.16)' }} onClick={addRow}>
        <Edit3 size={13} /> Add row
      </motion.button>

      <div className="flex gap-3">
        <MagneticButton className="btn-ghost flex-1 text-sm" onClick={onBack}>Back</MagneticButton>
        <MagneticButton className="btn-primary flex-1 flex items-center justify-center gap-2 text-sm" onClick={handleSave} disabled={saving}>
          {saving ? <Spinner size={16} color="white" /> : <><span>Save timetable</span><ArrowRight size={14} /></>}
        </MagneticButton>
      </div>
    </div>
  )
}

// ─── Step 3: Preferences ──────────────────────────────────────────
function StepPreferences({ onFinish }) {
  const [prefs, setPrefs] = useState({ chronotype: 'flexible', break_style: 'pomodoro', default_study_duration: 90 })
  const [saving, setSaving] = useState(false)
  const { updateUser } = useAuthStore()

  const handleFinish = async () => {
    setSaving(true)
    try {
      const { data } = await api.patch('/users/me', { ...prefs, is_onboarded: true })
      updateUser(data)
      onFinish()
    } catch { toast.error('Failed to save preferences') }
    finally { setSaving(false) }
  }

  const ChronoBtn = ({ val, label, emoji }) => (
    <motion.button
      className="flex-1 py-3 rounded-xl text-sm font-medium"
      style={{
        background: prefs.chronotype === val ? 'linear-gradient(135deg, #F4A261, #E76F51)' : 'rgba(255,255,255,0.15)',
        color: prefs.chronotype === val ? 'white' : 'var(--text-2)',
        border: prefs.chronotype === val ? 'none' : '1px solid rgba(255,255,255,0.3)',
      }}
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.97 }}
      onClick={() => setPrefs((p) => ({ ...p, chronotype: val }))}
    >
      {emoji} {label}
    </motion.button>
  )

  return (
    <div>
      <h2 className="text-2xl font-bold mb-2 text-center" style={{ fontFamily: 'Inter', color: 'var(--text-1)' }}>
        Your preferences
      </h2>
      <p className="text-sm text-center mb-6" style={{ color: 'var(--text-2)' }}>
        Help the AI schedule tasks in the slots you prefer.
      </p>

      <div className="flex flex-col gap-5">
        <div>
          <p className="text-sm font-medium mb-2" style={{ color: 'var(--text-1)' }}>Are you a morning or night person?</p>
          <div className="flex gap-2">
            <ChronoBtn val="morning" label="Morning" emoji="☀️" />
            <ChronoBtn val="flexible" label="Flexible" emoji="🌤️" />
            <ChronoBtn val="night" label="Night" emoji="🌙" />
          </div>
        </div>

        <div>
          <p className="text-sm font-medium mb-2" style={{ color: 'var(--text-1)' }}>Preferred break style</p>
          <div className="flex gap-2">
            {[
              { val: 'pomodoro', label: '🍅 Pomodoro (25/5)' },
              { val: 'long', label: '⏱️ Long (50/10)' },
            ].map(({ val, label }) => (
              <motion.button key={val}
                className="flex-1 py-3 rounded-xl text-sm font-medium"
                style={{
                  background: prefs.break_style === val ? 'linear-gradient(135deg, #2A9D8F, #264653)' : 'rgba(255,255,255,0.15)',
                  color: prefs.break_style === val ? 'white' : 'var(--text-2)',
                  border: prefs.break_style === val ? 'none' : '1px solid rgba(255,255,255,0.3)',
                }}
                whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.97 }}
                onClick={() => setPrefs((p) => ({ ...p, break_style: val }))}>
                {label}
              </motion.button>
            ))}
          </div>
        </div>

        <div>
          <p className="text-sm font-medium mb-2" style={{ color: 'var(--text-1)' }}>
            Default study session: {prefs.default_study_duration} minutes
          </p>
          <input type="range" min={30} max={180} step={15}
            value={prefs.default_study_duration}
            onChange={(e) => setPrefs((p) => ({ ...p, default_study_duration: Number(e.target.value) }))}
            className="w-full"
            style={{ accentColor: 'var(--peach)' }} />
          <div className="flex justify-between text-xs mt-1" style={{ color: 'var(--text-3)' }}>
            <span>30 min</span><span>180 min</span>
          </div>
        </div>
      </div>

      <MagneticButton className="btn-primary w-full flex items-center justify-center gap-2 mt-6" onClick={handleFinish} disabled={saving}>
        {saving ? <Spinner size={16} color="white" /> : <><span>Start Planning! 🚀</span><ArrowRight size={14} /></>}
      </MagneticButton>
    </div>
  )
}

// ─── Wizard ───────────────────────────────────────────────────────
export default function Onboarding() {
  const [step, setStep] = useState(0)
  const [direction, setDirection] = useState(1)
  const [uploadedEntries, setUploadedEntries] = useState([])
  const navigate = useNavigate()

  const goNext = (dir = 1) => { setDirection(dir); setStep((s) => s + 1) }
  const goBack = () => { setDirection(-1); setStep((s) => s - 1) }

  const STEPS = [
    <StepUpload key="upload" onNext={(entries) => { setUploadedEntries(entries); goNext() }} />,
    <StepReview key="review" entries={uploadedEntries} onNext={goNext} onBack={goBack} />,
    <StepPreferences key="preferences" onFinish={() => navigate('/dashboard')} />,
  ]

  return (
    <div className="min-h-screen flex items-center justify-center px-4 pt-20 pb-10">
      <div className="w-full max-w-xl">
        <GlassCard className="p-8">
          <StepDots current={step} total={STEPS.length} />
          <AnimatePresence mode="wait" custom={direction}>
            <motion.div
              key={step}
              custom={direction}
              variants={STEP_VARIANTS}
              initial="enter"
              animate="center"
              exit="exit"
              transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
            >
              {STEPS[step]}
            </motion.div>
          </AnimatePresence>
        </GlassCard>
      </div>
    </div>
  )
}
