import { create } from 'zustand'
import { format } from 'date-fns'

export const useTaskStore = create((set, get) => ({
  tasks: [],
  selectedDate: format(new Date(), 'yyyy-MM-dd'),
  isLoading: false,
  error: null,

  setTasks: (tasks) => set({ tasks, isLoading: false, error: null }),
  addTask: (task) => set((state) => ({ tasks: [task, ...state.tasks] })),
  updateTask: (updated) => set((state) => ({
    tasks: state.tasks.map(t => t.task_id === updated.task_id ? updated : t)
  })),
  removeTask: (task_id) => set((state) => ({
    tasks: state.tasks.filter(t => t.task_id !== task_id)
  })),
  setSelectedDate: (date) => set({ selectedDate: date }),
  setLoading: (isLoading) => set({ isLoading }),
  setError: (error) => set({ error, isLoading: false }),
  clearTasks: () => set({ tasks: [] }),
  seedDemoTasks: () => {
    const today = new Date().toISOString().split('T')[0];
    set({
      tasks: [
        { task_id: 'demo-1', title: 'DSA Practice', date: today, start_time: '09:00', end_time: '10:30', duration_minutes: 90, importance: 'important', recurrence: 'none', completed: false, rescheduled: false },
        { task_id: 'demo-2', title: 'Fluid Mechanics Revision', date: today, start_time: '11:00', end_time: '12:00', duration_minutes: 60, importance: 'important', recurrence: 'none', completed: false, rescheduled: false },
        { task_id: 'demo-3', title: 'Break / Walk', date: today, start_time: '13:00', end_time: '13:30', duration_minutes: 30, importance: 'not_important', recurrence: 'none', completed: false, rescheduled: false }
      ],
      isLoading: false,
      error: null
    });
  },
}))
