import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { api } from '@/shared/api/client'
import type { StartTestParams } from '@/shared/api/queries'
import type { AttemptPayload, Question, StartTestResponse, SubmitResponse } from '@/shared/types'
import { scoreAnswer } from '@/shared/lib/scoring'
import { arrowStep, isTypingTarget, optionIndexFromKey } from '@/shared/lib/keyboard'
import { sfx } from '@/shared/lib/sfx'
import { usePrefs } from '@/app/prefs'
import { Icon } from '@/shared/ui/icons'
import { fmtClock, fmtInt } from '@/shared/lib/format'
import { Button, Empty } from '@/shared/ui/primitives'
import { BalancingView } from '@/features/balancing/BalancingView'
import { ResultsView } from './ResultsView'

type Phase = 'loading' | 'answer' | 'feedback' | 'done' | 'error'

const AUTO_NEXT_MS = 620
const AUTO_NEXT_WRONG_MS = 1150

/**
 * The quiz hot loop. Everything here is client-side: one bulk fetch to start,
 * one batched POST to finish. Zero network traffic per question, which is what
 * makes transitions instant and the whole thing work offline.
 */
export function QuizPage() {
  const location = useLocation()
  const navigate = useNavigate()
  const params: StartTestParams = (location.state as any)?.params ?? { mode_key: 'rush_60s' }
  const label: string | undefined = (location.state as any)?.label

  const [phase, setPhase] = useState<Phase>('loading')
  const [error, setError] = useState<string>('')
  const [test, setTest] = useState<StartTestResponse | null>(null)
  const [index, setIndex] = useState(0)
  const [selected, setSelected] = useState<string | null>(null)
  const [lastScore, setLastScore] = useState<{ points: number; correct: boolean } | null>(null)
  const [streak, setStreak] = useState(0)
  const [liveScore, setLiveScore] = useState(0)
  const [remainingMs, setRemainingMs] = useState<number | null>(null)
  const [result, setResult] = useState<SubmitResponse | null>(null)
  const [attempts, setAttempts] = useState<AttemptPayload[]>([])
  /**
   * Keyboard highlight: an option that is chosen but not yet submitted.
   *
   * Distinct from `selected`, which means the answer has been committed and the
   * question is locked. Keeping them apart is what lets a student press 2, then
   * change to 3, and only then press Enter.
   */
  const [cursor, setCursor] = useState<number | null>(null)

  const answerMode = usePrefs((s) => s.answerMode)
  const sfxEnabled = usePrefs((s) => s.sfxEnabled)
  const setSfxEnabled = usePrefs((s) => s.setSfxEnabled)

  const shownAt = useRef<number>(0)
  const startedAt = useRef<number>(0)
  const advancing = useRef(false)
  const autoNextTimer = useRef<number | null>(null)
  const attemptsRef = useRef<AttemptPayload[]>([])
  attemptsRef.current = attempts

  const questions: Question[] = test?.questions ?? []
  const question = questions[index]
  const isTimed = (test?.duration_limit_ms ?? 0) > 0

  const load = useCallback(async () => {
    setPhase('loading')
    try {
      const data = await api.post<StartTestResponse>('/quiz/sessions', params)
      setTest(data)
      setRemainingMs(data.duration_limit_ms ?? null)
      startedAt.current = performance.now()
      shownAt.current = performance.now()
      setPhase('answer')
    } catch (err) {
      setError((err as Error).message || 'Could not start the test')
      setPhase('error')
    }
  }, [JSON.stringify(params)])

  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const finish = useCallback(
    async (finalAttempts: AttemptPayload[]) => {
      if (!test) return
      setPhase('done')
      try {
        const payload = await api.post<SubmitResponse>(`/quiz/sessions/${test.session_id}/submit`, {
          elapsed_ms: Math.round(performance.now() - startedAt.current),
          wrong_penalty: test.wrong_penalty ?? 0,
          attempts: finalAttempts,
        })
          setResult(payload)
          sfx.play('finish')
      } catch (err) {
        setError((err as Error).message || 'Could not save the session')
      }
    },
    [test],
  )

  const next = useCallback(() => {
    advancing.current = false
    if (!test) return
    if (isTimed && (remainingMs ?? 0) <= 0) {
      void finish(attemptsRef.current)
      return
    }
    if (index + 1 >= questions.length) {
      void finish(attemptsRef.current)
      return
    }
    setIndex((i) => i + 1)
    setSelected(null)
    setCursor(null)
    setLastScore(null)
    shownAt.current = performance.now()
      setPhase('answer')
    }, [index, questions.length, test, isTimed, remainingMs, finish])

  /**
   * After a question is answered the app moves on by itself. A keyboard user
   * should not have to wait out that delay, so Enter can advance immediately —
   * and the pending timer then has to be cancelled, or it would fire after the
   * manual advance and skip a whole question.
   */
  const scheduleNext = useCallback(
    (ms: number) => {
      if (autoNextTimer.current != null) window.clearTimeout(autoNextTimer.current)
      autoNextTimer.current = window.setTimeout(() => {
        autoNextTimer.current = null
        next()
      }, ms)
    },
    [next],
  )

  const advanceNow = useCallback(() => {
    if (autoNextTimer.current != null) {
      window.clearTimeout(autoNextTimer.current)
      autoNextTimer.current = null
    }
    next()
  }, [next])

  // A timer left running past unmount would call next() on a dead component.
  useEffect(
    () => () => {
      if (autoNextTimer.current != null) window.clearTimeout(autoNextTimer.current)
    },
    [],
  )

  const answer = useCallback(
    (key: string | null, coefficients?: number[]) => {
      if (!question || phase !== 'answer' || advancing.current) return
      advancing.current = true

      const responseMs = Math.round(performance.now() - shownAt.current)
      const correct = coefficients
        ? true // balancing grades on the server; locally we only know it was checked
        : key === question.answer_key

      const scored = scoreAnswer({
        difficulty: question.difficulty,
        responseMs,
        timeBudgetMs: question.time_budget_ms,
        streakBefore: streak,
        isCorrect: correct,
        wrongPenaltyFactor: test?.wrong_penalty ?? 0,
      })

      const attempt: AttemptPayload = {
        seq: attemptsRef.current.length + 1,
        question_id: question.id,
        selected_key: key,
        option_order: (question.options ?? []).map((o) => o.key),
        response_ms: responseMs,
        shown_ms: responseMs,
        ...(coefficients ? { coefficients } : {}),
      }
      const merged = [...attemptsRef.current, attempt]
      setAttempts(merged)

      // Every third correct answer in a row gets its own cue, played instead of
      // the plain correct one so the two never overlap into noise.
      const nextStreak = correct ? streak + 1 : 0
      if (correct && nextStreak >= 3 && nextStreak % 3 === 0) sfx.play('streak')
      else sfx.play(correct ? 'correct' : 'wrong')

      if (coefficients) {
        // Balancing results come back from the engine; treat a checked answer as scored.
        setSelected(key)
        setLastScore({ points: scored.points, correct })
        setStreak(nextStreak)
        setLiveScore((s) => s + scored.points)
        setPhase('feedback')
        scheduleNext(AUTO_NEXT_MS)
        return
      }

      setSelected(key)
      setLastScore({ points: scored.points, correct })
      setStreak(nextStreak)
      setLiveScore((s) => Math.max(0, s + scored.points))
      setPhase('feedback')
      scheduleNext(correct ? AUTO_NEXT_MS : AUTO_NEXT_WRONG_MS)
    },
    [question, phase, streak, test, next, scheduleNext],
  )

  /** Balancing mode reports its own verdict from the local verifier. */
  const onBalanced = useCallback(
    (coefficients: number[], balanced: boolean) => {
      if (!question || advancing.current) return
      advancing.current = true
      const responseMs = Math.round(performance.now() - shownAt.current)
      const scored = scoreAnswer({
        difficulty: question.difficulty,
        responseMs,
        timeBudgetMs: question.time_budget_ms,
        streakBefore: streak,
        isCorrect: balanced,
      })
      const attempt: AttemptPayload = {
        seq: attemptsRef.current.length + 1,
        question_id: question.id,
        selected_key: balanced ? 'balanced' : null,
        option_order: [],
        response_ms: responseMs,
        shown_ms: responseMs,
        coefficients,
      }
      setAttempts([...attemptsRef.current, attempt])
        sfx.play(balanced ? 'correct' : 'wrong')
        setLastScore({ points: scored.points, correct: balanced })
        setStreak(balanced ? streak + 1 : 0)
      setLiveScore((s) => Math.max(0, s + scored.points))
      setPhase('feedback')
      window.setTimeout(() => {
        advancing.current = false
        if (index + 1 >= questions.length) void finish(attemptsRef.current)
        else next()
      }, balanced ? 900 : 1400)
    },
    [question, streak, index, questions.length, next, finish],
  )

  // Master clock for timed modes.
  useEffect(() => {
    if (!isTimed || phase === 'done' || phase === 'loading' || phase === 'error') return
    const id = window.setInterval(() => {
      setRemainingMs((ms) => {
        if (ms == null) return ms
        const nextValue = ms - 100
        if (nextValue <= 0) {
          window.clearInterval(id)
          void finish(attemptsRef.current)
          return 0
        }
        return nextValue
      })
    }, 100)
    return () => window.clearInterval(id)
  }, [isTimed, phase, finish])

  // Keyboard. Two modes, because speed and safety pull in opposite directions:
  //
  //   confirm — 1-4 highlights, arrows move the highlight, Enter commits. You
  //             can change your mind, which matters because a careless keypress
  //             breaks a streak and the app never lets you take it back.
  //   instant — 1-4 answers immediately. Faster, for timed rush modes.
  //
  // Enter does double duty: it commits an answer, and once the question is
  // locked it advances. That is the whole point — a run of questions can be
  // played without ever leaving the number row and Enter.
  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (event.metaKey || event.ctrlKey || event.altKey) return

      // A balancing question has coefficient inputs. Typing in one must not be
      // read as a shortcut, or the student cannot enter a subscript.
      if (isTypingTarget(event.target)) return

      if (event.key === 'Escape') {
        navigate('/')
        return
      }

      if (phase === 'feedback') {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault()
          // Skips the auto-advance delay. Safe to call while `advancing` is
          // still true: next() is what clears it.
          advanceNow()
        }
        return
      }

      if (phase !== 'answer' || question?.question_type !== 'mcq_single') return
      const options = question.options ?? []
      if (!options.length) return

      const optionIndex = optionIndexFromKey(event.key)
      if (optionIndex != null) {
        event.preventDefault()
        if (!options[optionIndex]) return
        if (answerMode === 'instant') {
          answer(options[optionIndex].key)
        } else {
          // Move the highlight, and say so — the sound is how you know the key
          // registered without looking away from the question.
          setCursor(optionIndex)
          sfx.play('select')
        }
        return
      }

      const step = arrowStep(event.key)
      if (step != null) {
        event.preventDefault()
        // Starting from nothing, Down/Right picks the first option and Up/Left
        // the last, so either direction feels like it does something.
        const base = cursor == null ? (step > 0 ? -1 : 0) : cursor
        setCursor((base + step + options.length) % options.length)
        sfx.play('select')
        return
      }

      // Enter with nothing highlighted does nothing. Answering on a blind Enter
      // would be the app guessing on the student's behalf.
      if (event.key === 'Enter' && answerMode === 'confirm') {
        event.preventDefault()
        if (cursor != null && options[cursor]) answer(options[cursor].key)
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [phase, question, answer, next, advanceNow, navigate, answerMode, cursor])

  const progressPct = useMemo(() => {
    if (!test) return 0
    if (isTimed && test.duration_limit_ms) return 1 - (remainingMs ?? 0) / test.duration_limit_ms
    return questions.length ? index / questions.length : 0
  }, [test, isTimed, remainingMs, index, questions.length])

  if (phase === 'loading') {
    return (
      <div className="quiz-shell" style={{ justifyContent: 'center', alignItems: 'center' }}>
        <p className="muted">Loading questions…</p>
      </div>
    )
  }

  if (phase === 'error') {
    return (
      <div className="quiz-shell" style={{ justifyContent: 'center' }}>
        <Empty title="Could not start this test" hint={error} action={<Button onClick={load}>Retry</Button>} />
      </div>
    )
  }

  if (phase === 'done') {
    return (
      <div className="quiz-shell" style={{ justifyContent: 'center' }}>
        {result ? (
          <ResultsView
            result={result}
            label={label ?? test?.mode?.name ?? 'Test'}
            questionCount={questions.length}
            onRetry={() => {
              setAttempts([])
              setIndex(0)
              setStreak(0)
              setLiveScore(0)
              setResult(null)
              setTest(null)
              void load()
            }}
            onPracticeMistakes={() => navigate('/play', { state: { params: { mode_key: 'previous_mistakes' }, label: 'Previous Mistakes' } })}
            onNewTest={() => navigate('/')}
            onDashboard={() => navigate('/')}
          />
        ) : (
          <p className="muted center">{error || 'Saving your session…'}</p>
        )}
      </div>
    )
  }

  if (!question) return null

  const answered = selected != null || phase === 'feedback'
  const correctKey = question.answer_key

  return (
    <div className="quiz-shell">
      <div className="quiz-head">
        <Button size="sm" variant="ghost" onClick={() => (attempts.length ? void finish(attempts) : navigate('/'))}>
          ✕
        </Button>
        <span className="small muted grow" style={{ fontWeight: 600 }}>
          {label ?? test?.mode?.name ?? question.branch_name}
          <span className="dim"> · {question.chapter_name}</span>
        </span>
        {streak >= 2 && <span className="streak-badge">🔥 {streak}</span>}
        <span className="chip mono">{fmtInt(liveScore)}</span>
          {isTimed ? (
            <span className={`timer mono ${remainingMs != null && remainingMs < 10000 ? 'timer-urgent' : ''}`}>{fmtClock(remainingMs ?? 0)}</span>
          ) : (
            <span className="small muted mono">
              {index + 1} / {questions.length}
            </span>
          )}
          {/* Mute is here rather than in Settings because the moment you want
              it is the moment you are mid-quiz, with no way back to a menu. */}
          <button
            className="icon-btn"
            data-on={sfxEnabled}
            onClick={() => setSfxEnabled(!sfxEnabled)}
            aria-label={sfxEnabled ? 'Mute sound' : 'Unmute sound'}
            aria-pressed={sfxEnabled}
            title={sfxEnabled ? 'Mute sound' : 'Unmute sound'}
          >
            <Icon name={sfxEnabled ? 'sound' : 'muted'} size={16} />
          </button>
      </div>

      <div className="quiz-progress">
        <div className="quiz-progress-fill" style={{ width: `${Math.min(100, progressPct * 100)}%` }} />
      </div>

      <div key={question.id} className="question-enter" style={{ flex: 1 }}>
        {question.question_type === 'balancing' ? (
          <BalancingView question={question} locked={phase === 'feedback'} verdict={lastScore} onChecked={onBalanced} />
        ) : (
          <>
            <Stimulus question={question} />
            <p className="prompt">{question.prompt}</p>

            <div className="options" role="group" aria-label="Answer options">
                {question.options.map((option, optionIndex) => {
                  const isCorrect = option.key === correctKey
                  const isPicked = option.key === selected
                  const isCursored = !answered && cursor === optionIndex
                  let state = ''
                  if (answered) {
                    if (isCorrect) state = 'option-correct'
                    else if (isPicked) state = 'option-wrong'
                  } else if (isCursored) {
                    state = 'option-selected'
                  }
                  return (
                    <button
                      key={option.key}
                      className={`option ${state}`}
                      disabled={answered}
                      onClick={() => answer(option.key)}
                      aria-pressed={isPicked}
                      // Screen readers get the shortcut, and the highlight is
                      // announced rather than only being a border colour.
                      aria-keyshortcuts={String(optionIndex + 1)}
                      data-cursor={isCursored ? 'true' : undefined}
                    >
                      <span className="option-key">{optionIndex + 1}</span>
                      <span className="option-text">{option.text}</span>
                      {answered && isCorrect && <span aria-hidden>✓</span>}
                      {answered && isPicked && !isCorrect && <span aria-hidden>✕</span>}
                    </button>
                  )
                })}
            </div>

            {phase === 'feedback' && lastScore && (
              <div className={`feedback ${lastScore.correct ? 'feedback-correct' : 'feedback-wrong'}`}>
                <div className="row-between">
                  <span style={{ fontWeight: 700, color: lastScore.correct ? 'var(--success)' : 'var(--error)' }}>
                    {lastScore.correct ? '✓ Correct' : '✕ Not quite'}
                  </span>
                  <span className="points-float">{lastScore.points > 0 ? `+${lastScore.points}` : lastScore.points}</span>
                </div>
                {!lastScore.correct && (
                  <p className="small" style={{ marginTop: 6 }}>
                    Answer: <strong>{question.options.find((o) => o.key === correctKey)?.text}</strong>
                  </p>
                )}
                {question.explanation && (test?.show_explanation === 'always' || !lastScore.correct) && (
                  <p className="small muted" style={{ marginTop: 6 }}>
                    {question.explanation}
                  </p>
                )}
              </div>
            )}
          </>
        )}
      </div>

        {/* Two hints, one shown per input type. Telling a phone user about the
            1-4 keys is noise; telling a laptop user to tap is worse. */}
        <p className="tiny dim center keyboard-hint" style={{ marginTop: 18 }}>
          {phase === 'answer' && answerMode === 'confirm' ? (
            <>
              <span className="kbd">1</span>–<span className="kbd">4</span> or{' '}
              <span className="kbd">↑</span>
              <span className="kbd">↓</span> to choose · <span className="kbd">Enter</span> to answer
              · <span className="kbd">Esc</span> to quit
            </>
          ) : phase === 'answer' ? (
            <>
              <span className="kbd">1</span>–<span className="kbd">4</span> to answer ·{' '}
              <span className="kbd">Esc</span> to quit
            </>
          ) : (
            <>
              <span className="kbd">Enter</span> for the next question · <span className="kbd">Esc</span> to quit
            </>
          )}
        </p>
        <p className="tiny dim center touch-hint" style={{ marginTop: 18 }}>
          Tap an answer to choose it
        </p>
    </div>
  )
}

/** Big centre-screen element: element symbol, chemical equation, formula. */
function Stimulus({ question }: { question: Question }) {
  const stimulus = question.stimulus ?? {}
  if (!stimulus || !stimulus.kind || stimulus.kind === 'sequence') return null

  if (stimulus.kind === 'element_symbol') {
    return <div className="stimulus">{String(stimulus.symbol)}</div>
  }
  if (stimulus.kind === 'equation') {
    return <div className="stimulus stimulus-equation">{String(stimulus.text ?? stimulus.display ?? '')}</div>
  }
  if (stimulus.kind === 'formula') {
    return <div className="stimulus stimulus-equation">{String(stimulus.formula)}</div>
  }
  return null
}
