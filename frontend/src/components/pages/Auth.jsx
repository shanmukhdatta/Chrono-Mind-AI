import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Clock, Eye, EyeOff, ArrowRight } from 'lucide-react'
import { useAuthStore } from '../../store'
import { GlassCard, MagneticButton, Spinner } from '../ui'
import api from '../../api'
import toast from 'react-hot-toast'

function AuthCard({ title, subtitle, children }) {
  return (
    <div className="min-h-screen flex items-center justify-center px-4 pt-20">
      <motion.div
        className="w-full max-w-md"
        initial={{ opacity: 0, y: 40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
      >
        {/* Logo */}
        <div className="flex items-center justify-center gap-3 mb-8">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center"
            style={{ background: 'linear-gradient(135deg, #F4A261, #E76F51)' }}>
            <Clock size={20} color="white" />
          </div>
          <span className="text-xl font-bold" style={{ fontFamily: 'Inter', color: 'var(--text-1)' }}>
            Chrono<span className="text-gradient-peach">Mind AI</span>
          </span>
        </div>

        <GlassCard className="p-8">
          <h1 className="text-2xl font-bold mb-1 text-center" style={{ fontFamily: 'Inter', color: 'var(--text-1)' }}>
            {title}
          </h1>
          <p className="text-sm text-center mb-7" style={{ color: 'var(--text-2)' }}>{subtitle}</p>
          {children}
        </GlassCard>
      </motion.div>
    </div>
  )
}

function InputField({ label, type = 'text', value, onChange, placeholder, rightEl }) {
  const [show, setShow] = useState(false)
  const isPassword = type === 'password'
  return (
    <div>
      <label className="text-xs font-medium block mb-1.5" style={{ color: 'var(--text-2)' }}>{label}</label>
      <div className="relative">
        <input
          className="glass-input pr-10"
          type={isPassword && show ? 'text' : type}
          value={value}
          onChange={onChange}
          placeholder={placeholder}
        />
        {isPassword && (
          <button
            type="button"
            className="absolute right-3 top-1/2 -translate-y-1/2 opacity-50 hover:opacity-100 transition-opacity"
            onClick={() => setShow((s) => !s)}
          >
            {show ? <EyeOff size={15} /> : <Eye size={15} />}
          </button>
        )}
      </div>
    </div>
  )
}

// ─── Login ────────────────────────────────────────────────────────
export function Login() {
  const [form, setForm] = useState({ email: '', password: '' })
  const [loading, setLoading] = useState(false)
  const { setAuth } = useAuthStore()
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      const { data } = await api.post('/auth/login', form)
      setAuth(data.user, data.access_token)
      toast.success(`Welcome back, ${data.user.name.split(' ')[0]}!`)
      navigate('/dashboard')
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  const handleDemo = async () => {
    setLoading(true)
    try {
      const { data } = await api.post('/auth/demo')
      setAuth(data.user, data.access_token)
      toast.success('Welcome to the demo!')
      navigate('/dashboard')
    } catch {
      toast.success('UI Showcase Mode (Backend is currently installing)')
      setAuth({ name: 'Demo User', email: 'demo@chronomind.ai', id: 1 }, 'mock-token-123')
      navigate('/dashboard')
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthCard title="Welcome back" subtitle="Sign in to your ChronoMind account">
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <InputField label="Email" type="email" value={form.email}
          onChange={(e) => setForm((p) => ({ ...p, email: e.target.value }))}
          placeholder="you@college.edu" />
        <InputField label="Password" type="password" value={form.password}
          onChange={(e) => setForm((p) => ({ ...p, password: e.target.value }))}
          placeholder="••••••••" />

        <MagneticButton type="submit" className="btn-primary w-full flex items-center justify-center gap-2 mt-2" disabled={loading}>
          {loading ? <Spinner size={18} color="white" /> : <><span>Sign in</span><ArrowRight size={15} /></>}
        </MagneticButton>

        <div className="relative flex items-center gap-3 my-1">
          <div className="flex-1 h-px" style={{ background: 'rgba(244,162,97,0.2)' }} />
          <span className="text-xs" style={{ color: 'var(--text-3)' }}>or</span>
          <div className="flex-1 h-px" style={{ background: 'rgba(244,162,97,0.2)' }} />
        </div>

        <MagneticButton type="button" className="btn-ghost w-full flex items-center justify-center gap-2" onClick={handleDemo} disabled={loading}>
          🚀 Try Demo Account
        </MagneticButton>

        <p className="text-sm text-center" style={{ color: 'var(--text-3)' }}>
          Don't have an account?{' '}
          <Link to="/register" className="font-medium" style={{ color: 'var(--deep-peach)' }}>
            Sign up free
          </Link>
        </p>
      </form>
    </AuthCard>
  )
}

// ─── Register ─────────────────────────────────────────────────────
export function Register() {
  const [form, setForm] = useState({ name: '', email: '', password: '' })
  const [loading, setLoading] = useState(false)
  const { setAuth } = useAuthStore()
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (form.password.length < 6) { toast.error('Password must be at least 6 characters'); return }
    setLoading(true)
    try {
      const { data } = await api.post('/auth/register', form)
      setAuth(data.user, data.access_token)
      toast.success(`Account created! Welcome, ${data.user.name.split(' ')[0]} 🎉`)
      navigate('/onboarding')
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthCard title="Get started free" subtitle="Create your ChronoMind account in seconds">
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <InputField label="Full Name" value={form.name}
          onChange={(e) => setForm((p) => ({ ...p, name: e.target.value }))}
          placeholder="Rohan Kumar" />
        <InputField label="Email" type="email" value={form.email}
          onChange={(e) => setForm((p) => ({ ...p, email: e.target.value }))}
          placeholder="you@college.edu" />
        <InputField label="Password" type="password" value={form.password}
          onChange={(e) => setForm((p) => ({ ...p, password: e.target.value }))}
          placeholder="Min. 6 characters" />

        <MagneticButton type="submit" className="btn-primary w-full flex items-center justify-center gap-2 mt-2" disabled={loading}>
          {loading ? <Spinner size={18} color="white" /> : <><span>Create Account</span><ArrowRight size={15} /></>}
        </MagneticButton>

        <p className="text-xs text-center" style={{ color: 'var(--text-3)' }}>
          By signing up, you agree to our Terms & Privacy Policy
        </p>

        <p className="text-sm text-center" style={{ color: 'var(--text-3)' }}>
          Already have an account?{' '}
          <Link to="/login" className="font-medium" style={{ color: 'var(--deep-peach)' }}>
            Sign in
          </Link>
        </p>
      </form>
    </AuthCard>
  )
}
