import { describe, expect, it } from 'vitest'

import { formatCompactNumber, formatCompactWhen, formatDateTime } from '@/utils/display'

describe('formatDateTime', () => {
  it('renders a locale date-time string', () => {
    const formatted = formatDateTime('2026-06-10T12:53:00Z')
    expect(formatted).toContain('2026')
  })
})

describe('formatCompactWhen', () => {
  it('shows only the time for a same-day timestamp', () => {
    const now = new Date('2026-06-10T15:00:00')
    const formatted = formatCompactWhen('2026-06-10T12:53:00', now)
    expect(formatted).toMatch(/12[:.]53/)
    expect(formatted).not.toContain('2026')
  })

  it('shows the date for an older timestamp', () => {
    const now = new Date('2026-06-10T15:00:00')
    const formatted = formatCompactWhen('2026-06-08T12:53:00', now)
    expect(formatted).toContain('2026')
  })
})

describe('formatCompactNumber', () => {
  it('keeps small numbers as-is', () => {
    expect(formatCompactNumber(127)).toBe('127')
  })

  it('compacts thousands with one decimal', () => {
    expect(formatCompactNumber(2400)).toBe('2.4k')
  })
})
