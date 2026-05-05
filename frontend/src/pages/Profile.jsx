import React, { useEffect, useState } from 'react'
import { User, Flame, CheckCircle2, RefreshCw, LogOut, Trash2, AlertTriangle } from 'lucide-react'
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
  const [loading, setLoading] = useState(true)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const res = await api.get('/api/tasks/stats')
        if (res.data.success) setStats(res.data.data)
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

      {/* Stats */}
      <div>
        <h3 className="font-semibold text-dark mb-3">Your Stats</h3>
        {loading ? (
          <div className="flex justify-center py-10"><Spinner size="lg" /></div>
        ) : (
          <div className="grid grid-cols-2 gap-4">
            {statCards.map((s, i) => (
              <div key={i} className="bg-white rounded-xl border border-gray-100 p-5 shadow-sm">
                <s.icon className={`w-6 h-6 ${s.color} mb-2`} />
                <p className="text-3xl font-bold text-dark">{s.value}</p>
                <p className="text-sm text-dark-muted mt-1">{s.label}</p>
              </div>
            ))}
            {stats && (
              <div className="col-span-2 bg-white rounded-xl border border-gray-100 p-5 shadow-sm">
                <div className="flex items-center justify-between mb-2">
                  <p className="text-sm font-medium text-dark">Completion Rate</p>
                  <p className="text-lg font-bold text-peach-dark">{stats.completion_rate}%</p>
                </div>
                <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-peach rounded-full transition-all duration-700"
                    style={{ width: `${stats.completion_rate}%` }}
                  />
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* App Info */}
      <div className="bg-white rounded-2xl border border-gray-100 p-5 shadow-sm space-y-3">
        <h3 className="font-semibold text-dark">About ChronoMind AI</h3>
        <div className="space-y-2 text-sm text-dark-muted">
          <p>🤖 AI Engine: Groq LLaMA 3.3-70B</p>
          <p>🧠 Agent: LangGraph 7-node rescheduling graph</p>
          <p>⚡ Backend: FastAPI + Firebase Firestore</p>
          <p>🔔 Nightly auto-reschedule: 23:55 IST</p>
          <p>🛠 Built by Datta · Nerds Room · NIT Jalandhar</p>
        </div>
      </div>

      {/* Actions */}
      <div className="space-y-3">
        <Button variant="outline" onClick={handleSignOut} className="w-full">
          <LogOut className="w-4 h-4 mr-2" /> Sign Out
        </Button>

        {!showDeleteConfirm ? (
          <button
            onClick={() => setShowDeleteConfirm(true)}
            className="w-full text-red-400 text-sm hover:text-red-600 transition-colors py-2"
          >
            Delete all my data
          </button>
        ) : (
          <div className="bg-red-50 border border-red-200 rounded-xl p-4 space-y-3">
            <div className="flex items-start gap-2">
              <AlertTriangle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-red-700">This will permanently delete all your tasks and data. This cannot be undone.</p>
            </div>
            <div className="flex gap-2">
              <button onClick={() => setShowDeleteConfirm(false)} className="flex-1 py-2 bg-gray-100 rounded-xl text-sm font-medium text-dark">Cancel</button>
              <button
                onClick={async () => {
                  try {
                    await api.delete('/api/profile/data')
                    await handleSignOut()
                  } catch (e) {
                    console.error(e)
                  }
                }}
                className="flex-1 py-2 bg-red-500 text-white rounded-xl text-sm font-medium hover:bg-red-600"
              >
                <Trash2 className="w-4 h-4 inline mr-1" /> Yes, Delete All
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
