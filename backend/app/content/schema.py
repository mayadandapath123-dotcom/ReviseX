"""Pydantic models for the authorable content files.

Content authors edit JSON; these models are the contract. Anything that does not
parse is rejected at seed time with a precise, file-qualified error — never at
runtime in front of a student.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

Difficulty = Literal["easy", "medium", "hard"]
SyllabusStatus = Literal["core", "foundation", "optional", "removed"]
QuestionType = Literal["mcq_single", "balancing", "numeric_input"]
Origin = Literal["template", "ai", "manual"]
Status = Literal["draft", "pending_review", "approved", "archived"]

OPTION_KEYS = ("a", "b", "c", "d")


class TopicDef(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    name: str
    display_order: int = 0
    meta: dict[str, Any] = Field(default_factory=dict)


class ChapterDef(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    code: str | None = None
    name: str
    display_order: int = 0
    syllabus_status: SyllabusStatus = "core"
    exam_board: str = "cbse"
    meta: dict[str, Any] = Field(default_factory=dict)
    topics: list[TopicDef] = Field(default_factory=list)


class BranchDef(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    name: str
    icon: str | None = None
    display_order: int = 0
    is_active: bool = True
    meta: dict[str, Any] = Field(default_factory=dict)
    chapters: list[ChapterDef] = Field(default_factory=list)


class SubjectDef(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    name: str
    icon: str | None = None
    display_order: int = 0
    is_active: bool = True
    note: str | None = None
    meta: dict[str, Any] = Field(default_factory=dict)
    branches: list[BranchDef] = Field(default_factory=list)


class CurriculumFile(BaseModel):
    model_config = ConfigDict(extra="ignore")
    exam_board: str = "cbse"
    grade: str = "class-10"
    syllabus_session: str | None = None
    subjects: list[SubjectDef]

    @field_validator("subjects")
    @classmethod
    def _unique_subject_ids(cls, value: list[SubjectDef]) -> list[SubjectDef]:
        ids = [s.id for s in value]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate subject ids in curriculum.json")
        return value


class ModeScoring(BaseModel):
    model_config = ConfigDict(extra="forbid")
    wrong_penalty: float = 0.0
    shuffle_options: bool = True
    stop_on_time: bool = False
    per_question_time_ms: int | None = None
    prioritise_weak: bool = False
    spread_evenly: bool = False
    max_attempts: int = 1
    show_explanation: str = "on_wrong"


class ModeFilters(BaseModel):
    model_config = ConfigDict(extra="forbid")
    subject: str | None = None
    branch: str | None = None
    chapter: str | None = None
    topic: str | None = None
    question_types: list[QuestionType] | None = None
    difficulties: list[Difficulty] | None = None
    tags: list[str] | None = None
    syllabus_status: list[SyllabusStatus] | None = None
    source: Literal["bank", "mistakes"] = "bank"


class ModeDef(BaseModel):
    model_config = ConfigDict(extra="forbid")
    key: str
    name: str
    description: str = ""
    icon: str | None = None
    group: str = "custom"
    featured: bool = False
    quick_start: bool = False
    duration_limit_ms: int | None = None
    question_count: int | None = None
    filters: ModeFilters = Field(default_factory=ModeFilters)
    scoring: ModeScoring = Field(default_factory=ModeScoring)


class ModesFile(BaseModel):
    model_config = ConfigDict(extra="ignore")
    modes: list[ModeDef]


class QuestionOption(BaseModel):
    model_config = ConfigDict(extra="forbid")
    key: str
    text: str
    render: dict[str, Any] = Field(default_factory=dict)

    @field_validator("text")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("Option text cannot be blank")
        return value.strip()


class QuestionDef(BaseModel):
    """A directly authored question (used by manual/AI content).

    Generated questions are produced by `generators.py`, which returns these.
    """

    model_config = ConfigDict(extra="forbid")
    id: str
    chapter: str
    topic: str | None = None
    question_type: QuestionType = "mcq_single"
    prompt: str
    stimulus: dict[str, Any] = Field(default_factory=dict)
    options: list[QuestionOption]
    answer_key: str
    explanation: str | None = None
    hint: str | None = None
    difficulty: Difficulty = "medium"
    time_budget_ms: int = 10000
    source_ref: str
    tags: list[str] = Field(default_factory=list)
    origin: Origin = "template"
    status: Status = "approved"
    meta: dict[str, Any] = Field(default_factory=dict)


class FactFile(BaseModel):
    """A structured-knowledge file that drives question generation."""

    model_config = ConfigDict(extra="forbid")
    chapter: str | None = None
    topic: str | None = None
    kind: str
    source_ref: str
    generator: str | None = None
    generator_note: str | None = None
    note: str | None = None
    items: list[dict[str, Any]]
