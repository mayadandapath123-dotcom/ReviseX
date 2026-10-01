import { useMemo, useState } from 'react'
import type { Question } from '@/shared/types'
import { Button } from '@/shared/ui/primitives'

/**
 * Client-side atom counter, mirroring backend/services/balancing_engine.py.
 * Verification is by atom conservation — never by comparing to a stored string —
 * so a student who writes a valid multiple still gets credited, and the server
 * independently re-checks the same coefficients on submit.
 */

type Atoms = Record<string, number>

function parseFormula(formula: string): Atoms {
  const text = formula.replace(/\s+/g, '').replace(/[[\]]/g, (m) => (m === '[' ? '(' : ')'))
  const atoms: Atoms = {}
  let index = 0

  const readInt = (): number => {
    let digits = ''
    while (index < text.length && /\d/.test(text[index])) digits += text[index++]
    return digits ? parseInt(digits, 10) : 1
  }

  const parseGroup = (): Atoms => {
    const group: Atoms = {}
    while (index < text.length) {
      const char = text[index]
      if (char === '(') {
        index++
        const inner = parseGroup()
        if (text[index] === ')') index++
        const multiplier = readInt()
        for (const [element, count] of Object.entries(inner)) group[element] = (group[element] ?? 0) + count * multiplier
        continue
      }
      if (char === ')') break

      const match = /^[A-Z][a-z]?/.exec(text.slice(index))
      if (!match) {
        index++
        continue
      }
      index += match[0].length
      const count = readInt()
      group[match[0]] = (group[match[0]] ?? 0) + count
    }
    return group
  }

  Object.assign(atoms, parseGroup())
  return atoms
}

function multiply(atoms: Atoms, factor: number): Atoms {
  const out: Atoms = {}
  for (const [element, count] of Object.entries(atoms)) out[element] = count * factor
  return out
}

function sumAll(list: Atoms[]): Atoms {
  const out: Atoms = {}
  for (const atoms of list) for (const [element, count] of Object.entries(atoms)) out[element] = (out[element] ?? 0) + count
  return out
}

function gcd(a: number, b: number): number {
  return b === 0 ? Math.abs(a) : gcd(b, a % b)
}

interface CheckResult {
  balanced: boolean
  simplest: boolean
  mismatched: string[]
  left: Atoms
  right: Atoms
  elements: string[]
}

function check(reactants: string[], products: string[], coefficients: number[]): CheckResult {
  const leftAtoms = reactants.map(parseFormula)
  const rightAtoms = products.map(parseFormula)
  const left = sumAll(leftAtoms.map((atoms, i) => multiply(atoms, coefficients[i] ?? 1)))
  const right = sumAll(rightAtoms.map((atoms, i) => multiply(atoms, coefficients[reactants.length + i] ?? 1)))

  const elements = Array.from(new Set([...Object.keys(left), ...Object.keys(right)])).sort()
  const mismatched = elements.filter((element) => (left[element] ?? 0) !== (right[element] ?? 0))
  const balanced = mismatched.length === 0

  let common = 0
  for (const value of coefficients) common = gcd(common, value)

  return { balanced, simplest: balanced && common <= 1, mismatched, left, right, elements }
}

