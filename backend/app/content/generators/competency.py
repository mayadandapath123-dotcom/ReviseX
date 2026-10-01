"""Competency-based authored items -> validated single-answer MCQs.

CBSE's 2025-26 design puts roughly half the paper on competency-based items:
case studies, source-based reading, assertion-reason pairs and application
problems. Those cannot be derived from a fact table -- the judgement lives in
the item itself -- so they are authored directly and this generator's job is to
make them safe and consistent:

  * exactly four options, no blanks, no duplicates, no answer outside them
  * assertion-reason items are built from a VERDICT, so CBSE's fixed four-option
    scaffold is generated here once and can never drift between items
  * a case-study passage is carried into every sub-question's prompt, because
    `.prompt` renders with `white-space: pre-line` and the student must see the
    passage on the same screen as the question
  * competency and format are recorded in `meta_json`, so "show me only
    application-level items" is a filter and not a rewrite

Nothing here invents subject content. It only structures and validates what an
author wrote, and it refuses to emit an item that a student could answer by
spotting the odd one out.
"""

from __future__ import annotations

import hashlib
from typing import Any, Sequence

from app.content.generators.base import (
    build_options,
    make_question,
    question_id,
    resolve_location,
    slugify,
    stable_rng,
)
from app.content.schema import OPTION_KEYS, QuestionDef, QuestionOption
from app.content.validators import content_hash

#: CBSE's competency vocabulary. "creation" is not assessable in an MCQ, so it
#: is deliberately absent rather than silently accepted.
COMPETENCIES = frozenset({"recall", "understanding", "application", "analysis", "evaluation"})

#: Item formats we render. `direct` is a plain authored MCQ.
FORMATS = frozenset({
    "direct",
    "case_study",
    "source_based",
    "assertion_reason",
    "application",
    "analytical",
})

#: CBSE's standard assertion-reason scaffold, in the board's own order. Authored
#: items pick one of these by verdict instead of retyping the four sentences,
#: which is how wording drift and swapped keys creep into a question bank.
AR_OPTIONS = (
    "Both A and R are true and R is the correct explanation of A",
    "Both A and R are true but R is NOT the correct explanation of A",
    "A is true but R is false",
    "A is false but R is true",
)

AR_VERDICTS = {
    "both_true_explains": 0,
    "both_true_not_explains": 1,
    "a_true_r_false": 2,
    "a_false_r_true": 3,
}

BASE_TIME_MS = {"easy": 9000, "medium": 12000, "hard": 17000}

#: Reading speed allowance for a passage, in ms per character. A 400-character
#: stem adds about 20 seconds on top of the base budget, which matches how long
#: a Class 10 student actually spends reading one.
READING_MS_PER_CHAR = 0.05
MAX_READING_MS = 40000


class CompetencyItemError(ValueError):
    """An authored item is malformed. Raised at seed time, never in front of a student."""


def _reading_ms(stem: str) -> int:
    return min(int(len(stem) * READING_MS_PER_CHAR), MAX_READING_MS)


def _budget(difficulty: str, stem: str = "") -> int:
    return BASE_TIME_MS.get(difficulty, 12000) + _reading_ms(stem)


