export function dateTimeLocalToIso(value) {
  if (!value) return null
  const parsed = new Date(value)
  if (!Number.isFinite(parsed.getTime())) throw new Error('Enter a valid deadline')
  return parsed.toISOString()
}

export function isoToDateTimeLocal(value) {
  if (!value) return ''
  const date = new Date(value)
  if (!Number.isFinite(date.getTime())) return ''
  const pad = number => String(number).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`
}

export function normalizeContextTags(value) {
  const raw = Array.isArray(value) ? value : String(value || '').split(',')
  const tags = []
  const seen = new Set()
  for (const item of raw) {
    const tag = String(item).trim().replace(/\s+/g, ' ')
    if (!tag) continue
    if (tag.length > 40) throw new Error('Context tags must be 40 characters or fewer')
    const key = tag.toLowerCase()
    if (seen.has(key)) continue
    seen.add(key)
    tags.push(tag)
  }
  if (tags.length > 5) throw new Error('At most 5 context tags are allowed')
  return tags
}

export function contextTagsToInput(tags) {
  return (tags || []).join(', ')
}

export function taskPayload(form) {
  const title = form.title.trim()
  const duration = Number(form.duration_minutes)
  if (!title || title.length > 160) throw new Error('Task title is required, up to 160 characters')
  if (!Number.isInteger(duration) || duration < 1 || duration > 1440) {
    throw new Error('Task duration must be 1–1440 minutes')
  }
  return {
    title, description: form.description || '', duration_minutes: duration,
    splittable: form.splittable !== false,
    importance: form.importance,
    deadline_at: dateTimeLocalToIso(form.deadline_at),
    goal_id: form.goal_id || null,
    context_tags: normalizeContextTags(form.context_tags),
  }
}
