# Guia: atualizar o progresso no README

A seção "Progresso do desenvolvimento" do [`README.md`](../../README.md) mostra, por spec, as tarefas concluídas e a situação, com link para a spec e para o `tasks.md`. A tabela é **gerada**; nunca edite à mão o trecho entre `<!-- progresso:inicio ... -->` e `<!-- progresso:fim -->`.

O mecanismo não depende de ferramenta de agente (Claude Code, Codex, Antigravity, opencode, Cursor ou pessoa): é um script em Python, só com a biblioteca padrão, reforçado por um hook do git e pelo CI.

## Quando executar

Em todo commit que marque tarefa `[x]` em `docs/specs/NNN-*/tasks.md` (regra 6 do [`AGENTS.md`](../../.agents/AGENTS.md)) ou mude o status no `README.md` da spec.

## Como executar

```bash
python scripts/atualizar_readme_progresso.py          # reescreve a tabela
python scripts/atualizar_readme_progresso.py --check  # só confere (usado no CI)
```

Inclua o `README.md` no mesmo commit da tarefa. A situação vem do campo `Status` do `README.md` de cada spec; a contagem vem das caixas `[x]` e `[ ]` do `tasks.md`.

## Automação

| Camada | O que faz |
|---|---|
| Hook `.githooks/pre-commit` | Se o commit mexe em `tasks.md` ou no `README.md` de uma spec, roda o script e adiciona o `README.md` ao commit. Ativação, uma vez por clone: `git config core.hooksPath .githooks` |
| CI (job `readme`) | Falha se a tabela divergir dos `tasks.md`, mesmo sem o hook ativado |
| `AGENTS.md` | Lido por Codex, opencode, Antigravity e Claude Code; manda rodar o script |

A skill do Claude Code em `.claude/skills/atualizar-readme-progresso/` só aponta para este guia.
