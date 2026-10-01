"""ContentService — curriculum tree, chapter/topic stats and content administration.

Reads are shaped for the UI drill-down (subject -> branch -> chapter -> topic) and
carry per-profile progress so the Science page can render mastery bars in one call.
"""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from app.db.connection import query_all, query_one, transaction
from app.services import question_service as qs
from app.services.scoring_engine import confidence


class ContentService:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def tree(self, *, profile_id: str | None = None, include_inactive: bool = False,
             syllabus_status: tuple[str, ...] = ("core", "foundation", "optional")) -> list[dict[str, Any]]:
        subject_rows = query_all(
            self.conn,
            "SELECT * FROM subjects ORDER BY display_order",
        )
        branch_rows = query_all(self.conn, "SELECT * FROM branches ORDER BY display_order")
        chapter_rows = query_all(self.conn, "SELECT * FROM chapters ORDER BY display_order")
        topic_rows = query_all(self.conn, "SELECT * FROM topics ORDER BY display_order")

        counts = {
            r["chapter_id"]: int(r["bank_size"])
            for r in query_all(
                self.conn,
                """SELECT chapter_id, COUNT(*) AS bank_size
                   FROM questions WHERE status='approved' GROUP BY chapter_id""",
            )
        }

        progress_by_chapter: dict[str, dict[str, Any]] = {}
        mastery_by_topic: dict[str, dict[str, Any]] = {}
        if profile_id:
            for row in query_all(
                self.conn,
                """SELECT chapter_id, COUNT(*) AS attempts, SUM(is_correct) AS correct, AVG(is_correct) AS accuracy
                   FROM attempts WHERE profile_id = ? GROUP BY chapter_id""",
                (profile_id,),
            ):
                progress_by_chapter[row["chapter_id"]] = dict(row)
            for row in query_all(
                self.conn,
                "SELECT topic_id, mastery, attempts, correct FROM topic_mastery WHERE profile_id = ?",
                (profile_id,),
            ):
                mastery_by_topic[row["topic_id"]] = dict(row)

        subjects: list[dict[str, Any]] = []
        for subject in subject_rows:
            if not subject["is_active"] and not include_inactive:
                continue

            branches = []
            for branch in branch_rows:
                if branch["subject_id"] != subject["id"]:
                    continue
                if not branch["is_active"] and not include_inactive:
                    continue

                chapters = []
                for chapter in chapter_rows:
                    if chapter["branch_id"] != branch["id"]:
                        continue
                    if chapter["syllabus_status"] not in syllabus_status:
                        continue

                    bank_size = counts.get(chapter["id"], 0)
                    progress = progress_by_chapter.get(chapter["id"], {})
                    attempts = int(progress.get("attempts") or 0)
                    correct = int(progress.get("correct") or 0)

                    topics = []
                    for topic in topic_rows:
                        if topic["chapter_id"] != chapter["id"]:
                            continue
                        mastery_row = mastery_by_topic.get(topic["id"], {})
                        topic_attempts = int(mastery_row.get("attempts") or 0)
                        topics.append(
                            {
                                "id": topic["id"],
                                "name": topic["name"],
                                "mastery": float(mastery_row.get("mastery") or 0.0),
                                "attempts": topic_attempts,
                                "confidence": confidence(topic_attempts),
                            }
                        )

                    chapters.append(
                        {
                            "id": chapter["id"],
                            "code": chapter["code"],
                            "name": chapter["name"],
                            "syllabus_status": chapter["syllabus_status"],
                            "bank_size": bank_size,
                            "attempts": attempts,
                            "accuracy": (correct / attempts) if attempts else 0.0,
                            "mastery": float(progress.get("accuracy") or 0.0),
                            "topics": topics,
                            "meta": json.loads(chapter["meta_json"] or "{}"),
                        }
                    )

                if not chapters and not include_inactive:
                    continue

                branches.append(
                    {
                        "id": branch["id"],
                        "name": branch["name"],
                        "icon": branch["icon"],
                        "is_active": bool(branch["is_active"]),
                        "chapters": chapters,
                        "question_count": sum(c["bank_size"] for c in chapters),
                    }
                )

            subjects.append(
                {
                    "id": subject["id"],
                    "name": subject["name"],
                    "icon": subject["icon"],
                    "is_active": bool(subject["is_active"]),
                    "note": json.loads(subject["meta_json"] or "{}").get("note"),
                    "branches": branches,
                    "question_count": sum(b["question_count"] for b in branches),
                }
            )

        return subjects

    def chapter(self, chapter_id: str, *, profile_id: str | None = None) -> dict[str, Any] | None:
        row = query_one(
            self.conn,
            """SELECT c.*, b.id AS branch_id, b.name AS branch_name, s.id AS subject_id, s.name AS subject_name
               FROM chapters c JOIN branches b ON b.id = c.branch_id JOIN subjects s ON s.id = b.subject_id
               WHERE c.id = ?""",
            (chapter_id,),
        )
        if row is None:
            return None

        topics = query_all(self.conn, "SELECT * FROM topics WHERE chapter_id = ? ORDER BY display_order", (chapter_id,))
        types = qs.question_types_available(self.conn, chapter_id)

        topic_payload = []
        for topic in topics:
            mastery_row = None
            if profile_id:
                mastery_row = query_one(
                    self.conn,
                    "SELECT mastery, attempts, correct FROM topic_mastery WHERE profile_id=? AND topic_id=?",
                    (profile_id, topic["id"]),
                )
            bank = query_one(
                self.conn,
                "SELECT COUNT(*) AS n FROM questions WHERE topic_id=? AND status='approved'",
                (topic["id"],),
            )
            attempts = int(mastery_row["attempts"]) if mastery_row else 0
            topic_payload.append(
                {
                    "id": topic["id"],
                    "name": topic["name"],
                    "bank_size": int(bank["n"]) if bank else 0,
                    "mastery": float(mastery_row["mastery"]) if mastery_row else 0.0,
                    "attempts": attempts,
                    "accuracy": (int(mastery_row["correct"]) / attempts) if mastery_row and attempts else 0.0,
                    "confidence": confidence(attempts),
                }
            )

        return {
            "id": row["id"],
            "code": row["code"],
            "name": row["name"],
            "syllabus_status": row["syllabus_status"],
            "branch": row["branch_id"],
            "branch_name": row["branch_name"],
            "subject": row["subject_id"],
            "subject_name": row["subject_name"],
            "topics": topic_payload,
            "question_types": types,
            "bank_size": sum(t["bank_size"] for t in topic_payload),
        }

    # ───────────────────────── admin / content studio ─────────────────────────

    def list_questions(self, *, chapter_id: str | None = None, topic_id: str | None = None,
                       question_type: str | None = None, status: str | None = None,
                       search: str | None = None, limit: int = 50, offset: int = 0) -> dict[str, Any]:
        clauses: list[str] = []
        params: list[Any] = []

        if chapter_id:
            clauses.append("q.chapter_id = ?")
            params.append(chapter_id)
        if topic_id:
            clauses.append("q.topic_id = ?")
            params.append(topic_id)
        if question_type:
            clauses.append("q.question_type = ?")
            params.append(question_type)
        if status:
            clauses.append("q.status = ?")
            params.append(status)
        if search:
            clauses.append("(q.prompt LIKE ? OR q.id LIKE ?)")
            params.extend([f"%{search}%", f"%{search}%"])

        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        total = query_one(self.conn, f"SELECT COUNT(*) AS n {qs._base_from()} {where}", tuple(params))
        rows = query_all(
            self.conn,
            f"""SELECT {qs._select_columns()} {qs._base_from()} {where}
                ORDER BY q.chapter_id, q.topic_id, q.id LIMIT ? OFFSET ?""",
            (*params, limit, offset),
        )
        questions = [qs.row_to_question(r) for r in rows]
        qs.attach_options(self.conn, questions)

        return {
            "items": questions,
            "total": int(total["n"]) if total else 0,
            "limit": limit,
            "offset": offset,
        }

    def upsert_question(self, question: dict[str, Any]) -> dict[str, Any]:
        """Content-studio write path. Validates before touching the DB."""
        from app.content.schema import QuestionDef, QuestionOption
        from app.content.validators import content_hash, validate_question

        payload = dict(question)
        payload["options"] = [
            QuestionOption(key=o["key"], text=o["text"], render=o.get("render", {})) for o in payload.get("options", [])
        ]
        definition = QuestionDef.model_validate(payload)
        definition.origin = "manual"

        index = self._curriculum_index()
        result = validate_question(definition, index)
        if not result.ok:
            raise ContentValidationError(result.errors)

        digest = content_hash(definition)
        from app.db.seed import _insert_options, _question_row

        row = _question_row(definition, digest)
        with transaction(self.conn):
            existing = self.conn.execute("SELECT id, dedupe_hash FROM questions WHERE id = ?", (definition.id,)).fetchone()
            if existing is None:
                self.conn.execute(
                    f"INSERT INTO questions ({', '.join(row.keys())}, revision) VALUES ({', '.join('?' * len(row))}, 1)",
                    tuple(row.values()),
                )
            else:
                assignments = ", ".join(f"{c}=?" for c in row if c != "id")
                values = [v for c, v in row.items() if c != "id"]
                self.conn.execute(
                    f"UPDATE questions SET {assignments}, revision = revision + 1, updated_at = datetime('now') WHERE id = ?",
                    (*values, definition.id),
                )
                self.conn.execute("DELETE FROM question_options WHERE question_id = ?", (definition.id,))
            _insert_options(self.conn, definition)

        return qs.get_question(self.conn, definition.id) or {}

    def set_status(self, question_id: str, status: str) -> bool:
        if status not in {"draft", "pending_review", "approved", "archived"}:
            raise ContentValidationError([f"Invalid status: {status}"])
        with transaction(self.conn):
            cursor = self.conn.execute(
                "UPDATE questions SET status = ?, updated_at = datetime('now') WHERE id = ?",
                (status, question_id),
            )
        return cursor.rowcount > 0

    def delete_question(self, question_id: str) -> bool:
        with transaction(self.conn):
            cursor = self.conn.execute("DELETE FROM questions WHERE id = ?", (question_id,))
        return cursor.rowcount > 0

    def _curriculum_index(self):
        from app.content.validators import CurriculumIndex

        chapter_ids = {r["id"] for r in query_all(self.conn, "SELECT id FROM chapters")}
        topic_rows = query_all(self.conn, "SELECT id, chapter_id FROM topics")
        chapter_topics: dict[str, set[str]] = {}
        for row in topic_rows:
            chapter_topics.setdefault(row["chapter_id"], set()).add(row["id"])
        return CurriculumIndex(chapter_ids, {r["id"] for r in topic_rows}, chapter_topics)

    def bank_stats(self) -> dict[str, Any]:
        return qs.bank_stats(self.conn)


class ContentValidationError(ValueError):
    def __init__(self, errors: list[str]):
        super().__init__("; ".join(errors))
        self.errors = errors
