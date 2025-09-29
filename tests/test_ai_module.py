import os

from python_actions_automation.ai import generate_summary, suggest_labels


def test_generate_summary_no_key():
    # Sem chave deve retornar uma string não vazia (fallback neutro permitido)
    if "GEMINI_API_KEY" in os.environ:
        del os.environ["GEMINI_API_KEY"]
    out = generate_summary("diff exemplo")
    assert isinstance(out, str)
    assert out  # algo retornado


def test_suggest_labels_fallback():
    if "GEMINI_API_KEY" in os.environ:
        del os.environ["GEMINI_API_KEY"]
    labels = suggest_labels("Title", "Body", "diff", ["bug", "tests"])
    # Sem chave não deve quebrar; pode retornar vazio
    assert isinstance(labels, list)
