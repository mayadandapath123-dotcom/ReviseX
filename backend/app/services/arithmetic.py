"""Live arithmetic question generation.

Unlike the seeded bank, nothing here is stored: every request builds fresh
questions from the chosen level and operations. That is deliberate — mental
maths needs unbounded novelty, and a preloaded bank would repeat itself.

Design rules:
  * The answer is always computed, never looked up, so it cannot be wrong.
  * Every distractor is a named misconception (place-value slip, sign error,
    off-by-one factor, partial product) rather than a random number.
  * Options are always 4 distinct values with the correct one shuffled in.
"""

from __future__ import annotations

import random
from typing import Any, Sequence

LEVELS = ("easy", "medium", "hard")
OPERATIONS = ("add", "subtract", "multiply", "divide", "square", "percent")

# Operations that make sense at each level. Squares and percentages only
# appear from medium upwards because they assume times-table fluency.
LEVEL_OPS: dict[str, tuple[str, ...]] = {
    "easy": ("add", "subtract", "multiply", "divide"),
    "medium": ("add", "subtract", "multiply", "divide", "square"),
    "hard": OPERATIONS,
}


class ArithmeticError(ValueError):
    """Raised when a generation request cannot be satisfied."""


def _near_misses(answer: int, count: int, rng: random.Random) -> list[int]:
    """Fallback distractors: small offsets that stay plausible."""
    pool = [1, -1, 2, -2, 10, -10, 5, -5, 100, -100, 3, -3]
    out: list[int] = []
    rng.shuffle(pool)
    for delta in pool:
        candidate = answer + delta
        if candidate >= 0 and candidate != answer and candidate not in out:
            out.append(candidate)
        if len(out) >= count:
            break
    # Extremely small answers can exhaust the positive pool; pad upwards.
    step = 1
    while len(out) < count:
        candidate = answer + step
        if candidate >= 0 and candidate != answer and candidate not in out:
            out.append(candidate)
        step += 1
    return out


def _build_options(answer: int, wrong: Sequence[int], rng: random.Random) -> tuple[list[dict[str, Any]], str]:
    """Return 4 options, correct one included, in a stable-shuffled order."""
    seen: list[int] = []
    for value in wrong:
        value = int(value)
        if value < 0 or value == answer or value in seen:
            continue
        seen.append(value)
        if len(seen) == 3:
            break
    if len(seen) < 3:
        for value in _near_misses(answer, 3 - len(seen), rng):
            if value not in seen:
                seen.append(value)
    options = seen[:3] + [answer]
    rng.shuffle(options)
    keys = ["a", "b", "c", "d"]
    correct_key = keys[options.index(answer)]
    return [
        {"key": keys[i], "text": str(options[i]), "is_correct": options[i] == answer}
        for i in range(4)
    ], correct_key


def _digits_reversed(n: int) -> int:
    return int(str(n)[::-1])


# --------------------------------------------------------------------------
# Per-operation generators. Each returns (prompt, answer, [distractors]).
# --------------------------------------------------------------------------

def _gen_add(level: str, rng: random.Random) -> tuple[str, int, list[int], str]:
    bounds = {"easy": (2, 9), "medium": (11, 89), "hard": (105, 899)}[level]
    a = rng.randint(*bounds)
    b = rng.randint(*bounds)
    answer = a + b
    wrong = [
        a + b + 10,          # place-value slip on the tens column
        a + b - 10,
        a + b + 1,           # off by one (carry dropped)
        a - b if a > b else b - a,   # added instead of subtracted
        _digits_reversed(answer),
    ]
    return f"{a} + {b} = ?", answer, wrong, "addition"


