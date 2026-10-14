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
  return null
}

export function supportsSpeechRecognition() {
  if (typeof window === 'undefined') return false
  return Boolean(window.SpeechRecognition || window.webkitSpeechRecognition)
}
