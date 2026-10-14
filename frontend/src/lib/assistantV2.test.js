import { describe, expect, it } from 'vitest'
import { extractDraft } from './assistantV2'

describe('structured AI drafts', () => {
  it('does not turn plain text into writes', () => {
    expect(extractDraft({ kind: 'answer', message: 'Saved it!' })).toBeNull()
  })
  it('maps only known validated task and goal drafts', () => {
    expect(extractDraft({
      kind: 'draft_task', draft_task: { title: 'Study', duration_minutes: 50, importance: 'important', goal_id: null }
    })).toEqual({ kind: 'task', payload: { title: 'Study', duration_minutes: 50, importance: 'important', goal_id: null } })
    expect(extractDraft({ kind: 'draft_goal', draft_goal: { title: 'Internship', description: '' } }))
      .toEqual({ kind: 'goal', payload: { title: 'Internship', description: '' } })
    expect(extractDraft({ kind: 'unexpected', draft_goal: { title: 'X' } })).toBeNull()
  })
})
