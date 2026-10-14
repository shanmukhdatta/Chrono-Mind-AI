import { addDays, format, parseISO } from 'date-fns'

export function calendarDayWindow(dateStr) {
  const day = parseISO(dateStr)
  if (!Number.isFinite(day.getTime()) || format(day, 'yyyy-MM-dd') !== dateStr) {
    throw new Error('Invalid local calendar date')
  }
  return {
    starts_at: day.toISOString(),
    ends_at: addDays(day, 1).toISOString(),
  }
}

export function localEventPayload(dateStr, title, start, end) {
  const begins = new Date(dateStr + 'T' + start + ':00')
  const finishes = new Date(dateStr + 'T' + end + ':00')
  if (!title.trim() || !Number.isFinite(begins.getTime()) ||
      !Number.isFinite(finishes.getTime()) || finishes <= begins) {
    throw new Error('Enter an event title and a valid start/end time')
  }
  return { title: title.trim(), starts_at: begins.toISOString(), ends_at: finishes.toISOString() }
}
