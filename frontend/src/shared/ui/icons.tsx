/**
 * The icon set.
 *
 * Hand-written inline SVG rather than an icon package: nine icons is not worth
 * a dependency, and every one of these inherits `currentColor`, so a theme
 * change is handled by the token system like everything else. No image files,
 * no network requests, nothing to 404 offline.
 *
 * All are drawn on a 24×24 grid with a 1.7px stroke, which reads correctly at
 * both the 22px used in the tab bar and the 18px used in buttons.
 */

export type IconName =
  | 'home'
  | 'subjects'
  | 'maths'
  | 'friends'
  | 'progress'
  | 'mistakes'
  | 'settings'
  | 'more'
  | 'sound'
  | 'muted'
  | 'close'
  | 'check'
  | 'chevron-right'

const PATHS: Record<IconName, JSX.Element> = {
  home: (
    <>
      <path d="M3 10.7 12 3.5l9 7.2" />
      <path d="M5.6 9.6V19a1.5 1.5 0 0 0 1.5 1.5h9.8a1.5 1.5 0 0 0 1.5-1.5V9.6" />
    </>
  ),
  subjects: (
    <>
      <rect x="3.5" y="3.5" width="7" height="7" rx="1.6" />
      <rect x="13.5" y="3.5" width="7" height="7" rx="1.6" />
      <rect x="3.5" y="13.5" width="7" height="7" rx="1.6" />
      <rect x="13.5" y="13.5" width="7" height="7" rx="1.6" />
    </>
  ),
  maths: (
    <>
      <rect x="5" y="2.8" width="14" height="18.4" rx="2.2" />
      <path d="M8.4 7.2h7.2" />
      <path d="M9 12h.01M12 12h.01M15 12h.01M9 16h.01M12 16h.01M15 16h.01" strokeWidth="2.4" strokeLinecap="round" />
    </>
  ),
  friends: (
    <>
      <circle cx="9" cy="7.8" r="3.6" />
      <path d="M2.8 20.2a6.2 6.2 0 0 1 12.4 0" />
      <path d="M16.2 5.2a3.1 3.1 0 0 1 0 6" />
      <path d="M17.6 14.4a5.6 5.6 0 0 1 3.6 5.2" />
    </>
  ),
  progress: (
    <>
      <path d="M4 20V13" strokeLinecap="round" />
      <path d="M10 20V6.5" strokeLinecap="round" />
      <path d="M16 20v-4.5" strokeLinecap="round" />
      <path d="M21.2 20H2.8" strokeLinecap="round" />
    </>
  ),
  mistakes: (
    <>
      <path d="M6.2 3.4h11.6v17.2l-5.8-3.9-5.8 3.9z" />
    </>
  ),
  settings: (
    <>
      <circle cx="12" cy="12" r="3.3" />
      <path d="M12 2.6v2.6M12 18.8v2.6M2.6 12h2.6M18.8 12h2.6M5.4 5.4l1.8 1.8M16.8 16.8l1.8 1.8M18.6 5.4l-1.8 1.8M7.2 16.8l-1.8 1.8" strokeLinecap="round" />
    </>
  ),
  more: (
    <>
      <circle cx="5.5" cy="12" r="1.6" fill="currentColor" stroke="none" />
      <circle cx="12" cy="12" r="1.6" fill="currentColor" stroke="none" />
      <circle cx="18.5" cy="12" r="1.6" fill="currentColor" stroke="none" />
    </>
  ),
  sound: (
    <>
      <path d="M11.4 5.2 7 9H3.6v6H7l4.4 3.8z" />
      <path d="M15.4 9.2a4 4 0 0 1 0 5.6" strokeLinecap="round" />
      <path d="M18 6.6a7.6 7.6 0 0 1 0 10.8" strokeLinecap="round" />
    </>
  ),
  muted: (
    <>
      <path d="M11.4 5.2 7 9H3.6v6H7l4.4 3.8z" />
      <path d="M16 9.5 21 14.5M21 9.5 16 14.5" strokeLinecap="round" />
    </>
  ),
  close: <path d="M6 6l12 12M18 6L6 18" strokeLinecap="round" />,
  check: <path d="M4.8 12.6 9.5 17.3 19.2 7.6" strokeLinecap="round" strokeLinejoin="round" />,
  'chevron-right': <path d="M9 5.5 15.5 12 9 18.5" strokeLinecap="round" strokeLinejoin="round" />,
}

export function Icon({
  name,
  size = 20,
  className = '',
}: {
  name: IconName
  size?: number
  className?: string
}) {
  return (
    <svg
      className={className}
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.7}
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
    >
      {PATHS[name]}
    </svg>
  )
}
