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

Cada spec pertence a um único estágio. Os incrementos do final acadêmico de uma funcionalidade do MVP têm pasta própria e citam a spec do MVP que ampliam. A numeração segue a ordem de execução do [backlog](../produto/backlog.md#ordem): primeiro o MVP, depois o final acadêmico.

### MVP

| Pasta | Funcionalidade | Status |
|---|---|---|
| [001-conta-acesso](001-conta-acesso/README.md) | F-01: conta, sessão, isolamento e preferências | Implementando |
| [002-materias-fontes](002-materias-fontes/README.md) | F-02 e F-03: matérias, envio e processamento de fontes | Convergida |
| [003-cartoes-manuais](003-cartoes-manuais/README.md) | F-04: cartões criados e gerenciados pelo estudante | Tarefas aprovadas |
| [004-geracao-cartoes](004-geracao-cartoes/README.md) | F-04: geração por IA, revisão dos gerados, "Gerar mais" (EX-02, EX-03) | Tarefas aprovadas |
| [005-licao-trilha](005-licao-trilha/README.md) | F-05 e F-07: lição com FSRS e trilha | Tarefas aprovadas |
| [006-xp-meta-sequencia](006-xp-meta-sequencia/README.md) | F-09 e F-10: XP, meta diária e sequência | Tarefas aprovadas |
| [007-evolucao](007-evolucao/README.md) | F-12 (parte): evolução mínima | Tarefas aprovadas |

As specs do MVP são implementadas em sequência (001 → 002 → 003 → 004 → 005 → 006 → 007), uma de cada vez, por Artur Lins com o agente (decisão de 14/10/2026). A proposta de divisão entre duas pessoas, com ondas e pontos de sincronização, foi descontinuada e fica em [`divisao-implementacao-mvp.md`](divisao-implementacao-mvp.md) como histórico.

### Final acadêmico

| Pasta | Funcionalidade | Status |
|---|---|---|
| [008-recuperacao-senha](008-recuperacao-senha/README.md) | F-01 (incremento): recuperação de senha por e-mail | Especificando |
| [009-formatos-fontes](009-formatos-fontes/README.md) | F-02 (incremento): SRT, VTT, DOCX e envio múltiplo | Especificando |
| [010-geracao-materia](010-geracao-materia/README.md) | F-04 (incremento): geração para a matéria inteira e quantidade proporcional | Especificando |
| [011-cartao-imagem](011-cartao-imagem/README.md) | F-04 (incremento): cartão com imagem | Especificando |
| [012-filtro-dominio-materia](012-filtro-dominio-materia/README.md) | F-07 (incremento): filtro da lição e domínio por matéria | Especificando |
| [013-evolucao-completa](013-evolucao-completa/README.md) | F-12 (incremento): painel de evolução completo | Especificando |
| [014-chat-fontes](014-chat-fontes/README.md) | F-06 e F-03 (indexação): chat com as fontes | Especificando |
| [015-tira-duvidas-cartao](015-tira-duvidas-cartao/README.md) | F-16: tira-dúvidas a partir de um cartão (EX-04) | Especificando |
| [016-painel-administrativo](016-painel-administrativo/README.md) | F-17: painel administrativo simples | Especificando |
