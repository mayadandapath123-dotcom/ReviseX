"""AIService — provider selection, fact loading, validation and persistence.

The service is the only place that talks to a provider. Everything else in the
app calls this, so swapping providers (or running with AI disabled entirely)
never touches the quiz engine.
"""

from __future__ import annotations

import json
import logging
import sqlite3
import uuid
from typing import Any, Sequence

from app.ai.base import AIProvider, FactInput, GeneratedItem, GenerationSpec
from app.ai.local import LocalAIProvider
from app.ai.validation import validate_generated
from app.config.settings import get_settings
from app.db.connection import query_all, query_one, transaction
from app.services.recommendation_engine import RecommendationEngine

logger = logging.getLogger("leap.ai")

SOURCE_REF = "AI-generated from approved curriculum facts (pending review)."


class AIService:
    def __init__(self, conn: sqlite3.Connection, provider: AIProvider | None = None):
        self.conn = conn
        self.settings = get_settings()
        self.local = LocalAIProvider()
        self.provider = provider or self._select_provider()

    def _select_provider(self) -> AIProvider:
        requested = (self.settings.ai_provider or "local").strip().lower()

        if requested in {"none", "off", "disabled"}:
            return self.local  # local provider is deterministic and free; 'none' still keeps rewording working

        if requested == "ollama":
            from app.ai.ollama import OllamaProvider

            provider = OllamaProvider(self.local)
            if provider.available():
                return provider
            logger.info("Ollama requested but unavailable; using LocalAIProvider")
            return self.local

        if requested == "free_api":
            from app.ai.free_api import FreeAPIProvider

            provider = FreeAPIProvider(self.local)
            return provider if provider.available() else self.local

        if requested == "paid_api":
            from app.ai.paid_api import PaidAPIProvider

            provider = PaidAPIProvider(self.local)
            return provider if provider.available() else self.local

        return self.local

    # ───────────────────────── status ─────────────────────────

    def status(self) -> dict[str, Any]:
        available = False
        try:
            available = bool(self.provider.available())
        except Exception:  # a provider probe must never break the app
            available = False

        return {
            "configured_provider": self.settings.ai_provider,
            "active_provider": self.provider.name,
            "available": available,
            "capabilities": sorted(self.provider.capabilities()) if available else sorted(self.local.capabilities()),
            "message": (
                "AI is active."
                if available and self.provider.name != "local"
                else "AI unavailable — core revision still works."
                if self.provider.name != "local"
                else "Using the built-in offline generator. No model or internet required."
            ),
            "auto_approve": self.settings.auto_approve_ai_items,
        }

    # ───────────────────────── generation ─────────────────────────

    def load_facts(self, chapter_id: str | None = None, topic_id: str | None = None,
                   kind: str | None = None, limit: int = 60) -> list[FactInput]:
        sql = "SELECT id, kind, label, payload_json, chapter_id, topic_id, source_ref FROM facts WHERE 1=1"
        params: list[Any] = []
        if chapter_id:
            sql += " AND chapter_id = ?"
            params.append(chapter_id)
        if topic_id:
            sql += " AND topic_id = ?"
            params.append(topic_id)
        if kind:
            sql += " AND kind = ?"
            params.append(kind)
        sql += " LIMIT ?"
        params.append(limit)

        return [
            FactInput(
                id=row["id"],
                kind=row["kind"],
                label=row["label"],
                payload=json.loads(row["payload_json"] or "{}"),
                chapter_id=row["chapter_id"],
                topic_id=row["topic_id"],
                source_ref=row["source_ref"],
            )
            for row in query_all(self.conn, sql, tuple(params))
        ]

    def generate(self, *, chapter_id: str, topic_id: str | None = None, count: int = 5,
                 difficulty: str = "medium", extra_instructions: str = "") -> dict[str, Any]:
        facts = self.load_facts(chapter_id, topic_id)
        if not facts:
            return {"generated": 0, "accepted": 0, "rejected": [], "errors": ["No approved facts for this chapter/topic."]}

        spec = GenerationSpec(
            chapter_id=chapter_id,
            topic_id=topic_id,
            difficulty=difficulty,
            count=min(count, 20),
            extra_instructions=extra_instructions,
        )

        try:
            items = self.provider.generate_items(facts, spec)
        except Exception as exc:  # provider misbehaving must never break the app
            logger.warning("Provider %s failed: %s; falling back to local", self.provider.name, exc)
            items = self.local.generate_items(facts, spec)

        existing = {r["dedupe_hash"] for r in query_all(self.conn, "SELECT dedupe_hash FROM questions WHERE dedupe_hash IS NOT NULL")}

        accepted: list[str] = []
        rejected: list[dict[str, Any]] = []

        for index, item in enumerate(items):
            question_id = f"ai.{chapter_id}.{uuid.uuid4().hex[:10]}"
            gate = validate_generated(
                item,
                facts,
                chapter_id=chapter_id,
                topic_id=topic_id,
                source_ref=SOURCE_REF,
                existing_hashes=existing,
                question_id=question_id,
            )
            if not gate.accepted or gate.question is None:
                rejected.append({"prompt": item.prompt[:120], "issues": gate.issues, "provider": item.provider})
                continue

            status = "approved" if self.settings.auto_approve_ai_items else "pending_review"
            self._insert(gate.question, gate.dedupe_hash or "", status)
            existing.add(gate.dedupe_hash or "")
            accepted.append(question_id)

        return {
            "generated": len(items),
            "accepted": len(accepted),
            "status": "approved" if self.settings.auto_approve_ai_items else "pending_review",
            "provider": self.provider.name,
            "question_ids": accepted,
            "rejected": rejected[:20],
        }

    def _insert(self, question, dedupe_hash: str, status: str) -> None:
        with transaction(self.conn):
            self.conn.execute(
                """INSERT INTO questions (id, chapter_id, topic_id, question_type, prompt, stimulus_json, answer_key,
                                          explanation, hint, difficulty, time_budget_ms, source_ref, origin, status,
                                          revision, dedupe_hash, meta_json)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'ai', ?, 1, ?, ?)
                   ON CONFLICT(id) DO NOTHING""",
                (
                    question.id, question.chapter, question.topic, question.question_type, question.prompt,
                    json.dumps(question.stimulus, ensure_ascii=False), question.answer_key, question.explanation,
                    question.hint, question.difficulty, question.time_budget_ms, question.source_ref,
                    dedupe_hash, json.dumps({"tags": question.tags}, ensure_ascii=False),
                ),
            )
            self.conn.execute("UPDATE questions SET status = ? WHERE id = ?", (status, question.id))
            for order, option in enumerate(question.options):
                self.conn.execute(
                    """INSERT INTO question_options (question_id, opt_key, text, render_json, is_correct, display_order)
                       VALUES (?, ?, ?, '{}', ?, ?)""",
                    (question.id, option.key, option.text, int(option.key == question.answer_key), order),
                )

    # ───────────────────────── explanation / hints ─────────────────────────

    def explain(self, question_id: str) -> dict[str, Any]:
        row = query_one(
            self.conn,
            """SELECT q.prompt, q.explanation, q.topic_id, t.name AS topic_name,
                      qo.text AS answer_text
               FROM questions q
               LEFT JOIN topics t ON t.id = q.topic_id
               LEFT JOIN question_options qo ON qo.question_id = q.id AND qo.is_correct = 1
               WHERE q.id = ?""",
            (question_id,),
        )
        if row is None:
            return {"available": False, "explanation": None}

        item = {"prompt": row["prompt"], "topic_name": row["topic_name"], "answer_text": row["answer_text"]}
        facts = self.load_facts(topic_id=row["topic_id"], limit=20)

        explanation = row["explanation"]
        if not explanation:
            try:
                explanation = self.provider.generate_explanation(item, facts)
            except Exception:
                explanation = self.local.generate_explanation(item, facts)

        return {"available": True, "explanation": explanation, "provider": self.provider.name}

    def hints(self, question_id: str) -> list[str]:
        row = query_one(
            self.conn,
            "SELECT q.prompt, q.hint, q.topic_id, t.name AS topic_name FROM questions q LEFT JOIN topics t ON t.id=q.topic_id WHERE q.id = ?",
            (question_id,),
        )
        if row is None:
            return []
        item = {"prompt": row["prompt"], "topic_name": row["topic_name"]}
        if row["hint"]:
            return [row["hint"]]
        try:
            return self.provider.generate_hints(item, self.load_facts(topic_id=row["topic_id"], limit=10))
        except Exception:
            return self.local.generate_hints(item, [])

    # ───────────────────────── personalised insight ─────────────────────────

    def insights(self, profile_id: str, session: dict[str, Any] | None = None) -> dict[str, Any]:
        recommender = RecommendationEngine(self.conn)
        suggestions = recommender.suggestions(profile_id)
        payload = {
            "weak_areas": session.get("analysis", {}).get("weak_areas") if session else None,
            "strong_areas": session.get("analysis", {}).get("strong_areas") if session else None,
            "weak_topics": suggestions["weak_topics"],
        }
        try:
            insight = self.provider.analyse_session(payload)
        except Exception:
            insight = self.local.analyse_session(payload)

        return {
            "narrative": insight.narrative,
            "suggested_modes": insight.suggested_modes,
            "provider": insight.provider,
            "weak_topics": suggestions["weak_topics"],
            "unpractised": suggestions["unpractised"],
            "continue": suggestions["continue"],
        }

    def review_queue(self, limit: int = 50) -> list[dict[str, Any]]:
        rows = query_all(
            self.conn,
            """SELECT q.id, q.prompt, q.difficulty, q.status, q.created_at, q.stimulus_json,
                      qo.opt_key, qo.text, qo.is_correct, c.name AS chapter_name, t.name AS topic_name
               FROM questions q
               JOIN chapters c ON c.id = q.chapter_id
               LEFT JOIN topics t ON t.id = q.topic_id
               LEFT JOIN question_options qo ON qo.question_id = q.id
               WHERE q.status = 'pending_review'
               ORDER BY q.created_at DESC LIMIT ?""",
            (limit,),
        )
        grouped: dict[str, dict[str, Any]] = {}
        for row in rows:
            entry = grouped.setdefault(
                row["id"],
                {
                    "id": row["id"],
                    "prompt": row["prompt"],
                    "difficulty": row["difficulty"],
                    "status": row["status"],
                    "created_at": row["created_at"],
                    "chapter_name": row["chapter_name"],
                    "topic_name": row["topic_name"],
                    "stimulus": json.loads(row["stimulus_json"] or "{}"),
                    "options": [],
                },
            )
            if row["opt_key"]:
                entry["options"].append({"key": row["opt_key"], "text": row["text"], "is_correct": bool(row["is_correct"])})
        return list(grouped.values())
