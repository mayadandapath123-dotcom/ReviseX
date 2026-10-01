"""Shared helpers for question generators."""

from __future__ import annotations

import re

import hashlib
import random
from typing import Any, Iterable, Sequence

from app.content.schema import OPTION_KEYS, QuestionDef, QuestionOption

# Deterministic per-item RNG seed salt: reseeding produces identical question ids,
# wording and distractors, so a student's history stays meaningful across reimports.
SALT = "leap-gen-v1"


def stable_rng(*parts: str) -> random.Random:
    seed = hashlib.sha256(("|".join([SALT, *parts])).encode("utf-8")).hexdigest()
    return random.Random(int(seed[:16], 16))


def question_id(chapter: str, topic: str | None, question_type: str, slug: str) -> str:
    base = f"{chapter}.{(topic or 'general').split('.')[-1]}.{question_type}.{slug}"
    return base.replace(" ", "-").lower()[:120]


#: A minus sign and a word separator both become "-", so collapsing the run
#: destroyed the sign: "poly-roots-3--2" (alpha=3, beta=-2) and
#: "poly-roots--3-2" (alpha=-3, beta=2) both reduced to "poly-roots-3-2".
#: Those are different questions sharing one id, and the seeder upserts by id,
#: so one of them was silently dropped - 160 questions across the maths bank.
_NEGATIVE_NUMBER_RE = re.compile(r"--+(?=\d)")


def slugify(text: str, limit: int = 40) -> str:
    out = "".join(ch if ch.isalnum() else "-" for ch in text.lower()).strip("-")
    # Spell the sign out before collapsing, so it survives as information.
    out = _NEGATIVE_NUMBER_RE.sub("-neg", out)
    while "--" in out:
        out = out.replace("--", "-")
    if len(out) > limit:
        # Truncating alone is lossy in a way that costs questions: two subjects
        # agreeing for the first `limit` characters mint the same id, and the
        # seeder upserts by id, so one silently replaces the other. "The
        # equivalent resistance of resistors connected in series" and the same
        # phrase ending "...in parallel" both became
        # "the-equivalent-resistance-of-resistors-c". Keep a readable prefix and
        # append a digest of the whole text, so distinct inputs stay distinct.
        digest = hashlib.sha1(out.encode("utf-8")).hexdigest()[:6]
        out = f"{out[:limit - 7].rstrip('-')}-{digest}"
    return out or "item"


def build_options(correct: str, distractors: Sequence[str], rng: random.Random) -> tuple[list[QuestionOption], str]:
    """Shuffle a correct answer with distractors into a/b/c/d keys.

    Every value is stripped before comparison. QuestionOption strips option text,
    so comparing against an unstripped `correct` would silently fail to find the
    answer key whenever authored content carries trailing whitespace. That used
    to surface as a bare StopIteration deep inside seeding; it is now normalised
    away, and a genuine mismatch raises a precise error instead.
    """
    answer = str(correct).strip()
    pool = [answer, *[str(d).strip() for d in distractors]]
    rng.shuffle(pool)
    options = [QuestionOption(key=key, text=text) for key, text in zip(OPTION_KEYS, pool)]
    for option in options:
        if option.text == answer:
            return options, option.key
    raise ValueError(f"Correct answer {correct!r} did not survive option construction")


def pick_distractors(
    correct: str,
    pool: Iterable[str],
    count: int = 3,
    rng: random.Random | None = None,
    case_sensitive: bool = False,
) -> list[str]:
    """Pick `count` plausible distractors from a same-domain pool, excluding the answer.

    The pool must come from the same fact family (same attribute / same category),
    which is what keeps distractors plausible instead of random.

    Candidates are folded to lower case before comparison by default, so "Water"
    and "water" are never offered as two different answers. Some subjects are
    genuinely case-significant - the genotypes TT, Tt and tt are three different
    things, and CO is carbon monoxide while Co is cobalt - so those clusters pass
    case_sensitive=True and are compared exactly. Defaulting to the old behaviour
    keeps every existing question id and content hash unchanged.
    """
    rng = rng or random.Random(0)

    def key(text: str) -> str:
        return text.strip() if case_sensitive else text.strip().lower()

    seen: set[str] = {key(correct)}
    candidates: list[str] = []
    for value in pool:
        if value is None:
            continue
        text = str(value).strip()
        if not text:
            continue
        candidate_key = key(text)
        if candidate_key in seen:
            continue
        seen.add(candidate_key)
        candidates.append(text)

    if len(candidates) < count:
        raise ValueError(f"Not enough plausible distractors ({len(candidates)}) for answer {correct!r}; need {count}")

    return rng.sample(candidates, count)


def numeric_distractors(value: float, rng: random.Random, fmt: str = "{}") -> list[str]:
    """Distractors that look like real calculation mistakes.

    Strategies: sign flip, factor-of-10 slip, common transposition, near-miss offset.
    """
    correct_text = _fmt_number(value, fmt)
    seen = {correct_text}
    out: list[str] = []

    strategies = [
        lambda v: -v,
        lambda v: v * 10,
        lambda v: v / 10 if v else v + 1,
        lambda v: v + 1,
        lambda v: v - 1,
        lambda v: v * 2,
        lambda v: v / 2 if v else v + 2,
    ]
    for strategy in strategies:
        try:
            candidate = _fmt_number(strategy(value), fmt)
        except (ZeroDivisionError, OverflowError):
            continue
        if candidate not in seen:
            seen.add(candidate)
            out.append(candidate)

    rng.shuffle(out)
    return out[:3]


def _fmt_number(value: float, fmt: str) -> str:
    if value == int(value):
        return fmt.format(int(value))
    return fmt.format(round(value, 2))


def make_question(
    *,
    qid: str,
    chapter: str,
    topic: str | None,
    question_type: str,
    prompt: str,
    options: Sequence[QuestionOption],
    answer_key: str,
    source_ref: str,
    explanation: str | None = None,
    hint: str | None = None,
    difficulty: str = "medium",
    time_budget_ms: int = 10000,
    tags: Sequence[str] = (),
    stimulus: dict[str, Any] | None = None,
    meta: dict[str, Any] | None = None,
    origin: str = "template",
    status: str = "approved",
) -> QuestionDef:
    return QuestionDef(
        id=qid,
        chapter=chapter,
        topic=topic,
        question_type=question_type,  # type: ignore[arg-type]
        prompt=prompt,
        stimulus=stimulus or {},
        options=list(options),
        answer_key=answer_key,
        explanation=explanation,
        hint=hint,
        difficulty=difficulty,  # type: ignore[arg-type]
        time_budget_ms=time_budget_ms,
        source_ref=source_ref,
        tags=list(tags),
        meta=meta or {},
        origin=origin,  # type: ignore[arg-type]
        status=status,  # type: ignore[arg-type]
    )


def unique_preserving_order(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            out.append(value)
    return out


def resolve_location(item: dict[str, Any], default_chapter: str, default_topic: str | None) -> tuple[str, str | None]:
    """Resolve an item's (chapter, topic) pair.

    A fact file declares a default chapter/topic, and individual items may
    override the chapter. If an item overrides the chapter but not the topic,
    the inherited topic would belong to a *different* chapter, so it is dropped
    rather than creating a referential-integrity error.
    """
    chapter = str(item.get("chapter") or default_chapter)
    topic = item.get("topic") or default_topic
    if topic and not str(topic).startswith(chapter + "."):
        topic = None
    return chapter, (str(topic) if topic else None)
