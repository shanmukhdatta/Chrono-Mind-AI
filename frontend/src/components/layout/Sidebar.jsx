import { Link, useLocation } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { LayoutDashboard, Calendar, Bot, User, Zap, LogOut, Clock } from 'lucide-react'
import { useAuthStore } from '../../store'
import { useNavigate } from 'react-router-dom'

const NAV = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/calendar', label: 'Calendar', icon: Calendar },
  { to: '/assistant', label: 'AI Assistant', icon: Bot },
  { to: '/profile', label: 'Profile & Settings', icon: User },
]

export default function Sidebar() {
  const location = useLocation()
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()

  return (
    <motion.aside
      className="fixed left-0 top-0 bottom-0 w-64 z-40 hidden md:flex flex-col p-4 gap-2"
      initial={{ x: -260, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
      style={{
        background: 'rgba(255,255,255,0.6)',
        backdropFilter: 'blur(32px) saturate(180%)',
        borderRight: '1px solid rgba(255,255,255,0.55)',
      }}
    >
      {/* Logo */}
      <div className="flex items-center gap-3 px-4 py-5 mb-2">
        <div className="w-9 h-9 rounded-xl flex items-center justify-center"
          style={{ background: 'linear-gradient(135deg, #F4A261, #E76F51)' }}>
          <Clock size={18} color="white" />
        </div>
        <div>
          <div className="font-bold text-base leading-tight" style={{ fontFamily: 'Inter', color: 'var(--text-1)' }}>
            Chrono<span className="text-gradient-peach">Mind</span>
          </div>
          <div className="text-xs" style={{ color: 'var(--text-3)' }}>AI Planner</div>
        </div>
      </div>

      {/* User */}
      <div className="glass rounded-2xl px-4 py-3 mb-4 flex items-center gap-3">
        {user?.avatar_url ? (
          <img src={user.avatar_url} className="w-9 h-9 rounded-full object-cover" alt="" />
        ) : (
          <div className="w-9 h-9 rounded-full flex items-center justify-center text-sm font-bold text-white"
            style={{ background: 'linear-gradient(135deg, #F4A261, #E76F51)' }}>
            {user?.name?.[0] || 'U'}
          </div>
        )}
        <div className="min-w-0">
          <div className="text-sm font-semibold truncate" style={{ color: 'var(--text-1)' }}>{user?.name}</div>
          <div className="text-xs truncate" style={{ color: 'var(--text-3)' }}>{user?.year || '2nd Year B.Tech'}</div>
        </div>
      </div>

      {/* Nav Items */}
      <nav className="flex-1 flex flex-col gap-1">
        {NAV.map((item) => {
          const active = location.pathname === item.to
          const Icon = item.icon
          return (
            <Link key={item.to} to={item.to} className="relative no-underline sidebar-nav-item" style={active ? { color: 'var(--deep-peach)' } : {}}>
              {active && (
                <motion.div
                  layoutId="sidebar-active"
                  className="absolute inset-0 rounded-2xl"
                  style={{ background: 'linear-gradient(135deg, rgba(244,162,97,0.18), rgba(231,111,81,0.12))' }}
                  transition={{ type: 'spring', stiffness: 300, damping: 30 }}
                />
              )}
              <span className="relative z-10 flex items-center gap-3">
                <Icon size={18} />
                {item.label}
              </span>
            </Link>
          )
        })}
      </nav>

      {/* Quick Add */}
      <motion.button
        className="relative overflow-hidden rounded-2xl px-4 py-3.5 text-white font-semibold text-sm flex items-center gap-2 justify-center"
        style={{ background: 'linear-gradient(135deg, #F4A261, #E76F51)' }}
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.97 }}
        animate={{
          boxShadow: [
            '0 4px 16px rgba(231,111,81,0.25)',
            '0 4px 28px rgba(231,111,81,0.5)',
            '0 4px 16px rgba(231,111,81,0.25)',
          ],
        }}
        transition={{ duration: 2.5, repeat: Infinity }}
        onClick={() => navigate('/assistant')}
      >
        <Zap size={16} />
        Quick AI Schedule
      </motion.button>

      {/* Logout */}
      <button
        className="flex items-center gap-2 px-4 py-3 rounded-xl text-sm mt-1 transition-colors"
        style={{ color: 'var(--text-3)' }}
        onClick={() => { logout(); navigate('/login') }}
      >
        <LogOut size={15} />
        Sign out
      </button>
    </motion.aside>
  )
}
