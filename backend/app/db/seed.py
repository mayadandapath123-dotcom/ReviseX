"""Content + baseline data seeding.

Idempotent: safe to run on every start. Content is upserted by primary key; a
`revision` bump happens only when the content hash actually changed. User
progress tables are never touched.
"""

from __future__ import annotations

import json
import logging
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Sequence

from app.config.settings import get_settings
from app.content.generators import generate_from_fact_file
from app.content.schema import CurriculumFile, FactFile, ModesFile, QuestionDef
from app.content.validators import CurriculumIndex, ValidationResult, content_hash, validate_question
from app.db.connection import transaction

logger = logging.getLogger("leap.seed")

DEFAULT_SOURCE_REF = "Class 10 curriculum-aligned original content."

BADGES: list[dict[str, Any]] = [
    {"id": "first_test", "name": "First Steps", "description": "Complete your first test.", "icon": "flag",
     "criterion": {"type": "sessions_completed", "value": 1}},
    {"id": "streak_5", "name": "On Fire", "description": "Reach a 5-answer correct streak.", "icon": "flame",
     "criterion": {"type": "answer_streak", "value": 5}},
    {"id": "streak_10", "name": "Unstoppable", "description": "Reach a 10-answer correct streak.", "icon": "flame",
     "criterion": {"type": "answer_streak", "value": 10}},
    {"id": "streak_25", "name": "Perfect Run", "description": "Reach a 25-answer correct streak.", "icon": "crown",
     "criterion": {"type": "answer_streak", "value": 25}},
    {"id": "questions_100", "name": "Century", "description": "Answer 100 questions.", "icon": "target",
     "criterion": {"type": "questions_answered", "value": 100}},
    {"id": "questions_500", "name": "Grinder", "description": "Answer 500 questions.", "icon": "target",
     "criterion": {"type": "questions_answered", "value": 500}},
    {"id": "accuracy_90", "name": "Sharpshooter", "description": "Finish a 20+ question test with 90% accuracy.", "icon": "crosshair",
     "criterion": {"type": "session_accuracy", "value": 90, "min_questions": 20}},
    {"id": "speed_demon", "name": "Speed Demon", "description": "Average under 4 seconds per answer in a 15+ question test.", "icon": "bolt",
     "criterion": {"type": "session_avg_response_ms", "value": 4000, "min_questions": 15}},
    {"id": "balancer", "name": "Equation Balancer", "description": "Balance 10 chemical equations correctly.", "icon": "scale",
     "criterion": {"type": "question_type_correct", "question_type": "balancing", "value": 10}},
    {"id": "mistake_slayer", "name": "Mistake Slayer", "description": "Resolve 20 previously wrong questions.", "icon": "eraser",
     "criterion": {"type": "mistakes_resolved", "value": 20}},
    {"id": "level_5", "name": "Chapter Master", "description": "Reach level 5.", "icon": "star",
     "criterion": {"type": "level", "value": 5}},
    {"id": "daily_3", "name": "Consistent", "description": "Practise on 3 consecutive days.", "icon": "calendar",
     "criterion": {"type": "day_streak", "value": 3}},
]


