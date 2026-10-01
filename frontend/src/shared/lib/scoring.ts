/**
 * Client mirror of backend/app/services/scoring_engine.py.
 * Used only for instant on-screen feedback; the server recomputes and is authoritative.
 * Parity is covered by tests on both sides — if you change one, change the other.
 */

export const DIFFICULTY_POINTS: Record<string, number> = { easy: 100, medium: 150, hard: 220 }

const SPEED_BONUS_SHARE = 0.4
const SPEED_EXPONENT = 0.75
const MAX_STREAK_BONUS = 10
const STREAK_STEP = 0.05

export interface AnswerScore {
  points: number
  base_points: number
  speed_bonus: number
  multiplier: number
  is_correct: boolean
  speed_factor: number
}

export function speedFactor(responseMs: number, timeBudgetMs: number): number {
  if (timeBudgetMs <= 0) return 0
  const raw = (timeBudgetMs - Math.max(0, responseMs)) / timeBudgetMs
  const clamped = Math.min(1, Math.max(0, raw))
  return Math.pow(clamped, SPEED_EXPONENT)
}

export function streakMultiplier(streakBefore: number): number {
  const capped = Math.min(Math.max(streakBefore, 0), MAX_STREAK_BONUS)
  return Math.round((1 + STREAK_STEP * capped) * 10000) / 10000
}

export function scoreAnswer(opts: {
  difficulty: string
  responseMs: number
  timeBudgetMs: number
  streakBefore: number
  isCorrect: boolean
  wrongPenaltyFactor?: number
}): AnswerScore {
  const base = DIFFICULTY_POINTS[opts.difficulty] ?? DIFFICULTY_POINTS.medium
  const responseMs = Math.max(0, opts.responseMs)

  if (!opts.isCorrect) {
    const factor = opts.wrongPenaltyFactor ?? 0
    const penalty = factor <= 0 ? 0 : -Math.min(20, Math.round(factor * base))
    return { points: penalty, base_points: 0, speed_bonus: 0, multiplier: 1, is_correct: false, speed_factor: 0 }
  }

  const factor = speedFactor(responseMs, opts.timeBudgetMs)
  const bonus = Math.round(SPEED_BONUS_SHARE * base * factor)
  const multiplier = streakMultiplier(opts.streakBefore)
  return {
    points: Math.round((base + bonus) * multiplier),
    base_points: base,
    speed_bonus: bonus,
    multiplier,
    is_correct: true,
    speed_factor: factor,
  }
}

export const COMPLETION_BONUS = 100
export const ACCURACY_BONUS_FLOOR = 0.6
export const ACCURACY_BONUS_MAX = 500
