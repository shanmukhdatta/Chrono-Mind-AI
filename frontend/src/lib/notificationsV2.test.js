import { describe, it, expect } from 'vitest'
import { unreadNotifications, notificationLabel } from './notificationsV2'

describe('V2 notification helpers', () => {
  it('filters unread records without changing inputs', () => {
    const rows = [{id:'1',read_at:null}, {id:'2',read_at:'2026-10-14T08:00:00Z'}]
    expect(unreadNotifications(rows)).toHaveLength(1)
    expect(rows).toHaveLength(2)
  })
  it('only uses known kind labels', () => {
    expect(notificationLabel({kind:'due_today'})).toBe('Due soon')
    expect(notificationLabel({kind:'overdue'})).toBe('Overdue')
    expect(notificationLabel({kind:'unexpected'})).toBe('Notification')
  })
})
