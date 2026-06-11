export function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString()
}

// compact "when" for activity strips: time of day for today, date otherwise
export function formatCompactWhen(iso: string, now: Date = new Date()): string {
  const date = new Date(iso)
  const sameDay = date.toDateString() === now.toDateString()
  return sameDay
    ? date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    : date.toLocaleDateString()
}

// 2400 -> "2.4k" — hero stats stay short however large the board grows
export function formatCompactNumber(value: number): string {
  return new Intl.NumberFormat('en', { notation: 'compact', maximumFractionDigits: 1 })
    .format(value)
    .toLowerCase()
}
