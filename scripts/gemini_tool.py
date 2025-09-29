#!/usr/bin/env python
"""CLI unificado para funcionalidades Gemini.

Subcomandos:
  review         - Gera revisão agregada (comentário sticky)
  summary        - Gera/rescreve sumário (comentário sticky)
  labels         - Sugere labels e aplica
  line-review    - (Beta) Gera comentários linha a linha em um PR

Todos dependem de variáveis padrão já usadas pelos workflows:
  REPO_FULL, PR_NUMBER, GITHUB_TOKEN, DIFF_FILE, PR_TITLE, PR_BODY, ALLOWED_LABELS

Falhas de IA não derrubam o processo (retorna 0).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence

import requests

try:  # pragma: no cover
    import google.generativeai as genai  # type: ignore
except ImportError:  # pragma: no cover
    genai = None  # type: ignore


MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")


def _configure_model():  # noqa: ANN201
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or not genai:
        return None
    try:
        genai.configure(api_key=api_key)
        return genai.GenerativeModel(MODEL_NAME)
    except Exception:  # pragma: no cover
        return None


def _read_limited(path: str, limit: int) -> str:
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()[:limit]
    except FileNotFoundError:
        return ""


def _github_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}


def _list_issue_comments(repo: str, pr_number: int, token: str) -> List[dict]:
    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
    r = requests.get(url, headers=_github_headers(token), timeout=30)
    if r.status_code != 200:
        return []
    data = r.json()
    return data if isinstance(data, list) else []


def _upsert_sticky_comment(
    repo: str, pr_number: int, token: str, header_marker: str, body_markdown: str
) -> None:
    comments = _list_issue_comments(repo, pr_number, token)
    existing_id: Optional[int] = None
    for c in comments:
        if isinstance(c, dict) and str(c.get("body", "")).startswith(header_marker):
            existing_id = int(c.get("id"))
            break
    payload = {"body": f"{header_marker}\n{body_markdown}"}
    if existing_id:
        url = f"https://api.github.com/repos/{repo}/issues/comments/{existing_id}"
        requests.patch(url, headers=_github_headers(token), data=json.dumps(payload), timeout=30)
    else:
        url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
        requests.post(url, headers=_github_headers(token), data=json.dumps(payload), timeout=30)


# ---------------- Review Agregado ---------------- #
REVIEW_HEADER = "<!-- gemini-ai-review -->"


def cmd_review(args: argparse.Namespace) -> int:  # noqa: D401
    repo = os.getenv("REPO_FULL") or os.getenv("GITHUB_REPOSITORY")
    pr_number = os.getenv("PR_NUMBER")
    token = os.getenv("GITHUB_TOKEN")
    diff_path = os.getenv("DIFF_FILE", "diff.txt")
    if not (repo and pr_number and token):
        return 0
    diff = _read_limited(diff_path, 20000)
    model = _configure_model()
    if not model:
        return 0
    prompt = (
        "Revise o diff de um Pull Request em um projeto Python. Foque em: corretude, complexidade, "
        "legibilidade, segurança, edge cases e boas práticas. Responda em Markdown em Português.\n\n" + diff
    )
    try:
        resp = model.generate_content(prompt)
        review_text = getattr(resp, "text", "(sem resposta)").strip()
    except Exception as e:  # pragma: no cover
        review_text = f"(falha geração: {e})"
    body = f"### Revisão Automática (Gemini)\n\n{review_text}\n\n—\n<sub>Diff truncado.</sub>"
    _upsert_sticky_comment(repo, int(pr_number), token, REVIEW_HEADER, body)
    return 0


# ---------------- Summary ---------------- #
SUMMARY_HEADER = "<!-- gemini-pr-summary -->"


def cmd_summary(args: argparse.Namespace) -> int:
    repo = os.getenv("REPO_FULL") or os.getenv("GITHUB_REPOSITORY")
    pr_number = os.getenv("PR_NUMBER")
    token = os.getenv("GITHUB_TOKEN")
    diff_path = os.getenv("DIFF_FILE", "diff.txt")
    if not (repo and pr_number and token):
        return 0
    diff = _read_limited(diff_path, 25000)
    model = _configure_model()
    if not model:
        summary = "(Resumo indisponível: Gemini não configurado)"
    else:
        prompt = (
            "Resuma as mudanças deste Pull Request em formato Markdown com as seções: \n"
            "### 🌟 Resumo\n### 📊 Principais Mudanças\n### 🎯 Impacto\n"
            "Texto em Português. Seja sucinto.\n\nDIFF:\n" + diff[:20000]
        )
        try:
            resp = model.generate_content(prompt)
            summary = getattr(resp, "text", "").strip() or "(sem conteúdo)"
        except Exception as e:  # pragma: no cover
            summary = f"(Falha ao gerar resumo: {e})"
    body = f"{summary}\n\n<sub>Gerado automaticamente.</sub>"
    _upsert_sticky_comment(repo, int(pr_number), token, SUMMARY_HEADER, body)
    return 0


# ---------------- Labels ---------------- #
LABELS_HEADER = "<!-- gemini-ai-labels -->"


def _parse_allowed() -> List[str]:
    raw = os.getenv("ALLOWED_LABELS", "")
    return [x.strip().lower() for x in raw.split(",") if x.strip()]


def _extract_labels(raw: str, allowed: Sequence[str], max_labels: int) -> List[str]:
    match = re.search(r"\{.*\}", raw, flags=re.DOTALL)
    if not match:
        return []
    try:
        data = json.loads(match.group(0))
        labels = data.get("labels", [])
    except Exception:
        return []
    out: List[str] = []
    for item in labels:
        if isinstance(item, str):
            name = item.strip().lower()
            if name in allowed and name not in out:
                out.append(name)
            if len(out) >= max_labels:
                break
    return out


def cmd_labels(args: argparse.Namespace) -> int:
    repo = os.getenv("REPO_FULL") or os.getenv("GITHUB_REPOSITORY")
    pr_number = os.getenv("PR_NUMBER")
    token = os.getenv("GITHUB_TOKEN")
    title = os.getenv("PR_TITLE", "")
    body_text = os.getenv("PR_BODY", "")
    diff_path = os.getenv("DIFF_FILE", "diff.txt")
    allowed = _parse_allowed()
    max_labels = int(os.getenv("MAX_LABELS", "3"))
    if not (repo and pr_number and token and allowed):
        return 0
    diff = _read_limited(diff_path, 15000)
    model = _configure_model()
    if not model:
        return 0
    allow_str = ", ".join(allowed) or "(nenhuma)"
    prompt = (
        "Você é um assistente que classifica Pull Requests. Retorne SOMENTE JSON: {\"labels\": []}. "
        f"Máximo {max_labels}. Use apenas: {allow_str}. Sem explicações.\n\nTÍTULO: {title}\n\nCORPO:\n{body_text[:3000]}\n\nDIFF:\n{diff[:8000]}"
    )
    try:
        resp = model.generate_content(prompt)
        raw = getattr(resp, "text", "")
    except Exception as e:  # pragma: no cover
        raw = f"{{\"labels\":[]}}  /* error: {e} */"
    labels = _extract_labels(raw, allowed, max_labels)
    # aplica
    if labels:
        url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/labels"
        requests.post(
            url,
            headers=_github_headers(token),
            data=json.dumps({"labels": labels}),
            timeout=30,
        )
    comment_body = f"Labels sugeridas/aplicadas: {', '.join(labels) if labels else '(nenhuma)'}"
    _upsert_sticky_comment(repo, int(pr_number), token, LABELS_HEADER, comment_body)
    return 0


# ---------------- Line-by-line Review (Beta) ---------------- #
LINE_REVIEW_TAG = "<!-- gemini-line-review -->"


@dataclass
class FilePatch:
    filename: str
    patch: str


def _list_pr_files(repo: str, pr_number: int, token: str) -> List[FilePatch]:
    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}/files"
    r = requests.get(url, headers=_github_headers(token), timeout=30)
    if r.status_code != 200:
        return []
    out: List[FilePatch] = []
    for item in r.json():
        if not isinstance(item, dict):
            continue
        filename = item.get("filename")
        patch = item.get("patch")
        if isinstance(filename, str) and isinstance(patch, str):
            # ignorar arquivos muito grandes
            if len(patch) < 8000 and filename.endswith((".py", ".md")):
                out.append(FilePatch(filename, patch))
    return out[:20]  # limit de arquivos analisados


def cmd_line_review(args: argparse.Namespace) -> int:
    repo = os.getenv("REPO_FULL") or os.getenv("GITHUB_REPOSITORY")
    pr_number = os.getenv("PR_NUMBER")
    token = os.getenv("GITHUB_TOKEN")
    if not (repo and pr_number and token):
        return 0
    model = _configure_model()
    if not model:
        return 0
    files = _list_pr_files(repo, pr_number, token)
    # Montar bloco compacto para IA
    serialized = []
    for fp in files:
        serialized.append(f"FILE: {fp.filename}\nPATCH:\n{fp.patch}\n---")
    joined = "\n".join(serialized)[:18000]
        prompt = (
            "Você é um revisor de código. Para cada alteração relevante proponha zero ou mais comentários. "
            'Retorne JSON: {"comments":[{"file":"path","line":N,"body":"texto"}, ...]}. '
            "Comentários curtos, em Português, sugerindo melhorias objetivas. Sem texto fora do JSON.\n\n" + joined
        )
    try:
        resp = model.generate_content(prompt)
        raw = getattr(resp, "text", "")
    except Exception as e:  # pragma: no cover
        raw = f"{{\"comments\":[]}} /* error {e} */"
    comments: List[dict] = []
    m = re.search(r"\{.*\}", raw, flags=re.DOTALL)
    if m:
        try:
            data = json.loads(m.group(0))
            for c in data.get("comments", []):
                if (
                    isinstance(c, dict)
                    and isinstance(c.get("file"), str)
                    and isinstance(c.get("line"), int)
                    and isinstance(c.get("body"), str)
                ):
                    comments.append({
                        "path": c["file"],
                        "line": c["line"],
                        "body": c["body"][:500],
                        "side": "RIGHT",
                    })
                    if len(comments) >= 40:
                        break
        except Exception:  # pragma: no cover
            pass
    # Cria pull request review se houver comentários
    if comments:
        review_url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}/reviews"
        payload = {"event": "COMMENT", "body": "Revisão linha a linha (Beta)", "comments": comments}
        requests.post(review_url, headers=_github_headers(token), data=json.dumps(payload), timeout=30)
    else:
        # fallback: comentário único informando ausência
        _upsert_sticky_comment(
            repo,
            int(pr_number),
            token,
            LINE_REVIEW_TAG,
            "Nenhum comentário linha a linha gerado (pode ser mudança trivial ou parsing falhou).",
        )
    return 0


# ---------------- Main Dispatcher ---------------- #


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser("gemini-tool", description="Ferramentas AI para PRs")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("review")
    sub.add_parser("summary")
    sub.add_parser("labels")
    sub.add_parser("line-review")
    return p


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    mapping = {
        "review": cmd_review,
        "summary": cmd_summary,
        "labels": cmd_labels,
        "line-review": cmd_line_review,
    }
    func = mapping[args.cmd]
    return func(args)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
