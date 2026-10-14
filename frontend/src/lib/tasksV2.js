export function dateTimeLocalToIso(value) {
  if (!value) return null
  const parsed = new Date(value)
  if (!Number.isFinite(parsed.getTime())) throw new Error('Enter a valid deadline')
  return parsed.toISOString()
}

export function isoToDateTimeLocal(value) {
  if (!value) return ''
  const date = new Date(value)
  if (!Number.isFinite(date.getTime())) return ''
  const pad = number => String(number).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`
}

export function taskPayload(form) {
  const title = form.title.trim()
  const duration = Number(form.duration_minutes)
  if (!title || title.length > 160) throw new Error('Task title is required, up to 160 characters')
  if (!Number.isInteger(duration) || duration < 1 || duration > 1440) {
    throw new Error('Task duration must be 1–1440 minutes')
  }
  return {
    title, description: form.description || '', duration_minutes: duration,
    importance: form.importance,
    deadline_at: dateTimeLocalToIso(form.deadline_at),
    goal_id: form.goal_id || null,
  }
}
