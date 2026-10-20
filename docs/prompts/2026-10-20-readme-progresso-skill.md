# Progresso no README e skill de atualização

**Data:** 2026-10-20
**Autor:** Artur Lins
**Agente e modelo:** Claude Code / claude-sonnet-5-5
**Etapa SDD:** implementar
**Funcionalidade:** projeto

## Contexto fornecido

- `README.md`, `.agents/AGENTS.md`, `docs/skills/` e os `tasks.md` das specs 001 a 007.

## Prompts

### Prompt 1

```text
atualize o readme para constar o progresso de desenvolvimento (só referenciando a spec e tasks), atualmente está implementado até a spec 003. criar uma skill de atualização do readme sempre que for feito um commit de task realizada
```

### Prompt 2

```text
precisamos fazer algo que rode em outros provedores também, alguns colegas usam codex, antigravity e opencode
```

## Saída aceita

| Artefato | Ação |
|---|---|
| `README.md` | alterado: seção "Progresso do desenvolvimento" e estado atual |
| `docs/skills/atualizar-readme-progresso.md` | criado (guia canônico) |
| `.claude/skills/atualizar-readme-progresso/SKILL.md` | criado (skill do Claude Code que aponta para o guia) |
| `scripts/atualizar_readme_progresso.py` | criado: gera a tabela a partir dos `tasks.md` (`--check` para o CI) |
| `.githooks/pre-commit` | criado: roda o script e adiciona o README ao commit |
| `.github/workflows/ci.yml` | alterado: job `readme` |
| `docs/skills/README.md`, `.agents/AGENTS.md` | alterados: guia novo na tabela |

## Alterações humanas

Pendente de revisão.

## Verificação

Contagens obtidas dos `tasks.md` por `grep` (001: 64/65; 002: 51/51; 003 a 007: 0 tarefas feitas). O repositório não tem commits nem tarefas marcadas da 003; o README reflete isso.

## Pendências

- Confirmar com Artur Lins se a 003 já foi implementada fora do repositório; se sim, marcar as tarefas em `tasks.md` com evidência e reexecutar o guia.
