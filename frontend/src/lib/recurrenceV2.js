export function recurrencePayload(form) {
  const title = String(form.title || '').trim()
  const length = Number(form.duration_minutes)
  if (!title || title.length > 160) throw new Error('Enter a routine title')
  if (!Number.isInteger(length) || length < 1 || length > 1440) {
    throw new Error('Duration must be between 1 and 1440 minutes')
  }
  if (!['daily', 'weekly', 'monthly'].includes(form.frequency)) {
    throw new Error('Choose daily, weekly, or monthly recurrence')
  }
  const days = Array.isArray(form.weekdays) ? [...new Set(form.weekdays.map(Number))].sort() : []
  if (form.frequency === 'weekly' && (days.length === 0 || days.some(d => !Number.isInteger(d) || d < 0 || d > 6))) {
    throw new Error('Select one or more weekdays')
  }
  if (!/^\d{4}-\d{2}-\d{2}$/.test(form.start_date)) throw new Error('Select a valid start date')
  if (form.end_date && form.end_date < form.start_date) throw new Error('End date must follow start date')
  return {
    title, duration_minutes: length,
    importance: form.importance || 'important',
    frequency: form.frequency,
    weekdays: form.frequency === 'weekly' ? days : [],
    timezone: form.timezone || 'Asia/Kolkata',
    due_time: form.due_time ? form.due_time + ':00' : null,
    start_date: form.start_date,
    end_date: form.end_date || null,
  }
}
