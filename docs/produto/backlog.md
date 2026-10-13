# Backlog de funcionalidades

**Data:** 29/09/2026; atualizado em 12/10/2026 ([registro](../prompts/2026-10-12-alinhamento-produto-arquitetura.md)) com os três estágios do produto e o novo recorte do MVP
**Status:** recorte do MVP aprovado em 12/10/2026 ([PO-03](pauta-po.md#po-03-novo-recorte-do-mvp), [VAL-01](pendencias.md#val-01-validação-do-mvp-com-o-professor)). Seguem com o PO apenas as exigências EX-01 e EX-05 ([pauta](pauta-po.md))
**Base:** [visão do produto](visao.md), [constituição](../constitution.md), [exigências do PO](exigencias_po.md), [pendências](pendencias.md) e [base de especificação](../base-specs/spec.md)

Cada linha é uma **funcionalidade candidata**, ou seja, uma jornada que pode virar uma pasta `docs/specs/NNN-nome-curto/`. O identificador `F-xx` é estável e serve para referência no planejamento. O número `NNN` da pasta só é atribuído quando a spec é criada, na ordem de execução (ver [`../specs/README.md`](../specs/README.md)).

A coluna "Origem na base" aponta para os IDs da [base de especificação](../base-specs/spec.md). Ao escrever a spec, esses requisitos, histórias, regras e casos de borda devem ser revisados e reaproveitados, e não reescritos do zero.

## Estágios

| Estágio | Prazo | Onde roda |
|---|---|---|
| **MVP** | Apresentação em 15/10, 20/10 ou 22/10/2026; meta da equipe: 15/10 (alternativa: 20/10) | Localmente |
| **Final** (final acadêmico) | Novembro de 2026 | VPS com HTTPS (deploy obrigatório) |
| **Referência** (pós-acadêmica) | — | Documentada, não implementada ([referência](../arquitetura/referencia-pos-academica.md)) |

## Funcionalidades candidatas

| ID | Funcionalidade | Pilar | Estágio | Origem na base | Questões que bloqueiam | Spec |
|---|---|---|---|---|---|---|
| F-01 | Conta, sessão e isolamento de dados; perfil e preferências | Base | MVP; recuperação de senha no Final | HU-01, RF-01, RF-02, RF-19, RN-01, RN-15 | — | [001](../specs/001-conta-acesso/README.md) (MVP); [008](../specs/008-recuperacao-senha/README.md) (Final) |
| F-02 | Matérias e envio e gestão de fontes (acervo da matéria, exclusão definitiva com escolha sobre os cartões) | Materiais | MVP; formatos SRT, VTT, DOCX e envio múltiplo no Final | HU-02, HU-12, HU-13, RF-03, RF-04, RF-20, RN-02, RN-14, RN-23, CB-04, CB-23 | — | [002](../specs/002-materias-fontes/README.md) (MVP); [009](../specs/009-formatos-fontes/README.md) (Final) |
| F-03 | Processamento das fontes: extração e trechos (MVP); indexação para busca híbrida (Final) | Materiais | MVP; indexação no Final | HU-03, RF-05, RF-06, RN-03, CB-16 | QA-04 | [002](../specs/002-materias-fontes/README.md) (MVP); [014](../specs/014-chat-fontes/README.md) (Final, indexação) |
| F-04 | Cartões: criação manual; geração por IA com evidência e explicação do erro (EX-03); revisão dos gerados (aceitar, editar, recusar, aceitar todos), resumo e "Gerar mais" (EX-02); cartão com imagem no Final | Flashcards | MVP; imagem no Final | HU-11, HU-14, HU-15, RF-11, RF-17, RF-22, RF-27, RN-04, RN-05, RN-08, RN-16, RN-22, CB-09, CB-14, CB-15, CB-26 | QA-04, QA-23 | [003](../specs/003-cartoes-manuais/README.md) e [004](../specs/004-geracao-cartoes/README.md) (MVP); [010](../specs/010-geracao-materia/README.md) e [011](../specs/011-cartao-imagem/README.md) (Final) |
| F-05 | Revisão com repetição espaçada (FSRS): lição, autoavaliação com quatro botões, explicação ao errar | Flashcards | MVP | HU-06, HU-07, HU-16, RF-21, RF-23, RN-10, RN-17, RN-20, RN-26, CB-22, CB-24, CB-28, CB-29, CB-30 | QA-24 | [005](../specs/005-licao-trilha/README.md) (MVP) |
| F-06 | Chat com as fontes da matéria (RAG com busca híbrida e citações) | Chat | **Final** | HU-18, RF-25, RN-24 | QA-16, QA-31 | [014](../specs/014-chat-fontes/README.md) (Final) |
| F-07 | Trilha de progressão: lições como nós (MVP); filtro e domínio por matéria (Final) | Trilha | **MVP**; filtro e domínio no Final | HU-04, RF-08, RF-28, RN-19, RN-26, CB-13, CB-30 | UI-05 | [005](../specs/005-licao-trilha/README.md) (MVP); [012](../specs/012-filtro-dominio-materia/README.md) (Final) |
| F-08 | Questões de escolha única com correção | Complemento | **Absorvida** | RN-07 e RF-09 (removidos) | — | Absorvida pelos flashcards em 29/09/2026 (QA-17) |
| F-09 | XP e meta diária | Ritmo | MVP | RF-12, RN-18, RN-21 | QA-24 | [006](../specs/006-xp-meta-sequencia/README.md) (MVP) |
| F-10 | Sequência diária (*streak*) | Ritmo | MVP; congelamento depois | HU-17, RF-24, RN-15, RN-21, CB-25 | QA-24 | [006](../specs/006-xp-meta-sequencia/README.md) (MVP) |
| F-11 | Conquistas | Ritmo | Não | HU-09, RF-14, RN-13 | QA-08 | — |
| F-12 | Painel de evolução | Evolução | MVP parcial; completo no Final | HU-08, RF-15, RN-25 | QA-09 (períodos e filtros) | [007](../specs/007-evolucao/README.md) (MVP); [013](../specs/013-evolucao-completa/README.md) (Final) |
| F-13 | Cobertura de assuntos e lacunas de material | Materiais | Não | HU-10, RF-07, RF-16, RN-06 | QA-04 | — |
| F-14 | Plano de estudos a partir de um edital | Trilha | Não | Nova; relaciona-se com RN-06 | A abrir | — |
| F-15 | Criar flashcard a partir de uma resposta do chat | Chat | Não | Nova | A abrir | — |
| F-16 | Tira-dúvidas a partir de um cartão: durante a lição, o estudante abre o chat com o cartão como contexto e pede explicações, com referência (EX-04). Caminho opcional, fora do fluxo principal | Chat | **Final**; consulta externa (EX-01) em pauta com o PO | HU-19, RF-26, RN-24 | QA-16, QA-31; [PO-02](pauta-po.md#po-02-pesquisa-externa-ex-01) | [015](../specs/015-tira-duvidas-cartao/README.md) (Final) |
| F-17 | Painel administrativo simples, com acesso restrito ao papel administrador (RN-27). Escopo definido na spec | Base | **Final** | HU-20, RF-29, RN-27 | QA-32 | [016](../specs/016-painel-administrativo/README.md) (Final) |

## Exigências do PO

As exigências de [`exigencias_po.md`](exigencias_po.md) foram incorporadas ao backlog em 29/09/2026 e revistas em 12/10/2026. A spec de cada funcionalidade de destino cita o `EX-xx` e o cobre com requisitos ou com uma questão `Q-xxx`.

| Exigência | Resumo | Destino | Estágio | Observações |
|---|---|---|---|---|
| EX-01 | Pesquisa externa sobre o assunto | F-16 (incremento) | Em pauta | A equipe considera incompatível com o Princípio I e propõe retirá-la ([PO-02](pauta-po.md#po-02-pesquisa-externa-ex-01)) |
| EX-02 | Gerar novos flashcards (incrementar) | F-04 | MVP | "Gerar mais" no resumo da revisão dos cartões gerados, sem repetir existentes nem recusados (RN-22) |
| EX-03 | Explicação curta do motivo do erro | F-04 e F-05 | MVP | Criada junto com o cartão gerado (RN-16) e exibida ao marcar "Errei" |
| EX-04 | Pedir explicações adicionais, com referência | F-16 | Final | Reaproveita a busca e as citações de F-06 |
| EX-05 | Níveis de dificuldade (fácil, médio, difícil) | F-05 / F-12 | Em pauta | A equipe considera a seleção por dificuldade incompatível com o FSRS e propõe exibir a dificuldade calculada pelo algoritmo ([PO-01](pauta-po.md#po-01-níveis-de-dificuldade-ex-05)) |

## Requisitos transversais

Os itens abaixo não são funcionalidades isoladas. Eles se aplicam a todas as specs e estão cobertos pela [constituição](../constitution.md) e pela [base de especificação](../base-specs/spec.md#9-requisitos-de-qualidade).

| Tema | Origem na base | Onde está |
|---|---|---|
| API documentada por OpenAPI | RF-18, RQ-08 | Princípio V |
| Acessibilidade e responsividade | RQ-06, CS-05 | Princípio V e [`../skills/padroes-interface.md`](../skills/padroes-interface.md) |
| Segurança, isolamento e logs | RQ-01 | Princípio II |
| Consistência sob falha e concorrência | RQ-02, RN-10 | Princípio IV |
| Custo operacional e deploy | RQ-09 | [Arquitetura](../arquitetura/README.md) e [QA-11](pendencias.md#qa-11-vps-e-operação-do-deploy) |
| Avaliação da IA | RQ-10 | Princípio V e [DTEC 011](../research.md#decisão-dtec-011-observabilidade-e-avaliação-da-ia) |
| Execução em contêineres | — | Restrições do projeto |
| Princípio de gamificação | — | [Visão](visao.md#princípio-de-gamificação) |

## Recorte do MVP

**Proposto em:** 29/09/2026; revisto em 12/10/2026 ([registro](../prompts/2026-10-12-alinhamento-produto-arquitetura.md)). **Validação com o professor:** aprovado em 12/10/2026 ([PO-03](pauta-po.md#po-03-novo-recorte-do-mvp)).
**Prazo:** a apresentação do MVP pode ser em 15/10, 20/10 ou 22/10/2026. A equipe mira 15/10, com 20/10 como alternativa (informado por Artur Lins em 12/10/2026). Roda localmente.

As guidelines limitam o MVP a uma persona, uma jornada principal e até três capacidades essenciais (`sdd_guidelines/detalhes_projeto.md`, "Acordo do MVP com o PO").

- **Persona:** estudante individual com fontes próprias de várias matérias.
- **Jornada:** criar matéria, enviar fonte, revisar os cartões gerados, fazer a lição do dia na trilha e manter a sequência.
- **Hipótese de valor:** ver a [visão](visao.md#diferencial).

### Capacidades

| Capacidade | Funcionalidades | Motivo |
|---|---|---|
| 1. Fontes em cartões revisados pelo estudante | F-01, F-02, F-03, F-04 | Base da jornada e IA no fluxo principal |
| 2. Repetição espaçada numa trilha unificada | F-05, F-07 (lições como nós, sem filtro) | O centro do produto: o FSRS decide o que revisar, e a trilha torna o progresso visível |
| 3. Gamificação | F-09, F-10 e parte de F-12 (dias estudados, XP, sequência, cartões dominados) | Constância: o diferencial do produto |

### Ordem

```text
F-01 -> F-02/F-03 -> em paralelo: [F-04]  e  [F-05 + F-07 + F-09 + F-10 + F-12 parcial]
```

A criação manual de cartões (parte de F-04) permite construir e testar a revisão e a trilha **sem esperar o pipeline de IA**. Isso viabiliza as duas frentes paralelas com cinco pessoas.

Se algo precisar sair por prazo, o primeiro corte é o painel de evolução, reduzido a XP e sequência. O segundo é a edição na revisão dos cartões gerados (mantendo aceitar e recusar).

### Final acadêmico

| Funcionalidade | Entrega |
|---|---|
| F-06 | Chat com as fontes da matéria: busca híbrida, reranking, citações, busca agêntica e avaliação contra a solução de referência |
| F-16 | Tira-dúvidas do cartão, restrito às fontes (EX-04) |
| F-02 | Formatos SRT, VTT e DOCX; envio de mais de um arquivo; novos limites definidos pela equipe |
| F-03 | Indexação (embeddings e índice textual) |
| F-04 | Cartão com imagem (manual, até 3 MB); avaliação da quantidade gerada em relação ao volume da fonte |
| F-07 | Filtro da lição por matéria e domínio por matéria |
| F-12 | Painel completo (tempo dedicado, por matéria) |
| F-01 | Recuperação de senha por e-mail |
| F-17 | Painel administrativo simples (escopo na spec, QA-32) |

### Fora dos estágios acadêmicos

| Item | Motivo |
|---|---|
| F-08 Questões de escolha única | Absorvida pelos flashcards |
| F-11 Conquistas | Não é essencial à hipótese de valor; critérios a redefinir (QA-08) |
| F-13 e F-14 Edital, plano e lacunas | Evolução do produto |
| F-15 Flashcard a partir do chat | Depende de F-04 e F-06 estáveis |
| OCR, XLSX e PPTX | Custo de VPS ([referência](../arquitetura/referencia-pos-academica.md)) |
| Desfazer revisão (F-05) e congelamento da sequência (F-10) | Incrementos posteriores |
