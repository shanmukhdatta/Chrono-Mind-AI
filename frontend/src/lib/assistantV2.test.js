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



describe('confirmable changes to existing tasks', () => {
  it('maps an allowlisted completion with server version', () => {
    const draft = extractDraft({
      kind: 'draft_task_change',
      draft_task_change: {task_id: 'abc', version: 4, operation: 'complete'},
    })
    expect(draft).toEqual({
      kind: 'task_change',
      payload: {task_id: 'abc', version: 4, operation: 'complete'},
    })
  })
  it('does not execute unknown operations or arbitrary endpoints', () => {
    expect(extractDraft({
      kind: 'draft_task_change',
      draft_task_change: {task_id: 'abc', version: 1, operation: 'transfer_money'},
    })).toBeNull()
  })
  it('maps an update only with allowlisted fields', () => {
    const draft = extractDraft({
      kind: 'draft_task_change',
      draft_task_change: {
        task_id: 'abc', version: 2, operation: 'update',
        title: 'New title', duration_minutes: 50, hidden_field: 'ignored',
      },
    })
    expect(draft.payload).toEqual({
      task_id:'abc', version:2, operation:'update',
      title:'New title', duration_minutes:50,
    })
  })

  it('maps an allowlisted goal change', () => {
    const draft = extractDraft({
      kind: 'draft_goal_change',
      draft_goal_change: { goal_id: 'g-1', operation: 'pause' },
    })
    expect(draft).toEqual({
      kind: 'goal_change',
      payload: { goal_id: 'g-1', operation: 'pause' },
    })
  })

  it('maps a decomposition draft', () => {
    const draft = extractDraft({
      kind: 'draft_decomposition',
      draft_decomposition: {
        task_id: 't-1',
        task_title: 'Big Task',
        subtasks: [{ title: 'Subtask 1', duration_minutes: 30 }],
      },
    })
    expect(draft).toEqual({
      kind: 'decomposition',
      payload: {
        task_id: 't-1',
        task_title: 'Big Task',
        subtasks: [{ title: 'Subtask 1', duration_minutes: 30 }],
      },
    })
  })
})