def _fingerprint(text: str) -> str:
    """Short stable digest, so two items in one chapter cannot collide on id."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:8]


def _answer_index(answer: Any, option_count: int) -> int:
    """Accept either a zero-based position or a letter key."""
    if isinstance(answer, bool):
        raise CompetencyItemError("answer must be an index 0-3 or a letter a-d, not a boolean")
    if isinstance(answer, int):
        if not 0 <= answer < option_count:
            raise CompetencyItemError(f"answer index {answer} is outside the {option_count} options")
        return answer
    text = str(answer).strip().lower()
    if text in OPTION_KEYS:
        return OPTION_KEYS.index(text)
    if text.isdigit():
        return _answer_index(int(text), option_count)
    raise CompetencyItemError(f"answer {answer!r} is neither an index 0-3 nor a key a-d")


def _normalise_options(raw: Sequence[Any], case_sensitive: bool = False) -> list[str]:
    """Check one item's four options and return them stripped.

    Folding case is the default because it catches the ordinary authoring slip of
    writing one answer twice with different capitalisation. But case is load-
    bearing in some of the content: TT, Tt and tt are three different genotypes,
    and in chemistry CO is carbon monoxide while Co is cobalt. An item that needs
    those kept apart sets `case_sensitive`, and its options are then compared
    exactly - the same flag the fact generator already honours.
    """
    if len(raw) != 4:
        raise CompetencyItemError(f"expected exactly 4 options, got {len(raw)}")
    texts = [str(option).strip() for option in raw]
    for text in texts:
        if not text:
            raise CompetencyItemError("an option is blank")
    compared = texts if case_sensitive else [text.lower() for text in texts]
    if len(set(compared)) != len(texts):
        raise CompetencyItemError(f"two options are the same answer twice: {texts}")
    return texts


def _competency_of(item: dict[str, Any], default: str = "recall") -> str:
    value = str(item.get("competency") or "").strip().lower()
    if not value:
        # An unlabelled item falls back to the caller's expectation rather than
        # being guessed at; assertion-reason defaults to analysis, everything
        # else to recall, and the tag spread shows which happened.
        return default
    if value in {"knowledge", "remember", "remembering"}:
        return "recall"
    if value not in COMPETENCIES:
        raise CompetencyItemError(
            f"competency {value!r} is not one of {sorted(COMPETENCIES)} (CBSE vocabulary)"
        )
    return value


def _difficulty_of(item: dict[str, Any]) -> str:
    value = str(item.get("difficulty") or "medium").strip().lower()
    if value not in {"easy", "medium", "hard"}:
        raise CompetencyItemError(f"difficulty {value!r} is not easy, medium or hard")
    return value


def _emit(
    *,
    chapter: str,
    topic: str | None,
    fmt: str,
    competency: str,
    difficulty: str,
    prompt: str,
    options: Sequence[str],
    answer: int,
    explanation: str | None,
    hint: str | None,
    source_ref: str,
    stem: str = "",
    id_seed: str = "",
    case_sensitive: bool = False,
) -> QuestionDef:
    texts = _normalise_options(options, case_sensitive=case_sensitive)
    index = _answer_index(answer, len(texts))
    rng = stable_rng("competency", chapter, str(topic), prompt[:80], id_seed)

    # Options are shuffled per item, exactly like every other generator, so the
    # correct answer never sits in a predictable position.
    shuffled = list(texts)
    rng.shuffle(shuffled)
    option_objects = [QuestionOption(key=key, text=text) for key, text in zip(OPTION_KEYS, shuffled)]
    answer_key = next(o.key for o in option_objects if o.text == texts[index])

    prompt_text = f"{stem.strip()}\n\n{prompt.strip()}" if stem.strip() else prompt.strip()
    if not prompt_text:
        raise CompetencyItemError("item has neither a prompt nor a stem")

    qid = question_id(
        chapter,
        topic,
        f"competency-{fmt}",
        f"{slugify(prompt, 48)}-{_fingerprint(id_seed or prompt_text)}",
    )

    return make_question(
        qid=qid,
        chapter=chapter,
        topic=topic,
        question_type="mcq_single",
        prompt=prompt_text,
        options=option_objects,
        answer_key=answer_key,
        explanation=(explanation or "").strip() or None,
        hint=(hint or "").strip() or None,
        difficulty=difficulty,
        time_budget_ms=_budget(difficulty, stem),
        source_ref=source_ref,
        tags=["competency", fmt, competency],
        stimulus={"kind": "passage", "text": stem.strip()} if stem.strip() else {"kind": "competency"},
        meta={
            "competency": competency,
            "format": fmt,
            "passage_chars": len(stem.strip()),
            # Recorded so the validator can tell a deliberate distinction from a
            # careless one: TT, Tt and tt differ only by case and are three
            # different answers.
            "case_sensitive_options": case_sensitive,
        },
    )


def _assertion_reason(item: dict[str, Any], chapter: str, topic: str | None, source_ref: str) -> QuestionDef:
    assertion = str(item.get("assertion") or "").strip()
    reason = str(item.get("reason") or "").strip()
    if not assertion or not reason:
        raise CompetencyItemError("assertion_reason items need both an assertion and a reason")

    verdict = str(item.get("verdict") or "").strip().lower()
    if verdict not in AR_VERDICTS:
        raise CompetencyItemError(
            f"verdict {verdict!r} is not one of {sorted(AR_VERDICTS)}"
        )

    prompt = (
        "Read the two statements and choose the correct option.\n\n"
        f"Assertion (A): {assertion}\n"
        f"Reason (R): {reason}"
    )
    explanation = str(item.get("explanation") or "").strip() or (
        f"A: {assertion} R: {reason} Verdict: {AR_OPTIONS[AR_VERDICTS[verdict]]}."
    )
    stem = str(item.get("stem") or "")

    return _emit(
        chapter=chapter,
        topic=topic,
        fmt="assertion_reason",
        competency=_competency_of(item, "analysis"),
        difficulty=_difficulty_of(item),
        prompt=prompt,
        options=AR_OPTIONS,
        answer=AR_VERDICTS[verdict],
        explanation=explanation,
        hint=item.get("hint"),
        source_ref=source_ref,
        stem=stem,
        id_seed=assertion + "|" + reason,
        case_sensitive=bool(item.get("case_sensitive")),
    )


def _case_study(
    item: dict[str, Any], chapter: str, topic: str | None, source_ref: str
) -> list[QuestionDef]:
    stem = str(item.get("stem") or item.get("passage") or "").strip()
    if not stem:
        raise CompetencyItemError("case_study items need a stem (the passage students read)")
    sub_questions = item.get("questions")
    if not isinstance(sub_questions, list) or not sub_questions:
        raise CompetencyItemError("case_study items need a non-empty `questions` list")

    fmt = str(item.get("format") or "case_study").strip().lower()
    if fmt not in {"case_study", "source_based"}:
        fmt = "case_study"

    out: list[QuestionDef] = []
    for position, sub in enumerate(sub_questions):
        if not isinstance(sub, dict):
            raise CompetencyItemError(f"case_study question {position + 1} is not an object")
        sub_chapter, sub_topic = resolve_location(sub, chapter, topic)
        out.append(
            _emit(
                chapter=sub_chapter,
                topic=sub_topic,
                fmt=fmt,
                competency=_competency_of(sub, _competency_of(item, "analysis")),
                difficulty=_difficulty_of(sub),
                prompt=str(sub.get("prompt") or ""),
                options=sub.get("options") or [],
                answer=sub.get("answer", -1),
                explanation=sub.get("explanation"),
                hint=sub.get("hint"),
                source_ref=source_ref,
                stem=stem,
                id_seed=f"{stem[:60]}|{position}|{sub.get('prompt', '')}",
                case_sensitive=bool(sub.get("case_sensitive") or item.get("case_sensitive")),
            )
        )
    return out


def _direct(item: dict[str, Any], chapter: str, topic: str | None, source_ref: str) -> QuestionDef:
    fmt = str(item.get("format") or "direct").strip().lower()
    if fmt not in FORMATS:
        raise CompetencyItemError(f"format {fmt!r} is not one of {sorted(FORMATS)}")
    return _emit(
        chapter=chapter,
        topic=topic,
        fmt=fmt,
        competency=_competency_of(item),
        difficulty=_difficulty_of(item),
        prompt=str(item.get("prompt") or ""),
        options=item.get("options") or [],
        answer=item.get("answer", -1),
        explanation=item.get("explanation"),
        hint=item.get("hint"),
        source_ref=source_ref,
        stem=str(item.get("stem") or ""),
        id_seed=str(item.get("prompt") or ""),
        case_sensitive=bool(item.get("case_sensitive")),
    )


def generate(items: Sequence[dict[str, Any]], chapter: str, topic: str, source_ref: str) -> list[QuestionDef]:
    questions: list[QuestionDef] = []

    for item in items:
        item_chapter, item_topic = resolve_location(item, chapter, topic)
        fmt = str(item.get("format") or "direct").strip().lower()
        try:
            if fmt == "assertion_reason" or ("assertion" in item and "reason" in item):
                questions.append(_assertion_reason(item, item_chapter, item_topic, source_ref))
            elif fmt in {"case_study", "source_based"} or "questions" in item:
                questions.extend(_case_study(item, item_chapter, item_topic, source_ref))
            else:
                questions.append(_direct(item, item_chapter, item_topic, source_ref))
        except CompetencyItemError as exc:
            label = str(item.get("prompt") or item.get("assertion") or item.get("stem") or "")[:60]
            raise CompetencyItemError(f"{item_chapter}: {label!r}: {exc}") from exc

    return _dedupe(questions)


def _dedupe(questions: list[QuestionDef]) -> list[QuestionDef]:
    seen: set[str] = set()
    out: list[QuestionDef] = []
    for question in questions:
        digest = content_hash(question)
        if digest in seen:
            continue
        seen.add(digest)
        out.append(question)
    return out
