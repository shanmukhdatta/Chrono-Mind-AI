export function summarizePlan(preview) {
  const blocks = Array.isArray(preview?.blocks) ? preview.blocks : []
  const unscheduled = Array.isArray(preview?.unscheduled) ? preview.unscheduled : []
  return {
    sessions: blocks.length,
    plannedMinutes: blocks.reduce((total, block) => total + Number(block.duration_minutes || 0), 0),
    remainingMinutes: unscheduled.reduce((total, task) => total + Number(task.remaining_minutes || 0), 0),
  }
}

export function formatPlanInstant(iso, timezone = 'Asia/Kolkata') {
  return new Intl.DateTimeFormat('en-IN', {
    timeZone: timezone,
    day: 'numeric', month: 'short', hour: 'numeric', minute: '2-digit',
  }).format(new Date(iso))
}