def _gen_subtract(level: str, rng: random.Random) -> tuple[str, int, list[int], str]:
    bounds = {"easy": (6, 20), "medium": (30, 149), "hard": (250, 1899)}[level]
    a = rng.randint(*bounds)
    b = rng.randint(bounds[0] // 2 or 1, a)
    answer = a - b
    wrong = [
        b - a if b > a else a + b,   # sign error: operands swapped
        answer + 10,
        answer - 10,
        answer + 1,                  # borrowing slip
        answer - 1,
    ]
    return f"{a} − {b} = ?", answer, wrong, "subtraction"


def _gen_multiply(level: str, rng: random.Random) -> tuple[str, int, list[int], str]:
    if level == "easy":
        a, b = rng.randint(2, 9), rng.randint(2, 9)
    elif level == "medium":
        a, b = rng.randint(11, 29), rng.randint(3, 9)
    else:
        a, b = rng.randint(13, 89), rng.randint(11, 39)
    answer = a * b
    wrong = [
        a * (b + 1),         # one factor too high
        a * (b - 1) if b > 1 else a * (b + 2),
        (a + 1) * b,         # partial-product slip
        a * b + a,           # forgot to carry a row
        a * b * 10,          # place-value slip
        a + b,               # multiplied instead of added
    ]
    return f"{a} × {b} = ?", answer, wrong, "multiplication"


def _gen_divide(level: str, rng: random.Random) -> tuple[str, int, list[int], str]:
    # Build dividend from divisor x quotient so the answer is always exact.
    if level == "easy":
        divisor, quotient = rng.randint(2, 9), rng.randint(2, 9)
    elif level == "medium":
        divisor, quotient = rng.randint(3, 12), rng.randint(5, 20)
    else:
        divisor, quotient = rng.randint(6, 24), rng.randint(13, 60)
    dividend = divisor * quotient
    answer = quotient
    wrong = [
        quotient + 1,        # off by one
        quotient - 1 if quotient > 1 else quotient + 2,
        quotient + 10,       # place-value slip
        divisor,             # reported the divisor instead
        dividend // (quotient + 1) if quotient + 1 else quotient,
        quotient * 10,
    ]
    return f"{dividend} ÷ {divisor} = ?", answer, wrong, "division"


def _gen_square(level: str, rng: random.Random) -> tuple[str, int, list[int], str]:
    lo, hi = (4, 10) if level == "medium" else (11, 25)
    n = rng.randint(lo, hi)
    answer = n * n
    wrong = [
        n * 2,               # doubled instead of squared
        (n + 1) * (n + 1),
        (n - 1) * (n - 1) if n > 1 else (n + 2) ** 2,
        n * n + n,           # n(n+1) confusion
        n * n - n,
    ]
    return f"{n}² = ?", answer, wrong, "squares"


def _gen_percent(level: str, rng: random.Random) -> tuple[str, int, list[int], str]:
    pct = rng.choice([5, 10, 15, 20, 25, 40, 50, 75])
    base = rng.choice([40, 60, 80, 120, 160, 200, 240, 400, 800])
    answer = base * pct // 100
    wrong = [
        answer * 10,         # decimal-point slip
        max(answer // 10, answer - 1),
        base * (pct + 10) // 100,
        base * max(pct - 10, 1) // 100,
        base - answer,       # the complement instead
    ]
    return f"{pct}% of {base} = ?", answer, wrong, "percentages"


_GENERATORS = {
    "add": _gen_add,
    "subtract": _gen_subtract,
    "multiply": _gen_multiply,
    "divide": _gen_divide,
    "square": _gen_square,
    "percent": _gen_percent,
}


def generate(
    *,
    level: str = "medium",
    operations: Sequence[str] = ("add", "subtract", "multiply", "divide"),
    count: int = 12,
    seed: int | None = None,
) -> dict[str, Any]:
    """Build `count` live MCQ questions for the requested level and operations."""
    if level not in LEVELS:
        raise ArithmeticError(f"Unknown level '{level}'. Choose one of: {', '.join(LEVELS)}")
    if not 1 <= count <= 60:
        raise ArithmeticError("count must be between 1 and 60")

    allowed = LEVEL_OPS[level]
    ops = [o for o in operations if o in allowed]
    if not ops:
        raise ArithmeticError(
            f"None of the requested operations are available at '{level}' level. "
            f"Available: {', '.join(allowed)}"
        )

    rng = random.Random(seed)
    questions: list[dict[str, Any]] = []
    seen_prompts: set[str] = set()

    # Cap attempts so a tiny operation pool cannot loop forever.
    attempts = 0
    while len(questions) < count and attempts < count * 40:
        attempts += 1
        op = rng.choice(ops)
        prompt, answer, wrong, topic = _GENERATORS[op](level, rng)
        if prompt in seen_prompts:
            continue
        seen_prompts.add(prompt)
        options, correct_key = _build_options(answer, wrong, rng)
        questions.append(
            {
                "id": f"arith-{level}-{op}-{len(questions) + 1}-{rng.randint(1000, 9999)}",
                "question_type": "mcq_single",
                "prompt": prompt,
                "stimulus": None,
                "difficulty": level,
                "operation": op,
                "topic_name": topic,
                "answer": answer,
                "answer_key": correct_key,
                "options": options,
                "explanation": f"{prompt.rstrip(' =?')} equals {answer}.",
            }
        )

    if len(questions) < count:
        raise ArithmeticError(
            f"Could only build {len(questions)} unique {level} questions for those operations."
        )

    return {
        "level": level,
        "operations": ops,
        "count": len(questions),
        "questions": questions,
    }


def grade(questions: Sequence[dict[str, Any]], attempts: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """Re-grade on the server. The client's own is_correct is never trusted."""
    by_id = {q["id"]: q for q in questions}
    graded: list[dict[str, Any]] = []
    correct = 0
    total_ms = 0
    for attempt in attempts:
        q = by_id.get(attempt.get("question_id", ""))
        if q is None:
            continue
        selected = attempt.get("selected_key")
        is_correct = selected == q["answer_key"]
        correct += 1 if is_correct else 0
        total_ms += int(attempt.get("response_ms") or 0)
        graded.append(
            {
                "question_id": q["id"],
                "prompt": q["prompt"],
                "selected_key": selected,
                "correct_key": q["answer_key"],
                "correct_value": q["answer"],
                "is_correct": is_correct,
                "explanation": q["explanation"],
            }
        )
    answered = len(graded)
    accuracy = (correct / answered) if answered else 0.0
    # Same shape as the seeded-bank scoring so the UI can reuse its display:
    # wrong answers score nothing, and the completion bonus is gated on accuracy.
    score = int(correct * {"easy": 8, "medium": 12, "hard": 18}.get(
        questions[0]["difficulty"] if questions else "medium", 12
    ))
    completion = (answered / len(questions)) if questions else 0.0
    bonus = int(100 * completion * accuracy)
    return {
        "score": score,
        "xp": (score + bonus) // 10,
        "correct": correct,
        "answered": answered,
        "question_count": len(questions),
        "accuracy": round(accuracy, 4),
        "avg_response_ms": round(total_ms / answered, 1) if answered else 0,
        "completion_bonus": bonus,
        "graded": graded,
    }
