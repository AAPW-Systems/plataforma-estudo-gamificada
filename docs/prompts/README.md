# Registro de prompts

Todas as sessões com agentes de programação que criem ou alterem arquivos são registradas aqui (Princípio VII da [constituição](../constitution.md)). O objetivo, conforme a seção 11 da [apostila](../sdd_guidelines/apostila/apostila_sdd_para_projetos.md), é permitir que outra pessoa entenda o que foi pedido, com qual contexto, o que foi aceito e como o grupo verificou o resultado.

## Convenção

- **Um arquivo por sessão**, nomeado `AAAA-MM-DD-tema-curto.md` (ex.: `2026-09-29-estruturacao-projeto.md`).
- Se o nome já existir, acrescente um sufixo: `-2`, `-3`.
- O tema é em kebab-case, sem acentos. Quando a sessão tratar de uma funcionalidade, use o nome da pasta da spec (ex.: `2026-10-02-001-envio-materiais-spec.md`).
- Os prompts são copiados **literalmente**, na ordem, incluindo as respostas a perguntas de esclarecimento do agente.
- Nunca registre segredos ou dados pessoais de terceiros: substitua por `[REMOVIDO]`.

## Modelo

````markdown
# [Tema da sessão]

**Data:** AAAA-MM-DD
**Autor:** [pessoa que conduziu a sessão]
**Agente e modelo:** [ferramenta e modelo, ex.: Claude Code / claude-opus-5-5]
**Etapa SDD:** [estruturação | especificar | esclarecer | revisar | pesquisar | planejar | tarefas | implementar | convergir]
**Funcionalidade:** [NNN-nome-curto ou "projeto"]

## Contexto fornecido

- [arquivos, links ou artefatos entregues ao agente]

## Prompts

### Prompt 1

```text
[texto literal]
```

### Resposta a esclarecimento 1

```text
[pergunta do agente, resumida] -> [resposta literal da pessoa]
```

## Saída aceita

| Artefato | Ação |
|---|---|
| `caminho/arquivo` | criado / alterado / removido |

## Alterações humanas

[O que a equipe mudou na saída do agente, ou "pendente de revisão".]

## Verificação

[Como o resultado foi conferido: leitura, checklist, testes executados e seus resultados.]

## Pendências

- [itens que ficaram para depois]
````

## Índice

Retomada mais recente, a partir da T027: [prompt para o próximo agente](2026-10-13-001-conta-acesso-retomada-2.md).

Retomada anterior após a pausa de 13/10/2026: [prompt para o próximo agente](2026-10-13-001-conta-acesso-retomada.md).

| Data | Sessão | Etapa | Autor |
|---|---|---|---|
| 2026-09-29 | [Estruturação do projeto](2026-09-29-estruturacao-projeto.md) | Estruturação | Artur Lins |
| 2026-09-29 | [Brainstorming aprofundado](2026-09-29-brainstorming-aprofundado.md) | Esclarecer | Artur Lins |
| 2026-09-29 | [Diretrizes sobre terceiros e exigências do PO](2026-09-29-diretrizes-terceiros-exigencias-po.md) | Estruturação | Artur Lins |
| 2026-09-29 | [Diretrizes de git e testes](2026-09-29-diretrizes-git-testes.md) | Estruturação | Artur Lins |
| 2026-10-12 | [Alinhamento do produto e da arquitetura](2026-10-12-alinhamento-produto-arquitetura.md) | Esclarecer | Artur Lins |
| 2026-10-12 | [Esquema inicial do banco e FSRS soberano](2026-10-12-esquema-inicial-banco.md) | Esclarecer | Artur Lins |
| 2026-10-12 | [Specs das funcionalidades do MVP e do final acadêmico](2026-10-12-specs-funcionalidades.md) | Especificar | Artur Lins |
| 2026-10-12 | [Esclarecimento das specs do MVP](2026-10-12-esclarecimento-specs-mvp.md) | Esclarecer | Artur Lins |
| 2026-10-12 | [Plano da spec 001 e estrutura base do repositório](2026-10-12-001-conta-acesso-plano.md) | Planejar | Artur Lins |
| 2026-10-13 | [Plano, tarefas e rastreabilidade da spec 002](2026-10-13-002-materias-fontes-plano.md) | Planejar | Artur Lins |
| 2026-10-13 | [Plano, tarefas e rastreabilidade da spec 003](2026-10-13-003-cartoes-manuais-plano.md) | Planejar | Artur Lins |
| 2026-10-13 | [Plano, tarefas e rastreabilidade da spec 004](2026-10-13-004-geracao-cartoes-plano.md) | Planejar | Artur Lins |
| 2026-10-13 | [Plano, tarefas e rastreabilidade da spec 005](2026-10-13-005-licao-trilha-plano.md) | Planejar | Artur Lins |
| 2026-10-13 | [Plano, tarefas e rastreabilidade da spec 006](2026-10-13-006-xp-meta-sequencia-plano.md) | Planejar | Artur Lins |
| 2026-10-13 | [Plano, tarefas e rastreabilidade da spec 007](2026-10-13-007-evolucao-plano.md) | Planejar | Artur Lins |
| 2026-10-13 | [Implementação da spec 001 e estrutura base](2026-10-13-001-conta-acesso-implementacao.md) | Implementar | Artur Lins |
| 2026-10-13 | [Divisão da implementação do MVP](2026-10-13-divisao-implementacao-mvp.md) | Implementar | Artur Lins |
| 2026-10-13 | [Continuação da implementação da spec 001 até S1](2026-10-13-001-conta-acesso-implementacao-2.md) | Implementar | A confirmar |
| 2026-10-13 | [Retomada da spec 001 a partir da T024](2026-10-13-001-conta-acesso-implementacao-3.md) | Implementar | A confirmar |
| 2026-10-13 | [Conversão dos prompts de retomada da spec 001](2026-10-13-001-conta-acesso-retomadas-markdown.md) | Implementar |  |
| 2026-10-13 | [Revisão do prompt de retomada da spec 001](2026-10-13-001-conta-acesso-retomada-revisao.md) | Implementar |  |
| 2026-10-13 | [Retomada da spec 001 a partir da T027](2026-10-13-001-conta-acesso-implementacao-4.md) | Implementar | A confirmar |
| 2026-10-14 | [Implementação da spec 002 (matérias e fontes)](2026-10-14-002-materias-fontes-implementacao.md) | Implementar | Artur Lins |
