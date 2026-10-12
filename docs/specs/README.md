# Specs das funcionalidades

Uma pasta por funcionalidade, no formato definido em [`../sdd_guidelines/00_COMECE_AQUI.md`](../sdd_guidelines/00_COMECE_AQUI.md). As guidelines usam `specs/` na raiz; este projeto adota `docs/specs/` para concentrar toda a documentação em `docs/`. O conteúdo e a estrutura interna seguem as guidelines sem alteração.

## Estrutura de uma funcionalidade

```text
docs/specs/NNN-nome-curto/
├── README.md                 # F-xx de origem, status atual e ordem de leitura
├── spec.md                   # núcleo: o quê e por quê
├── plan.md                   # núcleo: como
├── tasks.md                  # núcleo: em que ordem
├── research.md               # decisões técnicas com alternativas (se houver)
├── data-model.md             # entidades persistidas (se houver)
├── quickstart.md             # validação local do incremento
├── traceability.md           # requisito ↔ cenário ↔ teste ↔ tarefa
├── checklists/
│   └── requirements.md       # revisão da spec antes do plano
└── contracts/
    └── openapi.yaml          # interface exposta ou consumida (se houver)
```

`spec.md`, `plan.md` e `tasks.md` são obrigatórios. Os demais só entram quando têm uso. Nada de arquivo vazio: registre "não aplicável" com a justificativa.

## Como criar uma pasta

1. Escolha a funcionalidade `F-xx` no [backlog](../produto/backlog.md), conforme o recorte aprovado. Parta das regras da [base de especificação](../base-specs/spec.md) citadas na coluna "Origem na base".
2. Use o próximo número livre com 3 dígitos (`001`, `002`, …) e um nome curto em kebab-case, sem acentos (ex.: `001-envio-materiais`).
3. Copie os modelos de [`../sdd_guidelines/modelos/`](../sdd_guidelines/modelos/) conforme a etapa. Não copie tudo de uma vez: cada arquivo nasce na sua etapa.
4. Crie o `README.md` da pasta com: `F-xx` de origem, status e ordem de leitura.
5. Atualize a coluna "Spec" do backlog com o link da pasta.
6. Siga o [guia do fluxo SDD](../skills/fluxo-sdd.md).

## Status de uma funcionalidade

Mantido no `README.md` de cada pasta e refletido no índice abaixo.

`Especificando` → `Spec aprovada` → `Planejando` → `Plano aprovado` → `Tarefas aprovadas` → `Implementando` → `Convergida`

## Índice

| Pasta | Funcionalidade | Status |
|---|---|---|
| — | Nenhuma funcionalidade especificada ainda. Antes da primeira, vem o esquema inicial do banco em DBML (QA-21). A ordem está no [backlog](../produto/backlog.md#ordem). | — |
