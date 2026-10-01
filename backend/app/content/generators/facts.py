"""Structured (subject, attribute, value) facts -> rapid recall MCQs.

Distractor strategy, in order of preference:
  1. other values of the SAME attribute  (most plausible, e.g. colour in acid)
  2. other values from the SAME topic
  3. other values from the SAME chapter
The generator degrades through these rather than ever falling back to random text.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Sequence

from app.content.generators.base import (
    resolve_location,
    build_options,
    make_question,
    pick_distractors,
    question_id,
    slugify,
    stable_rng,
)
from app.content.schema import QuestionDef
from app.content.validators import content_hash

TIME_BUDGET_BY_DIFFICULTY = {"easy": 9000, "medium": 12000, "hard": 15000}


def generate(items: Sequence[dict[str, Any]], chapter: str, topic: str, source_ref: str) -> list[QuestionDef]:
    questions: list[QuestionDef] = []

    by_attribute: dict[str, list[str]] = defaultdict(list)
    by_topic: dict[str, list[str]] = defaultdict(list)
    by_chapter: dict[str, list[str]] = defaultdict(list)

    for item in items:
        value = str(item["value"])
        by_attribute[str(item["attribute"])].append(value)
        by_topic[str(item.get("topic") or topic)].append(value)
        by_chapter[str(item.get("chapter") or chapter)].append(value)

    for item in items:
        subject = str(item["subject"])
        attribute = str(item["attribute"])
        value = str(item["value"])
        item_chapter, item_topic = resolve_location(item, chapter, topic)
        difficulty = str(item.get("difficulty", "medium"))
        slug = slugify(f"{subject}-{attribute}")

        case_sensitive = bool(item.get("case_sensitive"))
        # Recorded so the validator can tell a deliberate case distinction from a
        # careless one. Genotypes and chemical symbols are the two places this
        # comes up: TT, Tt and tt are three different answers, and without this
        # every one of those option sets reads as a duplicate.
        meta = {"case_sensitive_options": True} if case_sensitive else {}
        pool = _pool_for(
            value, by_attribute[attribute], by_topic[item_topic], by_chapter[item_chapter],
            case_sensitive=case_sensitive,
        )
        if pool is None:
            continue

        # 1. Forward recall: "What is the <attribute> of <subject>?"
        rng = stable_rng("fact", subject, attribute, item_chapter)
        distractors = pick_distractors(value, pool, 3, rng, case_sensitive=case_sensitive)
        options, answer_key = build_options(value, distractors, rng)
        questions.append(
            make_question(
                qid=question_id(item_chapter, item_topic, "fact_attribute", slug),
                chapter=item_chapter,
                topic=item_topic,
                question_type="mcq_single",
                prompt=_prompt_for(subject, attribute),
                options=options,
                answer_key=answer_key,
                explanation=f"{subject} — {attribute}: {value}.",
                difficulty=difficulty,
                time_budget_ms=TIME_BUDGET_BY_DIFFICULTY.get(difficulty, 12000),
                source_ref=source_ref,
                tags=["fact", "recall"],
                meta=meta,
            )
        )

        # 2. Reverse recall: "Which subject has this value?" — only when unambiguous.
        same_value = [i for i in items if str(i["value"]) == value and str(i.get("attribute")) == attribute]
        if len(same_value) == 1:
            candidates = [str(i["subject"]) for i in items if str(i.get("attribute")) == attribute]
            if len({c if case_sensitive else c.lower() for c in candidates}) >= 4:
                rng = stable_rng("fact-reverse", subject, attribute, item_chapter)
                distractors = pick_distractors(subject, candidates, 3, rng, case_sensitive=case_sensitive)
                options, answer_key = build_options(subject, distractors, rng)
                questions.append(
                    make_question(
                        qid=question_id(item_chapter, item_topic, "subject_of_fact", slug),
                        chapter=item_chapter,
                        topic=item_topic,
                        question_type="mcq_single",
                        prompt=_reverse_prompt_for(value, attribute),
                        options=options,
                        answer_key=answer_key,
                        explanation=f"{subject} — {attribute}: {value}.",
                        difficulty="hard" if difficulty == "hard" else "medium",
                        time_budget_ms=TIME_BUDGET_BY_DIFFICULTY.get(difficulty, 12000) + 2000,
                        source_ref=source_ref,
                        tags=["fact", "recall", "reverse"],
                        meta=meta,
                    )
                )

        # 3. Negative recall: "Which statement is NOT correct?"
        if len(pool) >= 3:
            rng = stable_rng("fact-not", subject, attribute, item_chapter)
            wrong_value = rng.choice([p for p in pool if p != value])
            false_statement = f"{subject} — {attribute}: {wrong_value}"
            true_statements = [f"{subject} — {attribute}: {value}"]
            others = [i for i in items if i is not item and str(i.get("attribute")) == attribute]
            rng.shuffle(others)
            for other in others[:3]:
                true_statements.append(f"{other['subject']} — {attribute}: {other['value']}")
            if len(true_statements) >= 4:
                options, answer_key = build_options(false_statement, true_statements[1:4], rng)
                questions.append(
                    make_question(
                        qid=question_id(item_chapter, item_topic, "fact_not_correct", slug),
                        chapter=item_chapter,
                        topic=item_topic,
                        question_type="mcq_single",
                        prompt="Which of the following statements is NOT correct?",
                        options=options,
                        answer_key=answer_key,
                        explanation=f"The correct value is: {subject} — {attribute}: {value}.",
                        difficulty="hard",
                        time_budget_ms=16000,
                        source_ref=source_ref,
                        tags=["fact", "negative-recall"],
                        meta=meta,
                    )
                )

    return _dedupe(questions)


#: Attributes that read best as a direct noun phrase.
_LABELLED = {
    "value": "value", "unit": "SI unit", "formula": "chemical formula",
    "function": "function", "composition": "composition", "cause": "cause",
    "correction": "correction",
}

#: Attributes whose phrasing does not follow from a general rule, so they are
#: stated outright. Without these the generic templates produce questions that
#: are grammatical but ask the wrong way round.
_EXPLICIT_PROMPTS = {
    "term for": "What is the term for {s}?",
    "example of": "Which of the following is an example of {s}?",
    "meaning of": "What is the meaning of {s}?",
    "known for": "What is {s} known for?",
    "known as": "What is {s} known as?",
    "described as": "How is {s} described?",
    "defined as": "How is {s} defined?",
    # "reason for" heads with a noun, so the generic voice test reads it as an
    # active verb and drops the article: "X reason for which of the following?"
    "reason for": "What is the reason for {s}?",
    "expected of": "What is expected of {s}?",
    "energy change in": "What is the energy change in {s}?",
    "declined because": "Why did {s} decline?",
    "grew because": "Why did {s} grow?",
}

#: An attribute ending in one of these is a passive construction, so the subject
#: is the thing being acted on: "Insulin / secreted by" -> "Insulin is secreted by
#: which of the following?"
_PASSIVE_ENDINGS = (
    "by", "in", "at", "for", "with", "through", "as", "from", "on", "between",
    "to", "over", "under", "upon", "into",
)


#: Leading words that are capitalised because they start a sentence in the fact
#: file, but must not stay capitalised when the value is placed inside one.
#: Only these exact words are touched: "The French Revolution" becomes "the
#: French Revolution", and proper nouns are never altered.
_INLINE_LOWERCASE = {"the", "a", "an", "to", "it", "this", "these", "those"}


def inline(text: str) -> str:
    """Make a fragment safe to drop into the middle of a sentence.

    Facts are written as standalone phrases, so their values begin with a
    capital: "The Act recognising Sinhala as the only official language",
    "An armed conflict and a long civil war", "To carry nationalist feeling to a
    largely illiterate audience". Interpolating those unchanged produced real
    questions in the live bank that read:

        What is the year of The Act recognising Sinhala...?
        Which of the following resulted in An armed conflict...?
        Which of the following is used for To carry nationalist feeling...?

    566 approved questions had this defect. The fix belongs here, at the point
    of interpolation, rather than in a registry of offending values: the source
    facts stay readable and every future fact gets the same treatment.

    Only the first word is considered, and only if it is an article or an
    infinitive marker. Everything after it is untouched, so no proper noun can
    be broken by this.
    """
    text = text.strip()
    if not text:
        return text
    word, _, rest = text.partition(" ")
    if word.lower() in _INLINE_LOWERCASE and word.lower() != word:
        # Keep the article, drop its capital: "The Act..." -> "the Act...".
        return f"{word.lower()} {rest}" if rest else word.lower()
    return text


def _prompt_for(subject: str, attribute: str) -> str:
    """Turn a (subject, attribute) pair into a question stem.

    The attribute names the relationship, so the stem has to match its voice.
    Four shapes cover the bank:

      noun phrase  "year of"     -> "What is the year of the Act of Union?"
      passive      "secreted by" -> "Insulin is secreted by which of the following?"
      active       "occurs in"   -> "Photosynthesis occurs in which of the following?"
      bare verb    "supports"    -> "Tourism in India supports which of the following?"
    """
    attribute = attribute.strip()
    subject = subject.strip()
    lowered = attribute.lower()
    last = lowered.rsplit(" ", 1)[-1]
    prepositional = last in _PASSIVE_ENDINGS or last in ("because", "of")

    if attribute in _LABELLED:
        return f"What is the {_LABELLED[attribute]} of {inline(subject)}?"
    if lowered in _EXPLICIT_PROMPTS:
        return _EXPLICIT_PROMPTS[lowered].format(s=inline(subject))
    if attribute.endswith(" of ") or attribute.startswith("colour in"):
        return f"{subject}: {attribute.strip()}?"
    if lowered in _ACTIVE_PHRASES:
        return f"{subject} {attribute} which of the following?"
    if prepositional and _reads_passive(lowered):
        return f"{subject} is {attribute} which of the following?"
    # "year of", "function of", "ratio of" already carry the preposition, so
    # appending another "of" produced "What is the year of of the French
    # Revolution?" - which is how 306 questions in the bank used to read.
    if (last == "of" or " of " in lowered) and not _reads_passive(lowered):
        return f"What is the {attribute} {inline(subject)}?"
    # A noun phrase with no trailing preposition: "chemical formula", "main use",
    # "colour in basic solution". These take "of" rather than acting as verbs.
    if not _ends_in_verb(lowered):
        return f"What is the {attribute} of {inline(subject)}?"
    # Everything left is an active verb, with or without its preposition:
    # "caused", "supports", "connects", "occurs in", "resulted in".
    return f"{subject} {attribute} which of the following?"


#: Reverse-recall templates for attributes whose phrasing does not follow from a
#: general rule. The forward form asks "given the subject, what is the value?";
#: the reverse asks "given the value, which subject?" - which needs its own
#: wording, because plugging the attribute into a single template produces
#: "Which of the following has written as = TT?".
_EXPLICIT_REVERSE = {
    "example of": "{v} is an example of which of the following?",
    "term for": "{v} is the term for which of the following?",
    "meaning of": "{v} is the meaning of which of the following?",
    "known as": "Which of the following is known as {v}?",
    "known for": "Which of the following is known for {v}?",
    "described as": "Which of the following is described as {v}?",
    "defined as": "Which of the following is defined as {v}?",
    "expected of": "{v} is expected of which of the following?",
    "energy change in": "Which of the following shows this energy change: {v}?",
    "reason for": "{v} is the reason for which of the following?",
}

#: Verb phrases where the subject acts, so the reverse form must not add "is".
#: "Which of the following occurs in the small intestine?" is right;
#: "Which of the following is occurs in..." is not.
_ACTIVE_PHRASES = {
    "occurs in", "occurs as", "operates through", "benefits from", "suffers from",
    "depends on", "results in", "resulted in", "consists of", "includes",
    "connects to", "links to", "shifted in", "reflects", "arises from", "comes from",
    "leads to", "led to", "grew because", "declined because", "spread through",
    "spread to", "varies with",
}

#: Head verbs that are participles even though they do not end in -ed/-en.
_IRREGULAR_PARTICIPLES = {
    "written", "sown", "built", "led", "found", "made", "sent", "kept", "held",
    "given", "taken", "seen", "known", "shown", "drawn", "grown", "thrown",
    "spoken", "broken", "chosen", "forgotten", "brought", "bought", "taught",
    "caught", "laid", "paid", "said", "sold", "told", "thought", "understood",
    "won", "worn", "woven", "driven", "risen", "fallen", "hidden", "ridden",
}


#: -ed verbs that are intransitive, so the clause stays active even though the
#: word looks like a participle. "Which of the following originated in the
#: Garhwal Himalayas?" is right; "...is originated in..." is not.
_INTRANSITIVE_HEADS = {
    "originated", "occurred", "appeared", "emerged", "started", "began",
    "developed", "grew", "shifted", "spread", "declined", "resulted", "consisted",
    "evolved", "turned", "moved", "rose", "fell", "changed", "increased",
    "decreased", "expanded", "contracted", "migrated", "flowed", "travelled",
    "traveled", "returned", "continued", "ended", "followed", "preceded",
    "succeeded", "failed", "collapsed", "revived", "lasted", "reached",
}


def _is_participle(word: str) -> bool:
    """True when a word is a participle, i.e. it can head a passive clause."""
    word = word.strip().lower()
    return word.endswith(("ed", "en")) or word in _IRREGULAR_PARTICIPLES


def _reads_passive(attribute: str) -> bool:
    """True when `subject is <attribute> <value>` is the grammatical frame.

    A participle anywhere in the attribute signals passive - "best suited for"
    heads with an adverb, so testing only the first word misses it - except when
    the head verb is intransitive, which keeps the clause active.
    """
    words = attribute.strip().lower().split()
    if not words or words[0] in _INTRANSITIVE_HEADS:
        return False
    return any(_is_participle(w) for w in words)


def _ends_in_verb(attribute: str) -> bool:
    """True when the last word is a verb form, so the attribute is a verb phrase.

    There is no lexicon here, only morphology: a participle or a third-person
    -s form is a verb. Anything else - "formula", "method", "solution" - is a
    noun, which makes the whole attribute a noun phrase that takes "of".
    """
    last = attribute.strip().lower().rsplit(" ", 1)[-1]
    return _is_participle(last) or last.endswith("s")


def _reverse_prompt_for(value: str, attribute: str) -> str:
    """Given the value, ask which subject it belongs to.

    The four grammatical shapes that appear in the content bank are:

      passive    "secreted by"  -> "Which of the following is secreted by insulin?"
      active     "occurs in"    -> "Which of the following occurs in the leaf?"
      noun + of  "year of"      -> "The year of which of the following is 1919?"
      bare verb  "supports"     -> "Which of the following supports tourism?"

    Anything unrecognised falls back to the explicit `attribute = value` form,
    which is stiff but never wrong.
    """
    attribute = attribute.strip()
    lowered = attribute.lower()

    if lowered in _EXPLICIT_REVERSE:
        return _EXPLICIT_REVERSE[lowered].format(v=inline(value))
    if attribute in _LABELLED:
        return f"The {_LABELLED[attribute]} of which of the following is {inline(value)}?"
    if lowered in _ACTIVE_PHRASES:
        return f"Which of the following {attribute} {inline(value)}?"

    last = lowered.rsplit(" ", 1)[-1]
    prepositional = last in _PASSIVE_ENDINGS or last in ("because", "of")

    # A single-word attribute with no preposition is a finite verb taking a
    # direct object: "caused chaos", not "was caused chaos". The -ed ending that
    # marks a passive participle marks simple past tense here instead.
    if " " not in lowered:
        return f"Which of the following {attribute} {inline(value)}?"

    # A noun phrase carrying its own preposition, with or without a trailing one:
    # "year of" -> "The year of which of the following is 1707?" and
    # "share of population in" -> "The share of population in which ... is 59?"
    if (last == "of" or " of " in lowered) and not _reads_passive(lowered):
        return f"The {attribute} which of the following is {inline(value)}?"
    if prepositional and _reads_passive(lowered):
        return f"Which of the following is {attribute} {inline(value)}?"
    if prepositional:
        return f"Which of the following {attribute} {inline(value)}?"
    if not _ends_in_verb(lowered):
        return f"The {attribute} of which of the following is {inline(value)}?"
    return f"Which of the following has {attribute} = {inline(value)}?"


def _pool_for(correct: str, *pools: Sequence[str], case_sensitive: bool = False) -> list[str] | None:
    """Three or more siblings that are genuinely different from the answer.

    Comparison folds case unless the cluster says otherwise, because TT and tt are
    different genotypes while "Water" and "water" are not different values.
    """

    def key(text: str) -> str:
        return text.strip() if case_sensitive else text.strip().lower()

    for pool in pools:
        correct_key = key(correct)
        candidates = [p for p in pool if key(p) != correct_key]
        if len({key(c) for c in candidates}) >= 3:
            # Preserve first-seen order but collapse the repeats the same way.
            seen: set[str] = set()
            unique: list[str] = []
            for candidate in candidates:
                candidate_key = key(candidate)
                if candidate_key in seen:
                    continue
                seen.add(candidate_key)
                unique.append(candidate)
            return unique
    return None


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
