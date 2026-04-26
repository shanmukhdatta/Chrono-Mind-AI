import { useEffect, useRef, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Mic, Send, Trash2, Zap, BookOpen, Clock, Coffee } from 'lucide-react'
import { useChatStore, useAuthStore } from '../../store'
import { GlassCard, MagneticButton, RevealOnScroll, Spinner, CATEGORY_COLORS } from '../ui'
import toast from 'react-hot-toast'

const QUICK_PROMPTS = [
  { icon: BookOpen, text: "Schedule 2 hours of study for my exam tomorrow" },
  { icon: Clock, text: "Find free slots today for a 1-hour project session" },
  { icon: Zap, text: "Plan my entire day with AI" },
  { icon: Coffee, text: "What tasks do I have pending this week?" },
]

function TypingIndicator() {
  return (
    <motion.div
      className="flex items-end gap-2.5 mb-4"
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 10 }}
    >
      <div className="w-8 h-8 rounded-full flex items-center justify-center text-sm"
        style={{ background: 'linear-gradient(135deg, #2A9D8F, #264653)', color: 'white', fontWeight: 700, fontSize: 12 }}>
        AI
      </div>
      <div className="glass px-4 py-3 rounded-2xl rounded-bl-sm" style={{ borderRadius: '16px 16px 16px 4px' }}>
        <div className="flex items-center gap-1.5">
          {[0, 1, 2].map((i) => (
            <motion.div
              key={i}
              className="typing-dot"
              animate={{ y: [0, -5, 0] }}
              transition={{ duration: 0.6, delay: i * 0.15, repeat: Infinity }}
            />
          ))}
        </div>
      </div>
    </motion.div>
  )
}

