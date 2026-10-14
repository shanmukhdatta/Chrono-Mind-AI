import { describe, expect, it } from 'vitest'
import { focusClock, formatFocusMinutes } from './focusV2'

describe('persistent V2 focus timer', () => {
  it('derives progress from server timestamp even after a frontend restart', () => {
    const row = { status: 'active', planned_seconds: 1500, started_at: '2026-10-14T08:00:00Z' }
    expect(focusClock(row, new Date('2026-10-14T08:05:07Z').getTime()).label).toBe('19:53')
  })
  it('does not display negative countdown after exceeding the target', () => {
    const row = { status: 'active', planned_seconds: 600, started_at: '2026-10-14T08:00:00Z' }
    expect(focusClock(row, new Date('2026-10-14T09:00:00Z').getTime()).remaining).toBe(0)
  })
  it('uses recorded duration for completed sessions', () => {
    const row = { status: 'completed', planned_seconds: 1500, actual_seconds: 740, started_at: '2026-10-14T08:00:00Z' }
    expect(formatFocusMinutes(row.actual_seconds)).toBe(12)
    expect(focusClock(row).label).toBe('12:40')
  })
})
