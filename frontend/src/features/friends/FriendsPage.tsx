import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api, ApiError } from '@/shared/api/client'
import { useAppStore } from '@/app/store'
import { Button, ErrorNote } from '@/shared/ui/primitives'

interface Person {
  user_id: string
  username: string
  display_name: string
  level: number
  xp_total: number
  streak_day_count: number
  last_active_day?: string | null
}

interface Pending extends Person {
  request_id: string
  status?: string
  created_at?: string
}

interface BoardEntry extends Person {
  rank: number
  is_self: boolean
}

interface SearchResult extends Person {
  /** none | friends | outgoing | incoming - decides what the button does. */
  relationship: 'none' | 'friends' | 'outgoing' | 'incoming'
}

/**
 * Friends: invitations, approval, the friend list and a friends-only board.
 *
 * The global leaderboard stays on the Progress page. This one is scoped server
 * side to people you have actually added, which is the point of it - a class of
 * thirty competing against each other, not against every account that exists.
 */
export function FriendsPage() {
  const auth = useAppStore((s) => s.auth)
  const queryClient = useQueryClient()
  const [name, setName] = useState('')
  const [term, setTerm] = useState('')
  const [note, setNote] = useState<{ kind: 'ok' | 'err'; text: string } | null>(null)

  const refresh = () => {
    queryClient.invalidateQueries({ queryKey: ['friends'] })
    queryClient.invalidateQueries({ queryKey: ['friend-requests'] })
    queryClient.invalidateQueries({ queryKey: ['friend-leaderboard'] })
  }

  const friends = useQuery({
    queryKey: ['friends'],
    queryFn: () => api.get<{ friends: Person[]; friend_count: number; incoming_count: number }>('/friends'),
  })
  const requests = useQuery({
    queryKey: ['friend-requests'],
    queryFn: () => api.get<{ incoming: Pending[]; outgoing: Pending[] }>('/friends/requests'),
  })
  const board = useQuery({
    queryKey: ['friend-leaderboard'],
    queryFn: () => api.get<{ entries: BoardEntry[] }>('/friends/leaderboard'),
  })
  // Two characters minimum, matching the server, and debounced by the query key
  // so typing does not fire a request per keystroke into a remote database.
  const search = useQuery({
    queryKey: ['friend-search', term.trim().toLowerCase()],
    queryFn: () => api.get<{ results: SearchResult[] }>(`/friends/search?q=${encodeURIComponent(term.trim())}`),
    enabled: term.trim().length >= 2,
  })

  const send = useMutation({
    mutationFn: (username: string) => api.post<{ status: string }>('/friends/request', { username }),
    onSuccess: (r) => {
      setNote({
        kind: 'ok',
        text: r.status === 'accepted' ? `You are now friends.` : `Request sent.`,
      })
      setName('')
      refresh()
      queryClient.invalidateQueries({ queryKey: ['friend-search'] })
    },
    onError: (err) =>
      setNote({ kind: 'err', text: err instanceof ApiError ? err.message : 'Could not send the request.' }),
  })

  if (!auth) {
    return (
      <div className="col" style={{ gap: 10, paddingTop: '6vh', maxWidth: 520 }}>
        <h2>Friends need an account</h2>
        <p className="muted">
          Invitations are tied to a signed-in account, so this page is only available when you
          have one. Create an account to add friends and compete on a friends-only leaderboard.
        </p>
      </div>
    )
  }

  const incoming = requests.data?.incoming ?? []
  const outgoing = requests.data?.outgoing ?? []
  const pendingOut = outgoing.filter((o) => o.status === 'pending')
  const list = friends.data?.friends ?? []
  const entries = board.data?.entries ?? []

  return (
    <div className="col" style={{ gap: 18 }}>
      <div>
        <h2 style={{ marginBottom: 4 }}>Friends</h2>
        <p className="muted small">
          Add classmates by username. They have to accept before either of you appears on the
          other's list.
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

      <section className="col" style={{ gap: 8 }}>
        <h3>Find someone</h3>
        <input
          value={term}
          onChange={(e) => setTerm(e.target.value)}
          placeholder="Type at least 2 characters of a username or name"
          autoCapitalize="none"
          spellCheck={false}
        />
        {term.trim().length < 2 ? (
          <p className="tiny dim">Search needs two characters, so this is not a list of every student.</p>
        ) : search.isFetching ? (
          <p className="tiny dim">Searching…</p>
        ) : (search.data?.results ?? []).length === 0 ? (
          <p className="tiny dim">Nobody matches “{term.trim()}”. Usernames are all lowercase.</p>
        ) : (
          <div className="col" style={{ gap: 4 }}>
            {(search.data?.results ?? []).map((r) => (
              <div key={r.user_id} className="list-row">
                <span className="avatar" style={{ width: 34, height: 34, fontSize: 14 }}>
                  {(r.display_name ?? '?').charAt(0).toUpperCase()}
                </span>
                <span className="grow">
                  <span style={{ display: 'block', fontWeight: 650 }}>
                    {r.display_name} <span className="tiny dim">@{r.username}</span>
                  </span>
                  <span className="tiny dim">Level {r.level} · {r.xp_total.toLocaleString()} XP</span>
                </span>
                {r.relationship === 'friends' && <span className="tiny" style={{ color: '#3fb950' }}>Friends</span>}
                {r.relationship === 'outgoing' && <span className="tiny dim">Request sent</span>}
                {r.relationship === 'incoming' && <span className="tiny dim">Wants to add you</span>}
                {r.relationship === 'none' && (
                  <Button size="sm" onClick={() => send.mutate(r.username)} disabled={send.isPending}>
                    Add
                  </Button>
                )}
              </div>
            ))}
          </div>
        )}
      </section>

      <form
        className="row"
        style={{ gap: 8, flexWrap: 'wrap' }}
        onSubmit={(e) => {
          e.preventDefault()
          if (name.trim()) send.mutate(name.trim())
        }}
      >
        <input
          className="grow"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Username to add"
          autoCapitalize="none"
          spellCheck={false}
          style={{ minWidth: 180 }}
        />
        <Button type="submit" disabled={send.isPending || !name.trim()}>
          {send.isPending ? 'Sending…' : 'Send request'}
        </Button>
      </form>

      {incoming.length > 0 && (
        <section className="col" style={{ gap: 8 }}>
          <h3>
            Requests for you <span className="dim">({incoming.length})</span>
          </h3>
          {incoming.map((r) => (
            <RequestRow
              key={r.request_id}
              person={r}
              actions={
                <>
                  <AcceptButton requestId={r.request_id} onDone={refresh} onError={setNote} />
                  <DeclineButton requestId={r.request_id} onDone={refresh} onError={setNote} />
                </>
              }
            />
          ))}
        </section>
      )}

      {pendingOut.length > 0 && (
        <section className="col" style={{ gap: 8 }}>
          <h3>
            Waiting on a reply <span className="dim">({pendingOut.length})</span>
          </h3>
          {pendingOut.map((r) => (
            <RequestRow
              key={r.request_id}
              person={r}
              subtitle="Request sent — waiting for them to accept"
              actions={<CancelButton requestId={r.request_id} onDone={refresh} onError={setNote} />}
            />
          ))}
        </section>
      )}

      <section className="col" style={{ gap: 8 }}>
        <h3>
          Your friends <span className="dim">({list.length})</span>
        </h3>
        {list.length === 0 ? (
          <p className="muted small">
            No friends yet. Add someone above — nothing shows on either list until they accept.
          </p>
        ) : (
          list.map((f) => (
            <RequestRow
              key={f.user_id}
              person={f}
              actions={<RemoveButton userId={f.user_id} name={f.display_name} onDone={refresh} onError={setNote} />}
            />
          ))
        )}
      </section>

      <section className="col" style={{ gap: 8 }}>
        <h3>Friends leaderboard</h3>
        {entries.length === 0 ? (
          <p className="muted small">Your board fills up as soon as you have a friend.</p>
        ) : (
          <div className="col" style={{ gap: 4 }}>
            {entries.map((e) => (
              <div
                key={e.user_id}
                className="list-row"
                style={e.is_self ? { borderLeft: '3px solid #58a6ff' } : undefined}
              >
                <span className="avatar" style={{ width: 32, height: 32, fontSize: 13 }}>
                  {e.rank}
                </span>
                <span className="grow">
                  <span style={{ display: 'block', fontWeight: 650 }}>
                    {e.display_name}
                    {e.is_self && <span className="tiny dim"> (you)</span>}
                  </span>
                  <span className="tiny dim">Level {e.level} · {e.xp_total.toLocaleString()} XP</span>
                </span>
                <span className="tiny dim">{e.streak_day_count}d streak</span>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  )
}

function RequestRow({
  person,
  subtitle,
  actions,
}: {
  person: Person
  subtitle?: string
  actions: React.ReactNode
}) {
  return (
    <div className="list-row">
      <span className="avatar" style={{ width: 38, height: 38, fontSize: 15 }}>
        {(person.display_name ?? '?').charAt(0).toUpperCase()}
      </span>
      <span className="grow">
        <span style={{ display: 'block', fontWeight: 650 }}>{person.display_name}</span>
        <span className="tiny dim">
          {subtitle ?? `Level ${person.level} · ${person.xp_total.toLocaleString()} XP`}
        </span>
      </span>
      <span className="row" style={{ gap: 6 }}>
        {actions}
      </span>
    </div>
  )
}

type NoteSetter = (n: { kind: 'ok' | 'err'; text: string } | null) => void

function useAction(
  path: string,
  body: unknown,
  onDone: () => void,
  onError: NoteSetter,
  okText: string,
) {
  return useMutation({
    mutationFn: () => api.post<Record<string, unknown>>(path, body),
    onSuccess: () => {
      onError({ kind: 'ok', text: okText })
      onDone()
    },
    onError: (err) => onError({ kind: 'err', text: err instanceof ApiError ? err.message : 'Action failed.' }),
  })
}

function AcceptButton({ requestId, onDone, onError }: { requestId: string; onDone: () => void; onError: NoteSetter }) {
  const m = useAction('/friends/request/accept', { request_id: requestId }, onDone, onError, 'Request accepted.')
  return (
    <Button onClick={() => m.mutate()} disabled={m.isPending}>
      Accept
    </Button>
  )
}

function DeclineButton({ requestId, onDone, onError }: { requestId: string; onDone: () => void; onError: NoteSetter }) {
  const m = useAction('/friends/request/decline', { request_id: requestId }, onDone, onError, 'Request declined.')
  return (
    <Button variant="ghost" onClick={() => m.mutate()} disabled={m.isPending}>
      Decline
    </Button>
  )
}

function CancelButton({ requestId, onDone, onError }: { requestId: string; onDone: () => void; onError: NoteSetter }) {
  const m = useAction('/friends/request/cancel', { request_id: requestId }, onDone, onError, 'Request cancelled.')
  return (
    <Button variant="ghost" onClick={() => m.mutate()} disabled={m.isPending}>
      Cancel
    </Button>
  )
}

function RemoveButton({
  userId,
  name,
  onDone,
  onError,
}: {
  userId: string
  name: string
  onDone: () => void
  onError: NoteSetter
}) {
  const m = useAction('/friends/remove', { user_id: userId }, onDone, onError, `Removed ${name}.`)
  return (
    <Button variant="ghost" onClick={() => m.mutate()} disabled={m.isPending}>
      Remove
    </Button>
  )
}
