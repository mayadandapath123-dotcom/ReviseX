import { useEffect, useState } from 'react'
import { NavLink, Navigate, Route, Routes, useLocation } from 'react-router-dom'
import { BRAND } from '@/shared/brand'
import { useAppStore } from './store'
import { api, setAuthToken } from '@/shared/api/client'
import type { Profile } from '@/shared/types'
import { ProfileGate } from '@/features/profiles/ProfileGate'
import { AuthPage } from '@/features/auth/AuthPage'
import { FriendsPage } from '@/features/friends/FriendsPage'
import { AccountPage } from '@/features/account/AccountPage'
import { AdminPage } from '@/features/admin/AdminPage'
import { consumeOAuthCallback, setOAuthNotice } from '@/features/auth/oauthCallback'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { ArithmeticPage } from '@/features/arithmetic/ArithmeticPage'
import { MobileNav } from './MobileNav'
import { SettingsSheet } from '@/shared/ui/SettingsSheet'
import { Icon } from '@/shared/ui/icons'
import { sfx } from '@/shared/lib/sfx'
import { DashboardPage } from '@/features/dashboard/DashboardPage'
import { SciencePage } from '@/features/science/SciencePage'
import { QuizPage } from '@/features/quiz/QuizPage'
import { MistakesPage } from '@/features/mistakes/MistakesPage'
import { ProgressPage } from '@/features/progress/ProgressPage'

/**
 * Routes:
 *   /                dashboard
 *   /science         subject -> branch -> chapter drill-down
 *   /play            the quiz hot loop (full screen, no chrome)
 *   /arithmetic      live mental-maths trainer
 *   /friends         invitations, friend list, friends-only leaderboard
 *   /account         sign-in methods: password, Google, link and unlink
 *   /admin           owner view: live usage, students, audited account access
 *   /mistakes        mistake book
 *   /progress        XP, levels, badges, personal bests, mastery
 *   /login           sign in or create an account
 *
 * /play deliberately renders outside the shell: zero navigation chrome means
 * zero distraction and no layout shift while answering rapidly.
 */
