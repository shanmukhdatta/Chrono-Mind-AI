import React, { useState, useRef, useEffect } from 'react'
import { X, Send, Sparkles, CheckCircle2, Circle, Calendar } from 'lucide-react'
import { useAssistantStore } from '../store/assistantStore'
import { useAssistant } from '../hooks/useAssistant'
import { useTaskStore } from '../store/taskStore'
import { VoiceButton } from './VoiceButton'
import { TaskActionCard } from './TaskActionCard'
import { Spinner } from './ui/Spinner'
import { format } from 'date-fns'

function TasksListResult({ result }) {
  if (!result || !result.tasks) return null
  const { tasks, filter, date } = result
  return (
    <div className="mt-2 bg-gray-50 border border-gray-200 rounded-xl p-3 space-y-1.5">
      <p className="text-[10px] font-bold text-dark-muted uppercase tracking-wide">
        {filter === 'completed' ? '✅ Completed' : filter === 'incomplete' ? '⏳ Pending' : '📋 All'} Tasks
        {date ? ` · ${date}` : ''}
      </p>
      {tasks.length === 0 ? (
        <p className="text-sm text-dark-muted py-1">No tasks found.</p>
      ) : tasks.slice(0, 8).map((t, i) => (
        <div key={i} className="flex items-start gap-2 text-sm">
          {t.completed
            ? <CheckCircle2 className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
            : <Circle className="w-4 h-4 text-gray-400 mt-0.5 flex-shrink-0" />
          }
          <div className="min-w-0">
            <p className={`font-medium truncate ${t.completed ? 'line-through text-dark-muted' : 'text-dark'}`}>{t.title}</p>
            <p className="text-xs text-dark-muted">{t.date} · {t.start_time}–{t.end_time}</p>
          </div>
        </div>
      ))}
      {tasks.length > 8 && <p className="text-xs text-dark-muted">+{tasks.length - 8} more</p>}
    </div>
  )
}

const SUGGESTIONS = [
  'Schedule DSA practice for 1 hour from now',
  'What tasks did I not finish today?',
  'Remind me to revise every evening at 7 PM',
  'Schedule fluid mechanics for tomorrow 10 AM',
]

export function AssistantPanel() {
  const { messages, isOpen, setOpen, isLoading } = useAssistantStore()
  const { sendMessage, executeAction } = useAssistant()
  const { addTask } = useTaskStore()
  const [input, setInput] = useState('')
  const [actionResults, setActionResults] = useState({})
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  useEffect(() => {
    if (isOpen) setTimeout(() => inputRef.current?.focus(), 150)
  }, [isOpen])

  const handleSend = async (text) => {
    const msg = (text || input).trim()
    if (!msg || isLoading) return
    setInput('')

    const userMsg = { role: 'user', content: msg, timestamp: new Date().toISOString() }
    useAssistantStore.getState().addMessage(userMsg)

    const currentMessages = useAssistantStore.getState().messages
    const { action, action_result } = await sendMessage(msg, currentMessages)

    if (action_result) {
      const result = await executeAction(action, action_result)
      if (result) {
        const newLen = useAssistantStore.getState().messages.length
        setActionResults(prev => ({ ...prev, [newLen - 1]: result }))
      }
    }
  }

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend() }
  }

  if (!isOpen) {
    return (
      <button
        onClick={() => setOpen(true)}
        className="fixed bottom-6 right-6 z-40 p-4 bg-peach text-white rounded-full shadow-peach hover:bg-peach-dark transition-all hover:scale-105 active:scale-95"
        aria-label="Open AI Assistant"
      >
        <Sparkles className="w-6 h-6" />
      </button>
    )
  }

  return (
    <>
      <div className="fixed inset-0 bg-dark/20 backdrop-blur-sm z-40 md:hidden" onClick={() => setOpen(false)} />
      <div className="fixed right-0 top-0 h-full w-full md:w-[420px] bg-white/95 backdrop-blur-xl border-l border-gray-100 shadow-2xl z-50 flex flex-col animate-slide-in">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-gray-100 flex-shrink-0">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-peach/15 rounded-xl">
              <Sparkles className="w-5 h-5 text-peach-dark" />
            </div>
            <div>
              <h2 className="font-semibold text-dark">ChronoMind Assistant</h2>
              <p className="text-xs text-dark-muted">Schedule · Query · Plan</p>
            </div>
          </div>
          <button onClick={() => setOpen(false)} className="p-2 rounded-xl hover:bg-gray-100 transition-colors">
            <X className="w-5 h-5 text-dark-muted" />
          </button>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-5 space-y-4">
          {messages.length === 0 && (
            <div className="text-center py-4">
              <div className="w-14 h-14 bg-peach/10 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <Sparkles className="w-7 h-7 text-peach" />
              </div>
              <h3 className="font-semibold text-dark mb-3 text-sm">Try saying something like…</h3>
              <div className="space-y-2">
                {SUGGESTIONS.map((s, i) => (
                  <button key={i} onClick={() => handleSend(s)}
                    className="w-full text-left bg-gray-50 rounded-xl p-3 text-sm text-dark-muted hover:bg-peach/10 hover:text-dark-muted border border-transparent hover:border-peach/20 transition-all"
                  >
                    "{s}"
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg, idx) => (
            <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className="max-w-[88%]">
                <div className={`p-3.5 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap ${
                  msg.role === 'user'
                    ? 'bg-peach text-white rounded-br-md'
                    : 'bg-gray-50 text-dark border border-gray-100 rounded-bl-md'
                }`}>
                  {msg.content}
                </div>
                {/* Task created */}
                {msg.role === 'assistant' && actionResults[idx]?.task_id && (
                  <TaskActionCard task={actionResults[idx]} />
                )}
                {/* Tasks list */}
                {msg.role === 'assistant' && actionResults[idx]?.tasks && (
                  <TasksListResult result={actionResults[idx]} />
                )}
                <p className="text-[10px] text-dark-muted mt-1 px-1">
                  {msg.timestamp ? format(new Date(msg.timestamp), 'HH:mm') : ''}
                </p>
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-gray-50 border border-gray-100 rounded-2xl rounded-bl-md p-4 flex items-center gap-2">
                <Spinner size="sm" />
                <span className="text-sm text-dark-muted">Thinking…</span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="p-4 border-t border-gray-100 bg-white/80 backdrop-blur-sm flex-shrink-0">
          <div className="flex items-center gap-2">
            <VoiceButton onTranscript={(t) => handleSend(t)} />
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKey}
              placeholder="Schedule something or ask about tasks…"
              maxLength={500}
              className="flex-1 px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-peach/30 focus:border-peach text-sm"
            />
            <button
              onClick={() => handleSend()}
              disabled={!input.trim() || isLoading}
              className="p-3 bg-peach text-white rounded-xl hover:bg-peach-dark transition-all disabled:opacity-40 disabled:cursor-not-allowed active:scale-95"
            >
              <Send className="w-5 h-5" />
            </button>
          </div>
          <p className="text-[10px] text-dark-muted text-center mt-2 select-none">
            Scheduling assistant only · Not a general chatbot
          </p>
        </div>
      </div>
    </>
  )
}
