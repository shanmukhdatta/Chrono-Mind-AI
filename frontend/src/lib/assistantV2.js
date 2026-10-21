export function extractDraft(decision) {
  if (decision?.kind === 'draft_task' && decision.draft_task) {
    return { kind: 'task', payload: {
      title: decision.draft_task.title,
      duration_minutes: decision.draft_task.duration_minutes,
      importance: decision.draft_task.importance || 'important',
      goal_id: decision.draft_task.goal_id || null,
    } }
  }
  if (decision?.kind === 'draft_goal' && decision.draft_goal) {
    return { kind: 'goal', payload: {
      title: decision.draft_goal.title,
      description: decision.draft_goal.description || '',
    } }
  }
  if (decision?.kind === 'draft_task_change' && decision.draft_task_change) {
    const item = decision.draft_task_change
    const valid = ['update', 'complete', 'archive', 'delete']
    if (!valid.includes(item.operation)) return null
    const payload = { task_id: item.task_id, version: item.version, operation: item.operation }
    if (item.operation === 'update') {
      if (item.title != null) payload.title = item.title
      if (item.duration_minutes != null) payload.duration_minutes = item.duration_minutes
      if (item.importance != null) payload.importance = item.importance
    }
    return { kind: 'task_change', payload }
  }
  if (decision?.kind === 'draft_goal_change' && decision.draft_goal_change) {
    const item = decision.draft_goal_change
    const valid = ['update', 'complete', 'pause', 'archive', 'delete']
    if (!valid.includes(item.operation)) return null
    const payload = { goal_id: item.goal_id, operation: item.operation }
    if (item.operation === 'update') {
      if (item.title != null) payload.title = item.title
      if (item.description != null) payload.description = item.description
    }
    return { kind: 'goal_change', payload }
  }
  if (decision?.kind === 'draft_decomposition' && decision.draft_decomposition) {
    const item = decision.draft_decomposition
    if (!item.task_id) return null
    return {
      kind: 'decomposition',
      payload: {
        task_id: item.task_id,
        task_title: item.task_title || '',
        subtasks: Array.isArray(item.subtasks) ? item.subtasks : []
      }
    }
  }
  return null
}

export function supportsSpeechRecognition() {
  if (typeof window === 'undefined') return false
  return Boolean(window.SpeechRecognition || window.webkitSpeechRecognition)
}
