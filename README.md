# python-actions-automation

Este repositório oferece automações para projetos Python utilizando GitHub Actions, inspirado nas melhores práticas do [ultralytics/actions](https://github.com/ultralytics/actions).

## Funcionalidades
- **Auto-formatação**: Padroniza o código automaticamente com Black.
- **Lint**: Verifica estilo e possíveis erros com Ruff.
- **Spell Check**: Verificação ortográfica com Codespell.
- **Revisão por IA (Gemini)**: (placeholder) Estrutura pronta para integrar análise automática de PR por IA.
- **Testes Automatizados**: Pytest em múltiplas versões de Python (3.10–3.12) com relatório de cobertura.

## Workflows

| Workflow | Arquivo | Evento | Descrição |
|----------|---------|--------|-----------|
| Auto Format | `.github/workflows/autoformat.yml` | push, PR | Formata código com Black e commita se necessário |
| Lint | `.github/workflows/lint.yml` | push, PR | Executa Ruff (check + format --check) |
| Spell Check | `.github/workflows/spellcheck.yml` | push, PR | Roda Codespell em código e nomes de arquivos |
| Gemini AI Review | `.github/workflows/gemini.yml` | PR (opened, synchronize, reopened) | Gera diff e prepara integração futura com Gemini |
| Tests | `.github/workflows/tests.yml` | push, PR | Executa pytest + Ruff em matrix de versões |

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

## Próximos Passos (Sugestões)
- Adicionar testes automatizados (pytest) e cobertura.
- Publicar pacote (se aplicável) com workflow de release.
- Integrar chamada real à API Gemini.
- Adicionar Ruff no modo de correção automática em um job separado.

## Licença
Defina uma licença (ex: MIT, Apache-2.0) adicionando um arquivo `LICENSE`.