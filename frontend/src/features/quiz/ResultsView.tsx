import { useEffect, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import type { SubmitResponse } from '@/shared/types'
import { Button, Card, Chip, Section, Stat } from '@/shared/ui/primitives'
import { fmtInt, fmtPct, fmtSeconds } from '@/shared/lib/format'

const gradeFor = (accuracy: number, answered: number): string => {
  if (answered === 0) return 'No answers'
  if (accuracy >= 0.95) return 'Flawless'
  if (accuracy >= 0.85) return 'Excellent'
  if (accuracy >= 0.7) return 'Solid'
  if (accuracy >= 0.5) return 'Getting there'
  return 'Keep drilling'
}

export function ResultsView({
  result,
  label,
  questionCount,
  onRetry,
  onPracticeMistakes,
  onNewTest,
  onDashboard,
}: {
  result: SubmitResponse
  label: string
  questionCount: number
  onRetry: () => void
  onPracticeMistakes: () => void
  onNewTest: () => void
  onDashboard: () => void
}) {
  const queryClient = useQueryClient()
  const { summary, analysis } = result
  const [showLevelUp, setShowLevelUp] = useState(false)

  // Progress reads are stale the moment a session lands; invalidate once.
  useEffect(() => {
    queryClient.invalidateQueries({ queryKey: ['dashboard'] })
    queryClient.invalidateQueries({ queryKey: ['leaderboard'] })
    queryClient.invalidateQueries({ queryKey: ['bests'] })
    queryClient.invalidateQueries({ queryKey: ['mastery'] })
    queryClient.invalidateQueries({ queryKey: ['mistakes'] })
    queryClient.invalidateQueries({ queryKey: ['tree'] })
  }, [queryClient, result.session_id])

  useEffect(() => {
    const leveled = analysis.events.some((event) => event.kind === 'level_up')
    if (!leveled) return
    setShowLevelUp(true)
    const id = window.setTimeout(() => setShowLevelUp(false), 1800)
    return () => window.clearTimeout(id)
  }, [analysis.events])

  const newBests = analysis.personal_bests.filter((pb: any) => pb.scope === 'mode' && pb.metric === 'score')
  const badges = analysis.events.filter((event) => event.kind === 'badge')

  return (
    <div style={{ width: '100%', maxWidth: 640 }}>
      {showLevelUp && (
        <div className="levelup">
          <div className="levelup-card">
            <p style={{ fontSize: 40 }}>🎉</p>
            <h2>Level {analysis.level}</h2>
            <p className="muted small">{analysis.level_info.name}</p>
          </div>
        </div>
      )}

      <div className="result-hero">
        <p className="result-grade">{gradeFor(summary.accuracy, summary.answered)}</p>
        <p className="tiny dim" style={{ marginTop: 8, textTransform: 'uppercase', letterSpacing: '.08em' }}>
          {label} complete
        </p>
        <p className="result-score" style={{ marginTop: 6 }}>{fmtInt(summary.score)}</p>
        <div className="row" style={{ justifyContent: 'center', marginTop: 12, gap: 8 }}>
          <Chip tone="accent">+{fmtInt(summary.xp)} XP</Chip>
          <Chip tone="success">🔥 best streak {summary.best_streak}</Chip>
          {newBests.length > 0 && <Chip tone="accent">🏆 New personal best</Chip>}
        </div>
      </div>

      <Card className="card-flat">
        <div className="grid grid-4">
          <Stat label="Accuracy" value={fmtPct(summary.accuracy)} accent={summary.accuracy >= 0.85} />
          <Stat label="Correct" value={`${summary.correct} / ${summary.answered}`} />
          <Stat label="Avg response" value={fmtSeconds(summary.avg_response_ms)} />
          <Stat label="Fastest" value={summary.fastest_response_ms ? fmtSeconds(summary.fastest_response_ms) : '—'} />
        </div>
        {summary.completion_bonus > 0 && (
          <p className="tiny dim" style={{ marginTop: 12 }}>
            Includes completion bonus +{summary.completion_bonus}
            {summary.accuracy_bonus > 0 ? ` and accuracy bonus +${summary.accuracy_bonus}` : ''} · {questionCount} questions served
          </p>
        )}
      </Card>

      {badges.length > 0 && (
        <Section title="Badges earned">
          <div className="row wrap">
            {badges.map((badge: any) => (
              <Chip key={badge.badge_id} tone="accent">
                🏅 {badge.name}
              </Chip>
            ))}
          </div>
        </Section>
      )}

      {newBests.length > 0 && (
        <Section title="Personal best">
          <Card className="pb-flash">
            <div className="row-between">
              <div>
                <p className="small muted">{newBests[0].scope_key}</p>
                <p style={{ fontSize: 26, fontWeight: 800, letterSpacing: '-0.02em' }}>{fmtInt(newBests[0].value)}</p>
              </div>
              <div className="col" style={{ alignItems: 'flex-end', gap: 2 }}>
                <span className="tiny dim">Previous</span>
                <span className="mono" style={{ fontWeight: 700 }}>
                  {newBests[0].previous != null ? fmtInt(newBests[0].previous) : '—'}
                </span>
              </div>
            </div>
          </Card>
        </Section>
      )}

      <div className="grid grid-2" style={{ marginTop: 22 }}>
        <Card className="card-flat">
          <h3 className="section-title" style={{ marginBottom: 10 }}>Weak areas</h3>
          {analysis.weak_areas.length === 0 ? (
            <p className="small muted">Nothing weak in this set — nice.</p>
          ) : (
            <div className="col" style={{ gap: 7 }}>
              {analysis.weak_areas.map((area) => (
                <div className="row" key={area.topic_id}>
                  <span className="grow small">{area.name}</span>
                  <span className="chip chip-error">{fmtPct(area.accuracy)}</span>
                </div>
              ))}
            </div>
          )}
        </Card>

        <Card className="card-flat">
          <h3 className="section-title" style={{ marginBottom: 10 }}>Strong areas</h3>
          {analysis.strong_areas.length === 0 ? (
            <p className="small muted">Answer more questions to see strengths.</p>
          ) : (
            <div className="col" style={{ gap: 7 }}>
              {analysis.strong_areas.map((area) => (
                <div className="row" key={area.topic_id}>
                  <span className="grow small">{area.name}</span>
                  <span className="chip chip-success">{fmtPct(area.accuracy)}</span>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>

      <div className="grid grid-2" style={{ marginTop: 22 }}>
        <Button variant="primary" size="lg" onClick={onRetry}>
          ↻ Retry
        </Button>
        <Button size="lg" onClick={onPracticeMistakes}>
          Practice my mistakes
        </Button>
        <Button size="lg" variant="ghost" onClick={onNewTest}>
          New test
        </Button>
        <Button size="lg" variant="ghost" onClick={onDashboard}>
          Back to dashboard
        </Button>
      </div>
    </div>
  )
}
