import React from 'react'
import { Link } from 'react-router-dom'
import { CalendarDays, CheckCircle2, Clock3, ShieldCheck, Target } from 'lucide-react'

const tasks = [
  { title: 'DSA practice', goal: 'Placement preparation', duration: '60 min', priority: 'High', at: '16:30–17:30' },
  { title: 'Review project results', goal: 'Research presentation', duration: '45 min', priority: 'High', at: '18:00–18:45' },
  { title: 'Read ML notes', goal: 'Semester revision', duration: '30 min', priority: 'Normal', at: '19:30–20:00' },
]
export default function DemoPreview() {
  return (
    <main className="min-h-screen bg-cream p-5 text-dark sm:p-10">
      <div className="mx-auto max-w-5xl space-y-7">
        <header className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 pb-6">
          <div><Link to="/" className="text-sm font-medium text-peach-dark hover:underline">← ChronoMind home</Link><h1 className="mt-3 text-3xl font-semibold">Read-only product preview</h1><p className="mt-2 max-w-2xl text-sm text-dark-muted">Illustrative demo data. No account is created and nothing here is written to PostgreSQL. Sign in to use actual V2 features.</p></div>
        </header>
        <div className="grid gap-4 sm:grid-cols-3">
          {[[Target,'3','Sample goals'],[CheckCircle2,'3','Sample tasks'],[Clock3,'135 min','Sample scheduled work']].map(([Icon,num,label])=>(
            <div key={label} className="rounded-xl border border-slate-200 bg-white p-5"><Icon size={20} className="text-peach-dark"/><p className="mt-4 text-2xl font-semibold">{num}</p><p className="text-sm text-dark-muted">{label}</p></div>
          ))}
        </div>
        <section className="rounded-xl border border-slate-200 bg-white p-6">
          <div className="mb-5 flex items-center gap-2"><CalendarDays size={19}/><h2 className="text-lg font-semibold">Sample planning result</h2></div>
          <div className="space-y-3">{tasks.map(task=>(
            <div key={task.title} className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-slate-200 p-4">
              <div><p className="font-semibold">{task.title}</p><p className="mt-1 text-sm text-dark-muted">{task.goal} · {task.duration}</p></div>
              <div className="text-sm text-dark-muted"><p>{task.at}</p><p className="mt-1">{task.priority} priority</p></div>
            </div>
          ))}</div>
        </section>
        <section className="flex gap-3 rounded-xl border border-slate-200 bg-white p-5"><ShieldCheck size={22} className="shrink-0 text-peach-dark"/><div><h2 className="font-semibold">Review before saving</h2><p className="mt-1 text-sm text-dark-muted">In the connected V2 app, generated plans are proposals; approval validates constraints and saves schedule blocks in PostgreSQL.</p></div></section>
        <div className="flex flex-wrap gap-3"><Link className="btn-primary" to="/">Sign in to use V2</Link><a className="btn-outline" href="https://github.com/shanmukhdatta/Chrono-Mind-AI">View the source code</a></div>
      </div>
    </main>
  )
}
