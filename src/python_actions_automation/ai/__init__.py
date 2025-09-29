"""Subpacote de integrações internas com Gemini.

Exposição de funções utilitárias de alto nível:
- generate_review(diff: str) -> str
- generate_summary(diff: str, max_chars=800) -> str
- suggest_labels(title: str, body: str, diff: str, allowed: list[str], max_labels=3) -> list[str]

Todas usam a chave GEMINI_API_KEY se presente. Caso contrário retornam respostas neutras.
"""

from .core import (
    generate_review,
    generate_summary,
    suggest_labels,
    GeminiClient,
    GeminiNotAvailableError,
)

__all__ = [
    "GeminiClient",
    "GeminiNotAvailableError",
    "generate_review",
    "generate_summary",
    "suggest_labels",
]
