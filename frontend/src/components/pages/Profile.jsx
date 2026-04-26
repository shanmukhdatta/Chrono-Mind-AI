import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { User, Bell, Clock, Brain, Moon, Sun, Save, Camera } from 'lucide-react'
import { useAuthStore } from '../../store'
import { GlassCard, RevealOnScroll, MagneticButton, Toggle } from '../ui'
import api from '../../api'
import toast from 'react-hot-toast'

function SegmentedControl({ options, value, onChange }) {
  return (
    <div className="relative flex glass rounded-2xl p-1" style={{ width: 'fit-content' }}>
      {options.map((opt) => (
        <button
          key={opt.value}
          className="relative px-5 py-2 text-sm font-medium rounded-xl z-10 transition-colors"
          style={{ color: value === opt.value ? 'white' : 'var(--text-2)' }}
          onClick={() => onChange(opt.value)}
        >
          {value === opt.value && (
            <motion.div
              layoutId="segment-highlight"
              className="absolute inset-0 rounded-xl"
              style={{ background: 'linear-gradient(135deg, #F4A261, #E76F51)', zIndex: -1 }}
              transition={{ type: 'spring', stiffness: 300, damping: 30 }}
            />
          )}
          {opt.icon && <opt.icon size={13} className="inline mr-1.5 mb-0.5" />}
          {opt.label}
        </button>
      ))}
    </div>
  )
}