@dataclass
class SeedReport:
    subjects: int = 0
    branches: int = 0
    chapters: int = 0
    topics: int = 0
    facts: int = 0
    questions_inserted: int = 0
    questions_updated: int = 0
    questions_unchanged: int = 0
    questions_archived: int = 0
    modes: int = 0
    badges: int = 0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    #: Ids produced by this run. Not reported; used to find orphans afterwards.
    question_ids: set[str] = field(default_factory=set)

    def as_dict(self) -> dict[str, Any]:
        return {
            "subjects": self.subjects,
            "branches": self.branches,
            "chapters": self.chapters,
            "topics": self.topics,
            "facts": self.facts,
            "questions": {
                "inserted": self.questions_inserted,
                "updated": self.questions_updated,
                "unchanged": self.questions_unchanged,
                "total": self.questions_inserted + self.questions_updated + self.questions_unchanged,
                "archived": self.questions_archived,
            },
            "modes": self.modes,
            "badges": self.badges,
            "errors": self.errors,
            "warnings": self.warnings[:40],
            "warning_count": len(self.warnings),
        }


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def seed_all(conn: sqlite3.Connection, content_dir: Path | None = None, *, reset_content: bool = False) -> SeedReport:
    settings = get_settings()
    root = content_dir or settings.content_dir
    report = SeedReport()

    if not root.exists():
        raise FileNotFoundError(f"Content directory not found: {root}")

    curriculum = CurriculumFile.model_validate(_load_json(root / "curriculum.json"))
    index = _seed_curriculum(conn, curriculum, report, reset_content=reset_content)

    for fact_path in sorted(root.rglob("*.json")):
        if fact_path.name in {"curriculum.json", "modes.json"}:
            continue
        _seed_fact_file(conn, fact_path, index, report)

    _retire_orphan_questions(conn, report)
    _seed_modes(conn, root / "modes.json", report)
    _seed_badges(conn, report)
    _refresh_counts(conn)

    if report.errors:
        raise ContentSeedError(report)
    return report


class ContentSeedError(RuntimeError):
    def __init__(self, report: SeedReport):
        super().__init__(f"Content seeding failed with {len(report.errors)} error(s): " + "; ".join(report.errors[:5]))
        self.report = report


# ─────────────────────────── curriculum ───────────────────────────


def _seed_curriculum(conn: sqlite3.Connection, curriculum: CurriculumFile, report: SeedReport, *, reset_content: bool) -> CurriculumIndex:
    if reset_content:
        with transaction(conn):
            conn.execute("DELETE FROM question_options")
            conn.execute("DELETE FROM questions")
            conn.execute("DELETE FROM facts")
            conn.execute("DELETE FROM topics")
            conn.execute("DELETE FROM chapters")
            conn.execute("DELETE FROM branches")
            conn.execute("DELETE FROM subjects")

    chapter_ids: set[str] = set()
    topic_ids: set[str] = set()
    chapter_topics: dict[str, set[str]] = {}

    with transaction(conn):
        for subject in curriculum.subjects:
            conn.execute(
                """INSERT INTO subjects (id, name, icon, display_order, is_active, meta_json)
                   VALUES (?, ?, ?, ?, ?, ?)
                   ON CONFLICT(id) DO UPDATE SET
                     name=excluded.name, icon=excluded.icon,
                     display_order=excluded.display_order, is_active=excluded.is_active,
                     meta_json=excluded.meta_json""",
                (subject.id, subject.name, subject.icon, subject.display_order, int(subject.is_active),
                 json.dumps({"note": subject.note, **subject.meta}, ensure_ascii=False)),
            )
            report.subjects += 1

            for branch in subject.branches:
                conn.execute(
                    """INSERT INTO branches (id, subject_id, name, icon, display_order, is_active, meta_json)
                       VALUES (?, ?, ?, ?, ?, ?, ?)
                       ON CONFLICT(id) DO UPDATE SET
                         subject_id=excluded.subject_id, name=excluded.name, icon=excluded.icon,
                         display_order=excluded.display_order, is_active=excluded.is_active,
                         meta_json=excluded.meta_json""",
                    (branch.id, subject.id, branch.name, branch.icon, branch.display_order, int(branch.is_active),
                     json.dumps(branch.meta, ensure_ascii=False)),
                )
                report.branches += 1

                for chapter in branch.chapters:
                    conn.execute(
                        """INSERT INTO chapters (id, branch_id, code, name, display_order, syllabus_status, exam_board, meta_json)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                           ON CONFLICT(id) DO UPDATE SET
                             branch_id=excluded.branch_id, code=excluded.code, name=excluded.name,
                             display_order=excluded.display_order, syllabus_status=excluded.syllabus_status,
                             exam_board=excluded.exam_board, meta_json=excluded.meta_json""",
                        (chapter.id, branch.id, chapter.code, chapter.name, chapter.display_order,
                         chapter.syllabus_status, chapter.exam_board, json.dumps(chapter.meta, ensure_ascii=False)),
                    )
                    report.chapters += 1
                    chapter_ids.add(chapter.id)
                    chapter_topics.setdefault(chapter.id, set())

                    for topic_def in chapter.topics:
                        conn.execute(
                            """INSERT INTO topics (id, chapter_id, name, display_order, meta_json)
                               VALUES (?, ?, ?, ?, ?)
                               ON CONFLICT(id) DO UPDATE SET
                                 chapter_id=excluded.chapter_id, name=excluded.name,
                                 display_order=excluded.display_order, meta_json=excluded.meta_json""",
                            (topic_def.id, chapter.id, topic_def.name, topic_def.display_order,
                             json.dumps(topic_def.meta, ensure_ascii=False)),
                        )
                        report.topics += 1
                        topic_ids.add(topic_def.id)
                        chapter_topics[chapter.id].add(topic_def.id)

    return CurriculumIndex(chapter_ids, topic_ids, chapter_topics)


