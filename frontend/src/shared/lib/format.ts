export const fmtInt = (n: number | null | undefined): string =>
  n == null ? '—' : Math.round(n).toLocaleString('en-IN')

export const fmtPct = (ratio: number | null | undefined, digits = 0): string =>
  ratio == null ? '—' : `${(ratio * 100).toFixed(digits)}%`

export const fmtSeconds = (ms: number | null | undefined, digits = 1): string =>
  ms == null || ms <= 0 ? '—' : `${(ms / 1000).toFixed(digits)}s`

/** 00:07 style clock used by the quiz timer. */
export const fmtClock = (ms: number): string => {
  const total = Math.max(0, Math.ceil(ms / 1000))
  const m = Math.floor(total / 60)
  const s = total % 60
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

export const greeting = (d = new Date()): string => {
  const h = d.getHours()
  if (h < 5) return 'Still up'
  if (h < 12) return 'Good morning'
  if (h < 17) return 'Good afternoon'
  if (h < 21) return 'Good evening'
  return 'Good night'
}

export const relativeDay = (iso: string | null | undefined): string => {
  if (!iso) return '—'
  const day = iso.slice(0, 10)
  const today = new Date().toISOString().slice(0, 10)
  const yesterday = new Date(Date.now() - 86400000).toISOString().slice(0, 10)
  if (day === today) return 'Today'
  if (day === yesterday) return 'Yesterday'
  return day
}

export const initials = (name: string): string => (name || '?').trim().charAt(0).toUpperCase()
