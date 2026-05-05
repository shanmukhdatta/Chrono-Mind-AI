import { create } from 'zustand'

export const useAssistantStore = create((set) => ({
  messages: [],
  isOpen: false,
  isLoading: false,

  addMessage: (message) => set((state) => ({
    messages: [...state.messages, message]
  })),
  setOpen: (isOpen) => set({ isOpen }),
  setLoading: (isLoading) => set({ isLoading }),
  clearMessages: () => set({ messages: [] }),
}))
