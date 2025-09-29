from __future__ import annotations

from collections.abc import Iterable


def soma(valores: Iterable[float]) -> float:
    """Retorna a soma dos valores.

    Args:
        valores: Iterável de números.
    """
    total = 0.0
    for v in valores:
        total += float(v)
    return total


def normalizar(valores: Iterable[float]) -> list[float]:
    """Normaliza uma sequência para que a soma seja 1.0.

    Retorna lista vazia se não houver valores ou se soma for zero.
    """
    lista = [float(v) for v in valores]
    total = soma(lista)
    if total == 0 or not lista:
        return []
    return [v / total for v in lista]
