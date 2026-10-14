import { describe, expect, it } from 'vitest'
import { recurrencePayload } from './recurrenceV2'

const base = {
  title: ' Daily practice ', duration_minutes: '30', importance: 'important',
  frequency: 'daily', weekdays: [], timezone: 'Asia/Kolkata',
  start_date: '2026-10-15', end_date: '', due_time: '20:00',
}

describe('recurrence form', () => {
  it('maps daily schedule without unnecessary weekday constraint', () => {
    const value = recurrencePayload(base)
    expect(value.title).toBe('Daily practice')
    expect(value.weekdays).toEqual([])
    expect(value.due_time).toBe('20:00:00')
  })
  it('validates and sorts weekly weekdays', () => {
    expect(recurrencePayload({...base,frequency:'weekly',weekdays:[4,0,4]}).weekdays).toEqual([0,4])
    expect(() => recurrencePayload({...base,frequency:'weekly',weekdays:[]})).toThrow(/weekdays/)
  })
  it('rejects backwards date range and invalid duration', () => {
    expect(() => recurrencePayload({...base,end_date:'2026-10-14'})).toThrow(/End date/)
    expect(() => recurrencePayload({...base,duration_minutes:0})).toThrow(/Duration/)
  })
})
