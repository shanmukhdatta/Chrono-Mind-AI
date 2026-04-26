import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import api, { isDemoMode } from './api'
import { format } from 'date-fns'

// ─── Demo Data ────────────────────────────────────────────────────
const today = format(new Date(), 'yyyy-MM-dd')

const DEMO_TASKS = [
  { id: 'd1', title: 'DSA Practice — Arrays & Hashing', category: 'study', status: 'completed', scheduled_date: today, start_time: '08:00', end_time: '09:30', ai_placed: true },
  { id: 'd2', title: 'Linear Algebra Assignment', category: 'assignment', status: 'pending', scheduled_date: today, start_time: '10:00', end_time: '11:30', ai_placed: true },
  { id: 'd3', title: 'Gym + Cardio', category: 'health', status: 'pending', scheduled_date: today, start_time: '17:00', end_time: '18:00', ai_placed: false },
  { id: 'd4', title: 'DBMS Lecture Notes Review', category: 'study', status: 'pending', scheduled_date: today, start_time: '14:00', end_time: '15:30', ai_placed: true },
  { id: 'd5', title: 'Project Group Call', category: 'project', status: 'completed', scheduled_date: today, start_time: '11:30', end_time: '12:00', ai_placed: false },
  { id: 'd6', title: 'Read 30 pages — System Design', category: 'reading', status: 'pending', scheduled_date: today, start_time: '20:00', end_time: '21:00', ai_placed: true },
]

const DEMO_STATS = {
  slots_found_this_week: 23,
  tasks_ai_scheduled: 18,
  completion_rate: 76,
  streak_days: 5,
}

const DEMO_CALENDAR = {
  timetable: [
    { id: 'c1', subject: 'Data Structures', start_time: '09:30', end_time: '10:30', color: '#2A9D8F' },
    { id: 'c2', subject: 'Operating Systems', start_time: '11:00', end_time: '12:00', color: '#E76F51' },
    { id: 'c3', subject: 'DBMS Lab', start_time: '14:00', end_time: '16:00', color: '#E9C46A' },
  ],
  tasks: DEMO_TASKS,
  free_slots: ['06:00-08:00', '12:00-14:00', '16:00-17:00', '18:00-20:00'],
}

const DEMO_AI_RESPONSES = [
  "I found a great 2-hour slot for your DSA practice between 8:00 AM and 10:00 AM, right before your Data Structures lecture. I've scheduled it! ✅",
  "Looking at your schedule, you have 4 free slots today totaling 6 hours. The best blocks are 12 PM–2 PM and 6 PM–8 PM. Want me to fill them?",
  "Done! I've placed your study session for Linear Algebra at 10:00 AM. It's a 90-minute block that fits perfectly between your classes. 📚",
  "This week you've completed 76% of your tasks — that's up 12% from last week! Your most productive time has been mornings between 8–11 AM. 🔥",
  "I've analyzed your timetable and found 23 free slots this week. Your longest uninterrupted block is Wednesday 2 PM–6 PM. Great for deep work!",
]

// ─── Auth Store ───────────────────────────────────────────────────
export const useAuthStore = create(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isAuthenticated: false,

      setAuth: (user, token) => {
        api.defaults.headers.common['Authorization'] = `Bearer ${token}`
        set({ user, token, isAuthenticated: true })
      },

      updateUser: (updates) => set((s) => ({ user: { ...s.user, ...updates } })),

      logout: () => {
        delete api.defaults.headers.common['Authorization']
        set({ user: null, token: null, isAuthenticated: false })
      },

      rehydrateAuth: () => {
        const { token } = get()
        if (token) {
          api.defaults.headers.common['Authorization'] = `Bearer ${token}`
        }
      },
    }),
    {
      name: 'chronomind-auth',
      partialize: (s) => ({ user: s.user, token: s.token, isAuthenticated: s.isAuthenticated }),
    }
  )
)

// ─── Tasks Store ──────────────────────────────────────────────────
export const useTaskStore = create((set, get) => ({
  tasks: [],
  loading: false,

  fetchTasks: async (dateStr) => {
    if (isDemoMode()) {
      set({ tasks: DEMO_TASKS })
      return
    }
    set({ loading: true })
    try {
      const params = dateStr ? { date_str: dateStr } : {}
      const { data } = await api.get('/tasks/', { params })
      set({ tasks: data })
    } catch (e) {
      console.error('fetchTasks', e)
    } finally {
      set({ loading: false })
    }
  },

  addTask: (task) => set((s) => ({ tasks: [task, ...s.tasks] })),

  updateTask: (id, updates) =>
    set((s) => ({ tasks: s.tasks.map((t) => (t.id === id ? { ...t, ...updates } : t)) })),

  removeTask: (id) => set((s) => ({ tasks: s.tasks.filter((t) => t.id !== id) })),

  completeTask: async (id) => {
    if (isDemoMode()) {
      get().updateTask(id, { status: 'completed' })
      return { status: 'completed' }
    }
    try {
      const { data } = await api.patch(`/tasks/${id}`, { status: 'completed' })
      get().updateTask(id, data)
      return data
    } catch (e) {
      console.error('completeTask', e)
    }
  },
}))

