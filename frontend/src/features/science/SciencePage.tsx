import { Link, useNavigate, useParams } from 'react-router-dom'
import { useTree } from '@/shared/api/queries'
import type { StartTestParams } from '@/shared/api/queries'
import { Bar, Button, Card, Chip, Empty, Section, Skeleton } from '@/shared/ui/primitives'
import { fmtInt, fmtPct } from '@/shared/lib/format'

/**
 * Subject browser: subjects -> branches -> chapters -> topics, each with mastery.
 *
 * Deliberately subject-agnostic. Nothing here names Science, Maths or SST: every
 * level is read from /content/tree, so activating a new subject in curriculum.json
 * makes it browsable with no frontend change. The route is still spelled
 * /science for link stability with the original single-subject build.
 */

const SUBJECT_EMOJI: Record<string, string> = { science: '🔬', maths: '📐', sst: '🌏', english: '📖', hindi: '🪔' }
const BRANCH_EMOJI: Record<string, string> = {
  'sci-chem': '🧪', 'sci-phy': '⚙️', 'sci-bio': '🧬',
  'maths-all': '📐',
  'sst-history': '📜', 'sst-geography': '🗺️', 'sst-civics': '⚖️', 'sst-economics': '💹',
}
const emoji = (id: string, table: Record<string, string>, fallback: string) => table[id] ?? fallback

