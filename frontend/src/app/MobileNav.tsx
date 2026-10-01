import { useEffect, useState } from 'react'
import { NavLink, useLocation } from 'react-router-dom'
import { Icon, type IconName } from '@/shared/ui/icons'
import { sfx } from '@/shared/lib/sfx'

/**
 * The phone tab bar.
 *
 * A desktop top bar with ten links cannot be made to work on a 360px screen:
 * it either overflows, wraps into two rows and pushes the page down, or shrinks
 * to unreadable labels. So the four destinations that get used daily sit in a
 * fixed bar at the bottom of the screen, and the rest live behind More.
 *
 * It renders on every width and lets CSS hide it above 860px, so there is one
 * source of truth for what the phone shows.
 *
 * Hidden during a quiz by virtue of where it is mounted — /play renders outside
 * the shell — rather than by a route check, so it cannot be forgotten.
 */

interface Tab {
  to: string
  label: string
  icon: IconName
  end?: boolean
}

const TABS: Tab[] = [
  { to: '/', label: 'Home', icon: 'home', end: true },
  { to: '/science', label: 'Subjects', icon: 'subjects' },
  { to: '/arithmetic', label: 'Maths', icon: 'maths' },
  { to: '/mistakes', label: 'Mistakes', icon: 'mistakes' },
]

export function MobileNav({ isAdmin }: { isAdmin: boolean }) {
  const [moreOpen, setMoreOpen] = useState(false)
  const location = useLocation()

  // Any navigation closes the sheet: leaving it open over the new page reads as
  // a stuck overlay.
  useEffect(() => setMoreOpen(false), [location.pathname])

  const more: Tab[] = [
    { to: '/progress', label: 'Progress', icon: 'progress' },
    { to: '/friends', label: 'Friends', icon: 'friends' },
    { to: '/account', label: 'Account', icon: 'settings' },
    ...(isAdmin ? [{ to: '/admin', label: 'Admin', icon: 'settings' as IconName }] : []),
  ]

  // More is "active" when the current page lives inside it, so the bar does not
  // look like nothing is selected.
  const moreActive = more.some((m) => location.pathname.startsWith(m.to))

  return (
    <>
      <nav className="bottom-nav" aria-label="Main">
        {TABS.map((tab) => (
          <NavLink key={tab.to} to={tab.to} end={tab.end} className="tab-item" onClick={() => sfx.play('click')}>
            <Icon name={tab.icon} size={22} className="tab-icon" />
            <span className="tab-label">{tab.label}</span>
          </NavLink>
        ))}
        <button
          type="button"
          className="tab-item tab-button"
          aria-current={moreActive ? 'page' : undefined}
          aria-expanded={moreOpen}
          onClick={() => {
            sfx.play('click')
            setMoreOpen((open) => !open)
          }}
        >
          <Icon name="more" size={22} className="tab-icon" />
          <span className="tab-label">More</span>
        </button>
      </nav>

      {moreOpen && (
        <>
          <div
            className="sheet-backdrop"
            style={{ zIndex: 40 }}
            onClick={() => setMoreOpen(false)}
            aria-hidden="true"
          />
          <div
            className="sheet"
            style={{ zIndex: 41, paddingBottom: 'calc(18px + var(--tabbar) + var(--safe-bottom))' }}
            role="dialog"
            aria-label="More"
          >
            <div className="sheet-grip" />
            <div className="sheet-head">
              <span className="sheet-title">More</span>
            </div>
            <div className="col" style={{ gap: 0 }}>
              {more.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className="pref-row"
                  onClick={() => sfx.play('click')}
                  style={{ color: 'inherit' }}
                >
                  <span className="row" style={{ gap: 12 }}>
                    <Icon name={item.icon} size={19} />
                    <span className="pref-label">{item.label}</span>
                  </span>
                  <Icon name="chevron-right" size={17} />
                </NavLink>
              ))}
            </div>
          </div>
        </>
      )}
    </>
  )
}
