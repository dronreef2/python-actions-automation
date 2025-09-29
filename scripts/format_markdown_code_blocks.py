#!/usr/bin/env python
"""Formata blocos de código Python e Bash dentro de arquivos Markdown.

Simplificado em relação a soluções mais complexas: extrai blocos cercados por ```python ou ```bash,
formata usando ruff (python) ou prettier (bash) e reescreve o arquivo.
"""
from __future__ import annotations

import re
import subprocess
import tempfile
from pathlib import Path

CODE_BLOCK_RE = re.compile(r"```(python|bash|sh)\n(.*?)```", re.DOTALL)


def format_python(code: str) -> str:
    with tempfile.NamedTemporaryFile("w+", suffix=".py", delete=False) as tmp:
        tmp.write(code)
        tmp.flush()
        try:
            subprocess.run(["ruff", "format", tmp.name], check=True, capture_output=True)
        except Exception:
            return code
        tmp.seek(0)
        return tmp.read().rstrip("\n")


def format_bash(code: str) -> str:
    with tempfile.NamedTemporaryFile("w+", suffix=".sh", delete=False) as tmp:
        tmp.write(code)
        tmp.flush()
        try:
            subprocess.run(
                [
                    "npx",
                    "prettier",
                    "--plugin=@prettier/plugin-sh",
                    "--parser=sh",
                    tmp.name,
                    "--write",
                ],
                check=True,
                capture_output=True,
            )
        except Exception:
            return code
        tmp.seek(0)
        return tmp.read().rstrip("\n")


FORMATTERS = {"python": format_python, "bash": format_bash, "sh": format_bash}


def process_file(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    changed = False

    def repl(match):
        nonlocal changed
        lang, code = match.group(1), match.group(2)
        formatted = FORMATTERS.get(lang, lambda x: x)(code)
        if formatted != code.rstrip("\n"):
            changed = True
        return f"```{lang}\n{formatted}\n```"

    new_text = CODE_BLOCK_RE.sub(repl, text)
    if changed:
        path.write_text(new_text, encoding="utf-8")
    return changed


def main():  # noqa: D401
    total = updated = 0
    for md in Path.cwd().rglob("*.md"):
        total += 1
        if process_file(md):
            updated += 1
    print(f"Markdown analisados: {total}, atualizados: {updated}")


if __name__ == "__main__":  # pragma: no cover
    main()
