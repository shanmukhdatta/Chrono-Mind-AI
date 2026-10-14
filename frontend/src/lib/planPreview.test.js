import { describe, expect, it } from 'vitest'
import { formatPlanInstant, summarizePlan } from './planPreview'

describe('schedule preview presentation', () => {
  it('counts planned and unscheduled work without mutating input', () => {
    const plan = { blocks: [{ duration_minutes: 30 }, { duration_minutes: 45 }], unscheduled: [{ remaining_minutes: 20 }] }
    expect(summarizePlan(plan)).toEqual({ sessions: 2, plannedMinutes: 75, remainingMinutes: 20 })
    expect(plan.blocks.length).toBe(2)
  })
  it('uses the plan timezone rather than the local browser timezone', () => {
    expect(formatPlanInstant('2026-10-15T03:30:00+00:00', 'Asia/Kolkata')).toContain('9')
  })
  it('handles empty proposals', () => {
    expect(summarizePlan(null)).toEqual({ sessions: 0, plannedMinutes: 0, remainingMinutes: 0 })
  })
})
