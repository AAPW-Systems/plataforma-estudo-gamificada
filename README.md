# Plataforma de estudos gamificada

Plataforma web em que o estudante envia seus materiais de estudo e a IA os transforma em flashcards rastreáveis até o trecho de origem. A revisão segue repetição espaçada (inspiração: Anki), e o ritmo de estudo é ditado por mecânicas de jogo: XP, sequência diária e uma rota de progressão (inspiração: Duolingo). Um chat responde a perguntas **apenas** com base nos materiais enviados, com citações.

Projeto da disciplina de IA do curso de Sistemas de Informação, desenvolvido com **Spec-Driven Development (SDD)**.

> **Estado:** estruturação concluída. O recorte do MVP, a stack e o esquema do banco serão definidos no brainstorming aprofundado. Ainda não há código.

## Por onde começar

| Quero… | Leia |
|---|---|
| Entender o produto | [`docs/produto/visao.md`](docs/produto/visao.md) |
| Ver as funcionalidades planejadas | [`docs/produto/backlog.md`](docs/produto/backlog.md) |
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
    │   ├── visao.md         # escopo da plataforma completa e questões abertas
    │   └── backlog.md       # funcionalidades candidatas (F-01 a F-13)
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
