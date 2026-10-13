import { format } from 'date-fns'

/**
 * Calendar keys are local civil dates, not UTC dates.
 * Never derive a calendar day by splitting Date.toISOString().
 */
export function localDateKey(date = new Date()) {
  if (!(date instanceof Date) || Number.isNaN(date.getTime())) {
    throw new TypeError('A valid Date is required')
  }
  return format(date, 'yyyy-MM-dd')
}
