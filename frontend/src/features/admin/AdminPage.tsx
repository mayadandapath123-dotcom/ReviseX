import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { api, ApiError, setAuthToken } from '@/shared/api/client'
import { useAppStore } from '@/app/store'
import { Button, ErrorNote } from '@/shared/ui/primitives'

interface Overview {
  users_total: number
  users_online_now: number
  users_seen_today: number
  users_active_today: number
  admins: number
  google_linked: number
  answers_today: number
  answers_total: number
  questions_available: number
  online_window_minutes: number
  server_time: string
}

interface AdminUserRow {
  user_id: string
  username: string
  display_name: string
  google_email: string | null
  provider: string
  is_admin: boolean
  profile_id: string | null
  level: number
  xp_total: number
  streak_day_count: number
  answers: number
  accuracy: number | null
  sessions: number
  created_at: string | null
  last_login_at: string | null
  last_seen_at: string | null
  online_now: boolean
}

interface AuditEntry {
  id: string
  action: string
  detail: string | null
  created_at: string
  admin_username: string | null
  target_username: string | null
}

type SortKey = 'last_seen' | 'xp' | 'streak' | 'answered' | 'username' | 'created'

/**
 * Owner's view of the platform: who is here, what they have done, and - when
 * genuinely needed - a supervised look inside one account.
 *
 * Impersonation is deliberately friction-heavy: it is a separate explicit
 * action, it shows a banner that cannot be dismissed by navigating, it expires
 * after two hours, and every use is written to an audit log the admin can see.
 * That is not decoration. A control that silently lets an owner browse as a
 * student becomes indistinguishable from abuse, to the students and to the
 * owner later.
 */