export function SciencePage() {
  const { subjectId, branchId } = useParams()
  const navigate = useNavigate()
  const { data, isLoading, isError } = useTree()

  const play = (params: StartTestParams, label?: string) => navigate('/play', { state: { params, label } })

  if (isLoading) return <Skeleton height={110} count={4} />
  if (isError || !data) return <Empty title="Content unavailable" hint="Is the backend running?" />

  const active = data.subjects.filter((s: any) => s.is_active !== false)
  if (active.length === 0) {
    return <Empty title="No subjects seeded" hint="Run `python backend/run.py --seed`." />
  }

  // ---- level 1: subject picker ----
  if (!subjectId) {
    return (
      <>
        <Header title="Subjects" subtitle={`${active.length} subjects · ${fmtInt(active.reduce((n: number, s: any) => n + (s.question_count ?? 0), 0))} questions`} />
        <Section title="Choose a subject">
          <div className="grid grid-3">
            {active.map((s: any) => (
              <button
                key={s.id}
                className="list-row"
                style={{ flexDirection: 'column', alignItems: 'flex-start', gap: 6, padding: 18 }}
                onClick={() => navigate(`/science/${s.id}`)}
              >
                <span style={{ fontSize: 26 }}>{emoji(s.id, SUBJECT_EMOJI, '📘')}</span>
                <span style={{ fontWeight: 700, fontSize: 16 }}>{s.name}</span>
                <span className="tiny dim">
                  {s.branches.length > 1 ? `${s.branches.length} sections · ` : ''}
                  {s.branches.reduce((n: number, b: any) => n + b.chapters.length, 0)} chapters · {fmtInt(s.question_count ?? 0)} questions
                </span>
                <span className="tiny" style={{ marginTop: 8, color: 'var(--accent)', fontWeight: 700 }}>
                  {s.branches.length > 1 ? 'Choose a section →' : 'Choose a chapter →'}
                </span>
              </button>
            ))}
          </div>
        </Section>

        {data.subjects.filter((s: any) => s.is_active === false).length > 0 && (
          <Section title="Coming next">
            <div className="row wrap">
              {data.subjects
                .filter((s: any) => s.is_active === false)
                .map((s: any) => (
                  <span key={s.id} className="chip" title={s.note ?? 'Content not authored yet'} style={{ opacity: 0.6 }}>
                    {emoji(s.id, SUBJECT_EMOJI, '📘')} {s.name} · soon
                  </span>
                ))}
            </div>
          </Section>
        )}
      </>
    )
  }

  const subject = active.find((s: any) => s.id === subjectId)
  if (!subject) {
    return <Empty title="Subject not found" hint="It may not be seeded yet." action={<Link to="/science">← All subjects</Link>} />
  }

  // Subjects with a single section (Mathematics) skip the section picker so all
  // 14 chapters appear immediately instead of hiding behind an extra click.
  const onlyBranch = subject.branches.length === 1 ? subject.branches[0] : null
  const branch = branchId ? subject.branches.find((b: any) => b.id === branchId) : onlyBranch

  // ---- level 2: branch picker for one subject ----
  if (!branch) {
    return (
      <>
        <Crumbs subjectName={subject.name} />
        <Header
          title={`${emoji(subject.id, SUBJECT_EMOJI, '📘')} ${subject.name}`}
          subtitle={`${fmtInt(subject.question_count ?? 0)} questions across ${subject.branches.length} sections`}
          actions={
            <>
              <Button size="sm" onClick={() => play({ mode_key: 'rush_60s', subject: subject.id }, `${subject.name} Rush`)}>
                ⚡ 1 Minute {subject.name}
              </Button>
              <Button size="sm" variant="ghost" onClick={() => play({ mode_key: 'chapter_test', subject: subject.id }, 'Mixed test')}>
                Mixed test
              </Button>
            </>
          }
        />
        <Section title="Choose a section">
          <div className="grid grid-3">
            {subject.branches.map((b: any) => (
              <button
                key={b.id}
                className="list-row"
                style={{ flexDirection: 'column', alignItems: 'flex-start', gap: 6, padding: 18 }}
                onClick={() => navigate(`/science/${subject.id}/${b.id}`)}
              >
                <span style={{ fontSize: 24 }}>{emoji(b.id, BRANCH_EMOJI, '📗')}</span>
                <span style={{ fontWeight: 700, fontSize: 16 }}>{b.name}</span>
                <span className="tiny dim">
                  {b.chapters.length} {b.chapters.length === 1 ? 'chapter' : 'chapters'} · {fmtInt(b.question_count ?? 0)} questions
                </span>
                <div style={{ width: '100%', marginTop: 4 }}>
                  <Bar value={b.question_count ? 1 : 0} />
                </div>
              </button>
            ))}
          </div>
        </Section>
      </>
    )
  }

  // ---- level 3: chapters + topics for one branch ----
  return (
    <>
      <Crumbs
        subjectId={subject.id}
        subjectName={subject.name}
        branchName={onlyBranch ? undefined : branch.name}
      />
      <Header
        title={`${emoji(branch.id, BRANCH_EMOJI, '📗')} ${onlyBranch ? subject.name : branch.name}`}
        subtitle={`All ${branch.chapters.length} chapters · ${fmtInt(branch.question_count ?? 0)} questions`}
        actions={
          <>
            <Button size="sm" onClick={() => play({ mode_key: 'rush_60s', branch: branch.id }, `${branch.name} Rush`)}>
              ⚡ 1 Minute {branch.name}
            </Button>
            <Button size="sm" variant="ghost" onClick={() => play({ mode_key: 'chapter_test', branch: branch.id }, 'Section test')}>
              Unit test
            </Button>
          </>
        }
      />

      <Section title="Chapters">
        <div className="col" style={{ gap: 10 }}>
          {branch.chapters.map((chapter: any) => (
            <Card key={chapter.id} className="card-flat">
              <div className="row-between wrap" style={{ alignItems: 'flex-start' }}>
                <div className="grow" style={{ minWidth: 220 }}>
                  <div className="row" style={{ gap: 8 }}>
                    {chapter.code && <span className="chip mono">{chapter.code}</span>}
                    <h3 style={{ fontSize: 16 }}>{chapter.name}</h3>
                    {chapter.syllabus_status === 'optional' && <Chip tone="info">off-syllabus</Chip>}
                    {chapter.syllabus_status === 'removed' && <Chip tone="info">not in syllabus</Chip>}
                    {chapter.syllabus_status === 'foundation' && <Chip>fundamentals</Chip>}
                  </div>
                  <p className="tiny dim" style={{ marginTop: 5 }}>
                    {fmtInt(chapter.bank_size)} questions · {fmtInt(chapter.attempts)} attempted
                    {chapter.attempts > 0 ? ` · ${fmtPct(chapter.accuracy)} accuracy` : ''}
                  </p>
                  <div style={{ maxWidth: 260, marginTop: 9 }}>
                    <Bar
                      value={chapter.mastery}
                      tone={chapter.mastery >= 0.8 ? 'success' : chapter.mastery < 0.5 && chapter.attempts > 0 ? 'error' : 'accent'}
                    />
                    <p className="tiny dim" style={{ marginTop: 4 }}>
                      {chapter.attempts > 0 ? `${fmtPct(chapter.mastery)} mastery` : 'Not started'}
                    </p>
                  </div>
                </div>

                <div className="row wrap">
                  {chapter.bank_size > 0 && (
                    <>
                      <Button size="sm" variant="primary" onClick={() => play({ mode_key: 'rush_60s', chapter: chapter.id }, `${chapter.name} Rush`)}>
                        ⚡ Rush
                      </Button>
                      <Button size="sm" onClick={() => play({ mode_key: 'chapter_test', chapter: chapter.id }, chapter.name)}>
                        Practice
                      </Button>
                    </>
                  )}
                </div>
              </div>

              {chapter.topics?.length > 0 && (
                <div className="row wrap" style={{ marginTop: 12, gap: 6 }}>
                  {chapter.topics.map((topic: any) => (
                    <button
                      key={topic.id}
                      className="chip"
                      title={`${fmtInt(topic.bank_size ?? 0)} questions · ${fmtPct(topic.mastery ?? 0)} mastery`}
                      onClick={() => play({ mode_key: 'topic_test', chapter: chapter.id, topic: topic.id }, topic.name)}
                      style={{ cursor: 'pointer', border: '1px solid var(--border)' }}
                    >
                      {topic.name}
                      {topic.attempts > 0 && (
                        <span style={{ color: topic.mastery < 0.5 ? 'var(--error)' : topic.mastery >= 0.85 ? 'var(--success)' : 'var(--text-dim)' }}>
                          {Math.round((topic.mastery ?? 0) * 100)}%
                        </span>
                      )}
                    </button>
                  ))}
                </div>
              )}

              {chapter.bank_size === 0 && (
                <p className="tiny dim" style={{ marginTop: 10 }}>
                  No questions seeded for this chapter yet — it is declared in the curriculum so content can be added without code changes.
                </p>
              )}
            </Card>
          ))}
        </div>
      </Section>
    </>
  )
}

function Header({ title, subtitle, actions }: { title: string; subtitle: string; actions?: React.ReactNode }) {
  return (
    <div style={{ marginTop: 26 }}>
      <div className="row-between wrap">
        <div>
          <h1>{title}</h1>
          <p className="muted small" style={{ marginTop: 4 }}>{subtitle}</p>
        </div>
        {actions && <div className="row wrap">{actions}</div>}
      </div>
    </div>
  )
}

function Crumbs({ subjectId, subjectName, branchName }: { subjectId?: string; subjectName: string; branchName?: string }) {
  return (
    <div style={{ marginTop: 22 }}>
      <Link to={subjectId ? `/science/${subjectId}` : '/science'} className="tiny dim">
        ← {subjectId ? subjectName : 'All subjects'}
      </Link>
      {branchName && <span className="tiny dim"> / {branchName}</span>}
    </div>
  )
}
