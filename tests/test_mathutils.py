from python_actions_automation import normalizar, soma


def test_soma():
    assert soma([1, 2, 3]) == 6


def test_normalizar_empty():
    assert normalizar([]) == []


def test_normalizar():
    result = normalizar([2, 2, 4])
    # Soma = 8, valores normalizados devem ser [0.25, 0.25, 0.5]
    assert result == [0.25, 0.25, 0.5]
