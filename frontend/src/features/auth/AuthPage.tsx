import { useEffect, useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { api, ApiError } from '@/shared/api/client'
import { useAppStore, type AuthUser } from '@/app/store'
import { BRAND } from '@/shared/brand'
import type { Profile } from '@/shared/types'
import {
  Button,
  ErrorNote,
  PasswordField,
  RuleText,
  Segmented,
  TextField,
} from '@/shared/ui/primitives'

type Mode = 'login' | 'signup'

interface MeResponse {
  user: AuthUser
  profile: Profile | null
}

interface PublicConfig {
  app_name?: string
  google_sign_in: boolean
  allow_local_profiles: boolean
  max_local_profiles?: number
  content?: {
    questions: number
    subjects: { subject_id: string; name: string; questions: number }[]
  }
}

const USERNAME_RULE = /^[a-z0-9_]{3,24}$/i

/**
 * Why a username is rejected, worked out on the device instead of on the server.
 *
 * Returning the specific reason matters most for the single most common mistake,
 * which is typing an email address here. A round trip to a remote database to be
 * told something the browser already knows costs two seconds and arrives as a
 * generic message; this arrives instantly and says what to do instead.
 */
function usernameProblem(raw: string): string | null {
  const name = raw.trim()
  if (!name) return 'Enter a username.'
  if (name.includes('@')) {
    return 'A username is a short handle like sayan10, not an email address. Use your email only for Google sign-in.'
  }
  if (!USERNAME_RULE.test(name)) {
    if (name.length < 3) return 'Use at least 3 characters.'
    if (name.length > 24) return 'Use 24 characters or fewer.'
    if (name !== name.toLowerCase()) return 'Use lowercase letters only.'
    return 'Letters, numbers and underscores only - no spaces or punctuation.'
  }
  return null
}

/**
 * A filler in the shape of one point.
 *
 * The three points sit below the card, so a change in their height moves nothing
 * else on the screen; but a point's text arriving late still makes the text
 * change under the reader. Holding the row's height and showing a bar of about
 * the right length lets the content appear without the sentence being rewritten.
 */
function PointFiller({ width }: { width: string }) {
  return (
    <div className="auth-point-skeleton" aria-hidden="true">
      <span className="auth-point-fill" style={{ width: 6, height: 6, borderRadius: '50%' }} />
      <span className="auth-point-fill" style={{ width }} />
    </div>
  )
}

/**
 * Sign in / create account.
 *
 * Local mode is still offered, because the app must keep working with no account
 * and no network - but it is the secondary path now, and says plainly what it
 * costs: progress stays on this device only.
 */
export function AuthPage() {
  const setAuth = useAppStore((s) => s.setAuth)
  const setProfile = useAppStore((s) => s.setProfile)
  const setLocalMode = useAppStore((s) => s.setLocalMode)
  const queryClient = useQueryClient()

  const [mode, setMode] = useState<Mode>('login')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [notice, setNotice] = useState<string | null>(null)
  // Only flag a field once it has been left, so nothing argues with a student
  // who is still typing.
  const [touched, setTouched] = useState<{ username: boolean; confirm: boolean }>({
    username: false,
    confirm: false,
  })

  // One request describes which optional features THIS server turned on, so a
  // control that would only fail when clicked is never rendered. A public
  // deploy disables account-free profiles; a family install keeps them.
  const config = useQuery({
    queryKey: ['public-config'],
    queryFn: () =>
      api.get<PublicConfig>('/config'),
    staleTime: 5 * 60_000,
  })
  const configPending = config.isPending
  const googleEnabled = config.data?.google_sign_in ?? false
  const localAllowed = config.data?.allow_local_profiles ?? true
  // Read off the server rather than written into the JSX: a hard-coded count goes
  // stale the first time questions are added, and a stale number on the sign-in
  // screen is either a lie or an undersell.
  const questionCount = config.data?.content?.questions ?? 0
  const subjectNames = (config.data?.content?.subjects ?? []).map((s) => s.name)

  // Someone arriving here with progress already on this device should keep it.
  const existingProfile = useAppStore((st) => st.profile)

  useEffect(() => {
    if (existingProfile) {
      setNotice(
        `Progress found on this device (${existingProfile.display_name}). Creating an account will keep it.`,
      )
    }
  }, [existingProfile?.id])

  const startGoogle = async () => {
    setError(null)
    try {
      const { url } = await api.get<{ url: string }>('/auth/google/start?mode=signin')
      window.location.href = url
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not start Google sign-in.')
    }
  }

  const switchMode = (next: Mode) => {
    setMode(next)
    setError(null)
    setConfirm('')
    setTouched({ username: false, confirm: false })
  }

  const nameProblem = usernameProblem(username)
  const showNameProblem = touched.username && username.trim().length > 0 && nameProblem !== null
  const passwordsMatch = password === confirm
  const showMatchProblem = touched.confirm && confirm.length > 0 && !passwordsMatch

  const submit = async (event: React.FormEvent) => {
    event.preventDefault()
    setError(null)
    setTouched({ username: true, confirm: true })

    const name = username.trim()
    if (nameProblem) return setError(nameProblem)
    if (password.length < 6) return setError('Password must be at least 6 characters.')
    if (mode === 'signup' && !passwordsMatch) return setError('The two passwords do not match.')

    setBusy(true)
    try {
      const result =
        mode === 'signup'
          ? await api.post<{ token: string; user: AuthUser; claimed_profile?: boolean }>('/auth/signup', {
              username: name,
              password,
              // Adopt whatever progress already exists on this device rather
              // than starting the new account from zero.
              ...(mode === 'signup' && existingProfile && !existingProfile.user_id
                ? { claim_profile_id: existingProfile.id }
                : {}),
            })
          : await api.post<{ token: string; user: AuthUser }>('/auth/login', {
              username: name,
              password,
            })

      setAuth({ token: result.token, user: result.user })

      // The profile carries every streak, XP total and level, so it has to be
      // in the store before the dashboard renders or the first paint shows zeros.
      const me = await api.get<MeResponse>('/auth/me')
      if (me.profile) setProfile(me.profile)

      // Cached queries may hold another account's data from a previous session.
      queryClient.clear()
      setPassword('')
      setConfirm('')
    } catch (err) {
      setAuth(null)
      setError(err instanceof ApiError ? err.message : 'Could not reach the server.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="auth-shell">
      <div className="auth-head rise-in">
        <div className="row" style={{ justifyContent: 'center', gap: 10, marginBottom: 10 }}>
          <span className="brand-mark" style={{ width: 36, height: 36, fontSize: 19 }}>
            {BRAND.mark}
          </span>
          <h1 className="auth-title">{BRAND.name}</h1>
        </div>
        <p className="auth-sub">{BRAND.tagline}</p>
      </div>

      <div className="auth-card rise-in">
        <Segmented<Mode>
          ariaLabel="Sign in or create an account"
          value={mode}
          onChange={switchMode}
          options={[
            { value: 'login', label: 'Sign in' },
            { value: 'signup', label: 'Create account' },
          ]}
        />

        <div className="auth-message">
          {error ? (
            <div className="note-in">
              <ErrorNote message={error} onRetry={() => setError(null)} />
            </div>
          ) : notice ? (
            <div
              className="card card-pad-sm note-in"
              style={{ borderLeft: '3px solid var(--info)', background: 'var(--info-dim)' }}
            >
              <span className="small">{notice}</span>
            </div>
          ) : null}
        </div>

        <form className="auth-form" onSubmit={submit} style={{ marginTop: 6 }} noValidate>
          <TextField
            label="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            onBlur={() => setTouched((t) => ({ ...t, username: true }))}
            autoComplete="username"
            autoCapitalize="none"
            autoCorrect="off"
            spellCheck={false}
            placeholder={mode === 'signup' ? 'Pick one, e.g. sayan10' : 'Your username'}
            invalid={showNameProblem}
            hint={
              showNameProblem
                ? nameProblem
                : mode === 'signup'
                  ? '3-24 characters: lowercase letters, numbers, underscores. Not an email.'
                  : 'The username you chose when you created your account.'
            }
          />

          <PasswordField
            label="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete={mode === 'signup' ? 'new-password' : 'current-password'}
            placeholder={mode === 'signup' ? 'At least 6 characters' : 'Your password'}
            hint={mode === 'signup' ? 'You will need this to sign in from another device.' : undefined}
          />

          {mode === 'signup' && (
            <PasswordField
              label="Confirm password"
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              onBlur={() => setTouched((t) => ({ ...t, confirm: true }))}
              autoComplete="new-password"
              placeholder="Type it once more"
              invalid={showMatchProblem}
              hint={showMatchProblem ? 'The two passwords do not match.' : undefined}
            />
          )}

          <Button type="submit" variant="primary" size="lg" block disabled={busy} style={{ marginTop: 4 }}>
            {busy ? 'Working…' : mode === 'signup' ? 'Create account' : 'Sign in'}
          </Button>
        </form>

        {configPending ? (
          <div className="auth-alt" aria-hidden="true">
            <RuleText>or</RuleText>
            <div className="skeleton" style={{ height: 44, marginTop: 10 }} />
            <div className="skeleton" style={{ height: 30, marginTop: 8 }} />
          </div>
        ) : googleEnabled ? (
          <div className="auth-alt">
            <RuleText>or</RuleText>
            <Button variant="ghost" block onClick={startGoogle} disabled={busy} style={{ marginTop: 10 }}>
              Continue with Google
            </Button>
            <p className="tiny dim center" style={{ marginTop: 8, lineHeight: 1.5 }}>
              {mode === 'signup'
                ? 'Creates an account with your Google identity. You can add a password later, and link it to a username account from Account settings.'
                : 'Works if you signed up with Google, or already linked it to your account.'}
            </p>
          </div>
        ) : null}

        <p className="tiny dim center" style={{ marginTop: 16, lineHeight: 1.6 }}>
          {mode === 'signup'
            ? 'Your streaks, XP and mistake book are stored against this account, so they follow you to any device.'
            : 'An account keeps your progress on the server. No email is needed.'}
        </p>
      </div>

      <div className="auth-points rise-in">
        {configPending ? (
          <>
            <PointFiller width="78%" />
            <PointFiller width="86%" />
            <PointFiller width="70%" />
          </>
        ) : (
          <>
            <div className="auth-point">
              <span>
                {questionCount > 0 ? (
                  <>
                    <b>{questionCount.toLocaleString('en-IN')} questions</b> across{' '}
                    {subjectNames.length > 0 ? subjectNames.join(', ') : 'the syllabus'}, mapped to
                    the CBSE 2025-26 curriculum.
                  </>
                ) : (
                  <>
                    <b>Rapid revision</b> mapped to the CBSE 2025-26 curriculum.
                  </>
                )}
              </span>
            </div>
            <div className="auth-point">
              <span>
                <b>Streaks, XP and levels</b> that survive a device change, because they live on your
                account rather than in this browser.
              </span>
            </div>
            <div className="auth-point">
              <span>
                <b>A mistake book</b> that turns every wrong answer into the next question you are
                asked.
              </span>
            </div>
          </>
        )}
      </div>

      {localAllowed && (
        <div className="auth-foot rise-in">
          <div style={{ borderTop: '1px solid var(--border)', paddingTop: 16 }}>
            <button
              type="button"
              className="nav-link"
              style={{ width: '100%', opacity: 0.75 }}
              onClick={() => setLocalMode(true)}
            >
              Continue without an account
            </button>
            <p className="tiny dim center" style={{ marginTop: 6 }}>
              Progress is saved on this device only and will not transfer.
            </p>
          </div>
        </div>
      )}
    </div>
  )
}
