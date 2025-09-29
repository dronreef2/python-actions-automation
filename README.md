# python-actions-automation

![CI Tests](https://github.com/dronreef2/python-actions-automation/actions/workflows/tests.yml/badge.svg)
![Lint](https://github.com/dronreef2/python-actions-automation/actions/workflows/lint.yml/badge.svg)
![Formatting](https://github.com/dronreef2/python-actions-automation/actions/workflows/format-unified.yml/badge.svg)
![Links](https://github.com/dronreef2/python-actions-automation/actions/workflows/links.yml/badge.svg)
![AI Review](https://github.com/dronreef2/python-actions-automation/actions/workflows/gemini.yml/badge.svg)

Este repositório oferece automações avançadas para projetos Python utilizando GitHub Actions: formatação unificada, lint, spell-check, análise de links, revisão/rotulagem/sumário de PR por IA (Gemini), testes com cobertura e pipeline de release.

## Funcionalidades
- Formatação unificada (Black + docformatter + Prettier + normalização de blocos de código Markdown)
- Lint estático (Ruff)
- Verificação ortográfica (Codespell)
- Checagem de links quebrados (Lychee)
- Revisão de PR por IA (Gemini)
- Sumário automatizado de PR (Gemini)
- Auto-label inteligente (Gemini)
- Revisão linha a linha (Beta) via `gemini-tool line-review`
- Testes em matriz Python 3.10–3.12 + cobertura (Codecov opcional)
- Pipeline de release (semver tags + PyPI/TestPyPI)
- Atualização de cabeçalhos de arquivos

## Workflows

| Workflow | Arquivo | Evento | Descrição |
|----------|---------|--------|-----------|
| Unified Formatting | `.github/workflows/format-unified.yml` | push, PR | Black + docformatter + Prettier + blocos Markdown |
| Lint | `.github/workflows/lint.yml` | push, PR | Ruff lint/check |
| Spell Check | `.github/workflows/spellcheck.yml` | push, PR | Codespell |
| Gemini AI Review | `.github/workflows/gemini.yml` | PR (opened, synchronize, reopened) | Comentário de revisão automatizada |
| PR Summary | `.github/workflows/pr-summary.yml` | PR | Gera sumário estruturado via IA |
| AI Auto Label | `.github/workflows/ai-autolabel.yml` | PR | Sugere/aplica labels via IA |
| Broken Links | `.github/workflows/links.yml` | push, PR, schedule | Verifica links externos |
| Tests | `.github/workflows/tests.yml` | push, PR | Pytest + cobertura |
| Release | `.github/workflows/release.yml` | dispatch, tag | Build e publicação PyPI/TestPyPI |

## Estrutura (resumida)

```text
.github/workflows/*.yml   # Automação CI/CD e IA
scripts/                  # Scripts auxiliares (Gemini, headers, markdown)
src/python_actions_automation/  # Código fonte do pacote
tests/                    # Testes pytest
pyproject.toml            # Configuração e dependências
LICENSE                   # Licença MIT
README.md
```

## Como usar
1. Faça um commit e `git push`.
2. Acesse a aba **Actions** no GitHub.
3. Verifique a execução dos workflows nos commits ou Pull Requests.

### Ambiente local (opcional)

Crie e active um ambiente virtual e install dependências de desenvolvimento:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
pytest -q
ruff check .
black .  # para formatar
```

### API Interna Gemini

O pacote expõe funções internas para uso local em automações ou scripts:

```python
from python_actions_automation.ai import generate_review, generate_summary, suggest_labels

diff = "...conteúdo do diff..."
print(generate_summary(diff))
print(generate_review(diff))
print(suggest_labels("Fix bug", "Corrige edge case", diff, ["bug", "tests"]))
```

Para habilitar:
```bash
pip install -e .[ai]
export GEMINI_API_KEY="minha_chave"
python -c "from python_actions_automation.ai import generate_summary; print(generate_summary('diff exemplo'))"
```

Sem a variável `GEMINI_API_KEY`, as funções retornam respostas neutras e não falham.

### CLI Unificado (`gemini-tool`)

Após instalar com extras `ai`:

```bash
pip install -e .[ai]
gemini-tool review       # comentário agregado de revisão
gemini-tool summary      # comentário de sumário
gemini-tool labels       # sugere/aplica labels
gemini-tool line-review  # (beta) tenta gerar comentários linha a linha
```

O CLI lê as mesmas variáveis de ambiente usadas nos workflows (`REPO_FULL`, `PR_NUMBER`, `GITHUB_TOKEN`, etc.).


### Integração Gemini Code Assist

Se você já instalou o GitHub App "Gemini Code Assist" (como mostra a captura), ele poderá adicionar comentários automáticos nos PRs.

Para usar o workflow `gemini.yml` com chamada de API própria (script em `scripts/gemini_review.py`):

1. Crie um secret no repositório ou organização chamado `GEMINI_API_KEY` com sua chave da API Gemini.
2. Abra/atualize um Pull Request.
3. O job "Gemini AI Review" via gerar o diff e publicar/atualizar um comentário marcado com `<!-- gemini-ai-review -->`.

Caso o secret não exista ou a lib não esteja disponível, o job finaliza sem falhar o PR.

Você pode trocar o modelo definindo um secret ou variável `GEMINI_MODEL` (ex: `gemini-1.5-pro`).


## Próximos Passos (Sugestões)
- Consolidar scripts Gemini em um único CLI (`scripts/gemini_tool.py`).
- Adicionar pre-commit para espelhar format-unified.
- Adicionar testes para scripts (`update_headers.py`, `format_markdown_code_blocks.py`).
- Automatizar CHANGELOG em releases.
- Implementar modo "link replace" (futuro) com heurística de substituição.

## Licença
Este projeto está licenciado sob os termos da licença MIT. Veja `LICENSE`.