import React, { useEffect, useState } from 'react'
import { User, Flame, CheckCircle2, RefreshCw, LogOut, Trash2, AlertTriangle, Download } from 'lucide-react'
import { useAuthStore } from '../store/authStore'
import { useAuth } from '../hooks/useAuth'
import { useNavigate } from 'react-router-dom'
import { Spinner } from '../components/ui/Spinner'
import { Button } from '../components/ui/Button'
import api from '../lib/api'

export default function Profile() {
  const { user } = useAuthStore()
  const { signOutUser } = useAuth()
  const navigate = useNavigate()
  const [stats, setStats] = useState(null)
  const [v2Stats, setV2Stats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [showV2DeleteConfirm, setShowV2DeleteConfirm] = useState(false)
  const [exporting, setExporting] = useState(false)
  const [exportError, setExportError] = useState('')
  const [actionError, setActionError] = useState('')

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const [legacyRes, v2Res] = await Promise.allSettled([
          api.get('/api/tasks/stats'),
          api.get('/api/v2/dashboard'),
        ])
        if (legacyRes.status === 'fulfilled' && legacyRes.value?.data?.success) {
          setStats(legacyRes.value.data.data)
        }
        if (v2Res.status === 'fulfilled' && v2Res.value?.data) {
          setV2Stats(v2Res.value.data)
        }
      } catch (e) {
        console.error('Stats fetch error:', e)
      } finally {
        setLoading(false)
      }
    }
    fetchStats()
  }, [])

  const handleSignOut = async () => {
    await signOutUser()
    navigate('/')
  }

  const handleV2Purge = async () => {
    try {
      setActionError('')
      const response = await api.delete('/api/v2/account')
      if (response.data?.status !== 'complete') {
        setActionError(
          'V2 PostgreSQL records were purged, but complete account erasure was NOT confirmed. ' +
          (response.data?.remaining_scope || []).join('; ') +
          '. Your Firebase login remains active; contact the deployment administrator for remaining cleanup.'
        )
        setShowV2DeleteConfirm(false)
        return
      }
      await handleSignOut()
    } catch (err) {
      setActionError(err.response?.data?.detail || err.message || 'Failed to purge account data')
    }
  }

  const handleV2Export = async () => {
    if (user?.uid === 'demo') {
      setExportError('Sign in to export real PostgreSQL data.')
      return
    }
    setExporting(true)
    setExportError('')
    try {
      const response = await api.get('/api/v2/account/export', { responseType: 'blob' })
      const blob = new Blob([response.data], { type: 'application/json' })
      const downloadUrl = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = downloadUrl
      link.download = 'chronomind-v2-postgres-export.json'
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.setTimeout(() => URL.revokeObjectURL(downloadUrl), 1500)
    } catch (error) {
      setExportError('Export could not be downloaded. Please verify your V2 database configuration and sign-in.')
    } finally {
      setExporting(false)
    }
  }

  const statCards = stats ? [
    { label: 'Tasks Created', value: stats.total_created, icon: CheckCircle2, color: 'text-peach' },
    { label: 'Completed', value: stats.completed, icon: CheckCircle2, color: 'text-green-500' },
    { label: 'Rescheduled', value: stats.rescheduled, icon: RefreshCw, color: 'text-blue-500' },
    { label: 'Day Streak 🔥', value: stats.current_streak, icon: Flame, color: 'text-orange-500' },
  ] : []

  return (
    <div className="max-w-2xl space-y-6">
      {/* Profile Card */}
      <div className="bg-white rounded-2xl border border-gray-100 p-6 flex items-center gap-5 shadow-sm">
        <img
          src={user?.photoURL || `https://ui-avatars.com/api/?name=${encodeURIComponent(user?.displayName || 'U')}&background=E8A87C&color=fff&size=128`}
          alt="Profile"
          className="w-20 h-20 rounded-2xl object-cover border-2 border-peach/30"
        />
        <div className="flex-1 min-w-0">
          <h2 className="text-xl font-bold text-dark truncate">{user?.displayName || 'User'}</h2>
          <p className="text-dark-muted text-sm truncate">{user?.email}</p>
          <p className="text-xs text-dark-muted mt-1">Member since {user?.metadata?.creationTime ? new Date(user.metadata.creationTime).toLocaleDateString('en-IN', { month: 'long', year: 'numeric' }) : '—'}</p>
          <div className="mt-2 inline-flex items-center gap-1.5 bg-peach/10 text-peach-dark text-xs font-medium px-3 py-1 rounded-full">
            <User className="w-3 h-3" /> ChronoMind AI User
          </div>
        </div>
      </div>

      {/* V2 PostgreSQL Stats */}
      <div>
        <h3 className="font-semibold text-dark mb-3">ChronoMind V2 PostgreSQL Live Stats</h3>
        {loading ? (
          <div className="flex justify-center py-6"><Spinner size="md" /></div>
        ) : v2Stats ? (
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            <div className="bg-white rounded-xl border border-gray-100 p-4 shadow-sm">
              <CheckCircle2 className="w-5 h-5 text-peach mb-1" />
              <p className="text-2xl font-bold text-dark">{v2Stats.pending_count}</p>
              <p className="text-xs text-dark-muted">Pending Tasks</p>
            </div>
            <div className="bg-white rounded-xl border border-gray-100 p-4 shadow-sm">
              <CheckCircle2 className="w-5 h-5 text-green-500 mb-1" />
              <p className="text-2xl font-bold text-dark">{v2Stats.completed_count}</p>
              <p className="text-xs text-dark-muted">Completed Tasks</p>
            </div>
            <div className="bg-white rounded-xl border border-gray-100 p-4 shadow-sm">
              <RefreshCw className="w-5 h-5 text-blue-500 mb-1" />
              <p className="text-2xl font-bold text-dark">{v2Stats.active_goals}</p>
              <p className="text-xs text-dark-muted">Active Goals</p>
            </div>
            <div className="bg-white rounded-xl border border-gray-100 p-4 shadow-sm">
              <AlertTriangle className="w-5 h-5 text-red-500 mb-1" />
              <p className="text-2xl font-bold text-dark">{v2Stats.overdue_count}</p>
              <p className="text-xs text-dark-muted">Overdue Tasks</p>
            </div>
            <div className="bg-white rounded-xl border border-gray-100 p-4 shadow-sm">
              <Flame className="w-5 h-5 text-orange-500 mb-1" />
              <p className="text-2xl font-bold text-dark">{v2Stats.scheduled_minutes_today}m</p>
              <p className="text-xs text-dark-muted">Scheduled Today</p>
            </div>
            <div className="bg-white rounded-xl border border-gray-100 p-4 shadow-sm">
              <div className="flex justify-between items-center mb-1">
                <span className="text-xs text-dark-muted">Completion</span>
                <span className="text-xs font-bold text-peach-dark">{v2Stats.completion_rate}%</span>
              </div>
              <div className="h-2 bg-gray-100 rounded-full overflow-hidden mt-2">
                <div className="h-full bg-peach rounded-full" style={{ width: `${v2Stats.completion_rate}%` }} />
              </div>
            </div>
          </div>
        ) : (
          <p className="text-sm text-dark-muted">V2 database statistics unavailable.</p>
        )}
      </div>

      {/* Legacy Stats */}
      {stats && (
        <div>
          <h3 className="font-semibold text-dark mb-3">Legacy Firestore Stats (V1)</h3>
          <div className="grid grid-cols-2 gap-4">
            {statCards.map((s, i) => (
              <div key={i} className="bg-white rounded-xl border border-gray-100 p-5 shadow-sm">
                <s.icon className={`w-6 h-6 ${s.color} mb-2`} />
                <p className="text-3xl font-bold text-dark">{s.value}</p>
                <p className="text-sm text-dark-muted mt-1">{s.label}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* App Info */}
      <div className="bg-white rounded-2xl border border-gray-100 p-5 shadow-sm space-y-3">
        <h3 className="font-semibold text-dark">About ChronoMind AI V2</h3>
        <div className="space-y-2 text-sm text-dark-muted">
          <p>🤖 AI Engine: Groq LLaMA 3.3-70B & deterministic fallback</p>
          <p>🧠 Architecture: LangGraph resilient state machine with PostgreSQL checkpointing</p>
          <p>⚡ Storage: PostgreSQL 16 (18 tables) + Firebase Authentication</p>
          <p>📅 Scheduling: Constraint-aware deterministic solver with human approvals</p>
          <p>🛠 Built by Datta · Nerds Room · NIT Jalandhar</p>
        </div>
      </div>

      {/* Actions */}
      <div className="space-y-3">
        <Button variant="outline" onClick={handleSignOut} className="w-full">
          <LogOut className="w-4 h-4 mr-2" /> Sign Out
        </Button>

        <div className="rounded-xl border border-gray-100 p-4 bg-white space-y-2">
          <p className="font-semibold text-sm">Your V2 PostgreSQL data</p>
          <p className="text-xs text-dark-muted">Download an authenticated JSON export of V2 application records (tasks, goals, preferences, recurring series, schedule blocks, proposals, decisions, notifications).</p>
          <button type="button" disabled={exporting || user?.uid === 'demo'} onClick={handleV2Export}
            className="px-4 py-2 text-sm border rounded-xl flex items-center gap-2 disabled:opacity-50 hover:bg-gray-50">
            <Download className="w-4 h-4" />
            {exporting ? 'Preparing export...' : 'Export V2 PostgreSQL data'}
          </button>
          {exportError && <p role="alert" className="text-sm text-red-700">{exportError}</p>}
        </div>

        {actionError && <p role="alert" className="text-sm text-red-700">{actionError}</p>}

        {/* Danger Zone: best-effort application data purge; not Firebase account deletion */}
        <div className="rounded-xl border border-red-200 p-4 bg-red-50/50 space-y-3">
          <h4 className="text-sm font-bold text-red-900 flex items-center gap-1.5">
            <AlertTriangle className="w-4 h-4 text-red-600" /> Account Privacy & Data Erasure
          </h4>
          <p className="text-xs text-red-700">
            Purge your V2 PostgreSQL data and attempt cleanup of legacy Firestore and agent checkpoints. Firebase Authentication account deletion is not included. Results may be partial.
          </p>

          {!showV2DeleteConfirm ? (
            <button
              onClick={() => setShowV2DeleteConfirm(true)}
              disabled={user?.uid === 'demo'}
              className="text-xs font-semibold text-red-600 hover:text-red-800 underline"
            >
              Purge V2 app data (external cleanup is best-effort)
            </button>
          ) : (
            <div className="p-3 bg-red-100/70 border border-red-300 rounded-lg space-y-2">
              <p className="text-xs text-red-800 font-semibold">Are you sure? This irreversibly purges your V2 PostgreSQL records. External cleanup may remain incomplete; export your data first.</p>
              <div className="flex gap-2">
                <button onClick={() => setShowV2DeleteConfirm(false)} className="px-3 py-1.5 bg-white text-xs rounded border text-dark font-medium">Cancel</button>
                <button onClick={handleV2Purge} className="px-3 py-1.5 bg-red-600 hover:bg-red-700 text-white text-xs rounded font-medium flex items-center gap-1">
                  <Trash2 className="w-3.5 h-3.5" /> Confirm V2 Data Purge
                </button>
              </div>
            </div>
          )}

          <div className="pt-2 border-t border-red-100">
            {!showDeleteConfirm ? (
              <button
                onClick={() => setShowDeleteConfirm(true)}
                disabled={user?.uid === 'demo'}
                className="text-xs text-gray-500 hover:text-gray-700 underline"
              >
                Delete legacy Firestore tasks only
              </button>
            ) : (
              <div className="p-2 bg-gray-100 rounded space-y-2 mt-1">
                <p className="text-xs text-gray-600">Delete legacy Firestore tasks only. V2 PostgreSQL records remain intact.</p>
                <div className="flex gap-2">
                  <button onClick={() => setShowDeleteConfirm(false)} className="px-2 py-1 bg-white text-xs rounded border">Cancel</button>
                  <button
                    onClick={async () => {
                      try {
                        await api.delete('/api/profile/data')
                        await handleSignOut()
                      } catch (e) {
                        console.error(e)
                      }
                    }}
                    className="px-2 py-1 bg-red-500 text-white text-xs rounded"
                  >
                    Confirm Legacy Deletion
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

