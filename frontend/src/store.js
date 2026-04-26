import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import api from './api'

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

  fetchCalendarDay: async (dateStr) => {
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
    await api.delete('/ai/history')
    set({ messages: [] })
  },
}))

// ─── Dashboard Store ──────────────────────────────────────────────
export const useDashboardStore = create((set) => ({
  stats: null,
  loading: false,

  fetchStats: async () => {
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