# ─────────────────────────── facts & questions ───────────────────────────


def _seed_fact_file(conn: sqlite3.Connection, path: Path, index: CurriculumIndex, report: SeedReport) -> None:
    relative = path.name
    try:
        raw = _load_json(path)
    except json.JSONDecodeError as exc:
        report.errors.append(f"{relative}: invalid JSON ({exc})")
        return

    try:
        fact_file = FactFile.model_validate(raw)
    except Exception as exc:  # pydantic ValidationError
        report.errors.append(f"{relative}: schema error ({exc})")
        return

    try:
        questions = generate_from_fact_file(fact_file)
    except Exception as exc:
        report.errors.append(f"{relative}: generation failed ({type(exc).__name__}: {exc})")
        return

    # Persist the raw facts too, so the AI pipeline has structured knowledge to read.
    with transaction(conn):
        # Built up and flushed once. One INSERT per fact meant one network round
        # trip each, which is invisible on a local file and ruinous on a remote
        # database: 3,222 facts at ~180 ms is nine minutes on its own.
        fact_rows: list[tuple[Any, ...]] = []
        for item in fact_file.items:
            chapter_id = str(item.get("chapter") or fact_file.chapter or "")
            if chapter_id not in index.chapter_ids:
                report.warnings.append(f"{relative}: item references unknown chapter {chapter_id!r}")
                continue
            fact_id = _fact_id(chapter_id, item)
            fact_rows.append((
                fact_id,
                chapter_id,
                str(item.get("topic") or fact_file.topic or "") or None,
                str(item.get("kind") or fact_file.kind),
                str(item.get("term") or item.get("name") or item.get("subject") or item.get("symbol") or item.get("formula") or item.get("quantity") or fact_id),
                json.dumps(item, ensure_ascii=False),
                fact_file.source_ref or DEFAULT_SOURCE_REF,
                json.dumps({"source_file": relative}, ensure_ascii=False),
            ))
        if fact_rows:
            conn.executemany(
                """INSERT INTO facts (id, chapter_id, topic_id, kind, label, payload_json, source_ref, meta_json)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(id) DO UPDATE SET
                     chapter_id=excluded.chapter_id, topic_id=excluded.topic_id, kind=excluded.kind,
                     label=excluded.label, payload_json=excluded.payload_json,
                     source_ref=excluded.source_ref, meta_json=excluded.meta_json""",
                fact_rows,
            )
        report.facts += len(fact_rows)

    _persist_questions(conn, questions, index, report, source_file=relative)


def _fact_id(chapter_id: str, item: dict[str, Any]) -> str:
    from app.content.generators.base import slugify

    label = (
        item.get("term")
        or item.get("name")
        or item.get("quantity")
        or item.get("formula")
        or f"{item.get('subject', '')}-{item.get('attribute', '')}"
        or item.get("symbol")
        or "item"
    )
    kind = str(item.get("kind", "fact"))
    return f"fact.{chapter_id}.{kind}.{slugify(str(label), 48)}"


