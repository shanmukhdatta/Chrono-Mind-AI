import { addDays, format, parseISO, startOfWeek, endOfWeek, startOfMonth, endOfMonth, eachDayOfInterval } from 'date-fns'

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

export function calendarWeekWindow(dateStr) {
  const day = parseISO(dateStr)
  if (!Number.isFinite(day.getTime())) {
    throw new Error('Invalid local calendar date')
  }
  const weekStart = startOfWeek(day, { weekStartsOn: 1 })
  const weekEnd = addDays(weekStart, 7)
  const days = eachDayOfInterval({ start: weekStart, end: addDays(weekStart, 6) }).map(d => format(d, 'yyyy-MM-dd'))
  return {
    starts_at: weekStart.toISOString(),
    ends_at: weekEnd.toISOString(),
    days,
  }
}

export function calendarMonthWindow(dateStr) {
  const day = parseISO(dateStr)
  if (!Number.isFinite(day.getTime())) {
    throw new Error('Invalid local calendar date')
  }
  const monthStart = startOfMonth(day)
  const monthEnd = endOfMonth(day)
  const days = eachDayOfInterval({ start: monthStart, end: monthEnd }).map(d => format(d, 'yyyy-MM-dd'))
  return {
    starts_at: monthStart.toISOString(),
    ends_at: monthEnd.toISOString(),
    days,
    monthName: format(day, 'MMMM yyyy'),
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
