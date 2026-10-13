# Divisão da implementação do MVP

**Data:** 2026-10-13
**Autor:** Artur Lins
**Agente e modelo:** Claude Code / claude-opus-5-5
**Etapa SDD:** implementar (organização da execução)
**Funcionalidade:** 001 a 007 (MVP)

## Contexto fornecido

- `.agents/AGENTS.md` e `docs/skills/contexto-tecnico.md`
- `docs/specs/README.md`, os `tasks.md` da 001 à 006 (seções de fases, "Dependências" e "Estratégia de incremento") e a spec da 007
- `docs/prompts/2026-10-13-001-conta-acesso-implementacao.md`

## Prompts

### Prompt 1

```text
eu e o arthur moura vamos implementar o mvp, já estou iniciando a spec 001, crie um plano de divisão entre a gente (obs. a spec 007 já está sendo escrita agora em paralelo) da implementação de cada spec, especialmente no que puder ser feito de forma independente
```

## Saída aceita

| Artefato | Ação |
|---|---|
| `docs/specs/divisao-implementacao-mvp.md` | criado |
| `docs/specs/README.md` | alterado (link para a divisão) |
| `docs/prompts/README.md` | alterado (índice) |

## Alterações humanas

Pendente de revisão por Artur Lins e Arthur Moura (decisões D1 a D4 do documento).

## Verificação

- Faixas de tarefas por fase e dependências conferidas nos `tasks.md` da 001 à 006 (seções "Dependências"). Contagem de tarefas: 001 com 65, 002 com 51, 003 com 45, 004 com 59, 005 com 49 e 006 com 45.
- Ordem das migrações (`0001` a `0007`) conferida no `contexto-tecnico.md`.
- `fsrs==6.3.2` presente em `backend/pyproject.toml`, condição da antecipação da T009 e da T010 da 005.
- Nenhum código foi alterado, e nenhum checkbox de tarefa foi marcado.

## Pendências

- Aprovação das decisões D1 a D4 por Artur Lins e Arthur Moura.
- Os nomes dos responsáveis entram nos planos da 004, da 005 e da 006 na T001 de cada uma, ao iniciar a implementação.
- Revisar a atribuição da 007 (D3) quando o plano dela for aprovado.
