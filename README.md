# Plataforma de estudos gamificada

Plataforma web que funde **repetição espaçada** com uma **trilha visual de progressão**. O estudante organiza os estudos em matérias, guarda nelas suas fontes e cria flashcards à mão ou pede à IA que os gere a partir das fontes, com referência ao trecho de origem. Os cartões são respondidos numa trilha unificada de lições montadas pelo algoritmo FSRS, com XP, meta diária e sequência. No final acadêmico, cada matéria ganha um chat que responde **apenas** com base nas fontes, com citações.

Projeto da disciplina de IA do curso de Sistemas de Informação, desenvolvido com **Spec-Driven Development (SDD)**.

> **Estado (29/10/2026):** o MVP está em implementação, em sequência, uma spec de cada vez. A 002 está convergida e a 001 está implementada, faltando só a T063 (teste guiado com três pessoas); a 003 convergiu em 29/10/2026 (criar, editar, suspender, excluir, buscar e filtrar cartões); a próxima é a base da 004. O acompanhamento por spec e tarefa está em [Progresso do desenvolvimento](#progresso-do-desenvolvimento).

## Equipe

| Pessoa | Papel |
|---|---|
| Arthur Moura | Integrante |
| Artur Lins | Integrante |
| Caroline Santana | Integrante |
| Pedro Paulo Lucena | Integrante |
| William Johnson | Integrante |

**Professor e Product Owner:** Aldo Nunes

**Scrum Master:** rodízio semanal entre os integrantes, requisito obrigatório da disciplina. A escala está pendente ([VAL-03](docs/produto/pendencias.md#val-03-escala-do-rodízio-de-scrum-master)).

## Por onde começar

| Quero… | Leia |
|---|---|
| Entender o produto | [`docs/produto/visao.md`](docs/produto/visao.md) |
| Ver as funcionalidades planejadas e o MVP | [`docs/produto/backlog.md`](docs/produto/backlog.md) |
| Ver as regras globais que servem de base às specs | [`docs/base-specs/`](docs/base-specs/README.md) |
| Entender a arquitetura | [`docs/arquitetura/`](docs/arquitetura/README.md) e [`docs/research.md`](docs/research.md) |
| Ver o que está pendente de decisão | [`docs/produto/pendencias.md`](docs/produto/pendencias.md) e [`docs/produto/pauta-po.md`](docs/produto/pauta-po.md) |
| Ver as exigências do professor (PO) | [`docs/produto/exigencias_po.md`](docs/produto/exigencias_po.md) |
| Conhecer as regras do projeto | [`docs/constitution.md`](docs/constitution.md) |
| Entender o processo SDD | [`docs/sdd_guidelines/00_COMECE_AQUI.md`](docs/sdd_guidelines/00_COMECE_AQUI.md) e [`docs/skills/fluxo-sdd.md`](docs/skills/fluxo-sdd.md) |
| Trabalhar com um agente de IA | [`.agents/AGENTS.md`](.agents/AGENTS.md) |
| Ver o histórico de prompts | [`docs/prompts/`](docs/prompts/README.md) |

## Progresso do desenvolvimento

<!-- progresso:inicio (gerado por scripts/atualizar_readme_progresso.py; não edite à mão) -->
| Spec | Tarefas concluídas | Situação |
|---|---|---|
| [001: Conta, sessão, isolamento e preferências](docs/specs/001-conta-acesso/spec.md) | 64 de 65 ([tarefas](docs/specs/001-conta-acesso/tasks.md)) | Implementando (falta T063) |
| [002: Matérias, envio e processamento de fontes](docs/specs/002-materias-fontes/spec.md) | 51 de 51 ([tarefas](docs/specs/002-materias-fontes/tasks.md)) | Convergida |
| [003: Cartões criados e gerenciados pelo estudante](docs/specs/003-cartoes-manuais/spec.md) | 45 de 45 ([tarefas](docs/specs/003-cartoes-manuais/tasks.md)) | Convergida |
| [004: Geração de cartões pela IA e revisão dos gerados](docs/specs/004-geracao-cartoes/spec.md) | 1 de 59 ([tarefas](docs/specs/004-geracao-cartoes/tasks.md)) | Tarefas aprovadas |
| [005: Lição com repetição espaçada e trilha de progressão](docs/specs/005-licao-trilha/spec.md) | 0 de 49 ([tarefas](docs/specs/005-licao-trilha/tasks.md)) | Tarefas aprovadas |
| [006: XP, meta diária e sequência](docs/specs/006-xp-meta-sequencia/spec.md) | 0 de 45 ([tarefas](docs/specs/006-xp-meta-sequencia/tasks.md)) | Tarefas aprovadas |
| [007: Evolução mínima](docs/specs/007-evolucao/spec.md) | 0 de 26 ([tarefas](docs/specs/007-evolucao/tasks.md)) | Tarefas aprovadas |

As specs 008 a 016 pertencem ao final acadêmico e seguem em especificação; o índice completo está em [`docs/specs/`](docs/specs/README.md).
<!-- progresso:fim -->

## Estrutura

```text
.
├── .agents/
│   └── AGENTS.md            # instruções canônicas para qualquer agente
├── AGENTS.md                # ponteiro → .agents/AGENTS.md
├── CLAUDE.md                # ponteiro → .agents/AGENTS.md
└── docs/
    ├── constitution.md      # princípios estáveis do projeto
    ├── research.md          # decisões técnicas (DTEC)
    ├── arquitetura/         # arquitetura vigente e referência pós-acadêmica
    ├── base-specs/          # regras, telas e orientação técnica globais, base para as specs
    ├── produto/
    │   ├── visao.md         # diferencial, escopo, decisões de produto e questões
    │   ├── backlog.md       # funcionalidades candidatas (F-01 a F-16) e recorte por estágio
    │   ├── pendencias.md    # decisões em aberto, opções e impactos
    │   ├── exigencias_po.md # exigências do PO (EX-xx) e onde estão no backlog
    │   └── pauta-po.md      # itens em discussão com o PO
    ├── specs/               # uma pasta por funcionalidade: NNN-nome-curto/
    ├── skills/              # guias por tarefa, independentes de ferramenta
    ├── prompts/             # registro de todas as sessões com agentes
    └── sdd_guidelines/      # material SDD da disciplina (somente leitura)
```

O código da aplicação está em `backend/` e `frontend/`, e o `compose.yaml` da raiz sobe o ambiente completo. A estrutura detalhada está em [`.agents/AGENTS.md`](.agents/AGENTS.md#mapa-do-repositório).

## Fluxo de trabalho

```text
backlog -> spec -> revisão -> plano -> revisão -> tarefas -> revisão -> implementação -> convergência
```

Cada seta que passa por "revisão" é um portão humano: nenhum agente avança sem aprovação da equipe. Toda sessão com agente é registrada em `docs/prompts/`.
