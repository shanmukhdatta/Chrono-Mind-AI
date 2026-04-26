import { useState, useEffect } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { motion, AnimatePresence, useScroll } from 'framer-motion'
import { Clock, LayoutDashboard, Calendar, Bot, User, LogOut, Bell } from 'lucide-react'
import { useAuthStore } from '../../store'
import { MagneticButton } from '../ui'

const NAV_LINKS = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/calendar', label: 'Calendar', icon: Calendar },
  { to: '/assistant', label: 'Assistant', icon: Bot },
  { to: '/profile', label: 'Profile', icon: User },
]

export default function Navbar() {
  const [scrolled, setScrolled] = useState(false)
  const [menuOpen, setMenuOpen] = useState(false)
  const { user, logout, isAuthenticated } = useAuthStore()
  const location = useLocation()
  const navigate = useNavigate()

  useEffect(() => {
    const handler = () => setScrolled(window.scrollY > 50)
    window.addEventListener('scroll', handler, { passive: true })
    return () => window.removeEventListener('scroll', handler)
  }, [])

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <motion.nav
      className="fixed top-0 left-0 right-0 z-50 px-6 py-4"
      initial={{ y: -80, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.6, delay: 0.2, ease: [0.22, 1, 0.36, 1] }}
    >
      <motion.div
        className="max-w-7xl mx-auto flex items-center justify-between rounded-2xl px-6 py-3"
        animate={scrolled ? {
          background: 'rgba(255,255,255,0.75)',
          backdropFilter: 'blur(28px) saturate(180%)',
          boxShadow: '0 8px 32px rgba(244,162,97,0.12), 0 2px 8px rgba(0,0,0,0.04)',
          border: '1px solid rgba(255,255,255,0.55)',
        } : {
          background: 'transparent',
          backdropFilter: 'none',
          boxShadow: 'none',
          border: '1px solid transparent',
        }}
        transition={{ duration: 0.4, ease: 'easeOut' }}
      >
        {/* Logo */}
        <Link to={isAuthenticated ? '/dashboard' : '/'} className="flex items-center gap-2.5 no-underline">
          <motion.div
            whileHover={{ rotate: 180 }}
            transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
            className="w-9 h-9 rounded-xl flex items-center justify-center"
            style={{ background: 'linear-gradient(135deg, #F4A261, #E76F51)' }}
          >
            <Clock size={18} color="white" />
          </motion.div>
          <span className="font-bold text-lg" style={{ fontFamily: 'Inter', color: 'var(--text-1)' }}>
            Chrono<span className="text-gradient-peach">Mind</span>
          </span>
        </Link>

        {/* Desktop Nav */}
        {isAuthenticated && (
          <div className="hidden md:flex items-center gap-1">
            {NAV_LINKS.map((link) => {
              const active = location.pathname === link.to
              return (
                <Link key={link.to} to={link.to} className="relative px-4 py-2 no-underline">
                  <span className={`text-sm font-medium transition-colors ${active ? 'text-gradient-peach' : ''}`}
                    style={{ color: active ? undefined : 'var(--text-2)' }}>
                    {link.label}
                  </span>
                  {active && (
                    <motion.div
                      layoutId="nav-underline"
                      className="absolute bottom-0 left-4 right-4 h-0.5 rounded-full"
                      style={{ background: 'linear-gradient(90deg, #F4A261, #E76F51)' }}
                      transition={{ type: 'spring', stiffness: 300, damping: 30 }}
                    />
                  )}
                </Link>
              )
            })}
          </div>
        )}

        {/* Right */}
        <div className="flex items-center gap-3">
          {isAuthenticated ? (
            <>
              <MagneticButton
                className="w-9 h-9 glass rounded-xl flex items-center justify-center interactive"
                onClick={() => {}}
              >
                <Bell size={16} style={{ color: 'var(--text-2)' }} />
              </MagneticButton>

              <div className="relative">
                <MagneticButton
                  className="flex items-center gap-2 glass rounded-xl px-3 py-2 interactive"
                  onClick={handleLogout}
                >
                  {user?.avatar_url ? (
                    <img src={user.avatar_url} className="w-6 h-6 rounded-full object-cover" alt="" />
                  ) : (
                    <div className="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold text-white"
                      style={{ background: 'linear-gradient(135deg, #F4A261, #E76F51)' }}>
                      {user?.name?.[0] || 'U'}
                    </div>
                  )}
                  <span className="text-sm font-medium hidden sm:block" style={{ color: 'var(--text-2)' }}>
                    {user?.name?.split(' ')[0]}
                  </span>
                  <LogOut size={14} style={{ color: 'var(--text-3)' }} />
                </MagneticButton>
              </div>
            </>
          ) : (
            <div className="flex items-center gap-3">
              <Link to="/login">
                <MagneticButton className="btn-ghost text-sm interactive">Sign in</MagneticButton>
              </Link>
              <Link to="/register">
                <MagneticButton className="btn-primary text-sm interactive">Get Started</MagneticButton>
              </Link>
            </div>
          )}
        </div>
      </motion.div>
    </motion.nav>
  )
}