// ─── Calendar Store ───────────────────────────────────────────────
export const useCalendarStore = create((set) => ({
  selectedDate: new Date().toISOString().split('T')[0],
  calendarData: null,
  loading: false,

  setSelectedDate: (date) => set({ selectedDate: date }),
  addCalendarTask: (task) =>
    set((s) => ({
      calendarData: {
        ...(s.calendarData || DEMO_CALENDAR),
        tasks: [task, ...((s.calendarData || DEMO_CALENDAR).tasks || [])],
      },
    })),
  removeCalendarTask: (id) =>
    set((s) => ({
      calendarData: s.calendarData
        ? { ...s.calendarData, tasks: s.calendarData.tasks.filter((t) => t.id !== id) }
        : s.calendarData,
    })),

  fetchCalendarDay: async (dateStr) => {
    if (isDemoMode()) {
      set({
        calendarData: {
          ...DEMO_CALENDAR,
          tasks: DEMO_TASKS.filter((task) => task.scheduled_date === dateStr),
        },
        loading: false,
      })
      return
    }
    set({ loading: true })
    try {
      const { data } = await api.get(`/dashboard/calendar/${dateStr}`)
      set({ calendarData: data })
    } catch (e) {
      console.error('fetchCalendarDay', e)
    } finally {
      set({ loading: false })
    }
  },
}))

// ─── Chat Store ───────────────────────────────────────────────────
export const useChatStore = create((set, get) => ({
  messages: [],
  loading: false,
  isTyping: false,

  loadHistory: async () => {
    if (isDemoMode()) return // no history to load in demo
    try {
      const { data } = await api.get('/ai/history')
      set({ messages: data })
    } catch (e) {
      console.error('loadHistory', e)
    }
  },

  sendMessage: async (content) => {
    const userMsg = {
      id: `tmp-${Date.now()}`,
      role: 'user',
      content,
      created_at: new Date().toISOString(),
    }
    set((s) => ({ messages: [...s.messages, userMsg], isTyping: true }))

    if (isDemoMode()) {
      // Simulate AI thinking delay
      await new Promise((r) => setTimeout(r, 1200 + Math.random() * 800))
      const reply = DEMO_AI_RESPONSES[Math.floor(Math.random() * DEMO_AI_RESPONSES.length)]
      const aiMsg = {
        id: `ai-${Date.now()}`,
        role: 'assistant',
        content: reply,
        metadata: { tasks_created: Math.random() > 0.5 ? 1 : 0 },
        created_at: new Date().toISOString(),
      }
      set((s) => ({ messages: [...s.messages, aiMsg], isTyping: false }))
      return { message: reply }
    }

    try {
      const { data } = await api.post('/ai/chat', { content })
      const aiMsg = {
        id: `ai-${Date.now()}`,
        role: 'assistant',
        content: data.message,
        metadata: data,
        created_at: new Date().toISOString(),
      }
      set((s) => ({ messages: [...s.messages, aiMsg], isTyping: false }))
      return data
    } catch (e) {
      console.error('sendMessage', e)
      set((s) => ({
        messages: [
          ...s.messages,
          {
            id: `err-${Date.now()}`,
            role: 'assistant',
            content: "I'm having trouble connecting right now. Please try again.",
            created_at: new Date().toISOString(),
          },
        ],
        isTyping: false,
      }))
    }
  },

  clearHistory: async () => {
    if (!isDemoMode()) {
      try { await api.delete('/ai/history') } catch {}
    }
    set({ messages: [] })
  },
}))

// ─── Dashboard Store ──────────────────────────────────────────────
export const useDashboardStore = create((set) => ({
  stats: null,
  loading: false,

  fetchStats: async () => {
    if (isDemoMode()) {
      set({ stats: DEMO_STATS, loading: false })
      return
    }
    set({ loading: true })
    try {
      const { data } = await api.get('/dashboard/stats')
      set({ stats: data })
    } catch (e) {
      console.error('fetchStats', e)
    } finally {
      set({ loading: false })
    }
  },
}))
