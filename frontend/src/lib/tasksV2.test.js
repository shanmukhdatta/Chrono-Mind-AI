import { describe, it, expect } from 'vitest'
import { dateTimeLocalToIso, isoToDateTimeLocal, taskPayload } from './tasksV2'

describe('V2 task form', () => {
  it('converts explicit local deadline to an ISO timestamp', () => {
    expect(new Date(dateTimeLocalToIso('2026-10-19T09:30')).getTime()).toBe(
      new Date('2026-10-19T09:30').getTime()
    )
    expect(dateTimeLocalToIso('')).toBeNull()
  })
  it('rejects blank task and impossible effort', () => {
    const valid = {title: ' Study ',duration_minutes: '50',importance:'important',goal_id:'',deadline_at:''}
    expect(taskPayload(valid).title).toBe('Study')
    expect(() => taskPayload({...valid,title:'  '})).toThrow(/title/)
    expect(() => taskPayload({...valid,duration_minutes:0})).toThrow(/duration/)
  })
  it('supports editing deadlines without manual timezone manipulation', () => {
    const iso = dateTimeLocalToIso('2026-10-20T14:30')
    expect(isoToDateTimeLocal(iso)).toBe('2026-10-20T14:30')
  })
})
