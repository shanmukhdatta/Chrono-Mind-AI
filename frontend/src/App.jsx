import { useEffect } from 'react'
import { Routes, Route, Navigate, useLocation, Link } from 'react-router-dom'
import { AnimatePresence, motion } from 'framer-motion'
import { Toaster } from 'react-hot-toast'
import { LayoutDashboard, Calendar, Bot, User } from 'lucide-react'

import { useAuthStore } from './store'
import CustomCursor from './components/ui/CustomCursor'
import BackgroundOrbs from './components/ui/BackgroundOrbs'
import Navbar from './components/layout/Navbar'
import Sidebar from './components/layout/Sidebar'

import Landing from './components/pages/Landing'
import { Login, Register } from './components/pages/Auth'
import Onboarding from './components/pages/Onboarding'
import Dashboard from './components/pages/Dashboard'
import CalendarView from './components/pages/CalendarView'
import AIAssistant from './components/pages/AIAssistant'
import Profile from './components/pages/Profile'

// ─── Route Guards ─────────────────────────────────────────────────
function PrivateRoute({ children }) {
  const { isAuthenticated } = useAuthStore()
  return isAuthenticated ? children : <Navigate to="/login" replace />
}

function PublicRoute({ children }) {
  const { isAuthenticated } = useAuthStore()
  return !isAuthenticated ? children : <Navigate to="/dashboard" replace />
}

// ─── App Shell layouts ────────────────────────────────────────────
function PublicLayout({ children }) {
  return (
    <>
      <Navbar />
      <motion.main
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -20 }}
        transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
      >
        {children}
      </motion.main>
    </>
  )
}

function BottomTabBar() {
  const location = useLocation()
  const tabs = [
    { to: '/dashboard', icon: LayoutDashboard, label: 'Home' },
    { to: '/calendar', icon: Calendar, label: 'Calendar' },
    { to: '/assistant', icon: Bot, label: 'AI' },
    { to: '/profile', icon: User, label: 'Profile' },
  ]
  return (
    <div className="fixed bottom-0 left-0 right-0 z-50 glass md:hidden px-4 pb-safe"
      style={{ borderTop: '1px solid rgba(255,255,255,0.4)', paddingBottom: 'env(safe-area-inset-bottom)' }}>
      <div className="flex items-center justify-around py-2">
        {tabs.map(tab => {
          const active = location.pathname === tab.to
          const Icon = tab.icon
          return (
            <Link key={tab.to} to={tab.to} className="flex flex-col items-center gap-0.5 py-1 px-3">
              <motion.div animate={active ? { y: [0, -4, 0] } : {}}
                transition={{ type: 'spring', stiffness: 300, damping: 20 }}>
                <Icon size={22} style={{ color: active ? 'var(--peach)' : 'var(--text-3)' }} />
              </motion.div>
              <AnimatePresence>
                {active && (
                  <motion.span className="text-xs font-medium"
                    style={{ color: 'var(--peach)' }}
                    initial={{ opacity: 0, y: 4 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
                    {tab.label}
                  </motion.span>
                )}
              </AnimatePresence>
            </Link>
          )
        })}
      </div>
    </div>
  )
}

function AppLayout({ children }) {
  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="flex-1 md:ml-64 relative z-10 min-h-screen pb-16 md:pb-0">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
          transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
          className="h-full"
        >
          {children}
        </motion.div>
      </main>
      <BottomTabBar />
    </div>
  )
}

// ─── App ──────────────────────────────────────────────────────────
export default function App() {
  const location = useLocation()
  const { rehydrateAuth } = useAuthStore()

  useEffect(() => {
    rehydrateAuth()
  }, [])

  return (
    <>
      <CustomCursor />
      <BackgroundOrbs />

      <Toaster
        position="top-right"
        toastOptions={{
          duration: 3500,
          style: {
            background: 'rgba(255,255,255,0.85)',
            backdropFilter: 'blur(20px)',
            border: '1px solid rgba(244,162,97,0.3)',
            color: '#1a1a2e',
            fontFamily: 'DM Sans, sans-serif',
            fontSize: '14px',
            borderRadius: '14px',
            boxShadow: '0 8px 32px rgba(244,162,97,0.15)',
          },
          success: { iconTheme: { primary: '#2A9D8F', secondary: 'white' } },
          error: { iconTheme: { primary: '#E76F51', secondary: 'white' } },
        }}
      />

      <AnimatePresence mode="wait">
        <Routes location={location} key={location.pathname}>
          {/* Public pages */}
          <Route path="/" element={<PublicLayout><Landing /></PublicLayout>} />
          <Route path="/login" element={<PublicLayout><PublicRoute><Login /></PublicRoute></PublicLayout>} />
          <Route path="/register" element={<PublicLayout><PublicRoute><Register /></PublicRoute></PublicLayout>} />

          {/* Onboarding — authenticated but separate layout */}
          <Route path="/onboarding" element={
            <PrivateRoute>
              <Navbar />
              <Onboarding />
            </PrivateRoute>
          } />

          {/* App pages with sidebar */}
          <Route path="/dashboard" element={<PrivateRoute><AppLayout><Dashboard /></AppLayout></PrivateRoute>} />
          <Route path="/calendar" element={<PrivateRoute><AppLayout><CalendarView /></AppLayout></PrivateRoute>} />
          <Route path="/assistant" element={<PrivateRoute><AppLayout><AIAssistant /></AppLayout></PrivateRoute>} />
          <Route path="/profile" element={<PrivateRoute><AppLayout><Profile /></AppLayout></PrivateRoute>} />

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AnimatePresence>
    </>
  )
}
