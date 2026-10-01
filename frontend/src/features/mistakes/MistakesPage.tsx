import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMistakes } from '@/shared/api/queries'
import { Button, Card, Chip, Empty, Section, Skeleton } from '@/shared/ui/primitives'
import { fmtInt } from '@/shared/lib/format'

const BRANCHES = [
  { id: undefined, label: 'All mistakes' },
  { id: 'sci-chem', label: 'Chemistry' },
  { id: 'sci-phy', label: 'Physics' },
  { id: 'sci-bio', label: 'Biology' },
]

/** Mistake book — every wrong answer is stored locally and re-drillable. */
export function MistakesPage() {
  const [branch, setBranch] = useState<string | undefined>(undefined)
  const [showResolved, setShowResolved] = useState(false)
  const navigate = useNavigate()

  const { data, isLoading, isError } = useMistakes(branch)

  const mistakes = (data?.mistakes ?? []).filter((m) => (showResolved ? true : !m.resolved))
  const stats = data?.stats

  if (isLoading) return <Skeleton height={90} count={4} />

  return (
    <>
      <div className="row-between wrap" style={{ marginTop: 26 }}>
        <div>
          <h1>My mistakes</h1>
          <p className="muted small" style={{ marginTop: 4 }}>
            {fmtInt(stats?.open ?? 0)} open · {fmtInt(stats?.total ?? 0)} total recorded
          </p>
        </div>
        <div className="row">
          <Button variant="primary" onClick={() => navigate('/play', { state: { params: { mode_key: 'previous_mistakes' }, label: 'Previous Mistakes' } })} disabled={!stats?.open}>
            ⚡ Drill my mistakes
          </Button>
          <Button variant="ghost" onClick={() => navigate('/play', { state: { params: { mode_key: 'weak_topics' }, label: 'Weak Topics' } })}>
            Weak topics
          </Button>
        </div>
      </div>

      <Section title="Filter">
        <div className="row wrap">
          {BRANCHES.map((item) => (
            <Button key={item.label} size="sm" variant={branch === item.id ? 'primary' : 'default'} onClick={() => setBranch(item.id)}>
              {item.label}
            </Button>
          ))}
          <Button size="sm" variant="ghost" onClick={() => setShowResolved((v) => !v)}>
            {showResolved ? 'Hide resolved' : 'Show resolved'}
          </Button>
        </div>
      </Section>

      {isError ? (
        <Empty title="Could not load mistakes" />
      ) : mistakes.length === 0 ? (
        <Empty
          title={stats?.total ? 'Nothing open here' : 'No mistakes recorded yet'}
          hint={stats?.total ? 'Every mistake in this filter has been corrected twice.' : 'Answer some questions — wrong answers land here automatically.'}
        />
      ) : (
        <div className="col" style={{ gap: 8 }}>
          {mistakes.slice(0, 60).map((mistake) => (
            <Card key={mistake.question_id} className="card-flat card-pad-sm">
              <div className="row-between wrap" style={{ alignItems: 'flex-start', gap: 10 }}>
                <div className="grow">
                  <p className="small" style={{ fontWeight: 550, whiteSpace: 'pre-line' }}>
                    {mistake.prompt}
                  </p>
                  <p className="tiny dim" style={{ marginTop: 5 }}>
                    {mistake.branch_name} · {mistake.chapter_name}
                    {mistake.topic_name ? ` · ${mistake.topic_name}` : ''} · {mistake.difficulty}
                  </p>
                  {mistake.explanation && (
                    <p className="tiny muted" style={{ marginTop: 5 }}>
                      {mistake.explanation}
                    </p>
                  )}
                </div>
                <div className="row" style={{ gap: 6 }}>
                  <Chip tone={mistake.wrong_count > 2 ? 'error' : undefined}>✕ {mistake.wrong_count}</Chip>
                  {mistake.resolved && <Chip tone="success">resolved</Chip>}
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </>
  )
}
