import React, { useEffect, useRef } from 'react'
import { useTimerStore } from '../store/timerStore'
import { X, Pause, Play, StopCircle } from 'lucide-react'
import toast from 'react-hot-toast'

export function FocusTimer() {
  const { activeTimerId, secondsLeft, isRunning, taskTitle, tick, pauseTimer, resumeTimer, stopTimer } = useTimerStore()
  const intervalRef = useRef(null)
  const totalRef = useRef(secondsLeft)

  // Capture total seconds when timer starts
  useEffect(() => {
    if (activeTimerId) totalRef.current = secondsLeft
  }, [activeTimerId])

  useEffect(() => {
    clearInterval(intervalRef.current)
    if (isRunning && secondsLeft > 0) {
      intervalRef.current = setInterval(tick, 1000)
    }
    if (secondsLeft === 0 && activeTimerId) {
      toast.success(`⏰ Timer complete: "${taskTitle}"`, { duration: 8000 })
      stopTimer()
    }
    return () => clearInterval(intervalRef.current)
  }, [isRunning, secondsLeft, activeTimerId])

  if (!activeTimerId) return null

  const mins = Math.floor(secondsLeft / 60)
  const secs = secondsLeft % 60
  const timeStr = `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`
  const progress = totalRef.current > 0 ? 1 - secondsLeft / totalRef.current : 0
  const isWarning = secondsLeft < 60 && secondsLeft > 0

  return (
    <div className="fixed bottom-24 right-6 z-40 bg-white border border-gray-200 rounded-2xl shadow-card p-4 w-60 animate-fade-in">
      <div className="flex items-start justify-between mb-2">
        <div className="flex-1 min-w-0">
          <p className="text-[10px] text-dark-muted font-semibold uppercase tracking-wide">Focus Timer</p>
          <p className="text-sm font-semibold text-dark truncate">{taskTitle}</p>
        </div>
        <button onClick={stopTimer} className="p-1 hover:bg-gray-100 rounded-lg ml-2 flex-shrink-0">
          <X className="w-4 h-4 text-dark-muted" />
        </button>
      </div>

      {/* Time Display */}
      <div className={`text-4xl font-mono font-bold text-center my-3 tabular-nums ${isWarning ? 'text-red-500 animate-pulse' : 'text-peach'}`}>
        {timeStr}
      </div>

      {/* Progress bar */}
      <div className="h-1.5 bg-gray-100 rounded-full mb-3 overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-1000 ${isWarning ? 'bg-red-400' : 'bg-peach'}`}
          style={{ width: `${Math.min(progress * 100, 100)}%` }}
        />
      </div>

      {/* Controls */}
      <div className="flex gap-2">
        <button
          onClick={isRunning ? pauseTimer : resumeTimer}
          className="flex-1 flex items-center justify-center gap-1.5 py-2 bg-peach/10 text-peach-dark rounded-xl text-sm font-medium hover:bg-peach/20 transition-colors"
        >
          {isRunning ? <><Pause className="w-4 h-4" /> Pause</> : <><Play className="w-4 h-4" /> Resume</>}
        </button>
        <button
          onClick={stopTimer}
          className="p-2 bg-red-50 text-red-500 rounded-xl hover:bg-red-100 transition-colors"
          title="Stop Timer"
        >
          <StopCircle className="w-4 h-4" />
        </button>
      </div>
    </div>
  )
}
