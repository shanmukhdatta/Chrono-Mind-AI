import { describe, it, expect } from 'vitest'
import { calendarDayWindow, localEventPayload } from './calendarV2'

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
})
