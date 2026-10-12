# Base para a escrita das specs

**Atualizado em:** 12/10/2026 ([registro da sessão](../prompts/2026-10-12-alinhamento-produto-arquitetura.md))
**Origem:** pasta `docs/init/` (brainstorming inicial de 25/09/2026, resumido pela equipe em 07/10/2026), renomeada e alinhada em 12/10/2026.

Esta pasta reúne as regras, as telas e as orientações técnicas do produto inteiro, para que cada spec de funcionalidade (`docs/specs/NNN-nome-curto/`) parta delas em vez de recomeçar do zero. **Não é uma spec aprovada.** Quando uma spec é aprovada, ela prevalece para a sua funcionalidade, e as regras alteradas são atualizadas aqui.

## Arquivos

| Arquivo | Conteúdo | Usado em |
|---|---|---|
| [`spec.md`](spec.md) | Estágios, glossário, regras de negócio (RN), requisitos (RF), histórias (HU), casos de borda (CB), qualidade (RQ) e critérios de sucesso (CS), com IDs estáveis | `spec.md` de cada funcionalidade |
| [`design.md`](design.md) | Navegação, tokens, componentes e telas | Specs e planos com interface |
| [`plan.md`](plan.md) | Domínios, pipeline de geração, revisão, grupos da API, testes | `plan.md` de cada funcionalidade |
| [`skill.md`](skill.md) | Ponteiro para o [`AGENTS.md`](../../.agents/AGENTS.md) e os [skills](../skills/README.md) | — |
| [`tasks.md`](tasks.md) | Ponteiro: tarefas são geradas por spec; próximos passos do projeto | — |

## Onde está o resto

| Assunto | Documento |
|---|---|
| O que é o produto e por quê | [`../produto/visao.md`](../produto/visao.md) |
| Funcionalidades e recorte por estágio | [`../produto/backlog.md`](../produto/backlog.md) |
| Princípios invioláveis | [`../constitution.md`](../constitution.md) |
| Arquitetura vigente e de referência | [`../arquitetura/`](../arquitetura/README.md) |
| Decisões técnicas | [`../research.md`](../research.md) |
| Pendências e pauta com o PO | [`../produto/pendencias.md`](../produto/pendencias.md) e [`../produto/pauta-po.md`](../produto/pauta-po.md) |

## Histórico

| Data | Mudança |
|---|---|
| 25/09/2026 | Brainstorming inicial (`Spec.md`, `Plan.md`, `DESIGN.md`, `SKILL.md`, `Tasks.md`), escopo com trilhas, questões e flashcards |
| 29/09/2026 | Conteúdo redistribuído para `docs/produto/`, a constituição e os skills; pasta declarada histórica ([registro](../prompts/2026-09-29-estruturacao-projeto.md)) |
| 07/10/2026 | Arquivos resumidos e reorganizados pela equipe (commit `e32228a`), com IDs RN, RF e HU renumerados |
| 12/10/2026 | Esboço de arquitetura adicionado (commit `9f0f40d`) |
| 12/10/2026 | Pasta renomeada para `base-specs/`, arquivos em minúsculas, conteúdo alinhado ao produto de repetição espaçada com trilha, `Architecture.md` movido para [`../arquitetura/referencia-pos-academica.md`](../arquitetura/referencia-pos-academica.md). IDs de 07/10/2026 preservados e congelados ([registro](../prompts/2026-10-12-alinhamento-produto-arquitetura.md)) |

As versões anteriores de cada arquivo estão no histórico do git.
