# Plataforma de estudos gamificada

Plataforma web em que o estudante envia seus materiais de estudo e a IA os transforma em flashcards rastreáveis até o trecho de origem. A revisão segue repetição espaçada, e o ritmo de estudo é ditado por mecânicas de jogo: XP, sequência diária e uma rota de progressão. Um chat responde a perguntas **apenas** com base nos materiais enviados, com citações.

Projeto da disciplina de IA do curso de Sistemas de Informação, desenvolvido com **Spec-Driven Development (SDD)**.

> **Estado:** brainstorming aprofundado concluído. O recorte do MVP está no backlog, pendente de validação com o professor. Framework do backend, stack de IA e esquema do banco ainda estão em aberto ([pendências](docs/produto/pendencias.md)). Ainda não há código.

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
| Ver o que está pendente de decisão | [`docs/produto/pendencias.md`](docs/produto/pendencias.md) |
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
    ├── produto/
    │   ├── visao.md         # diferencial, escopo, decisões de produto e questões
    │   ├── backlog.md       # funcionalidades candidatas (F-01 a F-16) e recorte do MVP
    │   ├── pendencias.md    # decisões em aberto, opções e impactos
    │   └── exigencias_po.md # exigências do PO (EX-xx) e onde estão no backlog
    ├── specs/               # uma pasta por funcionalidade: NNN-nome-curto/
    ├── skills/              # guias por tarefa, independentes de ferramenta
    ├── prompts/             # registro de todas as sessões com agentes
    ├── init/                # brainstorming inicial (histórico, somente leitura)
    └── sdd_guidelines/      # material SDD da disciplina (somente leitura)
```

O código da aplicação e a orquestração Docker serão adicionados conforme o primeiro plano aprovado.

## Fluxo de trabalho

```text
backlog -> spec -> revisão -> plano -> revisão -> tarefas -> revisão -> implementação -> convergência
```

Cada seta que passa por "revisão" é um portão humano: nenhum agente avança sem aprovação da equipe. Toda sessão com agente é registrada em `docs/prompts/`.
