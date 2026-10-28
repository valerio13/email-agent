import { describe, expect, it } from 'vitest'
import { addressOf, formatDay, formatDuration, formatWeekday, nameOf } from './format'

describe('sender', () => {
  it('splits a sender into name and address', () => {
    expect(nameOf('Marcus Lee <marcus.lee@northwind.example.com>')).toBe('Marcus Lee')
    expect(addressOf('Marcus Lee <marcus.lee@northwind.example.com>')).toBe(
      'marcus.lee@northwind.example.com',
    )
  })

  it('falls back to the whole text when a part is missing', () => {
    expect(nameOf('plain@example.com')).toBe('plain@example.com')
    expect(addressOf('plain@example.com')).toBe('plain@example.com')
  })
})

describe('dates', () => {
  it('shows a UTC calendar day as that same day, whatever the timezone', () => {
    expect(formatDay('2026-10-26')).toContain('26 October 2026')
    expect(formatWeekday('2026-10-26')).toBe('Mon')
  })
})

describe('formatDuration', () => {
  it('reads minutes as hours and minutes', () => {
    expect(formatDuration(198)).toBe('3h 18m')
    expect(formatDuration(120)).toBe('2h 00m')
  })

  it('shows only minutes under an hour', () => {
    expect(formatDuration(45)).toBe('45m')
  })
})
