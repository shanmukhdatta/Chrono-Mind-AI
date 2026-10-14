import React, { useCallback, useEffect, useRef, useState } from 'react'
import { Bot, Send, Mic, MicOff, ShieldCheck, RefreshCw, Target, ListTodo } from 'lucide-react'
import { Link } from 'react-router-dom'
import toast from 'react-hot-toast'
import api from '../lib/api'
import { extractDraft, supportsSpeechRecognition } from '../lib/assistantV2'
import { useAuthStore } from '../store/authStore'

function friendlyError(error) {
  if (typeof error.response?.data?.detail === 'string') return error.response.data.detail
  if (error.response?.status === 503) return 'V2 PostgreSQL is not configured. Existing Firestore tasks are unaffected.'
  return error.message || 'The request failed'
}

const langs = [
  ['en-IN', 'English (India)'],
  ['te-IN', 'తెలుగు'],
  ['ta-IN', 'தமிழ்'],
  ['kn-IN', 'ಕನ್ನಡ'],
  ['hi-IN', 'हिन्दी'],
]

export default function AssistantV2() {
  const demo = useAuthStore(s => s.user?.uid === 'demo')
  const [message, setMessage] = useState('')
  const [history, setHistory] = useState([])
  const [briefing, setBriefing] = useState(null)
  const [listening, setListening] = useState(false)
  const [lang, setLang] = useState('en-IN')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const speechRef = useRef(null)

  const readBriefing = useCallback(async () => {
    if (demo) return
    try {
      const response = await api.get('/api/v2/assistant/briefing')
      setBriefing(response.data)
    } catch (err) {
      setError(friendlyError(err))
    }
  }, [demo])

  useEffect(() => { readBriefing() }, [readBriefing])
  useEffect(() => () => {
    if (speechRef.current) {
      speechRef.current.onresult = null
      speechRef.current.onerror = null
      speechRef.current.onend = null
      speechRef.current.abort()
    }
  }, [])

  const talk = () => {
    if (listening) {
      speechRef.current?.stop()
      setListening(false)
      return
    }
    const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!Recognition) {
      setError('Speech recognition is not available in this browser; type your request instead.')
      return
    }
    try {
      const recognition = new Recognition()
      speechRef.current = recognition
      recognition.lang = lang
      recognition.continuous = false
      recognition.interimResults = false
      recognition.onresult = event => {
        const transcript = event.results?.[0]?.[0]?.transcript || ''
        setMessage(current => [current, transcript].filter(Boolean).join(' ').slice(0, 2000))
      }
      recognition.onerror = event => {
        setError('Voice recognition error: ' + (event.error || 'unknown error'))
        setListening(false)
      }
      recognition.onend = () => setListening(false)
      recognition.start()
      setListening(true)
      setError('')
    } catch (err) {
      setError(err.message || 'Could not start speech input')
      setListening(false)
    }
  }

  const submit = async event => {
    event.preventDefault()
    const input = message.trim()
    if (input.length < 2 || busy || demo) return
    setBusy(true)
    setError('')
    setMessage('')
    try {
      const response = await api.post('/api/v2/assistant/chat', { message: input })
      const reply = response.data
      setHistory(existing => [...existing, { id: existing.length + 1, question: input, ...reply }])
    } catch (err) {
      setMessage(input)
      setError(friendlyError(err))
    } finally {
      setBusy(false)
    }
  }

  const saveDraft = async entry => {
    const draft = extractDraft(entry.decision)
    if (!draft || busy) return
    const actionLabel = draft.kind === 'task_change'
      ? draft.payload.operation + ' task ' + draft.payload.task_id
      : 'Save ' + draft.kind + ': ' + draft.payload.title
    if (!window.confirm('Confirm this ChronoMind operation?\\n\\n' + actionLabel)) return
    setBusy(true)
    setError('')
    try {
      let response
      if (draft.kind === 'task_change') {
        const { task_id, version, operation, ...changes } = draft.payload
        const url = '/api/v2/tasks/' + encodeURIComponent(task_id)
        if (operation === 'delete') {
          response = await api.delete(url)
        } else {
          const patch = operation === 'complete' ? { status: 'completed' }
            : operation === 'archive' ? { status: 'archived' } : changes
          response = await api.patch(url, { version, ...patch })
        }
        if (![200, 204].includes(response.status)) throw new Error('Task action was not confirmed')
      } else {
        const url = draft.kind === 'task' ? '/api/v2/tasks' : '/api/v2/goals'
        response = await api.post(url, draft.payload)
        if (response.status !== 201) throw new Error('Storage did not confirm creation')
      }
      setHistory(existing => existing.map(item => item.id === entry.id ? { ...item, saved: true } : item))
      toast.success(draft.kind === 'task_change' ? 'Task action saved to PostgreSQL'
        : draft.kind === 'task' ? 'Task saved to PostgreSQL' : 'Goal saved to PostgreSQL')
      await readBriefing()
    } catch (err) {
      const message = friendlyError(err)
      setError(message)
      toast.error(message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="max-w-5xl mx-auto space-y-5">
      <header>
        <p className="text-sm text-peach-dark font-semibold">Converse. Review. Confirm.</p>
        <h1 className="text-3xl font-bold text-dark">ChronoMind Assistant V2</h1>
        <p className="text-sm text-dark-muted mt-2">
          Understand requests and prepare safe drafts. Nothing is saved without your confirmation.
        </p>
      </header>
      {demo && (
        <div className="bg-white border rounded-xl p-4">
          This assistant uses your actual saved tasks and goals. Sign in with Google; demo mode does not invent persisted results.
        </div>
      )}
      {!demo && briefing && (
        <section className="bg-white border rounded-2xl p-5 space-y-3">
          <div className="flex justify-between gap-2 items-center">
            <h2 className="font-semibold flex gap-2"><Target className="w-5 h-5 text-peach" /> Daily briefing</h2>
            <button type="button" onClick={readBriefing} aria-label="Refresh briefing" className="p-2 hover:bg-gray-50 rounded-lg">
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
          <p className="text-sm text-dark-muted">{briefing.today} · {briefing.timezone}</p>
          <div className="flex gap-5 flex-wrap">
            <p className="text-sm"><span className="font-bold text-lg">{briefing.pending_count}</span> pending tasks</p>
            <p className="text-sm"><span className="font-bold text-lg">{briefing.overdue_count}</span> overdue</p>
            <p className="text-sm"><span className="font-bold text-lg">{briefing.upcoming_deadlines.length}</span> deadlines in 7 days</p>
          </div>
          {briefing.upcoming_deadlines.map((task,index) => (
            <p key={index} className="text-sm border-t pt-2">
              {task.title} · {new Date(task.deadline_at).toLocaleDateString()}
            </p>
          ))}
        </section>
      )}
      {error && <div role="alert" className="p-4 border border-red-200 rounded-xl bg-red-50 text-red-800 text-sm">{error}</div>}
      {!demo && (
        <section className="bg-white border rounded-2xl p-5 space-y-5">
          <div className="flex gap-2 items-center">
            <Bot className="w-5 h-5 text-peach" />
            <h2 className="font-semibold">Conversation</h2>
          </div>
          {history.length === 0 && <p className="text-sm text-dark-muted">
            Try “Create a 45-minute Python revision task”, “Set a goal to prepare for placements”, or “What tasks are pending?”
          </p>}
          {history.map(entry => (
            <div key={entry.id} className="border-t pt-4 space-y-3">
              <div className="bg-peach/10 rounded-xl px-4 py-3 text-sm"><strong>You:</strong> {entry.question}</div>
              <div className="bg-gray-50 rounded-xl px-4 py-3 text-sm">
                <strong>ChronoMind:</strong> {entry.decision?.message}
                {entry.mode === 'fallback' && <p className="text-xs text-amber-700 mt-2">AI provider unavailable — deterministic fallback used.</p>}
              </div>
              {extractDraft(entry.decision) && (
                <div className="rounded-xl border border-peach/40 p-4 space-y-2">
                  <p className="text-xs uppercase font-semibold text-peach-dark flex gap-2 items-center">
                    <ShieldCheck className="w-4 h-4" /> Awaiting your confirmation
                  </p>
                  <p className="font-semibold">{extractDraft(entry.decision).payload.title ||
                    (extractDraft(entry.decision).payload.operation + ' task ' + extractDraft(entry.decision).payload.task_id)}</p>
                  {extractDraft(entry.decision).kind === 'task' && (
                    <p className="text-sm text-dark-muted">{extractDraft(entry.decision).payload.duration_minutes} minutes</p>
                  )}
                  {entry.saved ? <p className="text-green-700 text-sm">Saved successfully.</p> : (
                    <button type="button" disabled={busy} onClick={() => saveDraft(entry)} className="btn-primary text-sm">
                      Confirm {extractDraft(entry.decision).kind === 'task_change'
                        ? extractDraft(entry.decision).payload.operation + ' task'
                        : 'save ' + extractDraft(entry.decision).kind}
                    </button>
                  )}
                </div>
              )}
            </div>
          ))}
          <form onSubmit={submit} className="space-y-3 pt-3 border-t">
            <label className="block text-sm font-semibold">Your request
              <textarea rows={3} className="input-field mt-2" value={message}
                maxLength={2000} minLength={2} required
                onChange={e => setMessage(e.target.value)} placeholder="What would you like to plan?" />
            </label>
            <div className="flex flex-col sm:flex-row gap-2 sm:items-end justify-between">
              <div className="flex items-center gap-2">
                <select aria-label="Voice language" value={lang} onChange={e => setLang(e.target.value)}
                  className="input-field text-sm max-w-40">
                  {langs.map(([value,label]) => <option key={value} value={value}>{label}</option>)}
                </select>
                <button type="button" aria-label={listening ? 'Stop recording' : 'Speak a request'}
                  onClick={talk} className="p-3 border rounded-xl hover:bg-gray-50">
                  {listening ? <MicOff className="w-5 h-5 text-red-600" /> : <Mic className="w-5 h-5" />}
                </button>
              </div>
              <button type="submit" disabled={busy || message.trim().length < 2}
                className="btn-primary flex items-center justify-center gap-2">
                <Send className="w-4 h-4" /> {busy ? 'Processing...' : 'Send request'}
              </button>
            </div>
            <p className="text-xs text-dark-muted">
              Voice recognition depends on your browser and microphone permissions. Supported languages vary by device.
            </p>
          </form>
        </section>
      )}
      <div className="flex gap-4 text-sm text-peach-dark">
        <Link className="underline" to="/goals"><Target className="w-4 h-4 inline mr-1" /> View goals</Link>
        <Link className="underline" to="/planning"><ListTodo className="w-4 h-4 inline mr-1" /> Plan your time</Link>
      </div>
    </div>
  )
}