export default function App() {
  const profile = useAppStore((s) => s.profile)
  const setProfile = useAppStore((s) => s.setProfile)
  const setOnline = useAppStore((s) => s.setOnline)
  const online = useAppStore((s) => s.online)
  const auth = useAppStore((s) => s.auth)
  const localMode = useAppStore((s) => s.localMode)
  const setAuth = useAppStore((s) => s.setAuth)
  const location = useLocation()
  const queryClient = useQueryClient()

  // Landing back from Google. Runs once, before any gate decides what to show.
  useEffect(() => {
    const result = consumeOAuthCallback()
    if (!result) return
    if (!result.ok) {
      setOAuthNotice('err', result.error ?? 'Google sign-in failed.')
      return
    }
    if (result.mode === 'signin' && result.token && result.user) {
      setAuth({ token: result.token, user: result.user })
      // Drop anything cached for a previous account before reading this one.
      queryClient.clear()
      api
        .get<{ profile: Profile | null }>('/auth/me')
        .then((me) => { if (me.profile) setProfile(me.profile) })
        .catch(() => { /* the 401 hook already cleared the session */ })
      setOAuthNotice('ok', `Signed in with Google as ${result.user.username}.`)
    } else if (result.mode === 'link') {
      setOAuthNotice('ok', `Google account linked${result.google_email ? ` (${result.google_email})` : ''}.`)
    }
  }, [setAuth, setProfile, queryClient])

  // The chosen profile lives in localStorage, but the database can be reset
  // independently (scripts/reset_progress.py, or a re-download). Trusting a
  // stale id made every profile-scoped call fail with 404 and stranded the
  // user on a blank app. So: confirm the id still exists before rendering.
  // null = not checked yet, true = confirmed, false = gone.
  const [profileValid, setProfileValid] = useState<boolean | null>(null)

  useEffect(() => {
    if (!profile) {
      setProfileValid(null)
      return
    }
    // A signed-in account's profile is authoritative - the token maps to exactly
    // one profile server side, so there is nothing stale to detect. Re-checking
    // it against the local /profiles listing would drop a valid session.
    if (auth) {
      setProfileValid(true)
      return
    }
    let cancelled = false
    api
      .get<{ profiles: Profile[] }>('/profiles')
      .then(({ profiles }) => {
        if (cancelled) return
        if (profiles.some((p) => p.id === profile.id)) setProfileValid(true)
        else {
          // Only drop it when the backend answered and the profile is absent.
          setProfile(null)
          setProfileValid(null)
        }
      })
      .catch(() => {
        // Backend unreachable: keep the stored profile rather than logging the
        // student out over a transient network error. The offline banner covers it.
        if (!cancelled) setProfileValid(true)
      })
    return () => {
      cancelled = true
    }
  }, [profile?.id, setProfile])

  // On load with a stored token, re-read the account so the level, XP and
  // streak shown are the server's, not last session's snapshot.
  useEffect(() => {
    if (!auth?.token) return
    let cancelled = false
    api
      .get<{ profile: Profile | null }>('/auth/me')
      .then((me) => {
        if (!cancelled && me.profile) setProfile(me.profile)
      })
      .catch(() => {
        // 401 is handled by the client's unauthorized hook, which clears auth.
      })
    return () => {
      cancelled = true
    }
  }, [auth?.token, setProfile])

  useEffect(() => {
    const up = () => setOnline(true)
    const down = () => setOnline(false)
    window.addEventListener('online', up)
    window.addEventListener('offline', down)
    return () => {
      window.removeEventListener('online', up)
      window.removeEventListener('offline', down)
    }
  }, [setOnline])

  const inQuiz = location.pathname.startsWith('/play')

  return (
    <>
      <ImpersonationBanner />
      {!online && !inQuiz && (
        <div className="offline-banner">
          Offline — already-loaded tests still work. Progress syncs when the backend is reachable.
        </div>
      )}

      <Routes>
        <Route path="/play" element={<QuizPage />} />
        <Route
          path="/login"
          element={profile ? <Navigate to="/" replace /> : localMode ? <ProfileGate /> : <AuthPage />}
        />
        <Route
          path="*"
          element={
            profile && profileValid === null ? (
              // A skeleton rather than a line of text: it shows the shape of the
              // dashboard that is about to arrive, so the wait reads as loading
              // instead of as a screen that failed to render.
              <div className="shell" style={{ paddingTop: '4vh' }}>
                <div className="skeleton" style={{ height: 34, width: 220, marginBottom: 18 }} />
                <div className="skeleton" style={{ height: 96, marginBottom: 12 }} />
                <div className="skeleton" style={{ height: 96, marginBottom: 12 }} />
                <div className="skeleton" style={{ height: 160 }} />
              </div>
            ) : profile && profileValid ? (
              <Shell>
                {/* Keyed on the path so a navigation replays the rise-in instead
                    of snapping: without the key React reuses the same subtree
                    and there is nothing for the animation to attach to. */}
                <div key={location.pathname} className="rise-in">
                <Routes>
                  <Route path="/" element={<DashboardPage />} />
                  <Route path="/science" element={<SciencePage />} />
                  <Route path="/science/:subjectId" element={<SciencePage />} />
                  <Route path="/science/:subjectId/:branchId" element={<SciencePage />} />
                  <Route path="/arithmetic" element={<ArithmeticPage />} />
                  <Route path="/friends" element={<FriendsPage />} />
                  <Route path="/account" element={<AccountPage />} />
                  <Route path="/admin" element={<AdminPage />} />
                  <Route path="/mistakes" element={<MistakesPage />} />
                  <Route path="/progress" element={<ProgressPage />} />
                  <Route path="*" element={<Navigate to="/" replace />} />
                </Routes>
                </div>
              </Shell>
            ) : localMode ? (
              <ProfileGate />
            ) : (
              <AuthPage />
            )
          }
        />
      </Routes>
    </>
  )
}

  function Shell({ children }: { children: React.ReactNode }) {
    const profile = useAppStore((s) => s.profile)
    const auth = useAppStore((s) => s.auth)
    const [settingsOpen, setSettingsOpen] = useState(false)
  // One extra request on shell mount buys a nav that does not advertise an
  // admin area to students. 403 simply means "not an admin".
  const account = useQuery({
    queryKey: ['account'],
    queryFn: () => api.get<{ is_admin: boolean }>('/auth/account'),
    enabled: !!auth,
    retry: false,
    staleTime: 5 * 60_000,
  })
  const setAuth = useAppStore((s) => s.setAuth)
  const setProfile = useAppStore((s) => s.setProfile)

  return (
    <>
      <header className="topbar">
        <div className="topbar-inner">
          <NavLink to="/" className="brand">
            <span className="brand-mark">{BRAND.mark}</span>
            <span>{BRAND.name}</span>
          </NavLink>

          <nav className="nav">
            <NavLink to="/" className="nav-link" end>
              Dashboard
            </NavLink>
            <NavLink to="/science" className="nav-link">
              Subjects
            </NavLink>
            <NavLink to="/arithmetic" className="nav-link">
              Mental Maths
            </NavLink>
            <NavLink to="/friends" className="nav-link">
              Friends
            </NavLink>
            <NavLink to="/account" className="nav-link">
              Account
            </NavLink>
            {account.data?.is_admin && (
              <NavLink to="/admin" className="nav-link">
                Admin
              </NavLink>
            )}
            <NavLink to="/mistakes" className="nav-link">
              Mistakes
            </NavLink>
            <NavLink to="/progress" className="nav-link">
              Progress
            </NavLink>
          </nav>

          <span className="row" style={{ gap: 8, alignItems: 'center' }}>
            <NavLink to="/progress" className="profile-chip" title={`${profile?.display_name} — level ${profile?.level}`}>
              <span className="avatar">{(profile?.display_name ?? '?').charAt(0).toUpperCase()}</span>
              <span className="small" style={{ fontWeight: 600 }}>
                {auth ? auth.user.username : profile?.display_name}
              </span>
            </NavLink>
              <button
                className="icon-btn"
                onClick={() => { sfx.play('click'); setSettingsOpen(true) }}
                aria-label="Settings"
                title="Settings — theme, sound, keyboard"
              >
                <Icon name="settings" size={17} />
              </button>
              {auth && (
                <button
                  className="nav-link tiny"
                  title="Sign out"
                  onClick={async () => {
                    // Tell the server first so the token dies there too; a local
                    // clear alone would leave a valid session in the database.
                    try { await api.post('/auth/logout') } catch { /* already gone */ }
                    setAuth(null)
                    setProfile(null)
                  }}
                >
                  Sign out
                </button>
              )}
            </span>
          </div>
        </header>
        <main className="shell">{children}</main>
        <MobileNav isAdmin={!!account.data?.is_admin} />
        <SettingsSheet open={settingsOpen} onClose={() => setSettingsOpen(false)} />
      </>
    )
  }

