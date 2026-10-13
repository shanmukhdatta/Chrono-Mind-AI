import { describe, expect, it } from 'vitest'
import { localDateKey } from './date'

describe('localDateKey', () => {
  it('returns the local calendar date with zero-padded fields', () => {
    expect(localDateKey(new Date(2026, 0, 5, 12, 30))).toBe('2026-01-05')
  })

  it('rejects invalid input rather than silently storing an invalid key', () => {
    expect(() => localDateKey(new Date('invalid'))).toThrow(TypeError)
    expect(() => localDateKey('2026-01-05')).toThrow(TypeError)
  })

  it('uses the local date even when the UTC date is still yesterday', () => {
    // CI runs this suite in Asia/Kolkata; 18:45 UTC is 00:15 the next day.
    expect(localDateKey(new Date('2026-01-01T18:45:00Z'))).toBe('2026-01-02')
  })
})
