# Plataforma de estudos gamificada

Plataforma web que funde **repetição espaçada** com uma **trilha visual de progressão**. O estudante organiza os estudos em matérias, guarda nelas suas fontes e cria flashcards à mão ou pede à IA que os gere a partir das fontes, com referência ao trecho de origem. Os cartões são respondidos numa trilha unificada de lições montadas pelo algoritmo FSRS, com XP, meta diária e sequência. No final acadêmico, cada matéria ganha um chat que responde **apenas** com base nas fontes, com citações.

Projeto da disciplina de IA do curso de Sistemas de Informação, desenvolvido com **Spec-Driven Development (SDD)**.

> **Estado (12/10/2026):** produto e arquitetura alinhados em três estágios: MVP (local), final acadêmico (publicado) e referência pós-acadêmica (documentada). A arquitetura foi aprovada em 12/10/2026; o novo recorte do MVP está em [pauta com o professor](docs/produto/pauta-po.md). Próximos passos: esquema inicial do banco em DBML e specs. A criação de código está liberada, mas ainda não há código.

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

O código da aplicação e a orquestração Docker serão adicionados conforme o primeiro plano aprovado.

## Fluxo de trabalho

```text
backlog -> spec -> revisão -> plano -> revisão -> tarefas -> revisão -> implementação -> convergência
```

Cada seta que passa por "revisão" é um portão humano: nenhum agente avança sem aprovação da equipe. Toda sessão com agente é registrada em `docs/prompts/`.