/**
 * Shown whenever an admin is inside someone else's account.
 *
 * Rendered outside the shell and above the offline banner so no page can hide
 * it: navigating away must not make it possible to forget who you are viewing
 * the app as. Restoring the admin's own token is one click.
 */
function ImpersonationBanner() {
  const impersonating = useAppStore((s) => s.impersonating)
  const auth = useAppStore((s) => s.auth)
  const setImpersonating = useAppStore((s) => s.setImpersonating)
  const setProfile = useAppStore((s) => s.setProfile)
  const queryClient = useQueryClient()
  const location = useLocation()

  if (!impersonating) return null

  const expired = Date.now() > impersonating.expiresAt
  const minsLeft = Math.max(0, Math.round((impersonating.expiresAt - Date.now()) / 60000))

  const stop = async () => {
    // Put the admin's own token back first, then re-read their profile, or the
    // app would keep showing the student's data under the admin's name.
    setAuthToken(auth?.token ?? null)
    setImpersonating(null)
    queryClient.clear()
    setProfile(null)
    if (auth?.token) {
      try {
        const me = await api.get<{ profile: Profile | null }>('/auth/me')
        if (me.profile) setProfile(me.profile)
      } catch {
        /* the 401 hook signs out */
      }
    }
  }

  return (
    <div
      style={{
        position: 'sticky', top: 0, zIndex: 1000, padding: '9px 14px',
        background: expired ? '#6e2c2c' : '#7a4d0b', color: '#fff',
        display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap',
        fontSize: 13, fontWeight: 600, borderBottom: '1px solid rgba(0,0,0,.3)',
      }}
    >
      <span style={{ flex: 1, minWidth: 220 }}>
        {expired
          ? `Session as ${impersonating.targetUsername} has expired.`
          : `You are viewing ${impersonating.targetUsername}'s account as ${impersonating.adminUsername}. ${minsLeft} min left. This is recorded in the audit log.`}
      </span>
      <button
        onClick={stop}
        style={{
          background: 'rgba(255,255,255,.16)', color: '#fff', border: '1px solid rgba(255,255,255,.35)',
          borderRadius: 6, padding: '5px 12px', fontWeight: 700, cursor: 'pointer', fontSize: 12,
        }}
      >
        Stop and return to {impersonating.adminUsername}
      </button>
      {location.pathname !== '/admin' && (
        <span style={{ opacity: 0.75, fontSize: 12 }}>Current page: {location.pathname}</span>
      )}
    </div>
  )
}
