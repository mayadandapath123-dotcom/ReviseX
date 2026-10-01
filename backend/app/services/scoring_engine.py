"""ScoringEngine — the canonical scoring rules.

Mirrored 1:1 in `frontend/src/shared/lib/scoring.ts` so the UI can show live
points without a round trip, and both sides are covered by parity tests.

Guarantees required by the brief:
  * a wrong answer can never outscore a correct one;
  * speed is rewarded only on correct answers, and capped (40% of base);
  * streaks give at most a 1.5x multiplier;
  * blind clicking has negative expected value.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Sequence

DIFFICULTY_POINTS: dict[str, int] = {"easy": 100, "medium": 150, "hard": 220}
DIFFICULTY_EXPECTED: dict[str, float] = {"easy": 0.85, "medium": 0.70, "hard": 0.55}

SPEED_BONUS_SHARE = 0.40
SPEED_EXPONENT = 0.75
MAX_STREAK_BONUS = 10  # streaks beyond 10 stop increasing the multiplier
STREAK_STEP = 0.05      # 0.10 * (streak/2) => +0.05 per correct answer
MAX_MULTIPLIER = 1.5

COMPLETION_BONUS = 100
ACCURACY_BONUS_FLOOR = 0.60
ACCURACY_BONUS_MAX = 500


@dataclass(frozen=True)
class AnswerScore:
    points: int
    base_points: int
    speed_bonus: int
    multiplier: float
    is_correct: bool
    response_ms: int
    speed_factor: float = 0.0


@dataclass
class SessionSummary:
    score: int = 0
    xp: int = 0
    correct: int = 0
    answered: int = 0
    accuracy: float = 0.0
    avg_response_ms: float = 0.0
    fastest_response_ms: int | None = None
    best_streak: int = 0
    completion_bonus: int = 0
    accuracy_bonus: int = 0
    per_attempt: list[AnswerScore] = field(default_factory=list)
    by_topic: dict[str, dict[str, float]] = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "score": self.score,
            "xp": self.xp,
            "correct": self.correct,
            "answered": self.answered,
            "accuracy": round(self.accuracy, 4),
            "avg_response_ms": round(self.avg_response_ms, 1),
            "fastest_response_ms": self.fastest_response_ms,
            "best_streak": self.best_streak,
            "completion_bonus": self.completion_bonus,
            "accuracy_bonus": self.accuracy_bonus,
        }


@dataclass(frozen=True)
class AttemptInput:
    question_id: str
    topic_id: str | None
    chapter_id: str | None
    difficulty: str
    response_ms: int
    is_correct: bool
    time_budget_ms: int = 10000


def speed_factor(response_ms: int, time_budget_ms: int) -> float:
    """1.0 at zero seconds, 0.0 at or beyond the budget. Flattened with an exponent
    so the difference between 1.0 s and 1.4 s does not dominate the score."""
    if time_budget_ms <= 0:
        return 0.0
    raw = (time_budget_ms - max(0, response_ms)) / time_budget_ms
    clamped = min(1.0, max(0.0, raw))
    return clamped ** SPEED_EXPONENT


def streak_multiplier(streak_before: int) -> float:
    capped = min(max(streak_before, 0), MAX_STREAK_BONUS)
    return round(1.0 + STREAK_STEP * capped, 4)


def score_answer(
    *,
    difficulty: str,
    response_ms: int,
    time_budget_ms: int,
    streak_before: int,
    is_correct: bool,
    wrong_penalty_factor: float = 0.0,
) -> AnswerScore:
    base = DIFFICULTY_POINTS.get(difficulty, DIFFICULTY_POINTS["medium"])

    if not is_correct:
        penalty = 0 if wrong_penalty_factor <= 0 else -min(20, int(round(wrong_penalty_factor * base)))
        return AnswerScore(
            points=penalty,
            base_points=0,
            speed_bonus=0,
            multiplier=1.0,
            is_correct=False,
            response_ms=max(0, response_ms),
        )

    factor = speed_factor(response_ms, time_budget_ms)
    bonus = int(round(SPEED_BONUS_SHARE * base * factor))
    multiplier = streak_multiplier(streak_before)
    points = int(round((base + bonus) * multiplier))

    return AnswerScore(
        points=points,
        base_points=base,
        speed_bonus=bonus,
        multiplier=multiplier,
        is_correct=True,
        response_ms=max(0, response_ms),
        speed_factor=factor,
    )


def summarise(
    attempts: Sequence[AttemptInput | dict],
    *,
    wrong_penalty_factor: float = 0.0,
    completion_ratio: float = 1.0,
    xp_divisor: int = 10,
) -> SessionSummary:
    """Grade a whole session, maintaining streak across attempts in order."""
    summary = SessionSummary()
    streak = 0

    for attempt in attempts:
        data = attempt if isinstance(attempt, dict) else attempt.__dict__
        result = score_answer(
            difficulty=str(data.get("difficulty", "medium")),
            response_ms=int(data.get("response_ms", 0)),
            time_budget_ms=int(data.get("time_budget_ms", 10000)),
            streak_before=streak,
            is_correct=bool(data.get("is_correct")),
            wrong_penalty_factor=wrong_penalty_factor,
        )
        summary.per_attempt.append(result)

        if result.is_correct:
            streak += 1
            summary.correct += 1
        else:
            streak = 0
        summary.best_streak = max(summary.best_streak, streak)
        summary.answered += 1

        response = int(data.get("response_ms", 0))
        if response > 0:
            summary.avg_response_ms += response
            if summary.fastest_response_ms is None or response < summary.fastest_response_ms:
                summary.fastest_response_ms = response

        topic_id = data.get("topic_id")
        if topic_id:
            bucket = summary.by_topic.setdefault(str(topic_id), {"attempts": 0, "correct": 0})
            bucket["attempts"] += 1
            bucket["correct"] += 1 if result.is_correct else 0

    if summary.answered:
        summary.accuracy = summary.correct / summary.answered
        summary.avg_response_ms /= summary.answered

    points_total = sum(result.points for result in summary.per_attempt)

    # The completion bonus rewards finishing a set rather than abandoning it. It is
    # scaled by accuracy because a flat bonus paid at 0% accuracy hands out points
    # for blind clicking, which the scoring contract forbids: answering every
    # question wrongly must not be worth anything.
    if summary.answered > 0 and completion_ratio > 0:
        summary.completion_bonus = int(round(COMPLETION_BONUS * completion_ratio * summary.accuracy))

    if summary.accuracy >= ACCURACY_BONUS_FLOOR:
        summary.accuracy_bonus = int(round(ACCURACY_BONUS_MAX * (summary.accuracy - ACCURACY_BONUS_FLOOR)))

    summary.score = max(0, points_total + summary.completion_bonus + summary.accuracy_bonus)
    summary.xp = summary.score // max(1, xp_divisor)

    for bucket in summary.by_topic.values():
        bucket["accuracy"] = (bucket["correct"] / bucket["attempts"]) if bucket["attempts"] else 0.0

    return summary


def weak_and_strong(by_topic: dict[str, dict[str, float]], topic_names: dict[str, str] | None = None, min_attempts: int = 2) -> dict[str, list[dict]]:
    """Split topics into weak/strong buckets for the results screen."""
    names = topic_names or {}
    scored = [
        {
            "topic_id": topic_id,
            "name": names.get(topic_id, topic_id),
            "accuracy": values["accuracy"],
            "attempts": int(values["attempts"]),
        }
        for topic_id, values in by_topic.items()
        if values["attempts"] >= min_attempts
    ]
    scored.sort(key=lambda item: (item["accuracy"], -item["attempts"]))
    return {
        "weak": [item for item in scored if item["accuracy"] < 0.7][:4],
        "strong": [item for item in scored if item["accuracy"] >= 0.85][-4:],
    }


def mastery_update(previous: float, is_correct: bool, difficulty: str, learning_rate: float = 0.25) -> float:
    """Leaky, recency-weighted mastery estimate (see docs/SCORING.md)."""
    expected = DIFFICULTY_EXPECTED.get(difficulty, 0.70)
    result = 1.0 if is_correct else 0.0
    updated = previous + learning_rate * (result - expected)
    return round(min(1.0, max(0.0, updated)), 4)


def confidence(attempts: int) -> float:
    return round(attempts / (attempts + 6), 4)
