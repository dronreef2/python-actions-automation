#!/usr/bin/env python
"""Script para gerar análise de PR usando Google Gemini.

Requer variável de ambiente GEMINI_API_KEY e acesso via GITHUB_TOKEN para comentar.

Fluxo:
1. Lê diff do arquivo indicado em DIFF_FILE.
2. Gera prompt estruturado para modelo Gemini.
3. Publica (ou atualiza) comentário no PR com tag fixa.

Se a chave GEMINI_API_KEY não estiver definida, o script falha silenciosamente com aviso.
"""
from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from typing import Optional

import requests

try:
    import google.generativeai as genai  # type: ignore
except ImportError:  # pragma: no cover
    genai = None  # type: ignore

COMMENT_HEADER = "<!-- gemini-ai-review -->"
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")


@dataclass
class PRContext:
    repo_full: str
    pr_number: int
    diff_file: str
    github_token: str

    @property
    def comments_api(self) -> str:
        return f"https://api.github.com/repos/{self.repo_full}/issues/{self.pr_number}/comments"


def load_diff(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()[:20000]  # limita para evitar prompt gigante
    except FileNotFoundError:
        return "(diff não encontrado)"


def build_prompt(diff: str) -> str:
    return (
        "Revise o diff de um Pull Request em um projeto Python. "
        "Foque em: corretude, complexidade, legibilidade, segurança, edge cases e aderência a boas práticas. "
        "Formate a resposta em seções com markdown.\n\n"
        "Responda em Português.\n\n"
        f"DIFF:\n{diff}\n"
    )


def configure_model() -> Optional[object]:  # noqa: ANN401
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or not genai:
        print("[gemini] GEMINI_API_KEY ausente ou biblioteca não instalada; pulando análise.")
        return None
    genai.configure(api_key=api_key)
    try:
        model = genai.GenerativeModel(MODEL_NAME)
    except Exception as e:  # pragma: no cover
        print(f"[gemini] Falha ao instanciar modelo: {e}")
        return None
    return model


def generate_review(model, prompt: str) -> str:  # noqa: ANN001, ANN401
    try:
        response = model.generate_content(prompt)
        text = getattr(response, "text", None) or "(sem resposta)"
        return text.strip()
    except Exception as e:  # pragma: no cover
        return f"(Falha ao gerar conteúdo: {e})"


def find_existing_comment(ctx: PRContext) -> Optional[int]:
    headers = {
        "Authorization": f"Bearer {ctx.github_token}",
        "Accept": "application/vnd.github+json",
    }
    r = requests.get(ctx.comments_api, headers=headers, timeout=30)
    if r.status_code != 200:
        print(f"[gemini] Não foi possível listar comentários: {r.status_code}")
        return None
    for comment in r.json():
        if isinstance(comment, dict) and str(comment.get("body", "")).startswith(COMMENT_HEADER):
            return int(comment.get("id"))
    return None


def post_comment(ctx: PRContext, body: str, update_id: Optional[int]) -> None:
    headers = {
        "Authorization": f"Bearer {ctx.github_token}",
        "Accept": "application/vnd.github+json",
    }
    payload = {"body": body}
    if update_id:
        url = f"https://api.github.com/repos/{ctx.repo_full}/issues/comments/{update_id}"
        r = requests.patch(url, headers=headers, data=json.dumps(payload), timeout=30)
        action = "update"
    else:
        r = requests.post(ctx.comments_api, headers=headers, data=json.dumps(payload), timeout=30)
        action = "create"
    if r.status_code not in (200, 201):
        print(f"[gemini] Falha ao {action} comentário: {r.status_code} -> {r.text[:300]}")
    else:
        print(f"[gemini] Comentário {action}d com sucesso.")


def main() -> int:
    repo_full = os.getenv("REPO_FULL")
    pr_number = os.getenv("PR_NUMBER")
    diff_file = os.getenv("DIFF_FILE", "diff.txt")
    github_token = os.getenv("GITHUB_TOKEN")

    if not (repo_full and pr_number and github_token):
        print("[gemini] Variáveis obrigatórias ausentes; encerrando.")
        return 0  # não falha o job

    ctx = PRContext(
        repo_full=repo_full,
        pr_number=int(pr_number),
        diff_file=diff_file,
        github_token=github_token,
    )

    diff_content = load_diff(ctx.diff_file)
    prompt = build_prompt(diff_content)
    model = configure_model()
    if not model:
        return 0

    review_text = generate_review(model, prompt)
    body = f"{COMMENT_HEADER}\n### Revisão Automática (Gemini)\n\n{review_text}\n\n---\n_Diff analisado parcialmente (limite de 20k chars)._"
    existing_id = find_existing_comment(ctx)
    post_comment(ctx, body, existing_id)
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