#: SQLite caps bound parameters, so an IN list is sent in chunks.
_PARAM_CHUNK = 500


def _retire_rows_sharing_content(
    conn: sqlite3.Connection,
    digests: Sequence[str],
    keep_ids: set[str],
    report: SeedReport,
) -> None:
    """Archive rows whose content a new question id is about to claim.

    `questions.dedupe_hash` carries a UNIQUE index, so a question whose id
    changed - because the slug it derives from was fixed - collides with the
    stale row it replaces: identical content, different id. Retiring the old row
    first keeps the insert legal.

    Archiving rather than deleting matters here: attempts, mistakes and srs_cards
    reference questions with ON DELETE CASCADE, so removing the row would erase a
    student's history for it. An archived row is outside the statuses=('approved',)
    filter that question selection uses, so it leaves quizzes while its history
    stays intact.

    The hash is cleared as well as the status flipped. `idx_q_dedupe` is UNIQUE
    over the whole table and does not exclude archived rows, so a retired row that
    kept its hash would still block the write that superseded it. Both SQLite and
    Postgres treat NULLs as distinct in a unique index, which frees the slot.

    Only origin='template' rows are considered, for the same reason as
    `_retire_orphan_questions`: generated content is the only kind this run can
    speak for. Rows this run is about to write are skipped, since an update
    legitimately keeps its own hash.
    """
    stale: list[str] = []
    for start in range(0, len(digests), _PARAM_CHUNK):
        chunk = list(digests[start:start + _PARAM_CHUNK])
        if not chunk:
            continue
        placeholders = ", ".join("?" * len(chunk))
        stale.extend(
            row[0]
            for row in conn.execute(
                f"""SELECT id FROM questions
                    WHERE dedupe_hash IN ({placeholders}) AND origin = 'template'""",
                chunk,
            ).fetchall()
            if row[0] not in keep_ids
        )
    if not stale:
        return
    conn.executemany(
        """UPDATE questions
           SET status = 'archived', dedupe_hash = NULL, updated_at = datetime('now')
           WHERE id = ?""",
        [(qid,) for qid in stale],
    )
    report.questions_archived += len(stale)
    report.warnings.append(
        f"archived {len(stale)} superseded row(s) whose content a new question id replaced"
    )


def _retire_orphan_questions(conn: sqlite3.Connection, report: SeedReport) -> None:
    """Archive generated questions that this run no longer produces.

    A question id embeds a slug of its source attribute, so renaming an attribute
    to fix its wording mints a new id and leaves the old row behind. Those rows
    still carry the broken prompt they were created from, and quiz selection would
    keep serving them.

    They are archived rather than deleted on purpose: attempts, mistakes and
    srs_cards reference questions with ON DELETE CASCADE, so deleting would erase
    a student's history for that item. 'archived' is already outside the
    statuses=('approved',) filter question selection uses, which retires the row
    from quizzes while leaving every history record intact.

    Only origin='template' rows are touched. Hand-authored and AI content is not
    regenerable, so its absence from this run's ids means nothing.
    """
    stale = [
        row[0]
        for row in conn.execute(
            "SELECT id FROM questions WHERE origin = 'template' AND status != 'archived'"
        ).fetchall()
        if row[0] not in report.question_ids
    ]
    if not stale:
        return
    conn.executemany(
        """UPDATE questions
           SET status = 'archived', dedupe_hash = NULL, updated_at = datetime('now')
           WHERE id = ?""",
        [(qid,) for qid in stale],
    )
    conn.commit()
    report.questions_archived = len(stale)
    report.warnings.append(f"archived {len(stale)} generated question(s) that no longer regenerate")


