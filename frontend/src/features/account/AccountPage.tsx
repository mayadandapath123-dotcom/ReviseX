import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api, ApiError } from '@/shared/api/client'
import { useAppStore } from '@/app/store'
import { Button, ErrorNote } from '@/shared/ui/primitives'

interface AccountInfo {
  username: string
  has_password: boolean
  google_linked: boolean
  google_email: string | null
  provider: string
  is_admin: boolean
  created_at: string | null
  last_login_at: string | null
}

/**
 * How you sign in: username+password, Google, or both.
 *
 * Linking and unlinking are both here because they are the same decision from
 * the student's side. The server refuses to unlink a Google-only account until
 * a password exists, and that refusal is surfaced as the reason to use "Set
 * password" - so the two controls are shown together rather than the student
 * meeting a dead end.
 */
export function AccountPage() {
  const auth = useAppStore((s) => s.auth)
  const setAuth = useAppStore((s) => s.setAuth)
  const setProfile = useAppStore((s) => s.setProfile)
  const queryClient = useQueryClient()
  const [note, setNote] = useState<{ kind: 'ok' | 'err'; text: string } | null>(null)

  const [currentPw, setCurrentPw] = useState('')
  const [newPw, setNewPw] = useState('')
  const [confirmPw, setConfirmPw] = useState('')

  const account = useQuery({
    queryKey: ['account'],
    queryFn: () => api.get<AccountInfo>('/auth/account'),
    enabled: !!auth,
  })
  const google = useQuery({
    queryKey: ['google-status'],
    queryFn: () => api.get<{ enabled: boolean }>('/auth/google/status'),
    staleTime: 5 * 60_000,
  })

  const info = account.data

  const connectGoogle = async () => {
    setNote(null)
    try {
      // The browser cannot send an Authorization header on a plain navigation,
      // so the link intent is registered server side first and the returned URL
      // carries a state value bound to this account.
      const { url } = await api.get<{ url: string }>('/auth/google/start?mode=link')
      window.location.href = url
    } catch (err) {
      setNote({ kind: 'err', text: err instanceof ApiError ? err.message : 'Could not start linking.' })
    }
  }

  const unlink = useMutation({
    mutationFn: () => api.post<{ linked: boolean }>('/auth/google/unlink'),
    onSuccess: () => {
      setNote({ kind: 'ok', text: 'Google account disconnected. Your password still works.' })
      queryClient.invalidateQueries({ queryKey: ['account'] })
    },
    onError: (err) =>
      setNote({ kind: 'err', text: err instanceof ApiError ? err.message : 'Could not disconnect.' }),
  })

  const changePassword = useMutation({
    mutationFn: async () => {
      if (info?.has_password) {
        // Invalidates every session including this one, so sign out locally.
        await api.post('/auth/change-password', { current_password: currentPw, new_password: newPw })
        return 'changed' as const
      }
      await api.post('/auth/set-password', { new_password: newPw })
      return 'set' as const
    },
    onSuccess: (kind) => {
      setCurrentPw(''); setNewPw(''); setConfirmPw('')
      queryClient.invalidateQueries({ queryKey: ['account'] })
      if (kind === 'changed') {
        setNote({ kind: 'ok', text: 'Password changed. Every session was signed out - please sign in again.' })
        setAuth(null)
        setProfile(null)
      } else {
        setNote({ kind: 'ok', text: 'Password set. You can now sign in with your username too, and disconnect Google whenever you like.' })
      }
    },
    onError: (err) =>
      setNote({ kind: 'err', text: err instanceof ApiError ? err.message : 'Could not update the password.' }),
  })

  if (!auth) {
    return (
      <div className="col" style={{ gap: 10, paddingTop: '6vh', maxWidth: 520 }}>
        <h2>Account</h2>
        <p className="muted">
          You are using this device without an account, so there is nothing to manage. Create an
          account to sign in from other devices and to keep your progress on the server.
        </p>
      </div>
    )
  }

  return (
    <div className="col" style={{ gap: 18, maxWidth: 640 }}>
      <div>
        <h2 style={{ marginBottom: 4 }}>Account</h2>
        <p className="muted small">
          Signed in as <strong>{info?.username ?? auth.user.username}</strong>
          {info?.is_admin && <span className="tiny"> · administrator</span>}
        </p>
      </div>

      {note &&
        (note.kind === 'err' ? (
          <ErrorNote message={note.text} onRetry={() => setNote(null)} />
        ) : (
          <div className="card" style={{ borderLeft: '3px solid #3fb950' }}>
            <span className="small">{note.text}</span>
          </div>
        ))}

      <section className="card col" style={{ gap: 10 }}>
        <h3 style={{ marginBottom: 0 }}>Ways to sign in</h3>

        <div className="list-row">
          <span className="grow">
            <span style={{ display: 'block', fontWeight: 650 }}>Username and password</span>
            <span className="tiny dim">
              {info?.has_password
                ? `Username: ${info.username}`
                : 'Not set yet — this account was created with Google.'}
            </span>
          </span>
          <span className="tiny" style={{ color: info?.has_password ? '#3fb950' : '#d29922' }}>
            {info?.has_password ? 'Active' : 'Not set'}
          </span>
        </div>

        <div className="list-row">
          <span className="grow">
            <span style={{ display: 'block', fontWeight: 650 }}>Google</span>
            <span className="tiny dim">
              {info?.google_linked ? info.google_email ?? 'Linked' : 'Not linked'}
            </span>
          </span>
          {info?.google_linked ? (
            <Button variant="ghost" size="sm" onClick={() => unlink.mutate()} disabled={unlink.isPending}>
              {unlink.isPending ? 'Working…' : 'Disconnect'}
            </Button>
          ) : google.data?.enabled ? (
            <Button size="sm" onClick={connectGoogle}>
              Connect
            </Button>
          ) : (
            <span className="tiny dim">Unavailable</span>
          )}
        </div>

        {info?.google_linked && !info.has_password && (
          <p className="tiny dim" style={{ lineHeight: 1.5 }}>
            Google is currently your only way in. Set a password below before disconnecting it,
            otherwise you would lock yourself out — the server will refuse the disconnect until
            you do.
          </p>
        )}

        {info && (
          <p className="tiny dim" style={{ lineHeight: 1.6 }}>
            Both methods open the same account and the same progress. Linking Google does not
            create a second account, and disconnecting it does not delete anything.
          </p>
        )}
      </section>

      <section className="card col" style={{ gap: 10 }}>
        <h3 style={{ marginBottom: 0 }}>{info?.has_password ? 'Change password' : 'Set a password'}</h3>

        <form
          className="col"
          style={{ gap: 10 }}
          onSubmit={(e) => {
            e.preventDefault()
            setNote(null)
            if (newPw.length < 6) return setNote({ kind: 'err', text: 'Password must be at least 6 characters.' })
            if (newPw !== confirmPw) return setNote({ kind: 'err', text: 'The two passwords do not match.' })
            if (info?.has_password && !currentPw) return setNote({ kind: 'err', text: 'Enter your current password.' })
            changePassword.mutate()
          }}
        >
          {info?.has_password && (
            <label className="col" style={{ gap: 4 }}>
              <span className="tiny dim">Current password</span>
              <input
                type="password"
                value={currentPw}
                onChange={(e) => setCurrentPw(e.target.value)}
                autoComplete="current-password"
              />
            </label>
          )}
          <label className="col" style={{ gap: 4 }}>
            <span className="tiny dim">New password</span>
            <input
              type="password"
              value={newPw}
              onChange={(e) => setNewPw(e.target.value)}
              autoComplete="new-password"
              placeholder="At least 6 characters"
            />
          </label>
          <label className="col" style={{ gap: 4 }}>
            <span className="tiny dim">Confirm new password</span>
            <input
              type="password"
              value={confirmPw}
              onChange={(e) => setConfirmPw(e.target.value)}
              autoComplete="new-password"
            />
          </label>

          {info?.has_password && (
            <p className="tiny dim" style={{ lineHeight: 1.5 }}>
              Changing your password signs out every device, including this one. That is deliberate:
              it is how you reclaim an account you think someone else has used.
            </p>
          )}

          <Button type="submit" disabled={changePassword.isPending}>
            {changePassword.isPending ? 'Working…' : info?.has_password ? 'Change password' : 'Set password'}
          </Button>
        </form>
      </section>

      {info && (
        <section className="col" style={{ gap: 4 }}>
          <h3>Session</h3>
          <p className="tiny dim">
            Account created {info.created_at ? info.created_at.slice(0, 10) : '—'} · last sign-in{' '}
            {info.last_login_at ? info.last_login_at.replace('T', ' ').replace('Z', '') : '—'}
          </p>
        </section>
      )}
    </div>
  )
}
