"""Content validation — the gate that keeps the question bank trustworthy.

Used in three places:
  1. seed pipeline (template + manual content),
  2. AI generation pipeline (`app/ai/validation.py` reuses these rules),
  3. content-studio edits from the local admin UI.

Nothing enters the bank as `approved` without passing this.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass, field

from app.content.schema import OPTION_KEYS, QuestionDef

MAX_PROMPT_CHARS = 400
#: A case-study item carries its passage inside the prompt, because the student
#: must read it on the same screen as the question. Those are held to a separate,
#: wider cap so the length warning stays meaningful for ordinary items.
MAX_PASSAGE_PROMPT_CHARS = 1400
MAX_OPTION_CHARS = 200
MAX_EXPLANATION_CHARS = 400
MAX_HINT_CHARS = 200
REQUIRED_OPTION_COUNT = 4

# Characters we never want in a student-facing string.
_CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_HTML_RE = re.compile(r"<\s*(script|iframe|style|object|embed|svg)\b", re.IGNORECASE)


@dataclass
class ValidationIssue:
    code: str
    message: str
    severity: str = "error"  # error | warning


@dataclass
class ValidationResult:
    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not any(i.severity == "error" for i in self.issues)

    @property
    def errors(self) -> list[str]:
        return [f"[{i.code}] {i.message}" for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> list[str]:
        return [f"[{i.code}] {i.message}" for i in self.issues if i.severity == "warning"]

    def add(self, code: str, message: str, severity: str = "error") -> None:
        self.issues.append(ValidationIssue(code=code, message=message, severity=severity))


class CurriculumIndex:
    """Fast lookup of what exists, so validators can enforce referential integrity."""

    def __init__(self, chapter_ids: set[str], topic_ids: set[str], chapter_topics: dict[str, set[str]]):
        self.chapter_ids = chapter_ids
        self.topic_ids = topic_ids
        self.chapter_topics = chapter_topics

    def has_chapter(self, chapter_id: str) -> bool:
        return chapter_id in self.chapter_ids

    def topic_in_chapter(self, topic_id: str | None, chapter_id: str) -> bool:
        if topic_id is None:
            return True
        return topic_id in self.chapter_topics.get(chapter_id, set())


_COSMETIC_RE = re.compile(r"[\'\"\u2018\u2019\u201c\u201d()\[\]{}!]")
_EDGE_RE = re.compile(r"^[.,;:\s]+|[.,;:\s]+$")


def normalise_text(text: str) -> str:
    """Normalise for duplicate detection.

    Deliberately conservative: only case, whitespace, quotes/brackets and edge
    punctuation are removed. Characters that carry meaning in science answers -
    `+ - = / ^ *` and subscript digits - are PRESERVED, otherwise "CnH2n+2" and
    "CnH2n-2" (or "-1" and "1") would falsely compare equal.
    """
    value = unicodedata.normalize("NFKC", text or "").lower()
    value = re.sub(r"\s+", " ", value)
    value = _COSMETIC_RE.sub("", value)
    value = _EDGE_RE.sub("", value)
    return value.strip()


def content_hash(question: QuestionDef) -> str:
    """Stable identity for duplicate detection and change detection on reseed.

    Order-independent (option texts are sorted) so re-shuffling options does not
    look like a content change, but it DOES include the correct answer text and
    the stimulus, so fixing a wrong answer key is detected on the next seed.
    """
    option_texts = sorted(normalise_text(o.text) for o in question.options)
    correct_text = normalise_text(next((o.text for o in question.options if o.key == question.answer_key), ""))
    stimulus_blob = json.dumps(question.stimulus, sort_keys=True, ensure_ascii=False) if question.stimulus else ""

    payload = "|".join(
        [
            question.question_type,
            normalise_text(question.prompt),
            *option_texts,
            f"answer={correct_text}",
            f"stimulus={stimulus_blob}",
        ]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:32]


def _check_text_field(result: ValidationResult, label: str, value: str | None, limit: int, field_code: str) -> None:
    if value is None:
        return
    if _CONTROL_RE.search(value):
        result.add(field_code, f"{label} contains control characters")
    if _HTML_RE.search(value):
        result.add(field_code, f"{label} contains markup that must not be rendered as HTML")
    if len(value) > limit:
        result.add(field_code, f"{label} exceeds {limit} characters (got {len(value)})", severity="warning")


def validate_question(question: QuestionDef, index: CurriculumIndex | None = None) -> ValidationResult:
    result = ValidationResult()

    # Identity
    if not question.id or not re.match(r"^[a-z0-9._\-]+$", question.id):
        result.add("id_format", f"Invalid question id {question.id!r}: use lowercase, digits, dot, dash, underscore")

    # Referential integrity against the curriculum
    if index is not None:
        if not index.has_chapter(question.chapter):
            result.add("unknown_chapter", f"Chapter {question.chapter!r} is not declared in curriculum.json")
        elif not index.topic_in_chapter(question.topic, question.chapter):
            result.add("topic_chapter_mismatch", f"Topic {question.topic!r} does not belong to chapter {question.chapter!r}")

    # Text safety / length
    if not question.prompt.strip():
        result.add("empty_prompt", "Prompt cannot be empty")
    prompt_cap = MAX_PASSAGE_PROMPT_CHARS if question.stimulus.get("kind") == "passage" else MAX_PROMPT_CHARS
    _check_text_field(result, "Prompt", question.prompt, prompt_cap, "prompt")
    _check_text_field(result, "Explanation", question.explanation, MAX_EXPLANATION_CHARS, "explanation")
    _check_text_field(result, "Hint", question.hint, MAX_HINT_CHARS, "hint")

    if not question.source_ref.strip():
        result.add("missing_source", "Every item needs a source_ref for curriculum traceability")

    # Timing / difficulty sanity
    if not (1000 <= question.time_budget_ms <= 120000):
        result.add("time_budget", f"time_budget_ms out of range: {question.time_budget_ms}")

    if question.question_type == "balancing":
        # Balancing items carry their data in `stimulus` and are graded by BalancingEngine.
        payload = question.stimulus
        if not payload.get("reactants") or not payload.get("products"):
            result.add("balancing_shape", "Balancing item needs stimulus.reactants and stimulus.products")
        return result

    if question.question_type == "mcq_single":
        _validate_mcq(question, result)

    return result


def _validate_mcq(question: QuestionDef, result: ValidationResult) -> None:
    options = question.options

    if len(options) != REQUIRED_OPTION_COUNT:
        result.add("option_count", f"MCQ needs exactly {REQUIRED_OPTION_COUNT} options, got {len(options)}")

    keys = [o.key for o in options]
    if len(set(keys)) != len(keys):
        result.add("duplicate_keys", f"Duplicate option keys: {keys}")
    for key in keys:
        if key not in OPTION_KEYS:
            result.add("unknown_key", f"Option key {key!r} must be one of {OPTION_KEYS}")

    if question.answer_key not in keys:
        result.add("answer_not_in_options", f"answer_key {question.answer_key!r} is not among the option keys {keys}")

    correct = [o for o in options if o.key == question.answer_key]
    if len(correct) != 1:
        result.add("answer_ambiguous", "Exactly one option must match answer_key")

    # Option hygiene
    seen: dict[str, str] = {}
    for option in options:
        if len(option.text) > MAX_OPTION_CHARS:
            result.add("option_length", f"Option {option.key!r} exceeds {MAX_OPTION_CHARS} characters", severity="warning")
        norm = normalise_text(option.text)
        if not norm:
            result.add("empty_option", f"Option {option.key!r} is blank")
        if norm in seen:
            # normalise_text folds case, which is right for spotting "Water" and
            # "water" offered as two answers, and wrong for TT, Tt and tt - three
            # genotypes that differ only by case, and CO versus Co in chemistry.
            # A true duplicate is an error; a case-only difference is a warning,
            # so a genuine slip still surfaces without blocking the seed.
            previous_key = seen[norm]
            previous_text = next(o.text for o in options if o.key == previous_key)
            if previous_text.strip() == option.text.strip():
                result.add("duplicate_option", f"Options {previous_key!r} and {option.key!r} are identical: {option.text!r}")
            elif question.meta.get("case_sensitive_options"):
                # The author has said case carries meaning in this item, so the
                # difference is the point rather than a slip. Genotypes and
                # chemical symbols are the two places this comes up.
                pass
            else:
                result.add(
                    "case_only_difference",
                    f"Options {previous_key!r} ({previous_text!r}) and {option.key!r} ({option.text!r}) differ only by case",
                    severity="warning",
                )
        seen[norm] = option.key

    # Anti-guessing guardrails
    _validate_distractor_plausibility(question, result)


# Throwaway distractors that signal unreviewed content. Kept narrow on purpose:
# a broad word list produces false positives on real science text ("bar magnet").
_PLACEHOLDER_RE = re.compile(
    r"""\b(
        banana | lorem | ipsum | xyz | asdf | placeholder | todo | fixme |
        foo\s+bar | dummy\s+option | test\s+option |
        none\s+of\s+these | all\s+of\s+the\s+above | none\s+of\s+the\s+above
    )\b""",
    re.IGNORECASE | re.VERBOSE,
)


def _validate_distractor_plausibility(question: QuestionDef, result: ValidationResult) -> None:
    """Reject obviously silly distractors. The brief is explicit about this."""
    for option in question.options:
        if _PLACEHOLDER_RE.search(option.text):
            result.add("implausible_distractor", f"Option {option.text!r} looks like a throwaway distractor")

    texts = [normalise_text(o.text) for o in question.options]
    # If three options are numeric and one is a long sentence, the odd one out is a giveaway.
    numeric = [t for t in texts if re.fullmatch(r"[-+0-9.,/ ]+", t)]
    if 0 < len(numeric) < len(texts) and len(numeric) >= len(texts) - 1:
        lengths = [len(t) for t in texts if t not in numeric]
        if lengths and max(lengths) > 40:
            result.add(
                "length_outlier",
                "One option is far longer than the numeric alternatives; it may give the answer away",
                severity="warning",
            )

    if not question.explanation and question.difficulty == "hard":
        result.add("missing_explanation_hard", "Hard items should carry an explanation", severity="warning")
