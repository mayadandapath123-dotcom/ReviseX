import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'
import { api } from '@/shared/api/client'
import { useBadges, useBests, useDashboard, useLeaderboard, useMastery } from '@/shared/api/queries'
import { useAppStore } from '@/app/store'
import { Bar, Button, Card, Chip, Empty, Section, Skeleton, Stat } from '@/shared/ui/primitives'
import { fmtInt, fmtPct, fmtSeconds, relativeDay } from '@/shared/lib/format'
import type { Profile } from '@/shared/types'

const METRIC_LABEL: Record<string, string> = {
  score: 'Highest score',
  accuracy: 'Best accuracy',
  fastest_avg: 'Fastest average',
  longest_streak: 'Longest streak',
  most_questions: 'Most questions',
}

export function ProgressPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const profile = useAppStore((s) => s.profile)
  const setProfile = useAppStore((s) => s.setProfile)
  const [scope, setScope] = useState<'today' | 'week' | 'all'>('today')
  const [renaming, setRenaming] = useState(false)
  const [name, setName] = useState(profile?.display_name ?? '')

  const { data: dash, isLoading } = useDashboard()
  const { data: bests } = useBests()
  const { data: badges } = useBadges()
  const { data: mastery } = useMastery()
  const { data: board } = useLeaderboard(scope)

  if (isLoading || !dash) return <Skeleton height={110} count={4} />

  const { lifetime, level, today } = dash
  const modeBests = (bests?.personal_bests ?? []).filter((b: any) => b.scope === 'mode')
  const chapterBests = (bests?.personal_bests ?? []).filter((b: any) => b.scope === 'chapter')
  const topics = (mastery?.topics ?? []).slice(0, 14)

  const rename = async () => {
    if (!profile || !name.trim()) return
    const updated = await api.patch<{ profile: Profile }>(`/profiles/${profile.id}`, { display_name: name.trim() })
    setProfile(updated.profile)
    queryClient.invalidateQueries()
    setRenaming(false)
  }

  return (
    <>
      <div className="row-between wrap" style={{ marginTop: 26 }}>
        <div className="row" style={{ gap: 14 }}>
          <span className="avatar" style={{ width: 52, height: 52, fontSize: 22 }}>
            {(profile?.display_name ?? '?').charAt(0).toUpperCase()}
          </span>
          <div>
            {renaming ? (
              <div className="row">
                <input className="input" style={{ width: 180 }} value={name} maxLength={24} autoFocus onChange={(e) => setName(e.target.value)} />
                <Button size="sm" variant="primary" onClick={rename}>Save</Button>
                <Button size="sm" variant="ghost" onClick={() => setRenaming(false)}>Cancel</Button>
              </div>
            ) : (
              <h1>{profile?.display_name}</h1>
            )}
            <p className="muted small" style={{ marginTop: 3 }}>
              Level {level.level} · {level.name} · {fmtInt(level.xp)} XP
            </p>
          </div>
        </div>
        <div className="row">
          {!renaming && <Button size="sm" variant="ghost" onClick={() => { setName(profile?.display_name ?? ''); setRenaming(true) }}>Rename</Button>}
          <Button size="sm" variant="ghost" onClick={() => { setProfile(null); navigate('/') }}>Switch profile</Button>
        </div>
      </div>

      <div style={{ maxWidth: 380, marginTop: 12 }}>
        <Bar value={level.level_progress} />
        <p className="tiny dim" style={{ marginTop: 6 }}>
          {fmtInt(level.xp_into_level)} / {fmtInt(level.xp_for_next_level - level.xp + level.xp_into_level)} XP to level {level.level + 1}
        </p>
      </div>

      <Section title="Lifetime">
        <Card>
          <div className="grid grid-4">
            <Stat label="Questions" value={fmtInt(lifetime.questions_answered)} />
            <Stat label="Accuracy" value={fmtPct(lifetime.accuracy)} accent={lifetime.accuracy >= 0.85} />
            <Stat label="Avg speed" value={fmtSeconds(lifetime.avg_response_ms)} />
            <Stat label="Fastest answer" value={lifetime.fastest_response_ms ? fmtSeconds(lifetime.fastest_response_ms) : '—'} />
            <Stat label="Tests" value={fmtInt(lifetime.sessions_completed)} />
            <Stat label="Total score" value={fmtInt(lifetime.total_score)} />
            <Stat label="Day streak" value={`🔥 ${lifetime.day_streak}`} accent />
            <Stat label="Today" value={`${fmtInt(today.questions)} q`} />
          </div>
        </Card>
      </Section>

      <Section title="Personal bests">
        {modeBests.length === 0 && chapterBests.length === 0 ? (
          <Card className="card-flat"><p className="muted small">Finish a test to set your first record.</p></Card>
        ) : (
          <div className="grid grid-2">
            {[...modeBests, ...chapterBests].slice(0, 12).map((pb: any) => (
              <Card key={`${pb.scope}-${pb.scope_key}-${pb.metric}`} className="card-flat card-pad-sm">
                <div className="row-between">
                  <div>
                    <p className="tiny dim">{pb.label}</p>
                    <p className="small" style={{ fontWeight: 600 }}>{METRIC_LABEL[pb.metric] ?? pb.metric}</p>
                  </div>
                  <span className="mono" style={{ fontSize: 20, fontWeight: 800 }}>
                    {pb.metric === 'accuracy' ? fmtPct(pb.value) : pb.metric === 'fastest_avg' ? fmtSeconds(pb.value) : fmtInt(pb.value)}
                  </span>
                </div>
                <p className="tiny dim" style={{ marginTop: 4 }}>{relativeDay(pb.achieved_at)}</p>
              </Card>
            ))}
          </div>
        )}
      </Section>

      <Section title="Topic mastery">
        {topics.length === 0 ? (
          <Card className="card-flat"><p className="muted small">Mastery appears after you answer questions in a topic.</p></Card>
        ) : (
          <Card className="card-flat">
            <div className="col" style={{ gap: 11 }}>
              {topics.map((topic: any) => (
                <div key={topic.topic_id}>
                  <div className="row-between" style={{ marginBottom: 4 }}>
                    <span className="small" style={{ fontWeight: 600 }}>{topic.topic_name}</span>
                    <span className="tiny dim">
                      {topic.chapter_name} · {fmtInt(topic.attempts)} attempts · {fmtPct(topic.accuracy)}
                    </span>
                  </div>
                  <Bar value={topic.mastery} tone={topic.mastery >= 0.85 ? 'success' : topic.mastery < 0.5 ? 'error' : 'accent'} />
                </div>
              ))}
            </div>
          </Card>
        )}
      </Section>

      <Section title="Badges">
        <div className="grid grid-4">
          {(badges?.badges ?? []).map((badge: any) => (
            <Card key={badge.id} className="card-flat card-pad-sm" >
              <div style={{ opacity: badge.earned ? 1 : 0.38 }}>
                <p style={{ fontSize: 20 }}>{badge.icon === 'flame' ? '🔥' : badge.icon === 'crown' ? '👑' : badge.icon === 'bolt' ? '⚡' : badge.icon === 'scale' ? '⚖️' : badge.icon === 'eraser' ? '🧽' : badge.icon === 'star' ? '⭐' : badge.icon === 'calendar' ? '📅' : badge.icon === 'crosshair' ? '🎯' : '🏅'}</p>
                <p className="small" style={{ fontWeight: 650, marginTop: 4 }}>{badge.name}</p>
                <p className="tiny dim" style={{ marginTop: 2 }}>{badge.description}</p>
              </div>
            </Card>
          ))}
        </div>
      </Section>

      <Section
        title="Leaderboard"
        action={
          <div className="row" style={{ gap: 4 }}>
            {(['today', 'week', 'all'] as const).map((s) => (
              <Button key={s} size="sm" variant={scope === s ? 'primary' : 'ghost'} onClick={() => setScope(s)}>
                {s}
              </Button>
            ))}
          </div>
        }
      >
        <Card className="card-flat">
          {(board?.entries ?? []).length === 0 ? (
            <p className="muted small">No scores in this window yet.</p>
          ) : (
            <div className="col" style={{ gap: 7 }}>
              {board!.entries.map((entry: any) => (
                <div className="row" key={entry.profile_id}>
                  <span className="mono dim" style={{ width: 22 }}>{entry.rank}</span>
                  <span className="grow small" style={{ fontWeight: entry.profile_id === profile?.id ? 700 : 500 }}>{entry.display_name}</span>
                  <span className="tiny dim">{fmtPct(entry.accuracy)}</span>
                  <span className="mono small" style={{ fontWeight: 700, minWidth: 58, textAlign: 'right' }}>{fmtInt(entry.score)}</span>
                </div>
              ))}
            </div>
          )}
          <div className="row" style={{ marginTop: 14, gap: 8 }}>
            <Chip>Local only</Chip>
            <span className="tiny dim">
              Compares profiles on this device. An opt-in online board is designed for but not built in the MVP — it would use nicknames only, never email.
            </span>
          </div>
        </Card>
      </Section>

      {dash.mistakes.open > 0 && (
        <Section title="Needs attention">
          <Card className="card-flat">
            <div className="row-between wrap">
              <p className="small muted">{fmtInt(dash.mistakes.open)} questions still in your mistake book.</p>
              <Button variant="primary" size="sm" onClick={() => navigate('/play', { state: { params: { mode_key: 'previous_mistakes' }, label: 'Previous Mistakes' } })}>
                Drill them
              </Button>
            </div>
          </Card>
        </Section>
      )}

      {dash.srs.due > 0 && (
        <Section title="Spaced repetition">
          <Card className="card-flat">
            <div className="row-between wrap">
              <p className="small muted">{fmtInt(dash.srs.due)} cards are due for review today.</p>
              <Button size="sm" onClick={() => navigate('/play', { state: { params: { mode_key: 'revision_mix' }, label: 'Revision Mix' } })}>
                Review now
              </Button>
            </div>
          </Card>
        </Section>
      )}

      {!dash.srs.due && dash.mistakes.open === 0 && (
        <Empty title="All clear" hint="Nothing due and no open mistakes. Start a rush to keep the streak alive." />
      )}
    </>
  )
}
