"""AI subsystem. Provider abstraction + anti-hallucination gate.

Everything here is optional: if no provider is configured or reachable,
`AIService` falls back to the deterministic `LocalAIProvider`.
"""

from app.ai.base import AIProvider, FactInput, GeneratedItem, GenerationSpec, Insights

__all__ = ["AIProvider", "FactInput", "GeneratedItem", "GenerationSpec", "Insights"]
