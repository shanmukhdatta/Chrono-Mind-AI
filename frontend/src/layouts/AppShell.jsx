import React, { useState } from 'react'
import { NavLink, useNavigate, useLocation } from 'react-router-dom'
import { LayoutDashboard, Calendar, Sparkles, User, LogOut, Clock, Menu, X } from 'lucide-react'
import { useAuth } from '../hooks/useAuth'
import { useAuthStore } from '../store/authStore'
import { ClockWidget } from '../components/ClockWidget'
import { NotificationBell } from '../components/NotificationBell'
import { AssistantPanel } from '../components/AssistantPanel'
import { FocusTimer } from '../components/FocusTimer'

const NAV_ITEMS = [
  { path: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/calendar',  label: 'Calendar',  icon: Calendar },
  { path: '/assistant', label: 'Assistant', icon: Sparkles },
  { path: '/profile',   label: 'Profile',   icon: User },
]

export function AppShell({ children }) {
  const { user } = useAuthStore()
  const { signOutUser } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [sidebarOpen, setSidebarOpen] = useState(false)

  const handleSignOut = async () => {
    await signOutUser()
    navigate('/')
  }

  const currentLabel = NAV_ITEMS.find(n => location.pathname.startsWith(n.path))?.label || 'ChronoMind AI'

  return (
    <div className="flex h-screen bg-cream overflow-hidden">
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div className="fixed inset-0 bg-dark/30 z-30 md:hidden" onClick={() => setSidebarOpen(false)} />
      )}

      {/* Sidebar */}
      <aside className={`
        fixed md:relative inset-y-0 left-0 z-40
        w-64 flex-shrink-0 bg-white/90 backdrop-blur-glass border-r border-gray-100 flex flex-col
        transition-transform duration-300 ease-in-out
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}
      `}>
        {/* Logo */}
        <div className="p-5 border-b border-gray-100 flex items-center justify-between flex-shrink-0">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-peach rounded-lg flex items-center justify-center flex-shrink-0">
              <Clock className="w-4 h-4 text-white" />
            </div>
            <div>
              <h1 className="text-lg font-bold leading-none">
                <span className="text-peach">Chrono</span><span className="text-dark">Mind</span>
              </h1>
              <p className="text-[10px] text-dark-muted">AI Planner</p>
            </div>
          </div>
          <button onClick={() => setSidebarOpen(false)} className="md:hidden p-1 hover:bg-gray-100 rounded-lg">
            <X className="w-5 h-5 text-dark-muted" />
          </button>
        </div>

        {/* User info */}
        <div className="p-4 border-b border-gray-100 flex-shrink-0">
          <div className="flex items-center gap-3">
            <img
              src={user?.photoURL || `https://ui-avatars.com/api/?name=${encodeURIComponent(user?.displayName || 'U')}&background=E8A87C&color=fff&size=80`}
              alt="Profile"
              className="w-10 h-10 rounded-full object-cover border-2 border-peach/20 flex-shrink-0"
            />
            <div className="min-w-0">
              <p className="text-sm font-semibold text-dark truncate">{user?.displayName || 'User'}</p>
              <p className="text-xs text-dark-muted truncate">{user?.email || ''}</p>
            </div>
          </div>
        </div>

        {/* Clock */}
        <div className="p-4 flex-shrink-0">
          <ClockWidget />
        </div>

        {/* Nav */}
        <nav className="flex-1 px-3 py-2 space-y-1 overflow-y-auto">
          {NAV_ITEMS.map(item => (
            <NavLink
              key={item.path}
              to={item.path}
              onClick={() => setSidebarOpen(false)}
              className={({ isActive }) =>
                `flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-peach/15 text-peach-dark border-l-[3px] border-peach pl-[13px]'
                    : 'text-dark-muted hover:bg-peach/5 hover:text-dark'
                }`
              }
            >
              <item.icon className="w-5 h-5 flex-shrink-0" />
              {item.label}
            </NavLink>
          ))}
        </nav>

        {/* Bottom */}
        <div className="p-4 border-t border-gray-100 flex-shrink-0">
          <button
            onClick={handleSignOut}
            className="flex items-center gap-3 px-4 py-3 w-full rounded-xl text-sm font-medium text-red-500 hover:bg-red-50 transition-colors"
          >
            <LogOut className="w-5 h-5" />
            Sign Out
          </button>
          <p className="text-[10px] text-dark-muted/60 text-center mt-3">
            ChronoMind AI v2.0 · Powered by Groq + LangGraph
          </p>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 flex flex-col overflow-hidden min-w-0">
        {/* Top bar */}
        <header className="h-16 bg-white/60 backdrop-blur-sm border-b border-gray-100 flex items-center justify-between px-4 md:px-6 flex-shrink-0">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setSidebarOpen(true)}
              className="md:hidden p-2 hover:bg-gray-100 rounded-xl transition-colors"
              aria-label="Open menu"
            >
              <Menu className="w-5 h-5 text-dark-muted" />
            </button>
            <h2 className="font-semibold text-dark">{currentLabel}</h2>
          </div>
          <NotificationBell />
        </header>

        {/* Page */}
        <div className="flex-1 overflow-auto p-4 md:p-6">
          {children}
        </div>
      </main>

      {/* Floating */}
      <AssistantPanel />
      <FocusTimer />
    </div>
  )
}
