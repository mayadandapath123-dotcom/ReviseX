import { useMemo, useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { api } from '@/shared/api/client'
import { Button, Chip, Section, Stat } from '@/shared/ui/primitives'
import { fmtInt, fmtPct } from '@/shared/lib/format'

/**
 * Mental maths trainer.
 *
 * Every question is generated live by the backend from the chosen level and
 * operations — nothing is preloaded, so the paper never repeats. The same
 * seed is echoed back on submit, which lets the server rebuild the identical
 * questions and re-grade them; the client's own right/wrong marking is never
 * trusted for the score.
 */

type Option = { key: string; text: string; is_correct: boolean }
type Question = {
  id: string
  prompt: string
  answer: number
  answer_key: string
  difficulty: string
  topic_name: string
  options: Option[]
  explanation: string
}
type Options = {
  levels: { id: string; name: string; operations: string[] }[]
  operations: { id: string; name: string; symbol: string }[]
}
type Replay = { level: string; operations: string[]; seed: number | null; count: number }
type Summary = {
  score: number
  xp: number
  correct: number
  answered: number
  question_count: number
  accuracy: number
  avg_response_ms: number
  completion_bonus: number
  graded: { question_id: string; prompt: string; is_correct: boolean; correct_value: number }[]
  profile?: { level: number; xp_total: number; level_progress: number }
}

const OP_LABEL: Record<string, string> = {
  add: 'Addition +',
  subtract: 'Subtraction −',
  multiply: 'Multiplication ×',
  divide: 'Division ÷',
  square: 'Squares n²',
  percent: 'Percentages %',
}

const LEVEL_HINT: Record<string, string> = {
  easy: 'Single digits · times tables up to 9×9',
  medium: 'Two digits · squares up to 10²',
  hard: 'Three digits · 2-digit × 2-digit · percentages',
}

export function ArithmeticPage() {
  const [level, setLevel] = useState('easy')
  const [ops, setOps] = useState<string[]>(['add', 'subtract', 'multiply', 'divide'])
  const [count, setCount] = useState(12)

  const [questions, setQuestions] = useState<Question[] | null>(null)
  const [replay, setReplay] = useState<Replay | null>(null)
  const [index, setIndex] = useState(0)
  const [picked, setPicked] = useState<Record<string, string>>({})
  const [shownAt, setShownAt] = useState<number>(Date.now())
  const [times, setTimes] = useState<Record<string, number>>({})
  const [summary, setSummary] = useState<Summary | null>(null)

  const { data: optionsData } = useQuery({
    queryKey: ['arithmetic-options'],
    queryFn: () => api.get<Options>('/quiz/arithmetic/options'),
    staleTime: Infinity,
  })
  const options = { data: optionsData }

  const available = useMemo(() => {
    const found = options.data?.levels.find((l) => l.id === level)
    return found ? found.operations : ['add', 'subtract', 'multiply', 'divide']
  }, [options.data, level])

  const start = useMutation({
    mutationFn: (seed: number) =>
      api.post<{ questions: Question[]; replay: Replay }>('/quiz/arithmetic/generate', {
        level,
        operations: ops.filter((o) => available.includes(o)),
        count,
        seed,
      }),
    onSuccess: (data) => {
      setQuestions(data.questions)
      setReplay(data.replay)
      setIndex(0)
      setPicked({})
      setTimes({})
      setSummary(null)
      setShownAt(Date.now())
    },
  })

  const submit = useMutation({
    mutationFn: () => {
      const attempts = (questions ?? []).map((q) => ({
        question_id: q.id,
        selected_key: picked[q.id] ?? null,
        response_ms: times[q.id] ?? 0,
      }))
      return api.post<{ summary: Summary }>('/quiz/arithmetic/submit', {
        level: replay?.level ?? level,
        operations: replay?.operations ?? ops,
        seed: replay?.seed ?? null,
        attempts,
      })
    },
    onSuccess: ({ summary: s }) => setSummary(s),
  })

  const begin = () => start.mutate(Math.floor(Math.random() * 1_000_000))

  const toggleOp = (op: string) => {
    if (!available.includes(op)) return
    setOps((prev) => (prev.includes(op) ? prev.filter((o) => o !== op) : [...prev, op]))
  }

  const chooseLevel = (next: string) => {
    setLevel(next)
    const allowed = options.data?.levels.find((l) => l.id === next)?.operations ?? []
    // Drop operations this level cannot serve so the request never 422s.
    setOps((prev) => {
      const kept = prev.filter((o) => allowed.includes(o))
      return kept.length ? kept : allowed.slice(0, 4)
    })
  }

  const validOps = ops.filter((o) => available.includes(o))

  // ---------------- setup screen ----------------
  if (!questions) {
    return (
      <>
        <div style={{ marginTop: 26 }}>
          <h1>🧮 Mental Maths Trainer</h1>
          <p className="muted small" style={{ marginTop: 4 }}>
            Questions are generated live for the level you pick — never preloaded, never the same paper twice.
          </p>
        </div>

        {start.isError && (
          <div className="card card-flat" style={{ marginTop: 14, borderColor: 'var(--error)' }}>
            <p className="small" style={{ color: 'var(--error)' }}>
              {(start.error as Error).message}
            </p>
          </div>
        )}

        <Section title="1 · Choose your level">
          <div className="grid grid-3">
            {(options.data?.levels ?? [{ id: 'easy', name: 'Easy', operations: [] }, { id: 'medium', name: 'Medium', operations: [] }, { id: 'hard', name: 'Hard', operations: [] }]).map((l) => (
              <button
                key={l.id}
                className="list-row"
                onClick={() => chooseLevel(l.id)}
                style={{
                  flexDirection: 'column',
                  alignItems: 'flex-start',
                  gap: 6,
                  padding: 16,
                  borderColor: level === l.id ? 'var(--accent)' : undefined,
                  background: level === l.id ? 'var(--accent-soft, rgba(99,102,241,0.12))' : undefined,
                }}
              >
                <span style={{ fontWeight: 750, fontSize: 16 }}>{l.name}</span>
                <span className="tiny dim">{LEVEL_HINT[l.id]}</span>
              </button>
            ))}
          </div>
        </Section>

        <Section title="2 · Choose what to practise">
          <div className="row wrap" style={{ gap: 8 }}>
            {(options.data?.operations ?? []).map((op) => {
              const enabled = available.includes(op.id)
              const on = validOps.includes(op.id)
              return (
                <button
                  key={op.id}
                  className="chip"
                  disabled={!enabled}
                  onClick={() => toggleOp(op.id)}
                  title={enabled ? OP_LABEL[op.id] : `Not available at ${level} level`}
                  style={{
                    cursor: enabled ? 'pointer' : 'not-allowed',
                    opacity: enabled ? 1 : 0.35,
                    border: `1px solid ${on ? 'var(--accent)' : 'var(--border)'}`,
                    background: on ? 'var(--accent-soft, rgba(99,102,241,0.14))' : 'transparent',
                    fontWeight: on ? 700 : 500,
                    padding: '8px 14px',
                  }}
                >
                  {OP_LABEL[op.id] ?? op.name}
                </button>
              )
            })}
          </div>
        </Section>

        <Section title="3 · How many questions">
          <div className="row wrap" style={{ gap: 8 }}>
            {[10, 12, 15, 20, 30].map((n) => (
              <button
                key={n}
                className="chip"
                onClick={() => setCount(n)}
                style={{
                  cursor: 'pointer',
                  padding: '8px 14px',
                  border: `1px solid ${count === n ? 'var(--accent)' : 'var(--border)'}`,
                  fontWeight: count === n ? 700 : 500,
                }}
              >
                {n}
              </button>
            ))}
          </div>
        </Section>

        <Button
          className="btn-block"
          variant="primary"
          size="lg"
          disabled={validOps.length === 0 || start.isPending}
          onClick={begin}
          style={{ marginTop: 18 }}
        >
          {start.isPending ? 'Generating…' : `Start ${count} live questions →`}
        </Button>
        {validOps.length === 0 && (
          <p className="tiny dim center" style={{ marginTop: 8 }}>
            Pick at least one operation.
          </p>
        )}
      </>
    )
  }

  // ---------------- results screen ----------------
  if (summary) {
    const reset = () => {
      setQuestions(null)
      setSummary(null)
      setReplay(null)
      setPicked({})
      setTimes({})
    }
    return (
      <>
        <div style={{ marginTop: 26 }}>
          <h1>Results</h1>
          <p className="muted small" style={{ marginTop: 4 }}>
            {level[0].toUpperCase() + level.slice(1)} · {validOps.map((o) => OP_LABEL[o]).join(', ')}
          </p>
        </div>

        <div className="grid grid-4" style={{ marginTop: 14 }}>
          <Stat label="Score" value={fmtInt(summary.score)} />
          <Stat label="Accuracy" value={fmtPct(summary.accuracy)} />
          <Stat label="Correct" value={`${summary.correct}/${summary.question_count}`} />
          <Stat label="XP earned" value={`+${fmtInt(summary.xp)}`} />
        </div>

        {summary.profile && (
          <p className="tiny dim" style={{ marginTop: 10 }}>
            Level {summary.profile.level} · {fmtInt(summary.profile.xp_total)} XP total
          </p>
        )}

        <Section title="Review">
          <div className="col" style={{ gap: 6 }}>
            {summary.graded.map((g) => (
              <div key={g.question_id} className="list-row" style={{ padding: '10px 14px' }}>
                <span style={{ color: g.is_correct ? 'var(--success)' : 'var(--error)', fontWeight: 800 }}>
                  {g.is_correct ? '✓' : '✗'}
                </span>
                <span className="grow mono">{g.prompt}</span>
                {!g.is_correct && <Chip tone="info">answer {g.correct_value}</Chip>}
              </div>
            ))}
          </div>
        </Section>

        <div className="row wrap" style={{ marginTop: 16, gap: 8 }}>
          <Button variant="primary" onClick={begin}>
            New paper ({count} questions)
          </Button>
          <Button variant="ghost" onClick={reset}>
            ← Change level or operations
          </Button>
        </div>
      </>
    )
  }

  // ---------------- quiz screen ----------------
  const q = questions[index]
  const chosen = picked[q.id]
  const answered = chosen !== undefined
  const last = index === questions.length - 1

  const choose = (key: string) => {
    if (answered) return
    setPicked((prev) => ({ ...prev, [q.id]: key }))
    setTimes((prev) => ({ ...prev, [q.id]: Date.now() - shownAt }))
  }

  const next = () => {
    if (last) submit.mutate()
    else {
      setIndex((i) => i + 1)
      setShownAt(Date.now())
    }
  }

  return (
    <div style={{ marginTop: 22, maxWidth: 720 }}>
      <div className="row-between" style={{ marginBottom: 10 }}>
        <span className="tiny dim">
          Question {index + 1} of {questions.length} · {q.topic_name}
        </span>
        <button className="tiny dim" style={{ cursor: 'pointer', background: 'none', border: 'none' }} onClick={() => setQuestions(null)}>
          ✕ quit
        </button>
      </div>

      <div
        style={{ height: 5, background: 'var(--border)', borderRadius: 99, overflow: 'hidden', marginBottom: 20 }}
      >
        <div
          style={{
            height: '100%',
            width: `${((index + (answered ? 1 : 0)) / questions.length) * 100}%`,
            background: 'var(--accent)',
            transition: 'width .18s ease',
          }}
        />
      </div>

      <div className="card card-flat" style={{ padding: 26, textAlign: 'center' }}>
        <p className="mono" style={{ fontSize: 40, fontWeight: 700, letterSpacing: 1, margin: 0 }}>
          {q.prompt}
        </p>
      </div>

      <div className="grid grid-2" style={{ marginTop: 16, gap: 10 }}>
        {q.options.map((o) => {
          const isPicked = chosen === o.key
          const reveal = answered && o.is_correct
          const wrong = answered && isPicked && !o.is_correct
          return (
            <button
              key={o.key}
              className="list-row"
              onClick={() => choose(o.key)}
              disabled={answered}
              style={{
                justifyContent: 'center',
                padding: '20px 14px',
                fontSize: 22,
                fontWeight: 700,
                cursor: answered ? 'default' : 'pointer',
                borderColor: reveal ? 'var(--success)' : wrong ? 'var(--error)' : isPicked ? 'var(--accent)' : undefined,
                background: reveal
                  ? 'rgba(34,197,94,0.14)'
                  : wrong
                    ? 'rgba(239,68,68,0.14)'
                    : isPicked
                      ? 'var(--accent-soft, rgba(99,102,241,0.14))'
                      : undefined,
              }}
            >
              <span className="mono">{o.text}</span>
            </button>
          )
        })}
      </div>

      {answered && (
        <div className="row-between" style={{ marginTop: 18 }}>
          <span className="small" style={{ color: chosen === q.answer_key ? 'var(--success)' : 'var(--error)', fontWeight: 700 }}>
            {chosen === q.answer_key ? '✓ Correct' : `✗ Answer: ${q.answer}`}
          </span>
          <Button variant="primary" onClick={next} disabled={submit.isPending}>
            {submit.isPending ? 'Scoring…' : last ? 'Finish →' : 'Next →'}
          </Button>
        </div>
      )}

      {submit.isError && (
        <p className="small" style={{ color: 'var(--error)', marginTop: 12 }}>
          {(submit.error as Error).message}
        </p>
      )}
    </div>
  )
}
