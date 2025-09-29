# python-actions-automation

Este repositório oferece automações para projetos Python utilizando GitHub Actions. Ele inclui workflows para formatação automática, linting, verificação ortográfica, revisão por IA (placeholder) e testes automatizados.

## Funcionalidades
- **Auto-formatação**: Padroniza o código automaticamente com Black.
- **Lint**: Verifica estilo e possíveis erros com Ruff.
- **Spell Check**: Verificação ortográfica com Codespell.
- **Revisão por IA (Gemini)**: (placeholder) Estrutura pronta para integrar análise automática de PR por IA.
- **Testes Automatizados**: Pytest em múltiplas versões de Python (3.10–3.12) com relatório de cobertura.
 - **Prettier Config**: Formatação consistente de Markdown/YAML/JSON.
 - **Docstrings Formatting**: Padronização automática com docformatter.
 - **Broken Links**: Checagem de links quebrados em Markdown (Lychee).
 - **Resumo de PR (IA)**: Geração de resumo estruturado de mudanças em PRs.
 - **Auto-Label IA**: Sugestão e aplicação automática de labels em PRs via Gemini (workflow `ai-autolabel.yml`).

## Workflows

| Workflow | Arquivo | Evento | Descrição |
|----------|---------|--------|-----------|
| Unified Formatting | `.github/workflows/format-unified.yml` | push, PR | Black + docformatter + Prettier + code blocks |
| Lint | `.github/workflows/lint.yml` | push, PR | Executa Ruff (check + format --check) |
| Spell Check | `.github/workflows/spellcheck.yml` | push, PR | Roda Codespell em código e nomes de arquivos |
| Gemini AI Review | `.github/workflows/gemini.yml` | PR (opened, synchronize, reopened) | Gera diff e prepara integração futura com Gemini |
| Tests | `.github/workflows/tests.yml` | push, PR | Executa pytest + Ruff em matrix de versões |
| Release | `.github/workflows/release.yml` | dispatch, tag | Build e publicação PyPI/TestPyPI |
| Prettier (LEGADO) | `.github/workflows/prettier.yml` | push, PR | (Será substituído pelo unified) |
| Docstrings (LEGADO) | `.github/workflows/docformatter.yml` | push, PR | (Coberto pelo unified) |
| Broken Links | `.github/workflows/links.yml` | push, PR, schedule | Verifica links em Markdown |
| PR Summary | `.github/workflows/pr-summary.yml` | PR | Comentário de resumo automatizado |
| AI Auto Label | `.github/workflows/ai-autolabel.yml` | PR | Sugere e aplica labels via Gemini |

## Estrutura Inicial

```text
.github/
	workflows/
		autoformat.yml
		lint.yml
		spellcheck.yml
		gemini.yml
README.md
.gitignore
```

## Como usar
1. Faça um commit e `git push`.
2. Acesse a aba **Actions** no GitHub.
3. Verifique a execução dos workflows nos commits ou Pull Requests.

### Ambiente local (opcional)

Crie e ative um ambiente virtual e instale dependências de desenvolvimento:

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


### Integração Gemini Code Assist

Se você já instalou o GitHub App "Gemini Code Assist" (como mostra a captura), ele poderá adicionar comentários automáticos nos PRs.

Para usar o workflow `gemini.yml` com chamada de API própria (script em `scripts/gemini_review.py`):

1. Crie um secret no repositório ou organização chamado `GEMINI_API_KEY` com sua chave da API Gemini.
2. Abra/atualize um Pull Request.
3. O job "Gemini AI Review" vai gerar o diff e publicar/atualizar um comentário marcado com `<!-- gemini-ai-review -->`.

Caso o secret não exista ou a lib não esteja disponível, o job finaliza sem falhar o PR.

Você pode trocar o modelo definindo um secret ou variável `GEMINI_MODEL` (ex: `gemini-1.5-pro`).


## Próximos Passos (Sugestões)
- Adicionar testes automatizados (pytest) e cobertura.
- Publicar pacote (se aplicável) com workflow de release.
- Integrar chamada real à API Gemini.
- Adicionar Ruff no modo de correção automática em um job separado.

## Licença
Defina uma licença (ex: MIT, Apache-2.0) adicionando um arquivo `LICENSE`.