export default function Profile() {
  const { user, updateUser } = useAuthStore()
  const [form, setForm] = useState({
    name: user?.name || '',
    institution: user?.institution || '',
    year: user?.year || '',
    chronotype: user?.chronotype || 'flexible',
    break_style: user?.break_style || 'pomodoro',
    default_study_duration: user?.default_study_duration || 90,
    preferred_start_hour: user?.preferred_start_hour || 8,
    preferred_end_hour: user?.preferred_end_hour || 22,
  })
  const [saving, setSaving] = useState(false)
  const [notifications, setNotifications] = useState(true)

  const handleSave = async () => {
    setSaving(true)
    try {
      const { data } = await api.patch('/users/me', form)
      updateUser(data)
      toast.success('Profile saved!')
    } catch (e) {
      toast.error('Failed to save profile')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="min-h-screen p-6 md:p-8">
      {/* Header */}
      <RevealOnScroll className="mb-8">
        <h1 className="text-3xl font-bold mb-1" style={{ fontFamily: 'Inter', color: 'var(--text-1)' }}>
          Profile & Settings
        </h1>
        <p style={{ color: 'var(--text-2)' }}>Customize your ChronoMind experience</p>
      </RevealOnScroll>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Avatar Card */}
        <RevealOnScroll>
          <GlassCard className="p-6 text-center">
            <div className="relative w-24 h-24 mx-auto mb-4 flex items-center justify-center">
              <motion.div 
                className="absolute -inset-1.5 rounded-full"
                style={{ background: 'conic-gradient(from 0deg, transparent, #F4A261, #E76F51, transparent)' }}
                animate={{ rotate: 360 }}
                transition={{ repeat: Infinity, duration: 4, ease: 'linear' }}
              />
              <div className="relative w-[92%] h-[92%] rounded-full overflow-hidden bg-[#0A0A10] z-10 p-[1px]">
                <div className="w-full h-full rounded-full overflow-hidden bg-[#0A0A10]">
                {user?.avatar_url ? (
                  <img src={user.avatar_url} className="w-full h-full object-cover" alt="" />
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-3xl font-bold text-white"
                    style={{ background: 'linear-gradient(135deg, #F4A261, #E76F51)' }}>
                    {user?.name?.[0]}
                  </div>
                )}
              </div>
              </div>
              <motion.button
                className="absolute bottom-0 right-0 w-8 h-8 rounded-full glass flex items-center justify-center"
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.9 }}
              >
                <Camera size={13} style={{ color: 'var(--text-2)' }} />
              </motion.button>
            </div>

            <h2 className="text-xl font-bold mb-1" style={{ fontFamily: 'Inter', color: 'var(--text-1)' }}>
              {user?.name}
            </h2>
            <p className="text-sm" style={{ color: 'var(--text-2)' }}>{user?.email}</p>
            {user?.institution && (
              <p className="text-xs mt-1" style={{ color: 'var(--text-3)' }}>
                {user.year} · {user.institution}
              </p>
            )}

            <div className="mt-4 pt-4 border-t" style={{ borderColor: 'rgba(244,162,97,0.12)' }}>
              <div className="flex justify-around">
                {[
                  { label: 'Tasks Done', value: '23' },
                  { label: 'Streak', value: '3d' },
                  { label: 'AI Scheduled', value: '18' },
                ].map((stat) => (
                  <div key={stat.label} className="text-center">
                    <p className="text-lg font-bold" style={{ fontFamily: 'Inter', color: 'var(--text-1)' }}>{stat.value}</p>
                    <p className="text-xs" style={{ color: 'var(--text-3)' }}>{stat.label}</p>
                  </div>
                ))}
              </div>
            </div>
          </GlassCard>
        </RevealOnScroll>

        {/* Settings */}
        <div className="lg:col-span-2 flex flex-col gap-5">
          {/* Basic Info */}
          <RevealOnScroll delay={0.1}>
            <GlassCard className="p-5">
              <div className="flex items-center gap-2 mb-4">
                <User size={16} style={{ color: 'var(--peach)' }} />
                <h3 className="font-semibold" style={{ fontFamily: 'Inter', color: 'var(--text-1)' }}>
                  Basic Info
                </h3>
              </div>
              <div className="grid grid-cols-2 gap-3">
                {[
                  { key: 'name', label: 'Full Name', placeholder: 'Your name' },
                  { key: 'institution', label: 'Institution', placeholder: 'IIT Delhi' },
                  { key: 'year', label: 'Year', placeholder: '2nd Year B.Tech' },
                ].map((field) => (
                  <div key={field.key} className={field.key === 'name' ? 'col-span-2' : ''}>
                    <label className="text-xs mb-1 block" style={{ color: 'var(--text-3)' }}>{field.label}</label>
                    <input
                      className="glass-input"
                      placeholder={field.placeholder}
                      value={form[field.key]}
                      onChange={(e) => setForm((p) => ({ ...p, [field.key]: e.target.value }))}
                    />
                  </div>
                ))}
              </div>
            </GlassCard>
          </RevealOnScroll>

          {/* Scheduling Preferences */}
          <RevealOnScroll delay={0.15}>
            <GlassCard className="p-5">
              <div className="flex items-center gap-2 mb-5">
                <Brain size={16} style={{ color: 'var(--teal)' }} />
                <h3 className="font-semibold" style={{ fontFamily: 'Inter', color: 'var(--text-1)' }}>
                  AI Scheduling Preferences
                </h3>
              </div>

              <div className="space-y-5">
                <div>
                  <label className="text-sm font-medium mb-2 block" style={{ color: 'var(--text-2)' }}>
                    Chronotype
                  </label>
                  <SegmentedControl
                    options={[
                      { value: 'morning', label: 'Morning', icon: Sun },
                      { value: 'flexible', label: 'Flexible', icon: Clock },
                      { value: 'night', label: 'Night', icon: Moon },
                    ]}
                    value={form.chronotype}
                    onChange={(v) => setForm((p) => ({ ...p, chronotype: v }))}
                  />
                </div>

                <div>
                  <label className="text-sm font-medium mb-2 block" style={{ color: 'var(--text-2)' }}>
                    Break Style
                  </label>
                  <SegmentedControl
                    options={[
                      { value: 'pomodoro', label: 'Pomodoro (25/5)' },
                      { value: 'long', label: 'Long (50/10)' },
                    ]}
                    value={form.break_style}
                    onChange={(v) => setForm((p) => ({ ...p, break_style: v }))}
                  />
                </div>

                <div className="grid grid-cols-3 gap-4">
                  {[
                    { key: 'default_study_duration', label: 'Study session (min)', min: 15, max: 240, step: 15 },
                    { key: 'preferred_start_hour', label: 'Day starts at (hr)', min: 4, max: 12 },
                    { key: 'preferred_end_hour', label: 'Day ends at (hr)', min: 16, max: 24 },
                  ].map((f) => (
                    <div key={f.key}>
                      <label className="text-xs mb-1 block" style={{ color: 'var(--text-3)' }}>{f.label}</label>
                      <input
                        type="number" className="glass-input"
                        value={form[f.key]} min={f.min} max={f.max} step={f.step || 1}
                        onChange={(e) => setForm((p) => ({ ...p, [f.key]: Number(e.target.value) }))}
                      />
                    </div>
                  ))}
                </div>
              </div>
            </GlassCard>
          </RevealOnScroll>

          {/* Notifications */}
          <RevealOnScroll delay={0.2}>
            <GlassCard className="p-5">
              <div className="flex items-center gap-2 mb-4">
                <Bell size={16} style={{ color: 'var(--gold)' }} />
                <h3 className="font-semibold" style={{ fontFamily: 'Inter', color: 'var(--text-1)' }}>
                  Notifications
                </h3>
              </div>
              <div className="space-y-3">
                <div className="flex items-center justify-between py-2">
                  <span className="text-sm" style={{ color: 'var(--text-1)' }}>Task reminders</span>
                  <Toggle checked={notifications} onChange={setNotifications} />
                </div>
                <div className="flex items-center justify-between py-2"
                  style={{ borderTop: '1px solid rgba(244,162,97,0.08)' }}>
                  <span className="text-sm" style={{ color: 'var(--text-1)' }}>AI scheduling suggestions</span>
                  <Toggle checked={true} onChange={() => {}} />
                </div>
                <div className="flex items-center justify-between py-2"
                  style={{ borderTop: '1px solid rgba(244,162,97,0.08)' }}>
                  <span className="text-sm" style={{ color: 'var(--text-1)' }}>Deadline warnings</span>
                  <Toggle checked={true} onChange={() => {}} />
                </div>
              </div>
            </GlassCard>
          </RevealOnScroll>

          {/* Save */}
          <RevealOnScroll delay={0.25}>
            <MagneticButton
              className="btn-primary w-full flex items-center justify-center gap-2"
              onClick={handleSave}
              disabled={saving}
            >
              <Save size={16} />
              {saving ? 'Saving...' : 'Save All Changes'}
            </MagneticButton>
          </RevealOnScroll>
        </div>
      </div>
    </div>
  )
}
