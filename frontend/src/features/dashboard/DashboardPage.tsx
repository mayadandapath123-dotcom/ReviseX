import { useNavigate } from 'react-router-dom'
import { useAiStatus, useDashboard, useLeaderboard, useModes } from '@/shared/api/queries'
import type { StartTestParams } from '@/shared/api/queries'
import { useAppStore } from '@/app/store'
import { Bar, Button, Card, Chip, Empty, Section, Skeleton, Stat } from '@/shared/ui/primitives'
import { fmtClock, fmtInt, fmtPct, fmtSeconds, greeting, relativeDay } from '@/shared/lib/format'

/** Dashboard: today's progress, one-tap quick start, continue, weak topics, PB. */
export function DashboardPage() {
  const profile = useAppStore((s) => s.profile)
  const navigate = useNavigate()
  const { data, isLoading, isError, error } = useDashboard()
  const { data: modes } = useModes()
  const { data: board } = useLeaderboard('today')
  const { data: ai } = useAiStatus()

  const play = (params: StartTestParams, label?: string) => navigate('/play', { state: { params, label } })

  if (isLoading) return <Skeleton height={120} count={3} />
  if (isError || !data) {
    // A status code means the server answered, so "cannot reach the backend"
    // would be a lie. Only a network failure gets that message.
    const status = (error as { status?: number } | null)?.status
    return (
      <Empty
        title={status ? `The server returned an error (${status})` : 'Cannot reach the local backend'}
        hint={
          status
            ? `${(error as Error)?.message ?? 'Unexpected response.'} If you recently reset progress, reload this page to pick a profile again.`
            : 'Run `python scripts/dev.py` from the project root, then reload.'
        }
      />
    )
  }

  const { today, lifetime, level, suggestions } = data
  const featured = modes?.modes.find((m) => m.featured) ?? modes?.modes.find((m) => m.key === 'rush_60s')
  const bestPB = board?.you

  return (
    <>
      <div className="row-between" style={{ marginTop: 26, marginBottom: 4 }}>
        <div>
          <h1>
            {greeting()}, {profile?.display_name} 👋
          </h1>
          <p className="muted small" style={{ marginTop: 4 }}>
            Level {level.level} · {level.name} · {fmtInt(level.xp)} XP
          </p>
        </div>
        <div className="col" style={{ alignItems: 'flex-end', gap: 4 }}>
          <Chip tone="accent">🔥 {lifetime.day_streak} day{lifetime.day_streak === 1 ? '' : 's'}</Chip>
          {data.srs.due > 0 && <Chip tone="info">{data.srs.due} due for review</Chip>}
        </div>
      </div>

      <div style={{ maxWidth: 320, marginTop: 10 }}>
        <Bar value={level.level_progress} />
        <p className="tiny dim" style={{ marginTop: 6 }}>
          {fmtInt(level.xp_into_level)} / {fmtInt(level.xp_for_next_level - (level.xp - level.xp_into_level))} XP to level{' '}
          {level.level + 1}
        </p>
      </div>

      <Section title="Today's progress">
        <Card>
          <div className="grid grid-4">
            <Stat label="Questions" value={fmtInt(today.questions)} />
            <Stat label="Accuracy" value={fmtPct(today.accuracy)} accent={today.accuracy >= 0.85} />
            <Stat label="Avg speed" value={fmtSeconds(today.avg_response_ms)} />
            <Stat label="XP today" value={`+${fmtInt(today.xp_today)}`} accent />
          </div>
        </Card>
      </Section>

      <Section title="Quick start">
        <div className="grid grid-4">
          <QuickTile
            emoji="⚡"
            title="1 Minute Science"
            subtitle="The classic sprint"
            primary
            onClick={() => featured && play({ mode_key: featured.key }, featured.name)}
          />
          <QuickTile emoji="🧪" title="Chemistry Rush" subtitle="Reactions & equations" onClick={() => play({ mode_key: 'rush_60s', branch: 'sci-chem' }, 'Chemistry Rush')} />
          <QuickTile emoji="⚙️" title="Physics Rush" subtitle="Formulas & numericals" onClick={() => play({ mode_key: 'rush_60s', branch: 'sci-phy' }, 'Physics Rush')} />
          <QuickTile emoji="🧬" title="Biology Rush" subtitle="Definitions & processes" onClick={() => play({ mode_key: 'rush_60s', branch: 'sci-bio' }, 'Biology Rush')} />
        </div>

        <div className="row wrap" style={{ marginTop: 12 }}>
          {(modes?.quick_start ?? [])
            .filter((m) => m.key !== featured?.key)
            .slice(0, 8)
            .map((mode) => (
              <Button key={mode.key} size="sm" onClick={() => play({ mode_key: mode.key }, mode.name)}>
                {mode.name}
              </Button>
            ))}
        </div>
      </Section>

      {suggestions.continue && (
        <Section title="Continue">
          <Card className="card-flat">
            <div className="row-between wrap">
              <div className="grow">
                <p style={{ fontWeight: 650 }}>{suggestions.continue.label}</p>
                <p className="small muted" style={{ marginTop: 3 }}>
                  {suggestions.continue.reason}
                  {suggestions.continue.chapter_name ? ` · ${suggestions.continue.chapter_name}` : ''}
                </p>
              </div>
              <div className="row">
                {typeof suggestions.continue.mastery === 'number' && (
                  <div style={{ width: 110 }}>
                    <Bar value={suggestions.continue.mastery} tone={suggestions.continue.mastery < 0.5 ? 'error' : 'accent'} />
                    <p className="tiny dim" style={{ marginTop: 4 }}>
                      {fmtPct(suggestions.continue.mastery)} mastery
                    </p>
                  </div>
                )}
                <Button
                  variant="primary"
                  onClick={() =>
                    play(
                      {
                        mode_key: suggestions.continue!.suggested_mode,
                        chapter: suggestions.continue!.chapter_id,
                        topic: suggestions.continue!.topic_id,
                      },
                      suggestions.continue!.label,
                    )
                  }
                >
                  Practice
                </Button>
              </div>
            </div>
          </Card>
        </Section>
      )}

      {suggestions.weak_topics.length > 0 && (
        <Section title="Weak topics">
          <div className="grid grid-3">
            {suggestions.weak_topics.slice(0, 6).map((topic: any) => (
              <button
                key={topic.topic_id}
                className="list-row"
                onClick={() => play({ mode_key: 'topic_test', topic: topic.topic_id, chapter: topic.chapter_id }, topic.topic_name)}
              >
                <span className="grow">
                  <span style={{ display: 'block', fontWeight: 600, fontSize: 14 }}>{topic.topic_name}</span>
                  <span className="tiny dim">{topic.chapter_name}</span>
                </span>
                <span className="chip chip-error">{fmtPct(topic.mastery)}</span>
              </button>
            ))}
          </div>
        </Section>
      )}

      <Section title="Personal best" action={<Button size="sm" variant="ghost" onClick={() => navigate('/progress')}>All records →</Button>}>
        <Card className="card-flat">
          {bestPB ? (
            <div className="row-between wrap">
              <div>
                <p className="tiny dim">
                  {bestPB.mode_key ?? 'Best session'} · {relativeDay(bestPB.achieved_at ?? null)}
                </p>
                <p style={{ fontSize: 30, fontWeight: 800, letterSpacing: '-0.03em' }}>{fmtInt(bestPB.score)}</p>
              </div>
              <div className="row" style={{ gap: 22 }}>
                <Stat label="Accuracy" value={fmtPct(bestPB.accuracy)} />
                <Stat label="Streak" value={`🔥 ${fmtInt(bestPB.best_streak ?? 0)}`} />
                {featured && (
                  <Button variant="primary" onClick={() => play({ mode_key: featured.key }, featured.name)}>
                    Beat it 🏆
                  </Button>
                )}
              </div>
            </div>
          ) : (
            <p className="muted small">No personal best yet — finish a test to set one.</p>
          )}
        </Card>
      </Section>

      <div className="grid grid-2" style={{ marginTop: 30 }}>
        <Card className="card-flat">
          <h3 className="section-title" style={{ marginBottom: 12 }}>Today's top scores</h3>
          {(board?.entries ?? []).length === 0 ? (
            <p className="muted small">No scores yet today.</p>
          ) : (
            <div className="col" style={{ gap: 6 }}>
              {board!.entries.slice(0, 5).map((entry: any) => (
                <div className="row" key={entry.profile_id}>
                  <span className="mono dim" style={{ width: 18 }}>{entry.rank}</span>
                  <span className="grow small" style={{ fontWeight: entry.profile_id === profile?.id ? 700 : 500 }}>
                    {entry.display_name}
                  </span>
                  <span className="mono small" style={{ fontWeight: 700 }}>{fmtInt(entry.score)}</span>
                </div>
              ))}
            </div>
          )}
          <p className="tiny dim" style={{ marginTop: 12 }}>
            Local leaderboard — profiles on this device only.
          </p>
        </Card>

        <Card className="card-flat">
          <h3 className="section-title" style={{ marginBottom: 12 }}>Recent sessions</h3>
          {data.recent_sessions.length === 0 ? (
            <p className="muted small">Nothing yet.</p>
          ) : (
            <div className="col" style={{ gap: 6 }}>
              {data.recent_sessions.map((session: any) => (
                <div className="row" key={session.session_id}>
                  <span className="grow small">{session.mode_name}</span>
                  <span className="tiny dim">{fmtPct(session.accuracy)}</span>
                  <span className="mono small" style={{ fontWeight: 700, minWidth: 54, textAlign: 'right' }}>
                    {fmtInt(session.score)}
                  </span>
                </div>
              ))}
            </div>
          )}
          <div className="row" style={{ marginTop: 12, gap: 8 }}>
            <Chip tone={ai?.available ? 'success' : undefined}>{ai?.active_provider === 'local' ? 'AI: offline generator' : `AI: ${ai?.active_provider}`}</Chip>
            <span className="tiny dim">{ai?.message}</span>
          </div>
        </Card>
      </div>

      <p className="tiny dim center" style={{ marginTop: 34 }}>
        Lifetime: {fmtInt(lifetime.questions_answered)} questions · {fmtPct(lifetime.accuracy)} accuracy ·{' '}
        {fmtSeconds(lifetime.avg_response_ms)} avg · fastest {lifetime.fastest_response_ms ? fmtSeconds(lifetime.fastest_response_ms) : '—'} ·{' '}
        {fmtInt(lifetime.sessions_completed)} tests · {fmtClock(0) === '00:00' ? '' : ''}
      </p>
    </>
  )
}

function QuickTile({
  emoji,
  title,
  subtitle,
  onClick,
  primary,
}: {
  emoji: string
  title: string
  subtitle: string
  onClick: () => void
  primary?: boolean
}) {
  return (
    <button
      className="list-row"
      onClick={onClick}
      style={
        primary
          ? { background: 'var(--accent-dim)', borderColor: 'color-mix(in srgb, var(--accent) 40%, var(--border))', flexDirection: 'column', alignItems: 'flex-start', gap: 4, padding: 16 }
          : { flexDirection: 'column', alignItems: 'flex-start', gap: 4, padding: 16 }
      }
    >
      <span style={{ fontSize: 20 }}>{emoji}</span>
      <span style={{ fontWeight: 650, fontSize: 14 }}>{title}</span>
      <span className="tiny dim">{subtitle}</span>
    </button>
  )
}
