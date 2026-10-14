import { describe, it, expect } from 'vitest'
import { calendarDayWindow, calendarWeekWindow, calendarMonthWindow, localEventPayload } from './calendarV2'

describe('V2 calendar serialization', () => {
  it('builds a positive local day query window', () => {
    const period = calendarDayWindow('2026-10-15')
    expect(new Date(period.ends_at) > new Date(period.starts_at)).toBe(true)
    expect(() => calendarDayWindow('2026-02-30')).toThrow(/Invalid/)
  })
  it('requires an ordered fixed-event interval', () => {
    expect(() => localEventPayload('2026-10-15', 'Class', '13:00', '12:00')).toThrow()
    const value = localEventPayload('2026-10-15', '  Class ', '10:00', '11:00')
    expect(value.title).toBe('Class')
    expect(new Date(value.ends_at) > new Date(value.starts_at)).toBe(true)
  })
  it('builds week and month query windows within the 31-day limit', () => {
    const week = calendarWeekWindow('2026-10-15')
    expect(week.days.length).toBe(7)
    expect(new Date(week.ends_at) > new Date(week.starts_at)).toBe(true)
    const month = calendarMonthWindow('2026-10-15')
    expect(month.days.length).toBe(31)
    const diffDays = (new Date(month.ends_at) - new Date(month.starts_at)) / (1000 * 60 * 60 * 24)
    expect(diffDays).toBeLessThanOrEqual(31)
  })
})
