import { describe, expect, it } from 'vitest'
import { normalizePlanningPreferences } from './planningPreferences'

const valid = { timezone: 'Asia/Kolkata', work_start: '08:00:00', work_end: '22:00:00', max_daily_minutes: '480', min_break_minutes: '10' }

describe('planning preferences', () => {
  it('normalizes time and numeric fields', () => {
    expect(normalizePlanningPreferences(valid)).toEqual({
      timezone: 'Asia/Kolkata', work_start: '08:00', work_end: '22:00',
      max_daily_minutes: 480, min_break_minutes: 10,
    })
  })
  it('rejects impossible work windows', () => {
    expect(() => normalizePlanningPreferences({ ...valid, work_start: '23:00' })).toThrow(/work window/)
  })
  it('rejects unsafe limits', () => {
    expect(() => normalizePlanningPreferences({ ...valid, max_daily_minutes: 10000 })).toThrow(/Daily work limit/)
  })
})
