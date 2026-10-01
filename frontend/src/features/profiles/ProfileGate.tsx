import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '@/shared/api/client'
import { useAppStore } from '@/app/store'
import { BRAND } from '@/shared/brand'
import type { Profile } from '@/shared/types'
import { Button, ErrorNote } from '@/shared/ui/primitives'
import { fmtInt, fmtPct } from '@/shared/lib/format'

/**
 * Local profile picker. No accounts, no email, no sign-up — the brief is explicit
 * that the MVP must not require an online identity.
 */
export function ProfileGate() {
  const setProfile = useAppStore((s) => s.setProfile)
  const setLocalMode = useAppStore((s) => s.setLocalMode)
  const queryClient = useQueryClient()
  const [name, setName] = useState('')
  const [creating, setCreating] = useState(false)

  // Local mode is a remembered choice, and this screen is what that choice
  // lands on. Two things must not trap anyone here:
  //
  //  - A public server can disable account-free profiles entirely. Showing a
  //    "Create profile" button that answers 400 would strand the visitor with
  //    no way forward, so fall back to the sign-in screen instead.
  //  - Even when local mode IS allowed, someone who picked it by accident has
  //    to be able to reach accounts. The button at the bottom is that door.
  const config = useQuery({
    queryKey: ['public-config'],
    queryFn: () => api.get<{ allow_local_profiles: boolean }>('/config'),
    staleTime: 5 * 60_000,
  })
  useEffect(() => {
    if (config.data && config.data.allow_local_profiles === false) setLocalMode(false)
  }, [config.data, setLocalMode])

  const { data, isError, error, refetch } = useQuery({
    queryKey: ['profiles'],
    queryFn: () => api.get<{ profiles: Profile[] }>('/profiles'),
  })

  const create = useMutation({
    mutationFn: (display_name: string) => api.post<{ profile: Profile }>('/profiles', { display_name }),
    onSuccess: async ({ profile }) => {
      await api.post(`/profiles/${profile.id}/activate`)
      queryClient.invalidateQueries({ queryKey: ['profiles'] })
      setProfile({ ...profile, is_active: true })
      setName('')
      setCreating(false)
    },
  })

  const choose = async (profile: Profile) => {
    await api.post(`/profiles/${profile.id}/activate`)
    setProfile(profile)
  }

  const profiles = data?.profiles ?? []

  return (
    <div className="shell" style={{ paddingTop: '8vh', maxWidth: 560 }}>
      <div className="row" style={{ justifyContent: 'center', gap: 10, marginBottom: 8 }}>
        <span className="brand-mark" style={{ width: 34, height: 34, fontSize: 18 }}>
          {BRAND.mark}
        </span>
        <h1 style={{ fontSize: 28 }}>{BRAND.name}</h1>
      </div>
      <p className="center muted" style={{ marginBottom: 30 }}>
        {BRAND.tagline}
      </p>

      {isError && (
        <ErrorNote
          message={`Cannot reach the local backend. Start it with "python scripts/dev.py". ${(error as Error)?.message ?? ''}`}
          onRetry={() => refetch()}
        />
      )}

      <div className="col" style={{ gap: 8 }}>
        {profiles.map((profile) => (
          <button key={profile.id} className="list-row" onClick={() => choose(profile)}>
            <span className="avatar" style={{ width: 38, height: 38, fontSize: 15 }}>
              {(profile.display_name ?? '?').charAt(0).toUpperCase()}
            </span>
            <span className="grow">
              <span style={{ display: 'block', fontWeight: 650 }}>{profile.display_name}</span>
              <span className="tiny dim">
                Level {profile.level} · {fmtInt(profile.xp_total)} XP
                {profile.questions_answered ? ` · ${fmtInt(profile.questions_answered)} answered · ${fmtPct(profile.accuracy ?? 0)} accuracy` : ''}
              </span>
            </span>
            <span className="chip">Play →</span>
          </button>
        ))}
      </div>

      {creating ? (
        <form
          className="card"
          style={{ marginTop: 14 }}
          onSubmit={(event) => {
            event.preventDefault()
            if (name.trim()) create.mutate(name.trim())
          }}
        >
          <label className="tiny dim" htmlFor="new-profile">
            Nickname (stored locally only)
          </label>
          <div className="row" style={{ marginTop: 8 }}>
            <input
              id="new-profile"
              className="input grow"
              value={name}
              maxLength={24}
              autoFocus
              placeholder="e.g. Sayan"
              onChange={(event) => setName(event.target.value)}
            />
            <Button type="submit" variant="primary" disabled={!name.trim() || create.isPending}>
              {create.isPending ? 'Creating…' : 'Create'}
            </Button>
          </div>
          {create.isError && (
            <p className="tiny" style={{ color: 'var(--error)', marginTop: 8 }}>
              {(create.error as Error).message}
            </p>
          )}
        </form>
      ) : (
        <Button className="btn-block" style={{ marginTop: 14 }} onClick={() => setCreating(true)}>
          + Create profile
        </Button>
      )}

      <p className="tiny dim center" style={{ marginTop: 26 }}>
        Everything is stored on this device. No account, no email, no internet required.
      </p>

      <div style={{ borderTop: '1px solid rgba(255,255,255,.08)', marginTop: 6, paddingTop: 14 }}>
        <button
          type="button"
          className="nav-link"
          style={{ width: '100%' }}
          onClick={() => setLocalMode(false)}
        >
          Sign in or create an account instead
        </button>
        <p className="tiny dim center" style={{ marginTop: 6 }}>
          An account keeps your progress on the server, so it follows you to other devices.
        </p>
      </div>
    </div>
  )
}