export function AdminPage() {
  const auth = useAppStore((s) => s.auth)
  const setImpersonating = useAppStore((s) => s.setImpersonating)
  const setProfile = useAppStore((s) => s.setProfile)
  const queryClient = useQueryClient()
  const navigate = useNavigate()

  const [search, setSearch] = useState('')
  const [sort, setSort] = useState<SortKey>('last_seen')
  const [confirmId, setConfirmId] = useState<string | null>(null)

  const overview = useQuery({
    queryKey: ['admin-overview'],
    queryFn: () => api.get<Overview>('/admin/overview'),
    refetchInterval: 30_000,
  })
  const userList = useQuery({
    queryKey: ['admin-users', search, sort],
    queryFn: () =>
      api.get<{ users: AdminUserRow[]; total: number }>(
        `/admin/users?q=${encodeURIComponent(search)}&sort=${sort}&limit=100`,
      ),
    refetchInterval: 30_000,
  })
  const audit = useQuery({
    queryKey: ['admin-audit'],
    queryFn: () => api.get<{ entries: AuditEntry[] }>('/admin/audit?limit=50'),
  })

  const impersonate = useMutation({
    mutationFn: (userId: string) =>
      api.post<{ token: string; username: string; expires_in_minutes: number }>(
        `/admin/users/${userId}/impersonate`,
        { user_id: userId, reason: 'owner support' },
      ),
    onSuccess: (result) => {
      if (!auth) return
      // Swap the live token so every subsequent request acts as the student,
      // but keep the admin's own token to get back.
      setAuthToken(result.token)
      setImpersonating({
        adminToken: auth.token,
        adminUsername: auth.user.username,
        targetUsername: result.username,
        expiresAt: Date.now() + result.expires_in_minutes * 60_000,
      })
      queryClient.clear()
      // The store still holds the ADMIN's profile. Without re-reading it the
      // dashboard would show the admin's numbers under the student's session.
      setProfile(null)
      api
        .get<{ profile: unknown }>('/auth/me')
        .then((me) => { if (me.profile) setProfile(me.profile as never) })
        .catch(() => undefined)
      navigate('/')
    },
  })

  if (overview.isError) {
    const status = (overview.error as ApiError)?.status
    return (
      <div className="col" style={{ gap: 10, paddingTop: '6vh', maxWidth: 560 }}>
        <h2>Admin</h2>
        {status === 403 ? (
          <p className="muted">
            This area is restricted. Your account is not an administrator. To grant yourself
            access, set <code>ADMIN_USERNAMES</code> to your username in the Render environment
            and sign up (or sign in) again.
          </p>
        ) : (
          <ErrorNote
            message={(overview.error as Error)?.message ?? 'Could not load the admin panel.'}
            onRetry={() => overview.refetch()}
          />
        )}
      </div>
    )
  }

  const o = overview.data
  const rows = userList.data?.users ?? []

  return (
    <div className="col" style={{ gap: 18 }}>
      <div>
        <h2 style={{ marginBottom: 4 }}>Admin</h2>
        <p className="muted small">
          Live platform usage. Refreshes every 30 seconds.
          {o && ` Server time ${o.server_time.replace('T', ' ').replace('Z', '')}.`}
        </p>
      </div>

      {o && (
        <div className="grid" style={{ display: 'grid', gap: 10, gridTemplateColumns: 'repeat(auto-fit,minmax(150px,1fr))' }}>
          <Stat label="Online now" value={o.users_online_now} hint={`seen in the last ${o.online_window_minutes} min`} accent />
          <Stat label="Accounts" value={o.users_total} hint={`${o.admins} admin · ${o.google_linked} Google`} />
          <Stat label="Active today" value={o.users_active_today} hint={`${o.users_seen_today} signed in today`} />
          <Stat label="Answers today" value={o.answers_today} hint={`${o.answers_total.toLocaleString()} all time`} />
          <Stat label="Question bank" value={o.questions_available} hint="approved items" />
        </div>
      )}

      <section className="col" style={{ gap: 8 }}>
        <div className="row" style={{ gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
          <h3 style={{ margin: 0, flex: 1 }}>
            Students <span className="dim">({userList.data?.total ?? 0})</span>
          </h3>
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search username, name or email"
            style={{ minWidth: 200 }}
            autoCapitalize="none"
            spellCheck={false}
          />
          <select value={sort} onChange={(e) => setSort(e.target.value as SortKey)}>
            <option value="last_seen">Last seen</option>
            <option value="xp">XP</option>
            <option value="streak">Streak</option>
            <option value="answered">Answers</option>
            <option value="username">Username</option>
            <option value="created">Newest</option>
          </select>
        </div>

        {userList.isError && (
          <ErrorNote message={(userList.error as Error)?.message ?? 'Could not load accounts.'} onRetry={() => userList.refetch()} />
        )}

        {rows.length === 0 ? (
          <p className="muted small">No accounts match.</p>
        ) : (
          <div className="col" style={{ gap: 4 }}>
            {rows.map((u) => (
              <div key={u.user_id} className="card" style={{ padding: '10px 12px' }}>
                <div className="row" style={{ gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
                  <span
                    title={u.online_now ? 'Online now' : `Last seen ${u.last_seen_at ?? 'never'}`}
                    style={{
                      width: 9, height: 9, borderRadius: '50%', flexShrink: 0,
                      background: u.online_now ? '#3fb950' : 'rgba(255,255,255,.18)',
                    }}
                  />
                  <span className="grow" style={{ minWidth: 140 }}>
                    <span style={{ display: 'block', fontWeight: 650 }}>
                      {u.display_name}
                      <span className="tiny dim"> @{u.username}</span>
                      {u.is_admin && <span className="tiny" style={{ color: '#d29922' }}> · admin</span>}
                    </span>
                    <span className="tiny dim">
                      Lvl {u.level} · {u.xp_total.toLocaleString()} XP · {u.streak_day_count}d streak ·{' '}
                      {u.answers.toLocaleString()} answers
                      {u.accuracy !== null && ` · ${Math.round(u.accuracy * 100)}%`}
                      {u.google_email && ` · ${u.google_email}`}
                    </span>
                  </span>
                  <span className="tiny dim" style={{ textAlign: 'right', minWidth: 120 }}>
                    {u.online_now ? 'online now' : u.last_seen_at ? `seen ${shortTime(u.last_seen_at)}` : 'never seen'}
                  </span>
                  {confirmId === u.user_id ? (
                    <span className="row" style={{ gap: 6 }}>
                      <Button
                        size="sm"
                        disabled={impersonate.isPending}
                        onClick={() => impersonate.mutate(u.user_id)}
                      >
                        {impersonate.isPending ? 'Entering…' : 'Yes, enter'}
                      </Button>
                      <Button size="sm" variant="ghost" onClick={() => setConfirmId(null)}>
                        Cancel
                      </Button>
                    </span>
                  ) : (
                    <Button size="sm" variant="ghost" onClick={() => setConfirmId(u.user_id)}>
                      View as
                    </Button>
                  )}
                </div>
                {confirmId === u.user_id && (
                  <p className="tiny" style={{ marginTop: 8, lineHeight: 1.5, color: '#d29922' }}>
                    You are about to open {u.username}'s account as if you were them, for two hours.
                    They will not be notified, so this should only be for support they would agree
                    to. It is written to the audit log below.
                  </p>
                )}
              </div>
            ))}
          </div>
        )}
      </section>

      {impersonate.isError && (
        <ErrorNote message={(impersonate.error as ApiError)?.message ?? 'Could not enter that account.'} onRetry={() => setConfirmId(null)} />
      )}

      <section className="col" style={{ gap: 8 }}>
        <h3>Audit log</h3>
        <p className="tiny dim">
          Every admin entry into a student account. This list is written by the server and is not
          deletable from the app.
        </p>
        {(audit.data?.entries ?? []).length === 0 ? (
          <p className="muted small">Nothing recorded yet.</p>
        ) : (
          <div className="col" style={{ gap: 4 }}>
            {(audit.data?.entries ?? []).map((e) => (
              <div key={e.id} className="list-row">
                <span className="grow">
                  <span style={{ display: 'block' }} className="small">
                    <strong>{e.admin_username ?? '?'}</strong> → <strong>{e.target_username ?? '?'}</strong>{' '}
                    <span className="tiny dim">({e.action})</span>
                  </span>
                  <span className="tiny dim">{e.detail}</span>
                </span>
                <span className="tiny dim">{shortTime(e.created_at)}</span>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  )
}

function Stat({ label, value, hint, accent }: { label: string; value: number; hint?: string; accent?: boolean }) {
  return (
    <div className="card" style={{ padding: '12px 14px', borderLeft: accent ? '3px solid #3fb950' : undefined }}>
      <div style={{ fontSize: 26, fontWeight: 700, lineHeight: 1.1 }}>{value.toLocaleString()}</div>
      <div className="small" style={{ fontWeight: 600, marginTop: 2 }}>{label}</div>
      {hint && <div className="tiny dim" style={{ marginTop: 2 }}>{hint}</div>}
    </div>
  )
}

/** Compact relative-ish time; the raw ISO string is too long for a table cell. */
function shortTime(iso: string): string {
  const t = Date.parse(iso.endsWith('Z') ? iso : iso + 'Z')
  if (Number.isNaN(t)) return iso.slice(0, 16).replace('T', ' ')
  const mins = Math.round((Date.now() - t) / 60000)
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.round(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  const days = Math.round(hrs / 24)
  if (days < 7) return `${days}d ago`
  return new Date(t).toISOString().slice(0, 10)
}
