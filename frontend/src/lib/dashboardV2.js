export function completionBars(entries) {
  if (!Array.isArray(entries) || entries.length === 0) return []
  const max = Math.max(1, ...entries.map(row => Number(row.completed || 0)))
  return entries.map(row => ({
    ...row,
    heightPercent: Math.max(4, Math.round(Number(row.completed || 0) / max * 100)),
    label: row.date.slice(5),
  }))
}
