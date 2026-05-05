import { create } from 'zustand'

export const useTimerStore = create((set, get) => ({
  activeTimerId: null,
  secondsLeft: 0,
  totalSeconds: 0,
  isRunning: false,
  taskTitle: '',

  startTimer: (taskId, durationMinutes, title) => set({
    activeTimerId: taskId,
    secondsLeft: durationMinutes * 60,
    totalSeconds: durationMinutes * 60,
    isRunning: true,
    taskTitle: title || 'Task',
  }),
  tick: () => set((state) => ({
    secondsLeft: Math.max(0, state.secondsLeft - 1),
    isRunning: state.secondsLeft > 1,
  })),
  pauseTimer: () => set({ isRunning: false }),
  resumeTimer: () => set((state) => ({
    isRunning: state.secondsLeft > 0,
  })),
  stopTimer: () => set({
    activeTimerId: null,
    secondsLeft: 0,
    totalSeconds: 0,
    isRunning: false,
    taskTitle: '',
  }),
}))
