# Scoring, streaks, XP, mastery and spaced repetition

Canonical implementation: `backend/app/services/scoring_engine.py`.
Client mirror (display only, server is authoritative): `frontend/src/shared/lib/scoring.ts`.
If you change one, change the other — `tests/test_core.py` pins the fixture values.

## 1. Per-answer points

```
difficulty_points = { easy: 100, medium: 150, hard: 220 }

speed_factor = clamp((time_budget_ms - response_ms) / time_budget_ms, 0, 1) ^ 0.75
speed_bonus  = round(0.40 * difficulty_points * speed_factor)        # correct only

streak_mult  = 1 + 0.05 * min(streak_before, 10)                     # 1.00 -> 1.50

correct: points = round((difficulty_points + speed_bonus) * streak_mult)
wrong:   points = 0                                                  # rush modes
                = -min(20, round(0.15 * difficulty_points))          # exam_simulation only
```

Worked example (pinned by a test): medium, 2500 ms of a 10 000 ms budget, streak 3.
`speed_factor = 0.75^0.75 = 0.8059` → `speed_bonus = round(0.4*150*0.8059) = 48`
→ `mult = 1.15` → `points = round((150+48)*1.15) = 228`.

### Why this cannot be gamed

| Guarantee | Mechanism |
|---|---|
| Fast wrong never beats slow correct | wrong ≤ 0 points; correct ≥ `difficulty_points` ≥ 100 |
| Speed cannot dominate | bonus capped at 40% of base |
| Streaks cannot explode | multiplier capped at 1.5× after 10 |
| Blind clicking loses | 25% hit rate, and each miss resets the multiplier; a test asserts guessing < 35% of honest play |
| Penalty cannot dominate a session | capped at −20 and off by default |

## 2. Session score

```
points_total      = Σ per-answer points
completion_bonus  = round(100 * completion_ratio * accuracy)
accuracy_bonus    = round(500 * (accuracy - 0.60))   if accuracy >= 0.60
score             = max(0, points_total + completion_bonus + accuracy_bonus)
xp                = score // 10
```

The completion bonus rewards finishing a set rather than abandoning it, but it is
**scaled by accuracy**. A flat bonus paid out at 0% accuracy used to hand a fully
wrong session 100 points, which rewarded blind clicking; that is now impossible and
a test pins it. Answering every question wrongly scores exactly 0.

`fastest_avg` personal bests are only recorded from sessions with ≥ 5 answers, so
a one-question fluke cannot set a speed record.

## 3. Levels

```
xp_for_level(n) = round(300 * (n-1)^1.6 / 10) * 10        # cumulative, level 1 = 0
```

Level 1 → 0, L2 → 300, L3 → 920, L4 → 1740, L5 → 2790, L6 → 4030 …
Names are data in `progress_service.LEVEL_NAMES`: Beginner, Learner, Quick Recall,
Fast Recall, Chapter Master, Speed Reader, Revision Pro, Concept Crusher, Syllabus
Slayer, Exam Ready, Top Scorer, Grandmaster.

Extra XP awards: +25 for any new mode/chapter/branch/day score record, +50 per badge.

## 4. Topic mastery

Leaky, recency-weighted estimate updated per attempt:

```
expected    = { easy: 0.85, medium: 0.70, hard: 0.55 }
result      = 1 if correct else 0
mastery_new = clamp(mastery_old + 0.25 * (result - expected), 0, 1)
confidence  = attempts / (attempts + 6)
```

UI shows a mastery percentage only when `confidence >= 0.3` so a single lucky
guess cannot display "44%".

## 5. Weak-topic selection

```
weakness = 0.70 * (1 - mastery) + 0.20 * recency_penalty + 0.10 * error_rate
recency_penalty = clamp(days_since_practised / 7, 0, 1)
```

Recency keeps one bad topic from dominating forever while still surfacing
neglected material. `weak_topics` mode reorders the pool by this score; it never
discards other questions, so a test still feels varied.

## 6. Spaced repetition (deliberately simple)

| Outcome | Next interval | State |
|---|---|---|
| wrong | immediately (re-shown after ~4 questions in-session) | `learning` |
| 1st correct | 1 day | `learning` |
| 2nd correct | 3 days | `review` |
| 3rd correct | 7 days | `review` |
| 4th+ | ×2.5, capped at 30 days | `mastered` at ≥ 21 days |

Due cards are front-loaded into a test (up to ~1/3 of the set) **only if they also
match the mode's filters** — a due MCQ must not leak into a balancing drill.
`ease` is stored per card (−0.2 per lapse, floor 1.3) but unused in V1, so a
future SM-2/FSRS swap needs no migration.

## 7. Mistake book

A wrong answer upserts `mistakes` (`wrong_count += 1`, `resolved = 0`). Each
subsequent correct answer increments `correct_since_count`; at 2 the mistake is
marked `resolved` and drops out of `previous_mistakes` mode.

## 8. Badges

Criteria are data (`badges.criterion_json`) evaluated in `ProgressService`:
`sessions_completed`, `questions_answered`, `answer_streak`, `mistakes_resolved`,
`question_type_correct`, `level`, `day_streak`, `session_accuracy` and
`session_avg_response_ms` (the last two require a minimum question count).

## 9. Anti-cheat posture (local MVP, designed for the online future)

* Server re-grades every attempt; client-reported points and `is_correct` are ignored.
* Balancing coefficients are re-verified by `BalancingEngine.verify()`.
* Per-attempt `response_ms` and `shown_ms` are persisted, so an online submission
  can later be checked against physically plausible timings (e.g. < 300 ms/answer).
* `sessions.client_version` and `sync_state` are recorded for future validation.
