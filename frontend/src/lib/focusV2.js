export function focusClock(session, nowMs = Date.now()) {
  if (!session) return { elapsed: 0, remaining: 0, label: '00:00' }
  const started = new Date(session.started_at).getTime()
  const planned = Number(session.planned_seconds)
  if (!Number.isFinite(started) || !Number.isFinite(planned)) throw new Error('Invalid focus session')
  const elapsed = session.status === 'active'
    ? Math.max(0, Math.floor((nowMs - started) / 1000))
    : Number(session.actual_seconds)
  const remaining = Math.max(0, planned - elapsed)
  const mins = String(Math.floor(remaining / 60)).padStart(2, '0')
  const secs = String(remaining % 60).padStart(2, '0')
  return { elapsed, remaining, label: mins + ':' + secs }
}

export function formatFocusMinutes(seconds) {
  return Math.floor(Math.max(0, Number(seconds || 0)) / 60)
}
