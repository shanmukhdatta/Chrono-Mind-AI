import React, { useState } from 'react'
import { Bot, ShieldCheck, RefreshCw, ArrowRight, Play, Database } from 'lucide-react'
import { Link, useSearchParams } from 'react-router-dom'
import api from '../lib/api'
import { useAuthStore } from '../store/authStore'

function explainError(error) {
  if (typeof error.response?.data?.detail === 'string') return error.response.data.detail
  if (error.response?.status === 503) return 'PostgreSQL or LangGraph checkpoints are not configured; see the operator setup guide.'
  return error.message || 'Agent operation failed'
}

export default function AgentRunsV2() {
  const demo = useAuthStore(s => s.user?.uid === 'demo')
  const [search, setSearch] = useSearchParams()
  const [runId, setRunId] = useState(search.get('runId') || '')
  const [days, setDays] = useState(7)
  const [run, setRun] = useState(null)
  const [working, setWorking] = useState(false)
  const [error, setError] = useState('')

  const operation = async action => {
    if (demo || working) return
    setWorking(true)
    setError('')
    try {
      await action()
    } catch (err) {
      setError(explainError(err))
    } finally {
      setWorking(false)
    }
  }

  const start = () => operation(async () => {
    const response = await api.post('/api/v2/agent/runs', { days: Number(days) })
    const id = response.data.run_id
    setRun(response.data)
    setRunId(id)
    setSearch({ runId: id })
  })

  const refresh = () => operation(async () => {
    if (!runId.trim()) throw new Error('Enter a valid saved run ID.')
    const response = await api.get('/api/v2/agent/runs/' + encodeURIComponent(runId.trim()))
    setRun(response.data)
    setSearch({ runId: runId.trim() })
  })

  const resume = () => operation(async () => {
    if (!runId.trim()) throw new Error('Choose a saved run first.')
    // The backend derives the final decision from the authenticated proposal,
    // not from client-supplied approval text.
    const response = await api.post('/api/v2/agent/runs/' + encodeURIComponent(runId.trim()) + '/resume')
    setRun(response.data)
  })

  return (
    <div className="max-w-4xl mx-auto space-y-5">
      <header>
        <p className="text-sm text-peach-dark font-semibold">Persistent planning workflow</p>
        <h1 className="text-3xl font-bold text-dark">LangGraph Agent</h1>
        <p className="text-sm text-dark-muted mt-2">
          Build a real scheduling proposal, pause for your decision, then resume the saved graph.
        </p>
      </header>
      <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 flex gap-3 text-sm text-amber-900">
        <ShieldCheck className="w-5 h-5 shrink-0" />
        <p>The agent cannot apply calendar changes itself. You must approve the stored proposal before it resumes. Production checkpoint recovery requires configured PostgreSQL.</p>
      </div>
      {demo && <p className="rounded-xl p-4 border bg-white">Sign in to run the real PostgreSQL-backed planning graph; demo sessions are not persisted.</p>}
      {error && <p role="alert" className="rounded-xl p-4 border border-red-200 bg-red-50 text-sm text-red-800">{error}</p>}
      {!demo && (
        <>
          <section className="rounded-2xl p-5 border bg-white space-y-4">
            <h2 className="font-semibold flex gap-2 items-center"><Bot className="w-5 h-5 text-peach"/> Start a planning run</h2>
            <label className="block text-sm font-medium">Planning horizon
              <select className="input-field mt-1" value={days} onChange={e => setDays(Number(e.target.value))}>
                <option value={3}>3 days</option>
                <option value={7}>7 days</option>
                <option value={14}>14 days</option>
              </select>
            </label>
            <button className="btn-primary flex gap-2 items-center" disabled={working} type="button" onClick={start}>
              <Play className="w-4 h-4"/> {working ? 'Processing...' : 'Start agent'}
            </button>
            <p className="text-xs text-dark-muted">Planning is deterministic. The LangGraph checkpoint stores the approval pause, not an automatic decision.</p>
          </section>
          <section className="rounded-2xl p-5 border bg-white space-y-4">
            <h2 className="font-semibold flex gap-2 items-center"><Database className="w-5 h-5 text-peach"/> Resume an existing run</h2>
            <label className="block text-sm font-medium">Run ID
              <input className="input-field mt-1" aria-label="Run ID" value={runId} maxLength={128}
                onChange={e => setRunId(e.target.value)} placeholder="Run UUID from a previous session"/>
            </label>
            <button type="button" disabled={working || !runId.trim()}
              onClick={refresh} className="border rounded-xl px-4 py-2 text-sm flex gap-2 items-center">
              <RefreshCw className="w-4 h-4"/> Refresh run status
            </button>
            {run && (
              <div className="rounded-xl border bg-gray-50 p-4 space-y-3">
                <p className="font-semibold">Run status: <span className="text-peach-dark">{run.status}</span></p>
                <p className="text-xs text-dark-muted break-all">Run ID: {run.run_id}</p>
                {run.proposal_id && (
                  <Link to={'/approvals?planId=' + encodeURIComponent(run.proposal_id)}
                    className="flex gap-2 items-center text-sm underline text-peach-dark">
                    <ShieldCheck className="w-4 h-4"/> Review and decide on this proposal <ArrowRight className="w-4 h-4"/>
                  </Link>
                )}
                {run.status === 'awaiting_review' && (
                  <button type="button" onClick={resume} disabled={working}
                    className="btn-primary text-sm">
                    Resume after recorded approval/rejection
                  </button>
                )}
                <p className="text-xs text-dark-muted">The server refuses to resume until the authenticated approval API has stored a real decision.</p>
              </div>
            )}
          </section>
        </>
      )}
    </div>
  )
}
