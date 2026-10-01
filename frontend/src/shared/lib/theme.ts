/**
 * Themes.
 *
 * The product is dark-first, so every dark theme is a complete, considered
 * palette rather than an afterthought, and the two light themes are there for
 * daylight and for people who cannot read light-on-dark comfortably.
 *
 * The actual colours live in `styles/tokens.css`; this file is the registry the
 * UI iterates over, plus the two pieces of browser chrome that CSS cannot
 * reach: the mobile status bar colour and `color-scheme`, which decides how
 * native scrollbars, form controls and the address bar are drawn.
 */

export type ThemeId = 'midnight' | 'nebula' | 'carbon' | 'forest' | 'paper' | 'daylight'

export interface ThemeDef {
  id: ThemeId
  label: string
  /** One-line description shown under the name in the picker. */
  note: string
  /** [background, surface, accent] — used for the preview swatch. */
  swatch: [string, string, string]
  /** Must match `--bg` in tokens.css so the status bar blends into the page. */
  metaColor: string
  dark: boolean
}

export const THEMES: ThemeDef[] = [
  {
    id: 'midnight',
    label: 'Midnight',
    note: 'Black and amber. The default.',
    swatch: ['#0b0b0f', '#16161f', '#f5c518'],
    metaColor: '#0b0b0f',
    dark: true,
  },
  {
    id: 'nebula',
    label: 'Nebula',
    note: 'Deep indigo with violet.',
    swatch: ['#0c0a18', '#191630', '#a78bfa'],
    metaColor: '#0c0a18',
    dark: true,
  },
  {
    id: 'carbon',
    label: 'Carbon',
    note: 'Neutral grey with cyan.',
    swatch: ['#0e1114', '#1a1f24', '#22d3ee'],
    metaColor: '#0e1114',
    dark: true,
  },
  {
    id: 'forest',
    label: 'Forest',
    note: 'Dark green, easy on the eyes.',
    swatch: ['#08120f', '#14241e', '#3ddc97'],
    metaColor: '#08120f',
    dark: true,
  },
  {
    id: 'paper',
    label: 'Paper',
    note: 'Warm cream for daytime.',
    swatch: ['#faf6ee', '#ffffff', '#b06f00'],
    metaColor: '#faf6ee',
    dark: false,
  },
  {
    id: 'daylight',
    label: 'Daylight',
    note: 'Clean white with blue.',
    swatch: ['#f6f7f9', '#ffffff', '#2563eb'],
    metaColor: '#f6f7f9',
    dark: false,
  },
]

export const DEFAULT_THEME: ThemeId = 'midnight'

const BY_ID = new Map(THEMES.map((t) => [t.id, t]))

/** Anything unrecognised (a stale value in localStorage) falls back to default. */
export function themeDef(id: string | null | undefined): ThemeDef {
  return (id && BY_ID.get(id as ThemeId)) || BY_ID.get(DEFAULT_THEME)!
}

export function applyTheme(id: string | null | undefined) {
  const theme = themeDef(id)
  const root = document.documentElement
  root.dataset.theme = theme.id
  // Tells the browser to draw scrollbars, spinners and the like to match, and
  // on mobile it tints the address bar.
  root.style.colorScheme = theme.dark ? 'dark' : 'light'

  const meta = document.querySelector('meta[name="theme-color"]')
  if (meta) meta.setAttribute('content', theme.metaColor)
}
