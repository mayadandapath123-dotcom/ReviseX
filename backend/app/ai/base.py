"""AIProvider abstraction.

Rules enforced by this design:
  * AI is an enhancement — every capability has a deterministic local fallback;
  * AI never invents facts: it is only ever handed approved `facts` rows;
  * AI output is validated, then quarantined as `pending_review` until approved.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Protocol, Sequence, runtime_checkable

Capability = Literal["generate_items", "generate_explanation", "generate_hints", "analyse_session", "reword"]


@dataclass(frozen=True)
class FactInput:
    """A single approved fact, exactly as stored in the `facts` table."""

    id: str
    kind: str
    label: str
    payload: dict[str, Any]
    chapter_id: str
    topic_id: str | None
    source_ref: str


@dataclass(frozen=True)
class GenerationSpec:
    chapter_id: str
    topic_id: str | None = None
    question_types: Sequence[str] = ("mcq_single",)
    difficulty: str = "medium"
    count: int = 4
    language: str = "en"
    extra_instructions: str = ""


@dataclass
class GeneratedItem:
    prompt: str
    options: list[str]
    answer_index: int
    question_type: str = "mcq_single"
    difficulty: str = "medium"
    explanation: str | None = None
    hint: str | None = None
    time_budget_ms: int = 12000
    fact_ids: list[str] = field(default_factory=list)
    provider: str = "unknown"
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class Insights:
    weak_topics: list[dict[str, Any]] = field(default_factory=list)
    narrative: str = ""
    suggested_modes: list[str] = field(default_factory=list)
    provider: str = "unknown"


@runtime_checkable
class AIProvider(Protocol):
    name: str

    def available(self) -> bool:
        """Cheap capability probe. Must never raise."""
        ...

    def capabilities(self) -> set[Capability]:
        ...

    def generate_items(self, facts: Sequence[FactInput], spec: GenerationSpec) -> list[GeneratedItem]:
        ...

    def generate_explanation(self, item: dict[str, Any], facts: Sequence[FactInput]) -> str | None:
        ...

    def generate_hints(self, item: dict[str, Any], facts: Sequence[FactInput]) -> list[str]:
        ...

    def analyse_session(self, session: dict[str, Any]) -> Insights:
        ...


class AIUnavailableError(RuntimeError):
    pass
