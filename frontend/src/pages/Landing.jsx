import React, { useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { CalendarDays, CheckCircle2, Clock3, ListTodo, ShieldCheck, Sparkles, Target, Workflow } from 'lucide-react'
import { useAuth } from '../hooks/useAuth'
import { useAuthStore } from '../store/authStore'
import { useTaskStore } from '../store/taskStore'

const capabilities = [
  { icon: Target, name: 'Plan around goals', detail: 'Keep important work connected to what matters.' },
  { icon: CalendarDays, name: 'Make time that fits', detail: 'Respect fixed events, work hours and deadlines.' },
  { icon: Workflow, name: 'Replan carefully', detail: 'Review proposed changes before they affect your calendar.' },
  { icon: ShieldCheck, name: 'Keep control', detail: 'Approve important decisions and inspect their history.' },
]

const sample = [
  ['09:00', 'College lectures', 'Fixed commitment'],
  ['16:30', 'DSA practice', '60-minute task'],
  ['18:00', 'Project review', '45-minute task'],
]

export default function Landing() {
  const { signIn } = useAuth()
  const user = useAuthStore(s => s.user)
  const navigate = useNavigate()
  const home = import.meta.env.VITE_V2_DEFAULT === 'true' ? '/dashboard-v2' : '/dashboard'

  useEffect(() => {
    if (user) navigate(user.uid === 'demo' ? '/dashboard' : home, { replace: true })
  }, [user, navigate, home])

  const exploreLegacyDemo = () => {
    useAuthStore.getState().enterDemoMode()
    useTaskStore.getState().seedDemoTasks()
    navigate('/dashboard')
  }

  return (
    <div className="min-h-screen bg-cream text-dark">
      <a href="#main" className="skip-link">Skip to content</a>
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-5 py-4 sm:px-8">
          <Link to="/" className="flex items-center gap-3 font-semibold tracking-tight" aria-label="ChronoMind home">
            <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-peach text-white"><Clock3 size={19} aria-hidden="true"/></span>
            <span>ChronoMind <span className="text-dark-muted font-normal">AI</span></span>
          </Link>
          <nav aria-label="Public navigation" className="flex items-center gap-4 text-sm">
            <a href="#features" className="hidden text-dark-muted hover:text-dark sm:inline">Features</a>
            <Link to="/demo" className="text-dark-muted hover:text-dark">Preview</Link>
            <button type="button" className="btn-primary !px-4 !py-2" onClick={signIn}>Sign in</button>
          </nav>
        </div>
      </header>
      <main id="main">
        <section className="mx-auto grid max-w-6xl gap-10 px-5 py-16 sm:px-8 md:grid-cols-2 md:items-center md:py-24">
          <div className="space-y-7">
            <p className="inline-flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-dark-muted"><Sparkles size={16} aria-hidden="true"/> Adaptive planning with human approval</p>
            <h1 className="max-w-xl text-4xl font-semibold leading-tight tracking-tight sm:text-5xl">A clear plan for the work that matters.</h1>
            <p className="max-w-lg text-lg leading-relaxed text-dark-muted">Organize tasks and goals, find realistic time for deep work, and review schedule changes with an AI-assisted planner that keeps you in control.</p>
            <div className="flex flex-wrap gap-3">
              <button onClick={signIn} className="btn-primary" type="button">Get started</button>
              <Link to="/demo" className="btn-outline">Explore sample workflow</Link>
            </div>
            <p className="text-sm text-dark-muted">Sign in to save real data. The public preview is illustrative and makes no database changes.</p>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-white p-5 sm:p-7" aria-label="Illustrative daily plan">
            <div className="mb-6 flex items-center justify-between gap-3">
              <div><p className="text-sm font-medium text-dark-muted">SAMPLE WORKSPACE</p><h2 className="mt-1 text-xl font-semibold">Today's plan</h2></div>
              <CalendarDays className="text-dark-muted" size={22} aria-hidden="true"/>
            </div>
            <div className="space-y-3">
              {sample.map(([time, title, subtitle]) => (
                <div key={time} className="flex gap-4 rounded-xl border border-slate-200 p-4">
                  <span className="w-12 shrink-0 text-sm font-medium tabular-nums text-dark-muted">{time}</span>
                  <div><p className="font-medium">{title}</p><p className="mt-1 text-sm text-dark-muted">{subtitle}</p></div>
                </div>
              ))}
            </div>
            <div className="mt-5 flex gap-3 rounded-xl bg-slate-50 p-4 text-sm text-dark-muted">
              <CheckCircle2 className="shrink-0 text-peach" size={19} aria-hidden="true"/>
              Suggested changes require your review before they are saved.
            </div>
          </div>
        </section>
        <section id="features" className="border-t border-slate-200 bg-white">
          <div className="mx-auto max-w-6xl px-5 py-16 sm:px-8">
            <p className="text-sm font-semibold text-peach-dark">WHY CHRONOMIND</p>
            <h2 className="mt-2 text-3xl font-semibold tracking-tight">More than another to-do list</h2>
            <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {capabilities.map(({ icon: Icon, name, detail }) => (
                <article key={name} className="rounded-xl border border-slate-200 p-5">
                  <Icon className="mb-5 text-peach-dark" size={23} aria-hidden="true"/>
                  <h3 className="font-semibold">{name}</h3><p className="mt-2 text-sm leading-relaxed text-dark-muted">{detail}</p>
                </article>
              ))}
            </div>
          </div>
        </section>
        <section className="mx-auto flex max-w-6xl flex-col gap-4 px-5 py-12 sm:flex-row sm:items-center sm:justify-between sm:px-8">
          <div><h2 className="font-semibold">Built for thoughtful daily planning.</h2><p className="mt-1 text-sm text-dark-muted">Explore the interface without connecting a database.</p></div>
          <div className="flex gap-3">
            <Link to="/demo" className="btn-outline">Read-only preview</Link>
            <button type="button" onClick={exploreLegacyDemo} className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium hover:bg-white">Legacy local demo</button>
          </div>
        </section>
      </main>
      <footer className="border-t border-slate-200 bg-white px-5 py-6 text-center text-sm text-dark-muted">ChronoMind AI · Human-controlled adaptive planning · <a className="underline" href="https://github.com/shanmukhdatta/Chrono-Mind-AI">Source on GitHub</a></footer>
    </div>
  )
}
