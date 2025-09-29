#!/usr/bin/env python
"""Gera resumo conciso de PR e publica como comentário fixo.

Inspirado em ideias de actions públicas, mas implementação independente.
"""

from __future__ import annotations

import json
import os
import sys

import requests

try:  # pragma: no cover
    import google.generativeai as genai  # type: ignore
except ImportError:  # pragma: no cover
    genai = None  # type: ignore

HEADER = "<!-- gemini-pr-summary -->"
MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")


def load_diff(path: str) -> str:
    try:
        with open(path, encoding="utf-8", errors="ignore") as f:
            return f.read()[:25000]
    except FileNotFoundError:
        return "(diff não encontrado)"


def generate_summary(diff: str) -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or not genai:
        return "(Resumo indisponível: GEMINI_API_KEY ausente)"
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(MODEL)
    prompt = (
        "Resuma as mudanças deste Pull Request em formato Markdown com as seções: \n"
        "### 🌟 Resumo\n### 📊 Principais Mudanças\n### 🎯 Impacto\n"
        "Texto em Português. Seja sucinto.\n\nDIFF:\n" + diff[:20000]
    )
    try:
        resp = model.generate_content(prompt)
        text = getattr(resp, "text", "").strip()
        return text or "(sem conteúdo)"
    except Exception as e:  # pragma: no cover
        return f"(Falha ao gerar resumo: {e})"


def post_comment(summary: str, repo: str, pr_number: str, token: str):
    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}

    # Procurar comentário existente
    existing = requests.get(url, headers=headers, timeout=30)
    comment_id = None
    if existing.status_code == 200:
        for c in existing.json():
            if isinstance(c, dict) and str(c.get("body", "")).startswith(HEADER):
                comment_id = c.get("id")
                break

    body = f"{HEADER}\n{summary}\n\n<sub>Gerado automaticamente.</sub>"
    payload = json.dumps({"body": body})
    if comment_id:
        r = requests.patch(
            f"https://api.github.com/repos/{repo}/issues/comments/{comment_id}",
            headers=headers,
            data=payload,
            timeout=30,
        )
    else:
        r = requests.post(url, headers=headers, data=payload, timeout=30)
    print(f"[summary] status={r.status_code}")


def main() -> int:
    diff_file = os.getenv("DIFF_FILE", "pr_diff.txt")
    repo = os.getenv("REPO_FULL")
    pr_number = os.getenv("PR_NUMBER")
    token = os.getenv("GITHUB_TOKEN")
    diff = load_diff(diff_file)
    summary = generate_summary(diff)
    if repo and pr_number and token:
        post_comment(summary, repo, pr_number, token)
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
