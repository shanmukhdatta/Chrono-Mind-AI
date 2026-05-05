import React, { useState, useEffect } from 'react'
import { format } from 'date-fns'

export function ClockWidget() {
  const [now, setNow] = useState(new Date())

  useEffect(() => {
    const interval = setInterval(() => setNow(new Date()), 1000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="bg-peach/10 border border-peach/20 rounded-xl p-3 text-center">
      <p className="text-2xl font-bold text-dark font-mono tracking-tight">
        {format(now, 'HH:mm')}
        <span className="text-peach text-xl animate-pulse">:{format(now, 'ss')}</span>
      </p>
      <p className="text-xs text-dark-muted mt-1">{format(now, 'EEE, d MMM')}</p>
    </div>
  )
}