export function BalancingView({
  question,
  locked,
  verdict,
  onChecked,
}: {
  question: Question
  locked: boolean
  verdict: { points: number; correct: boolean } | null
  onChecked: (coefficients: number[], balanced: boolean) => void
}) {
  const stimulus = question.stimulus ?? {}
  const reactants: string[] = stimulus.reactants ?? []
  const products: string[] = stimulus.products ?? []
  const maxCoefficient: number = stimulus.max_coefficient ?? 8

  const [coefficients, setCoefficients] = useState<number[]>(() => Array(reactants.length + products.length).fill(1))
  const [checked, setChecked] = useState<CheckResult | null>(null)
  const [attemptsUsed, setAttemptsUsed] = useState(0)

  const live = useMemo(() => check(reactants, products, coefficients), [reactants, products, coefficients])

  const bump = (position: number, delta: number) => {
    if (locked) return
    setCoefficients((current) =>
      current.map((value, index) => (index === position ? Math.min(maxCoefficient, Math.max(1, value + delta)) : value)),
    )
    setChecked(null)
  }

  const submitCheck = () => {
    const result = check(reactants, products, coefficients)
    setChecked(result)
    setAttemptsUsed((n) => n + 1)
    if (result.simplest) {
      onChecked(coefficients, true)
    } else if (attemptsUsed >= 2) {
      // Three tries: grade it and move on so the pace never stalls.
      onChecked(coefficients, false)
    }
  }

  const hint = () => {
    if (live.balanced) return 'It balances — now divide every coefficient by their common factor.'
    const element = live.mismatched[0]
    const leftCount = live.left[element] ?? 0
    const rightCount = live.right[element] ?? 0
    const side = leftCount < rightCount ? 'left' : 'right'
    return `${element}: ${leftCount} on the left vs ${rightCount} on the right. Adjust a coefficient on the ${side} side containing ${element}.`
  }

  const term = (formula: string, position: number) => (
    <span className="balance-term">
      <span className="stepper">
        <button className="stepper-btn" onClick={() => bump(position, -1)} disabled={locked || coefficients[position] <= 1} aria-label="decrease">
          −
        </button>
        <span className="stepper-value">{coefficients[position]}</span>
        <button
          className="stepper-btn"
          onClick={() => bump(position, 1)}
          disabled={locked || coefficients[position] >= maxCoefficient}
          aria-label="increase"
        >
          +
        </button>
      </span>
      <span className="balance-formula">{formula}</span>
    </span>
  )

  return (
    <>
      <p className="prompt center">{question.prompt}</p>

      <div className="balance-eq">
        {reactants.map((formula, i) => (
          <span key={`r-${formula}`} className="row" style={{ gap: 10 }}>
            {i > 0 && <span className="balance-op">+</span>}
            {term(formula, i)}
          </span>
        ))}
        <span className="balance-op">→</span>
        {products.map((formula, i) => (
          <span key={`p-${formula}`} className="row" style={{ gap: 10 }}>
            {i > 0 && <span className="balance-op">+</span>}
            {term(formula, reactants.length + i)}
          </span>
        ))}
      </div>

      <div className="card card-flat" style={{ marginBottom: 14 }}>
        <table className="atom-table">
          <thead>
            <tr>
              <th style={{ textAlign: 'left' }}>Element</th>
              <th>Left</th>
              <th>Right</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {live.elements.map((element) => {
              const left = live.left[element] ?? 0
              const right = live.right[element] ?? 0
              const ok = left === right
              return (
                <tr key={element}>
                  <td style={{ textAlign: 'left', fontWeight: 600 }}>{element}</td>
                  <td className={`mono ${ok ? 'atom-ok' : 'atom-bad'}`}>{left}</td>
                  <td className={`mono ${ok ? 'atom-ok' : 'atom-bad'}`}>{right}</td>
                  <td>{ok ? '✓' : '✕'}</td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {!locked && (
        <div className="row" style={{ justifyContent: 'center', gap: 10 }}>
          <Button variant="primary" size="lg" onClick={submitCheck}>
            Check
          </Button>
          <Button variant="ghost" onClick={() => setCoefficients(Array(reactants.length + products.length).fill(1))}>
            Reset
          </Button>
        </div>
      )}

      {checked && !checked.simplest && !locked && (
        <div className="feedback feedback-wrong" style={{ marginTop: 14 }}>
          <p style={{ fontWeight: 700, color: 'var(--error)' }}>
            {checked.balanced ? 'Balanced, but not in the simplest ratio' : 'Not balanced yet'}
          </p>
          <p className="small muted" style={{ marginTop: 5 }}>
            {hint()}
          </p>
          <p className="tiny dim" style={{ marginTop: 6 }}>
            Attempt {attemptsUsed} of 3 · {attemptsUsed >= 2 ? 'one more check will move you on' : 'try again'}
          </p>
        </div>
      )}

      {locked && verdict && (
        <div className={`feedback ${verdict.correct ? 'feedback-correct' : 'feedback-wrong'}`}>
          <div className="row-between">
            <span style={{ fontWeight: 700, color: verdict.correct ? 'var(--success)' : 'var(--error)' }}>
              {verdict.correct ? '✓ Balanced' : '✕ Not balanced'}
            </span>
            <span className="points-float">{verdict.points > 0 ? `+${verdict.points}` : verdict.points}</span>
          </div>
          {question.explanation && (
            <p className="small muted" style={{ marginTop: 6 }}>
              {question.explanation}
            </p>
          )}
        </div>
      )}
    </>
  )
}
