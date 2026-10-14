import { describe, it, expect } from 'vitest'
import { completionBars } from './dashboardV2'

describe('seven-day completion visual', () => {
  it('uses a stable baseline for empty activity', () => {
    const rows = completionBars([{ date: '2026-10-15', completed: 0 }])
    expect(rows[0].heightPercent).toBe(4)
    expect(completionBars([])).toEqual([])
  })
  it('scales to maximum daily completions', () => {
    const rows = completionBars([{date:'2026-10-14',completed:2},{date:'2026-10-15',completed:4}])
    expect(rows.map(item => item.heightPercent)).toEqual([50,100])
  })
})
