from __future__ import annotations

"""Camada interna de integração com Gemini.

Uso básico:
    from python_actions_automation.ai import generate_summary
    text = generate_summary(diff_text)

Projeto evita lançar exceções fatais quando a API não está configurada.
"""
from dataclasses import dataclass
from typing import Iterable, List
import os

try:  # pragma: no cover - import opcional
    import google.generativeai as genai  # type: ignore
except Exception:  # pragma: no cover
    genai = None  # type: ignore


class GeminiNotAvailableError(RuntimeError):
    pass


def _ensure_client():  # noqa: ANN201
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or not genai:
        raise GeminiNotAvailableError(
            "Gemini não disponível: defina GEMINI_API_KEY e install google-generativeai"
        )
    genai.configure(api_key=api_key)
    model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    return genai.GenerativeModel(model_name)


@dataclass
class GeminiClient:
    safe: bool = True  # se True, falhas retornam resposta neutra

    def _call(self, prompt: str) -> str:
        try:
            model = _ensure_client()
            resp = model.generate_content(prompt)
            return getattr(resp, "text", "").strip() or "(resposta vazia)"
        except GeminiNotAvailableError:
            if self.safe:
                return "(Gemini indisponível)"
            raise
        except Exception as e:  # pragma: no cover
            if self.safe:
                return f"(falha na geração: {e})"
            raise

    # ---- Funções de Alto Nível ---- #
    def review(self, diff: str) -> str:
        prompt = (
            "Revise este diff de código Python. Liste: Problemas Potenciais, "
            "Melhorias Recomendadas, Testes Sugeridos. Resposta em Markdown concisa.\n\n"
            + diff[:18000]
        )
        return self._call(prompt)

    def summary(self, diff: str, max_chars: int = 800) -> str:
        prompt = (
            (
                f"Resuma mudanças de um Pull Request em até {max_chars} characters. "
                "Formato: 1 linha de resumo + lista de bullets. Texto em Português."
            )
            + "\n\n"
            + diff[:12000]
        )
        text = self._call(prompt)
        return text[:max_chars]

    def labels(
        self,
        title: str,
        body: str,
        diff: str,
        allowed: Iterable[str],
        max_labels: int = 3,
    ) -> List[str]:
        allow = [a.strip().lower() for a in allowed if a.strip()]
        allow_str = ", ".join(allow) or "(none)"
        prompt = (
            'Classifique o Pull Request. Retorne apenas JSON: {"labels": [..]}. '
            f"Máx {max_labels} labels. Use somente: {allow_str}. Sem explicações extras.\n\n"
            f"TITLE: {title}\nBODY:\n{body[:3000]}\nDIFF:\n{diff[:8000]}"
        )
        raw = self._call(prompt)
        # parsing simples
        out: List[str] = []
        import json, re  # noqa

        match = re.search(r"\{.*\}", raw, flags=re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(0))
                for x in data.get("labels", []):
                    if isinstance(x, str):
                        name = x.lower().strip()
                        if name in allow and name not in out:
                            out.append(name)
                        if len(out) >= max_labels:
                            break
            except Exception:  # pragma: no cover
                pass
        return out


_default_client = GeminiClient()


def generate_review(diff: str) -> str:
    return _default_client.review(diff)


def generate_summary(diff: str, max_chars: int = 800) -> str:
    return _default_client.summary(diff, max_chars=max_chars)


def suggest_labels(title: str, body: str, diff: str, allowed: Iterable[str], max_labels: int = 3):
    return _default_client.labels(title, body, diff, allowed, max_labels=max_labels)