function MessageBubble({ message }) {
  const isUser = message.role === 'user'
  const hasTasks = message.metadata?.tasks_created > 0

  return (
    <motion.div
      className={`flex items-end gap-2.5 mb-4 ${isUser ? 'flex-row-reverse' : ''}`}
      initial={{ opacity: 0, x: isUser ? 20 : -20, y: 5 }}
      animate={{ opacity: 1, x: 0, y: 0 }}
      transition={{ type: 'spring', stiffness: 400, damping: 30 }}
    >
      {/* Avatar */}
      <div
        className="w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center text-xs font-bold text-white"
        style={{
          background: isUser
            ? 'linear-gradient(135deg, #F4A261, #E76F51)'
            : 'linear-gradient(135deg, #2A9D8F, #264653)',
        }}
      >
        {isUser ? 'Me' : 'AI'}
      </div>

      {/* Bubble */}
      <div className="max-w-[75%]">
        <div
          className={`px-4 py-3 text-sm leading-relaxed ${isUser ? 'glass-strong' : 'glass'}`}
          style={{
            borderRadius: isUser ? '16px 16px 4px 16px' : '16px 16px 16px 4px',
            color: 'var(--text-1)',
            background: isUser ? 'rgba(244,162,97,0.18)' : undefined,
            border: isUser ? '1px solid rgba(244,162,97,0.3)' : undefined,
          }}
        >
          {message.content}
        </div>

        {hasTasks && (
          <motion.div
            className="mt-2 flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-xl"
            style={{ background: 'rgba(42,157,143,0.12)', color: '#2A9D8F', width: 'fit-content' }}
            initial={{ scale: 0, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay: 0.3, type: 'spring' }}
          >
            <Zap size={11} />
            {message.metadata.tasks_created} task{message.metadata.tasks_created > 1 ? 's' : ''} scheduled ✅
          </motion.div>
        )}

        <p className="text-xs mt-1 px-1" style={{ color: 'var(--text-3)' }}>
          {new Date(message.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </p>
      </div>
    </motion.div>
  )
}

function VoiceButton({ onTranscript }) {
  const [active, setActive] = useState(false)
  const recognitionRef = useRef(null)

  const start = () => {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
      toast.error('Voice input not supported in this browser')
      return
    }
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition
    const recognition = new SR()
    recognition.lang = 'en-US'
    recognition.interimResults = false
    recognition.onresult = (e) => {
      const text = e.results[0][0].transcript
      onTranscript(text)
      setActive(false)
    }
    recognition.onerror = () => setActive(false)
    recognition.onend = () => setActive(false)
    recognition.start()
    recognitionRef.current = recognition
    setActive(true)
  }

  const stop = () => {
    recognitionRef.current?.stop()
    setActive(false)
  }

  return (
    <motion.button
      className="relative w-12 h-12 rounded-2xl flex items-center justify-center flex-shrink-0"
      style={{
        background: active ? 'linear-gradient(135deg, #2A9D8F, #264653)' : 'rgba(42,157,143,0.12)',
        border: '1px solid rgba(42,157,143,0.3)',
      }}
      whileTap={{ scale: 0.9 }}
      onClick={active ? stop : start}
      animate={active ? { boxShadow: ['0 0 0px rgba(42,157,143,0)', '0 0 20px rgba(42,157,143,0.5)', '0 0 0px rgba(42,157,143,0)'] } : {}}
      transition={{ duration: 1.5, repeat: Infinity }}
    >
      {active && (
        <>
          <motion.div className="voice-ring" style={{ animationDelay: '0s' }} />
          <motion.div className="voice-ring" style={{ animationDelay: '0.5s' }} />
        </>
      )}
      <AnimatePresence mode="popLayout" initial={false}>
        {active ? (
          <motion.div
            key="waveform"
            className="flex items-center justify-center gap-[2px] h-[18px]"
            initial={{ opacity: 0, scale: 0.5 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.5 }}
          >
            {[...Array(4)].map((_, i) => (
              <motion.div
                key={i}
                className="w-[2px] bg-white rounded-full"
                animate={{ height: ['40%', '100%', '40%'] }}
                transition={{ duration: 0.6, repeat: Infinity, delay: i * 0.15, ease: 'easeInOut' }}
              />
            ))}
          </motion.div>
        ) : (
          <motion.div key="mic" initial={{ opacity: 0, scale: 0.5 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.5 }}>
            <Mic size={18} color="#2A9D8F" />
          </motion.div>
        )}
      </AnimatePresence>
    </motion.button>
  )
}

export default function AIAssistant() {
  const { messages, isTyping, sendMessage, loadHistory, clearHistory } = useChatStore()
  const { user } = useAuthStore()
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef(null)

  useEffect(() => {
    loadHistory()
  }, [])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isTyping])

  const handleSend = async (text) => {
    const msg = text || input.trim()
    if (!msg || loading) return
    setInput('')
    setLoading(true)
    await sendMessage(msg)
    setLoading(false)
  }

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend() }
  }

  return (
    <div className="flex flex-col h-screen p-6 md:p-8 pb-0">
      {/* Header */}
      <RevealOnScroll className="mb-5 flex items-center justify-between flex-shrink-0">
        <div>
          <h1 className="text-3xl font-bold" style={{ fontFamily: 'Inter', color: 'var(--text-1)' }}>
            AI Assistant
          </h1>
          <p style={{ color: 'var(--text-2)' }}>
            Your intelligent scheduling companion — type or speak
          </p>
        </div>
        <MagneticButton
          className="glass px-3 py-2 rounded-xl flex items-center gap-2 text-sm"
          onClick={() => { clearHistory(); toast.success('History cleared') }}
        >
          <Trash2 size={14} style={{ color: 'var(--text-3)' }} />
          <span style={{ color: 'var(--text-2)' }}>Clear</span>
        </MagneticButton>
      </RevealOnScroll>

      {/* Quick Prompts */}
      {messages.length === 0 && (
        <RevealOnScroll delay={0.1} className="mb-5 flex-shrink-0">
          <div className="grid grid-cols-2 gap-3">
            {QUICK_PROMPTS.map((p, i) => (
              <motion.button
                key={i}
                className="glass text-left px-4 py-3 rounded-2xl flex items-center gap-3"
                whileHover={{ scale: 1.02, y: -1 }}
                whileTap={{ scale: 0.98 }}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.07 }}
                onClick={() => handleSend(p.text)}
              >
                <div className="w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0"
                  style={{ background: 'rgba(244,162,97,0.15)' }}>
                  <p.icon size={15} style={{ color: 'var(--peach)' }} />
                </div>
                <span className="text-sm" style={{ color: 'var(--text-1)' }}>{p.text}</span>
              </motion.button>
            ))}
          </div>
        </RevealOnScroll>
      )}

      {/* Messages */}
      <GlassCard className="flex-1 overflow-y-auto p-5 mb-4" style={{ minHeight: 0 }}>
        {messages.length === 0 && (
          <div className="h-full flex flex-col items-center justify-center text-center py-12">
            <motion.div
              className="w-16 h-16 rounded-2xl flex items-center justify-center mb-4"
              style={{ background: 'linear-gradient(135deg, #2A9D8F, #264653)' }}
              animate={{ y: [0, -6, 0] }}
              transition={{ duration: 3, repeat: Infinity }}
            >
              <Zap size={28} color="white" />
            </motion.div>
            <h3 className="text-lg font-bold mb-2" style={{ fontFamily: 'Inter', color: 'var(--text-1)' }}>
              Hey {user?.name?.split(' ')[0]}, I'm ChronoMind AI ✨
            </h3>
            <p style={{ color: 'var(--text-2)' }}>
              Tell me what you need to get done — I'll find the perfect time slot for it.
            </p>
          </div>
        )}

        <AnimatePresence mode="sync">
          {messages.map((msg) => (
            <MessageBubble key={msg.id} message={msg} />
          ))}
          {isTyping && <TypingIndicator key="typing" />}
        </AnimatePresence>
        <div ref={messagesEndRef} />
      </GlassCard>

      {/* Input */}
      <div className="flex-shrink-0 pb-6">
        <div className="glass rounded-2xl flex items-end gap-3 p-3">
          <textarea
            className="flex-1 bg-transparent outline-none resize-none text-sm py-2 px-1"
            style={{ color: 'var(--text-1)', minHeight: 40, maxHeight: 120, lineHeight: 1.5 }}
            placeholder="Type a task, ask for your schedule, or speak..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKey}
            rows={1}
          />
          <VoiceButton onTranscript={(text) => { setInput(text); setTimeout(() => handleSend(text), 100) }} />
          <MagneticButton
            className="w-12 h-12 rounded-2xl flex items-center justify-center flex-shrink-0"
            style={{
              background: input.trim() ? 'linear-gradient(135deg, #F4A261, #E76F51)' : 'rgba(244,162,97,0.12)',
              border: 'none',
            }}
            onClick={() => handleSend()}
            disabled={!input.trim() || loading}
          >
            {loading ? <Spinner size={18} color="white" /> : <Send size={18} color={input.trim() ? 'white' : 'var(--text-3)'} />}
          </MagneticButton>
        </div>
        <p className="text-center text-xs mt-2" style={{ color: 'var(--text-3)' }}>
          Press Enter to send · Shift+Enter for new line · Click mic for voice
        </p>
      </div>
    </div>
  )
}
