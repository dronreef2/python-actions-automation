#!/usr/bin/env python
"""Gera labels sugeridas por IA (Gemini) para um Pull Request.

Requer GEMINI_API_KEY e GITHUB_TOKEN. Só aplica labels se retornadas forem permitidas.
"""
from __future__ import annotations

import json
import os
import re
import sys

import requests

try:  # pragma: no cover - ambiente CI
    import google.generativeai as genai  # type: ignore
except ImportError:  # pragma: no cover
    genai = None  # type: ignore

COMMENT_HEADER = "<!-- gemini-ai-labels -->"
DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")


def read_file(path: str) -> str:
    try:
        with open(path, encoding="utf-8", errors="ignore") as f:
            return f.read()[:15000]
    except FileNotFoundError:
        return ""


def parse_allowed() -> set[str]:
    raw = os.getenv("ALLOWED_LABELS", "")
    return {x.strip() for x in raw.split(",") if x.strip()}


def build_prompt(title: str, body: str, diff: str, allowed: set[str], max_labels: int) -> str:
    allowed_list = ", ".join(sorted(allowed)) or "(nenhuma definida)"
    return (
        "Você é um assistente que classifica Pull Requests de um projeto Python. "
        "Retorne SOMENTE um JSON com a chave 'labels' contendo uma lista (até {max_labels}) "
        "de labels contidas neste conjunto permitido: {allowed}. "
        "Prefira diversidade e relevância; não invente labels fora da lista.\n\n"
        f"TÍTULO: {title}\n\nDESCRIÇÃO:\n{body[:3000]}\n\nDIFF:\n{diff[:8000]}\n"
    ).format(max_labels=max_labels, allowed=allowed_list)


def configure_model():  # noqa: ANN201
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or not genai:
        print("[labels] GEMINI_API_KEY ausente ou lib indisponível; abortando silenciosamente.")
        return None
    genai.configure(api_key=api_key)
    try:
        return genai.GenerativeModel(DEFAULT_MODEL)
    except Exception as e:  # pragma: no cover
        print(f"[labels] Falha ao criar modelo: {e}")
        return None


def extract_labels(text: str, allowed: set[str], max_labels: int) -> list[str]:
    # Tenta encontrar bloco JSON
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        return []
    try:
        data = json.loads(match.group(0))
        labels = data.get("labels", [])
        if not isinstance(labels, list):
            return []
        norm = []
        for item in labels:
            if not isinstance(item, str):
                continue
            name = item.strip().lower()
            if name in allowed and name not in norm:
                norm.append(name)
            if len(norm) >= max_labels:
                break
        return norm
    except json.JSONDecodeError:
        return []


def apply_labels(repo: str, pr_number: int, labels: list[str], token: str) -> None:
    if not labels:
        print("[labels] Nenhuma label aplicável.")
        return
    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/labels"
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
    r = requests.post(url, headers=headers, data=json.dumps({"labels": labels}), timeout=30)
    if r.status_code not in (200, 201):
        print(f"[labels] Falha ao aplicar labels: {r.status_code} -> {r.text[:300]}")
    else:
        print(f"[labels] Labels aplicadas: {labels}")


def comment_result(repo: str, pr_number: int, labels: list[str], token: str) -> None:
    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
    body = f"{COMMENT_HEADER}\nLabels sugeridas/aplicadas: {', '.join(labels) if labels else '(nenhuma)'}"
    r = requests.post(url, headers=headers, data=json.dumps({"body": body}), timeout=30)
    if r.status_code not in (200, 201):
        print(f"[labels] Falha ao comentar labels: {r.status_code}")


def main() -> int:
    repo = os.getenv("REPO_FULL") or os.getenv("GITHUB_REPOSITORY")
    pr_number = os.getenv("PR_NUMBER") or os.getenv("GITHUB_REF_NAME", "0")
    pr_title = os.getenv("PR_TITLE", "")
    pr_body = os.getenv("PR_BODY", "")
    diff_file = os.getenv("DIFF_FILE", "diff.txt")
    token = os.getenv("GITHUB_TOKEN")
    allowed = parse_allowed()
    max_labels = int(os.getenv("MAX_LABELS", "3"))

    if not (repo and pr_number and token and allowed):
        print("[labels] Variáveis obrigatórias ausentes; encerrando.")
        return 0

    diff_content = read_file(diff_file)
    prompt = build_prompt(pr_title, pr_body, diff_content, allowed, max_labels)
    model = configure_model()
    if not model:
        return 0

    try:
        response = model.generate_content(prompt)
        raw_text = getattr(response, "text", "")
    except Exception as e:  # pragma: no cover
        print(f"[labels] Error na geração: {e}")
        return 0

    labels = extract_labels(raw_text, allowed, max_labels)
    apply_labels(repo, int(pr_number), labels, token)
    comment_result(repo, int(pr_number), labels, token)
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