def _persist_questions(
    conn: sqlite3.Connection,
    questions: Iterable[QuestionDef],
    index: CurriculumIndex,
    report: SeedReport,
    *,
    source_file: str,
) -> None:
    # Validation is pure CPU, so it runs before the transaction: nothing here
    # should hold a write lock open while generating questions.
    approved: list[QuestionDef] = []
    for question in questions:
        result: ValidationResult = validate_question(question, index)
        for error in result.errors:
            report.errors.append(f"{source_file} :: {question.id}: {error}")
        for warning in result.warnings:
            report.warnings.append(f"{source_file} :: {question.id}: {warning}")
        if result.ok:
            approved.append(question)
    if not approved:
        return
    report.question_ids.update(q.id for q in approved)

    # A generator can emit the same question id twice from one file. Written one
    # row at a time that was self-correcting: the second sighting re-read the
    # database, saw the first, and took the update path. Batched, both land in
    # the same flush and the second one's options collide with the first on
    # (question_id, opt_key). Keep the last occurrence, which is what the
    # sequential version effectively did.
    deduped: dict[str, QuestionDef] = {}
    for question in approved:
        deduped[question.id] = question
    duplicates = len(approved) - len(deduped)
    if duplicates:
        report.warnings.append(
            f"{source_file}: {duplicates} duplicate question id(s) collapsed to the last definition"
        )
    approved = list(deduped.values())

    with transaction(conn):
        # Every existing hash in ONE query. The old code asked the database
        # about each question individually, so a full reseed of 5,034 questions
        # spent 5,034 round trips just discovering what was already there.
        known: dict[str, str] = {
            row["id"]: row["dedupe_hash"]
            for row in conn.execute("SELECT id, dedupe_hash FROM questions").fetchall()
        }

        columns: list[str] | None = None
        insert_rows: list[tuple[Any, ...]] = []
        update_rows: list[tuple[Any, ...]] = []
        written_digests: list[str] = []
        insert_digests: list[str] = []
        insert_ids: set[str] = set()
        stale_options: list[tuple[Any, ...]] = []
        option_rows: list[tuple[Any, ...]] = []

        for question in approved:
            digest = content_hash(question)
            row = _question_row(question, digest)
            if columns is None:
                columns = list(row.keys())
            prior = known.get(question.id)

            written_digests.append(digest)
            if prior is None:
                insert_rows.append(tuple(row.values()))
                insert_digests.append(digest)
                insert_ids.add(question.id)
                option_rows.extend(_option_rows(question))
                known[question.id] = digest
                report.questions_inserted += 1
            elif prior != digest:
                update_rows.append(
                    tuple(v for k, v in row.items() if k != "id") + (question.id,)
                )
                stale_options.append((question.id,))
                option_rows.extend(_option_rows(question))
                known[question.id] = digest
                report.questions_updated += 1
            else:
                report.questions_unchanged += 1

        assert columns is not None
        # Order matters here, because `dedupe_hash` is UNIQUE across the whole
        # table and a question's content can move to a different id. When a slug
        # is fixed, `poly-roots-4-1` stops meaning alpha=4/beta=1 and starts
        # meaning alpha=-4/beta=-1: the row keeps its id but takes new content,
        # while the content it used to hold is inserted under a new id. Writing
        # the insert first would collide with the hash the update is about to
        # release, so updates go first.
        _retire_rows_sharing_content(conn, written_digests, set(deduped), report)

        if stale_options:
            # Options must go before the re-insert, or the old ones collide.
            conn.executemany(
                "DELETE FROM question_options WHERE question_id = ?", stale_options
            )
        if update_rows:
            assignments = ", ".join(f"{column}=?" for column in columns if column != "id")
            conn.executemany(
                f"""UPDATE questions SET {assignments},
                      revision = revision + 1, updated_at = datetime('now')
                    WHERE id = ?""",
                update_rows,
            )

        # Anything still holding a hash an insert needs is now genuinely stale:
        # the updates above have already released the hashes that were merely
        # changing hands.
        _retire_rows_sharing_content(conn, insert_digests, insert_ids, report)
        if insert_rows:
            conn.executemany(
                f"""INSERT INTO questions ({', '.join(columns)}, revision)
                    VALUES ({', '.join('?' * len(columns))}, 1)""",
                insert_rows,
            )
        if option_rows:
            conn.executemany(
                """INSERT INTO question_options (question_id, opt_key, text, render_json, is_correct, display_order)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                option_rows,
            )


def _question_row(question: QuestionDef, digest: str) -> dict[str, Any]:
    return {
        "id": question.id,
        "chapter_id": question.chapter,
        "topic_id": question.topic,
        "question_type": question.question_type,
        "prompt": question.prompt,
        "stimulus_json": json.dumps(question.stimulus, ensure_ascii=False),
        "answer_key": question.answer_key,
        "explanation": question.explanation,
        "hint": question.hint,
        "difficulty": question.difficulty,
        "time_budget_ms": question.time_budget_ms,
        "source_ref": question.source_ref,
        "origin": question.origin,
        "status": question.status,
        "dedupe_hash": digest,
        "meta_json": json.dumps({"tags": question.tags, **question.meta}, ensure_ascii=False),
    }


def _option_rows(question: QuestionDef) -> list[tuple[Any, ...]]:
    """Option values for a batch insert.

    Returns rows rather than writing them so the caller can flush one file's
    worth of options in a single statement. Four options per question across
    5,034 questions is ~20,000 inserts; individually that is an hour of pure
    network latency against a remote database.
    """
    return [
        (
            question.id,
            option.key,
            option.text,
            json.dumps(option.render, ensure_ascii=False),
            int(option.key == question.answer_key),
            order,
        )
        for order, option in enumerate(question.options)
    ]


# ─────────────────────────── modes & badges ───────────────────────────


def _seed_modes(conn: sqlite3.Connection, path: Path, report: SeedReport) -> None:
    if not path.exists():
        report.warnings.append("modes.json not found; no test presets seeded")
        return

    modes = ModesFile.model_validate(_load_json(path))
    keys = [m.key for m in modes.modes]
    if len(keys) != len(set(keys)):
        report.errors.append("modes.json contains duplicate mode keys")
        return

    with transaction(conn):
        for order, mode in enumerate(modes.modes):
            conn.execute(
                """INSERT INTO test_modes
                     (key, name, description, icon, group_name, is_featured, is_quick_start,
                      duration_limit_ms, question_count, display_order, filters_json, scoring_json)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(key) DO UPDATE SET
                     name=excluded.name, description=excluded.description, icon=excluded.icon,
                     group_name=excluded.group_name, is_featured=excluded.is_featured,
                     is_quick_start=excluded.is_quick_start, duration_limit_ms=excluded.duration_limit_ms,
                     question_count=excluded.question_count, display_order=excluded.display_order,
                     filters_json=excluded.filters_json, scoring_json=excluded.scoring_json""",
                (
                    mode.key,
                    mode.name,
                    mode.description,
                    mode.icon,
                    mode.group,
                    int(mode.featured),
                    int(mode.quick_start),
                    mode.duration_limit_ms,
                    mode.question_count,
                    order,
                    json.dumps(mode.filters.model_dump(exclude_none=True), ensure_ascii=False),
                    json.dumps(mode.scoring.model_dump(), ensure_ascii=False),
                ),
            )
            report.modes += 1


def _seed_badges(conn: sqlite3.Connection, report: SeedReport) -> None:
    with transaction(conn):
        for badge in BADGES:
            conn.execute(
                """INSERT INTO badges (id, name, description, icon, criterion_json)
                   VALUES (?, ?, ?, ?, ?)
                   ON CONFLICT(id) DO UPDATE SET name=excluded.name, description=excluded.description,
                     icon=excluded.icon, criterion_json=excluded.criterion_json""",
                (badge["id"], badge["name"], badge["description"], badge.get("icon"),
                 json.dumps(badge.get("criterion", {}), ensure_ascii=False)),
            )
            report.badges += 1


def _refresh_counts(conn: sqlite3.Connection) -> None:
    total = conn.execute("SELECT COUNT(*) FROM questions WHERE status='approved'").fetchone()[0]
    logger.info("Question bank: %s approved items", total)
