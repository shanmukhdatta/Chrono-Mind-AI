import { create } from 'zustand'

export const useUiStore = create((set) => ({
  sidebarOpen: false,
  calendarView: 'day',
  setSidebarOpen: (open) => set({ sidebarOpen: open }),
  setCalendarView: (view) => set({ calendarView: view }),
}))
