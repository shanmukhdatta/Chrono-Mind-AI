export function normalizePlanningPreferences(form) {
  const start = String(form.work_start || '').slice(0, 5)
  const end = String(form.work_end || '').slice(0, 5)
  const minutes = Number(form.max_daily_minutes)
  const breakMinutes = Number(form.min_break_minutes)
  if (!/^\d{2}:\d{2}$/.test(start) || !/^\d{2}:\d{2}$/.test(end) || end <= start) {
    throw new Error('Choose a valid work window: end time must be after start time.')
  }
  if (!Number.isInteger(minutes) || minutes < 60 || minutes > 960) {
    throw new Error('Daily work limit must be between 60 and 960 minutes.')
  }
  if (!Number.isInteger(breakMinutes) || breakMinutes < 0 || breakMinutes > 120) {
    throw new Error('Minimum break must be between 0 and 120 minutes.')
  }
  if (!form.timezone || form.timezone.length > 64) {
    throw new Error('Enter an IANA timezone.')
  }
  const focusContext = String(form.focus_context || '').trim()
  if (focusContext.length > 64) {
    throw new Error('Focus context must be 64 characters or fewer.')
  }
  return {
    timezone: form.timezone.trim(),
    work_start: start,
    work_end: end,
    max_daily_minutes: minutes,
    min_break_minutes: breakMinutes,
    focus_context: focusContext || null,
  }
}
