#!/usr/bin/env python
"""Atualiza cabeçalhos de arquivos com aviso de licença simples.

Uso:
  python scripts/update_headers.py [--apply]

Sem --apply roda em modo somente leitura.
"""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

HEADER = "Projeto Demo - MIT License"
EXTS = {".py", ".yml", ".yaml", ".toml", ".sh"}
IGNORE_DIRS = {".git", "dist", "build", "node_modules", ".venv", "__pycache__"}


def needs_header(text: str) -> bool:
    return HEADER not in text.splitlines()[:5]


def update_file(path: Path, apply: bool) -> bool:
    try:
        content = path.read_text(encoding="utf-8")
    except Exception:
        return False
    if not needs_header(content):
        return False
    year = datetime.now().year
    header_line = f"# {HEADER} © {year}\n"
    if content.startswith("#!"):
        # preserve shebang
        lines = content.splitlines(True)
        shebang, rest = lines[0], "".join(lines[1:])
        new_content = shebang + header_line + rest
    else:
        new_content = header_line + content
    if apply:
        path.write_text(new_content, encoding="utf-8")
    return True


def main():  # noqa: D401
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Escreve alterações")
    args = parser.parse_args()
    changed = checked = 0
    for p in Path.cwd().rglob("*"):
        if p.is_dir():
            if p.name in IGNORE_DIRS:
                continue
            else:
                continue
        if p.suffix in EXTS:
            checked += 1
            if update_file(p, args.apply):
                changed += 1
    print(f"Headers verificados: {checked}, atualizados: {changed}")


if __name__ == "__main__":
    main()
