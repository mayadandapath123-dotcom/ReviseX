"""Request schemas — every write endpoint validates its input here.

Responses are plain dicts shaped by the services and typed on the client in
`frontend/src/shared/types/*`. Requests are strict: unknown fields are rejected
so a malformed client fails loudly instead of silently corrupting data.
"""

from __future__ import annotations

from typing import Any, Literal, Sequence

from pydantic import BaseModel, ConfigDict, Field, field_validator

Difficulty = Literal["easy", "medium", "hard"]


class CreateProfileRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    display_name: str = Field(min_length=1, max_length=24)
    avatar: str | None = Field(default=None, max_length=4)


class UpdateProfileRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    display_name: str | None = Field(default=None, min_length=1, max_length=24)
    avatar: str | None = Field(default=None, max_length=4)
    settings: dict[str, Any] | None = None
    online_enabled: bool | None = None
    public_handle: str | None = Field(default=None, max_length=24)


class StartTestRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode_key: str | None = None
    subject: str | None = None
    branch: str | None = None
    chapter: str | None = None
    topic: str | None = None
    question_types: list[str] | None = None
    difficulties: list[Difficulty] | None = None
    tags: list[str] | None = None
    question_count: int | None = Field(default=None, ge=1, le=100)
    duration_limit_ms: int | None = Field(default=None, ge=5000, le=3_600_000)
    include_off_syllabus: bool = False
    prioritise_weak: bool | None = None
    shuffle_options: bool | None = None
    seed: int | None = None


class AttemptPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    seq: int = Field(ge=0)
    question_id: str
    selected_key: str | None = None
    option_order: list[str] = Field(default_factory=list)
    is_correct: bool | None = None  # informational only; the server re-grades
    response_ms: int = Field(ge=0, le=600_000)
    shown_ms: int = Field(default=0, ge=0, le=600_000)
    coefficients: list[int] | None = None  # balancing mode


class SubmitSessionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    elapsed_ms: int = Field(default=0, ge=0, le=7_200_000)
    wrong_penalty: float = Field(default=0.0, ge=0.0, le=1.0)
    attempts: list[AttemptPayload] = Field(default_factory=list, max_length=200)
    client_version: str | None = Field(default=None, max_length=32)

    @field_validator("attempts")
    @classmethod
    def _bounded_attempts(cls, value: Sequence[AttemptPayload]) -> Sequence[AttemptPayload]:
        if len(value) > 200:
            raise ValueError("A single session cannot contain more than 200 attempts")
        return value


class OptionPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    key: Literal["a", "b", "c", "d"]
    text: str = Field(min_length=1, max_length=200)
    render: dict[str, Any] = Field(default_factory=dict)


class UpsertQuestionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=3, max_length=120)
    chapter: str
    topic: str | None = None
    question_type: Literal["mcq_single", "balancing"] = "mcq_single"
    prompt: str = Field(min_length=3, max_length=400)
    stimulus: dict[str, Any] = Field(default_factory=dict)
    options: list[OptionPayload] = Field(default_factory=list)
    answer_key: Literal["a", "b", "c", "d"]
    explanation: str | None = Field(default=None, max_length=400)
    hint: str | None = Field(default=None, max_length=200)
    difficulty: Difficulty = "medium"
    time_budget_ms: int = Field(default=10000, ge=1000, le=120000)
    source_ref: str = Field(min_length=3, max_length=200)
    tags: list[str] = Field(default_factory=list)
    status: Literal["draft", "pending_review", "approved", "archived"] = "approved"


class StatusUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Literal["draft", "pending_review", "approved", "archived"]


class GenerateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    chapter_id: str
    topic_id: str | None = None
    count: int = Field(default=5, ge=1, le=20)
    difficulty: Difficulty = "medium"
    extra_instructions: str = Field(default="", max_length=400)
