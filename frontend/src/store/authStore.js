import { create } from 'zustand'

export const useAuthStore = create((set) => ({
  user: null,
  isLoading: true,
  isAuthenticated: false,

  setUser: (user) => set({
    user,
    isLoading: false,
    isAuthenticated: !!user,
  }),
  clearUser: () => set({
    user: null,
    isLoading: false,
    isAuthenticated: false,
  }),
  enterDemoMode: () => set({
    user: { uid: 'demo', displayName: 'Demo User', email: 'demo@chronomind.ai', photoURL: null, isDemo: true },
    isAuthenticated: true,
    isLoading: false,
  }),
  setLoading: (isLoading) => set({ isLoading }),
}))
