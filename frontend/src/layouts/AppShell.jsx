import React, { useEffect, useState } from 'react'
import { NavLink, useLocation, useNavigate } from 'react-router-dom'
import { Bell, Bot, CalendarDays, CheckCheck, Clock3, LayoutDashboard, ListTodo, LogOut, Menu, Repeat2, Settings2, Target, Timer, UserRound, Workflow, X } from 'lucide-react'
import { useAuth } from '../hooks/useAuth'
import { useAuthStore } from '../store/authStore'
import { AssistantPanel } from '../components/AssistantPanel'
import { FocusTimer } from '../components/FocusTimer'

const V2_DEFAULT = import.meta.env.VITE_V2_DEFAULT === 'true'
const sections = [
  { title: 'Workspace', items: [
    ['/dashboard-v2', 'Overview', LayoutDashboard],
    ['/tasks-v2', 'Tasks', ListTodo],
    ['/calendar-v2', 'Calendar', CalendarDays],
    ['/goals', 'Goals', Target],
    ['/planning', 'AI planning', Workflow],
    ['/approvals', 'Plan approvals', CheckCheck],
  ] },
  { title: 'Tools', items: [
    ['/assistant-v2', 'Assistant', Bot],
    ['/focus-v2', 'Focus', Timer],
    ['/recurrence-v2', 'Routines', Repeat2],
    ['/notifications-v2', 'Notifications', Bell],
  ] },
  { title: 'Settings', items: [
    ['/preferences', 'Preferences', Settings2],
    ['/profile', 'Profile & data', UserRound],
    ['/agent-runs', 'Agent activity', Workflow],
  ] },
]

const legacy = [
  ['/dashboard', 'Legacy dashboard', LayoutDashboard],
  ['/calendar', 'Legacy calendar', CalendarDays],
  ['/assistant', 'Legacy assistant', Bot],
]

function SidebarLink({ to, name, Icon, onNavigate }) {
  return (
    <NavLink to={to} onClick={onNavigate} className={({ isActive }) =>
      'flex min-h-11 items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium ' +
      (isActive ? 'bg-slate-100 text-dark' : 'text-dark-muted hover:bg-slate-50 hover:text-dark')
    }>
      <Icon aria-hidden="true" size={18} className="shrink-0"/>
      <span>{name}</span>
    </NavLink>
  )
}

export function AppShell({ children }) {
  const user = useAuthStore(s => s.user)
  const { signOutUser } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [open, setOpen] = useState(false)
  const current = [...sections.flatMap(s => s.items), ...legacy].find(item => item[0] === location.pathname)
  useEffect(() => { setOpen(false) }, [location.pathname])
  useEffect(() => {
    if (!open) return undefined
    const onEscape = e => { if (e.key === 'Escape') setOpen(false) }
    window.addEventListener('keydown', onEscape)
    return () => window.removeEventListener('keydown', onEscape)
  }, [open])
  const signOut = async () => {
    await signOutUser()
    navigate('/', { replace: true })
  }
  return (
    <div className="flex min-h-screen bg-cream text-dark">
      <a href="#workspace-content" className="skip-link">Skip to main content</a>
      {open && <button type="button" aria-label="Close navigation" className="fixed inset-0 z-30 bg-slate-950/40 lg:hidden" onClick={() => setOpen(false)}/>}
      <aside id="app-navigation" aria-label="Primary navigation" className={
        'fixed inset-y-0 left-0 z-40 flex w-64 flex-col border-r border-slate-200 bg-white lg:sticky lg:top-0 lg:h-screen lg:translate-x-0 ' +
        (open ? 'translate-x-0' : '-translate-x-full')
      }>
        <div className="flex h-16 items-center justify-between border-b border-slate-200 px-5">
          <NavLink to={V2_DEFAULT ? '/dashboard-v2' : '/dashboard'} className="flex items-center gap-3 font-semibold tracking-tight">
            <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-peach text-white"><Clock3 size={18} aria-hidden="true"/></span>
            ChronoMind
          </NavLink>
          <button aria-label="Close menu" className="rounded-lg p-2 hover:bg-slate-100 lg:hidden" onClick={() => setOpen(false)}><X size={19}/></button>
        </div>
        <nav aria-label="App sections" className="flex-1 space-y-5 overflow-y-auto px-3 py-5">
          {sections.map(section => (
            <div key={section.title}>
              <p className="mb-2 px-3 text-xs font-semibold uppercase tracking-wide text-slate-500">{section.title}</p>
              <div className="space-y-1">{section.items.map(([path, label, Icon]) => (
                <SidebarLink key={path} to={path} name={label} Icon={Icon} onNavigate={() => setOpen(false)}/>
              ))}</div>
            </div>
          ))}
          {!V2_DEFAULT && <div><p className="mb-2 px-3 text-xs font-semibold uppercase tracking-wide text-slate-500">Legacy V1</p>{legacy.map(([path,label,Icon]) => <SidebarLink key={path} to={path} name={label} Icon={Icon} onNavigate={() => setOpen(false)}/>)}</div>}
        </nav>
        <div className="border-t border-slate-200 p-4">
          <p className="truncate px-2 text-sm font-semibold">{user?.displayName || 'ChronoMind user'}</p>
          <p className="mb-3 truncate px-2 text-xs text-dark-muted">{user?.email || (user?.uid === 'demo' ? 'Local demo · no V2 persistence' : '')}</p>
          <button type="button" onClick={signOut} className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-sm font-medium text-dark-muted hover:bg-slate-100 hover:text-dark"><LogOut size={17} aria-hidden="true"/> Sign out</button>
        </div>
      </aside>
      <div className="flex min-h-screen min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-20 flex h-16 items-center justify-between border-b border-slate-200 bg-white px-4 sm:px-8">
          <div className="flex items-center gap-3">
            <button type="button" aria-label="Open menu" aria-expanded={open} aria-controls="app-navigation" onClick={() => setOpen(true)} className="rounded-lg p-2 hover:bg-slate-100 lg:hidden"><Menu size={20}/></button>
            <h1 className="text-base font-semibold sm:text-lg">{current?.[1] || 'ChronoMind'}</h1>
          </div>
          <NavLink to="/notifications-v2" aria-label="Notifications" className="rounded-lg p-2 text-dark-muted hover:bg-slate-100 hover:text-dark"><Bell size={20}/></NavLink>
        </header>
        <main id="workspace-content" tabIndex={-1} className="w-full flex-1 px-4 py-6 sm:px-8 sm:py-8"><div className="mx-auto max-w-7xl">{children}</div></main>
      </div>
      {!V2_DEFAULT && <><AssistantPanel/><FocusTimer/></>}
    </div>
  )
}
