import React, { useCallback, useEffect, useState } from 'react'
import { CheckCircle2, CircleX, RotateCcw, ShieldCheck, CalendarDays } from 'lucide-react'
import { Link, useSearchParams } from 'react-router-dom'
import toast from 'react-hot-toast'
import api from '../lib/api'
import { isoToDateTimeLocal } from '../lib/tasksV2'
import { useAuthStore } from '../store/authStore'

function describeError(error) {
  if (typeof error.response?.data?.detail === 'string') return error.response.data.detail
  if (error.response?.status === 503) return 'PostgreSQL V2 storage is not configured.'
  return error.message || 'Unable to complete the operation'
}

function local(iso) {
  return new Date(iso).toLocaleString(undefined, {
    dateStyle: 'medium', timeStyle: 'short'
  })
}

const statusClasses = {
  pending: 'bg-amber-50 text-amber-900 border-amber-200',
  approved: 'bg-green-50 text-green-800 border-green-200',
  rejected: 'bg-gray-100 text-gray-700 border-gray-200',
  undone: 'bg-blue-50 text-blue-800 border-blue-200',
}

export default function ApprovalCenter() {
  const demo = useAuthStore(state => state.user?.uid === 'demo')
  const [query, setQuery] = useSearchParams()
  const [plans, setPlans] = useState([])
  const [selectedId, setSelectedId] = useState(query.get('planId') || null)
  const [loading, setLoading] = useState(!demo)
  const [working, setWorking] = useState(false)
  const [error, setError] = useState('')
  const [proposedStarts, setProposedStarts] = useState({})

  const refresh = useCallback(async () => {
    if (demo) return
    try {
      const response = await api.get('/api/v2/plans')
      setPlans(response.data)
      setError('')
    } catch (err) {
      setError(describeError(err))
    } finally {
      setLoading(false)
    }
  }, [demo])

  useEffect(() => { refresh() }, [refresh])
  const selected = plans.find(plan => plan.id === selectedId) || null

  const choose = (plan) => {
    setSelectedId(plan.id)
    setQuery({ planId: plan.id })
    setError('')
  }

  const run = async (operation, verb) => {
    if (!selected) return
    const question = operation === 'approve'
      ? `Apply ${selected.blocks.length} proposed calendar sessions? This will save them.`
      : operation === 'undo'
        ? 'Remove the scheduled sessions created by this approved plan?'
        : 'Reject this proposed schedule without saving it?'
    if (!window.confirm(question)) return
    setWorking(true)
    try {
      const result = await api.post('/api/v2/plans/' + selected.id + '/' + operation)
      await refresh()
      setError('')
      toast.success(verb + ' successfully')
      setSelectedId(result.data.id)
    } catch (err) {
      const message = describeError(err)
      setError(message)
      toast.error(message)
    } finally {
      setWorking(false)
    }
  }

  const moveSession = async (index, original) => {
    const value = proposedStarts[index] || isoToDateTimeLocal(original.starts_at)
    const parsed = new Date(value)
    if (!Number.isFinite(parsed.getTime())) {
      setError('Choose a valid new local start time')
      return
    }
    setWorking(true)
    setError('')
    try {
      await api.put('/api/v2/plans/' + selected.id + '/blocks', {
        block_index: index, starts_at: parsed.toISOString()
      })
      setProposedStarts({})
      await refresh()
      toast.success('Proposal updated. Calendar has not changed.')
    } catch (err) {
      setError(describeError(err))
      toast.error(describeError(err))
    } finally {
      setWorking(false)
    }
  }

  if (demo) return (
    <div className="max-w-3xl p-6 bg-white rounded-2xl border">
      <h1 className="text-2xl font-bold">Plan approvals</h1>
      <p className="mt-3 text-dark-muted">Sign in to review and approve real saved planning proposals.</p>
    </div>
  )

  return (
    <div className="max-w-6xl mx-auto space-y-5">
      <header>
        <p className="text-peach-dark text-sm font-semibold">You stay in control</p>
        <h1 className="text-3xl font-bold text-dark">Plan approvals</h1>
        <p className="text-sm text-dark-muted mt-2">
          Review every proposed change before it can be saved to your calendar.
        </p>
      </header>
      {error && <p role="alert" className="border border-red-200 bg-red-50 text-red-800 rounded-xl p-4 text-sm">{error}</p>}
      {loading ? <p>Loading proposals...</p> : (
        <div className="grid gap-5 lg:grid-cols-[1fr_1.5fr]">
          <section className="rounded-2xl bg-white border border-gray-100 p-5 space-y-3">
            <div className="flex justify-between items-center">
              <h2 className="font-semibold text-lg">Recent proposals ({plans.length})</h2>
              <button type="button" onClick={refresh} className="text-peach-dark text-sm">Refresh</button>
            </div>
            {plans.length === 0 && (
              <div className="space-y-3 py-8 text-sm text-dark-muted">
                <p>You have no proposals yet.</p>
                <Link className="underline text-peach-dark" to="/planning">Generate a scheduling preview</Link>
              </div>
            )}
            {plans.map(plan => (
              <button type="button" key={plan.id} onClick={() => choose(plan)}
                className={`w-full text-left border rounded-xl p-4 ${plan.id === selectedId ? 'border-peach bg-peach/5' : 'border-gray-100 hover:bg-gray-50'}`}>
                <div className="flex justify-between gap-2 items-center">
                  <span className="font-semibold text-sm">{local(plan.created_at)}</span>
                  <span className={`capitalize text-xs px-2 py-1 rounded-lg border ${statusClasses[plan.status] || ''}`}>{plan.status}</span>
                </div>
                <p className="text-xs text-dark-muted mt-2">{plan.blocks.length} proposed sessions · {plan.unscheduled.length} tasks with remaining work</p>
              </button>
            ))}
          </section>
          <section className="rounded-2xl bg-white border border-gray-100 p-5">
            {!selected ? (
              <div className="py-20 flex flex-col items-center text-center gap-3 text-dark-muted">
                <ShieldCheck className="w-9 h-9 text-peach" />
                <p>Select a proposal to inspect it and choose an action.</p>
              </div>
            ) : (
              <div className="space-y-5">
                <header className="flex flex-wrap justify-between gap-2">
                  <h2 className="font-semibold text-lg">Proposed calendar changes</h2>
                  <span className={`px-3 py-1 rounded-lg border capitalize text-xs ${statusClasses[selected.status] || ''}`}>{selected.status}</span>
                </header>
                <p className="text-xs text-dark-muted">Times shown in your device timezone. Proposals expire for approval after one hour, and stale tasks or calendar conflicts require regeneration.</p>
                <div className="space-y-2">
                  {selected.blocks.map((block, index) => (
                    <div key={block.task_id + block.starts_at + index} className="rounded-xl border p-3">
                      <p className="font-medium">{block.title}</p>
                      <p className="text-sm text-dark-muted mt-1">{local(block.starts_at)} → {local(block.ends_at)} · {block.duration_minutes} min</p>
                      {selected.status === 'pending' && (
                        <div className="mt-3 flex flex-col sm:flex-row sm:items-end gap-2">
                          <label className="block text-xs font-medium flex-1">Move session to
                            <input type="datetime-local" className="input-field mt-1"
                              value={proposedStarts[index] ?? isoToDateTimeLocal(block.starts_at)}
                              onChange={e => setProposedStarts(v => ({ ...v, [index]: e.target.value }))}/>
                          </label>
                          <button type="button" disabled={working}
                            onClick={() => moveSession(index, block)}
                            className="border rounded-lg px-3 py-2 text-sm disabled:opacity-50">
                            Update proposal
                          </button>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
                {selected.unscheduled.length > 0 && (
                  <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 space-y-2">
                    <p className="font-semibold text-sm">Work that could not be scheduled</p>
                    {selected.unscheduled.map(task => (
                      <p key={task.task_id} className="text-sm">{task.title}: {task.remaining_minutes} minutes remaining</p>
                    ))}
                  </div>
                )}
                {selected.status === 'pending' && (
                  <div className="flex flex-wrap gap-3 border-t pt-4">
                    <button type="button" disabled={working} onClick={() => run('approve', 'Approved')}
                      className="btn-primary flex items-center gap-2">
                      <CheckCircle2 className="w-4 h-4" /> Approve and save
                    </button>
                    <button type="button" disabled={working} onClick={() => run('reject', 'Rejected')}
                      className="rounded-xl border px-4 py-2 text-sm text-red-700 flex gap-2 items-center">
                      <CircleX className="w-4 h-4" /> Reject
                    </button>
                  </div>
                )}
                {selected.status === 'approved' && (
                  <div className="border-t pt-4">
                    <button type="button" disabled={working} onClick={() => run('undo', 'Undone')}
                      className="rounded-xl border px-4 py-2 text-sm flex gap-2 items-center">
                      <RotateCcw className="w-4 h-4" /> Undo this plan
                    </button>
                  </div>
                )}
                {selected.status === 'undone' && <p className="text-sm text-blue-700">This plan was undone.</p>}
                {selected.status === 'rejected' && <p className="text-sm text-dark-muted">This proposal was rejected without calendar changes.</p>}
                <Link to="/planning" className="text-sm text-peach-dark underline flex items-center gap-2">
                  <CalendarDays className="w-4 h-4" /> Compute a new preview
                </Link>
              </div>
            )}
          </section>
        </div>
      )}
    </div>
  )
}
