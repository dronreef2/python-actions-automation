"""Wrapper para expor o CLI gemini-tool como entry point do pacote.

Mantemos a implementação principal em scripts/gemini_tool.py para permitir
execução isolada sem instalação, mas oferecemos console_script instalado.
"""
from __future__ import annotations

from pathlib import Path
import runpy
import sys


def main() -> int:  # noqa: D401
    script_path = Path(__file__).parent.parent.parent / "scripts" / "gemini_tool.py"
    # Executa o script real repassando argumentos
    globals_dict = runpy.run_path(str(script_path))  # noqa: S102
    entry = globals_dict.get("main")
    if callable(entry):  # type: ignore
        return int(entry())  # type: ignore
    print("gemini_tool main não encontrado")
    return 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
