# Backlog de funcionalidades

**Data:** 29/09/2026 (atualizado no brainstorming aprofundado)
**Status:** recorte do MVP proposto por Artur Lins, pendente de validação com o professor ([VAL-01](pendencias.md#val-01-validação-do-mvp-com-o-professor))
**Base:** [visão do produto](visao.md), [constituição](../constitution.md) e [pendências](pendencias.md)

Cada linha é uma **funcionalidade candidata**, ou seja, uma jornada que pode virar uma pasta `docs/specs/NNN-nome-curto/`. O identificador `F-xx` é estável e serve para referência no planejamento. O número `NNN` da pasta só é atribuído quando a spec é criada, na ordem de execução (ver [`../specs/README.md`](../specs/README.md)).

A coluna "Origem no init" preserva a rastreabilidade com o brainstorming inicial: ao escrever a spec, os requisitos, casos de borda e regras citados devem ser revisados e reaproveitados, e não reescritos do zero.

## Funcionalidades candidatas

| ID | Funcionalidade | Pilar | MVP | Origem no init | Questões que bloqueiam | Spec |
|---|---|---|---|---|---|---|
| F-01 | Conta e isolamento de dados | Base | Sim | HU-01, RF-01, RN-01, CB-11 | — (QA-25 só para o deploy final) | — |
| F-02 | Envio e gestão de materiais (inclui matérias) | Materiais | Sim | HU-02, HU-10, RF-02, RF-03, RN-02, RN-09, CB-01 a CB-03, CB-12 | — | — |
| F-03 | Processamento e indexação de materiais | Materiais | Sim | HU-03, RF-04, RN-03, CB-04, CB-06, CB-14 | QA-04, QA-22 | — |
| F-04 | Geração de flashcards por IA com fontes rastreáveis, e cartões manuais | Flashcards | Sim | HU-07, HU-14, RF-08, RF-15, RN-04, RN-11, RN-13, CB-05, CB-16 | QA-04, QA-22, QA-23 | — |
| F-05 | Revisão com repetição espaçada numa rotina diária unificada | Flashcards | Sim | Nova (fora do escopo no init) | QA-23, QA-24 | — |
| F-06 | Chat com os materiais (RAG com citações) | Chat | Sim | Nova; aplica RN-11 e CB-14 | QA-16, QA-22 | — |
| F-07 | Rota de progressão | Rota | Não | HU-04, HU-11, RF-05, RF-10, RN-07, CB-09 | QA-06, QA-15 | — |
| F-08 | Questões de escolha única com correção | Complemento | **Absorvida** | HU-05, HU-06, RF-06, RF-07, RN-05, RN-06, CB-07, CB-08 | — | Absorvida pelos flashcards em 29/09/2026 (QA-17). RN-05 e RN-06 do init continuam aplicáveis à revisão |
| F-09 | XP e meta diária | Ritmo | Sim | HU-06, RF-09, RN-06 | QA-24 | — |
| F-10 | Sequência diária (*streak*) | Ritmo | Sim | Nova (fora do escopo no init); aplica RN-10 e CB-10 | QA-24 | — |
| F-11 | Conquistas | Ritmo | Não | HU-09, RF-11, RN-08 | QA-08 | — |
| F-12 | Painel de evolução | Evolução | Parcial | HU-08, RF-12, RN-07, RN-10 | QA-09 (períodos e filtros) | — |
| F-13 | Cobertura de assuntos e lacunas de material | Materiais | Não | HU-13, RF-14, RN-12, CB-15 | QA-04, QA-06 | — |
| F-14 | Plano de estudos a partir de um edital | Rota | Não | Nova (brainstorming aprofundado); relaciona-se com RN-12 | A abrir | — |
| F-15 | Criar flashcard a partir de uma resposta do chat | Chat | Não | Nova (brainstorming aprofundado) | A abrir | — |

## Requisitos transversais

Os itens abaixo não são funcionalidades isoladas. Eles se aplicam a todas as specs e estão cobertos pela [constituição](../constitution.md).

| Tema | Origem no init | Onde está |
|---|---|---|
| API documentada por OpenAPI | HU-12, RF-13 | Princípio V |
| Acessibilidade e responsividade | RQ-03, CS-05, CB-13 | Princípio V e [`../skills/padroes-interface.md`](../skills/padroes-interface.md) |
| Segurança, isolamento e logs | RQ-01, RQ-06 | Princípio II |
| Consistência sob falha e concorrência | RQ-02, CS-02 | Princípio IV |
| Desempenho, capacidade e recuperação | RQ-04, RQ-08, QA-11 | A definir no primeiro plano ([QA-11](pendencias.md#qa-11-vps-e-operação-do-deploy)) |
| Execução em contêineres | — | Restrições do projeto |
| Princípio de gamificação | — | [Visão](visao.md#princípio-de-gamificação) |

## Recorte do MVP

**Decidido em:** 29/09/2026 por Artur Lins ([registro](../prompts/2026-09-29-brainstorming-aprofundado.md)). **Validação com o professor:** pendente.
**Prazo:** 3 semanas a partir de 29/09/2026. Pode rodar localmente.

As guidelines limitam o MVP a uma persona, uma jornada principal e até três capacidades essenciais (`sdd_guidelines/detalhes_projeto.md`, "Acordo do MVP com o PO").

- **Persona:** estudante individual com materiais próprios de várias matérias.
- **Jornada:** enviar materiais, receber flashcards verificados, cumprir a rotina diária gamificada e tirar dúvidas no chat.
- **Hipótese de valor:** ver a [visão](visao.md#diferencial).

### Capacidades

| Capacidade | Funcionalidades | Motivo |
|---|---|---|
| 1. Materiais → flashcards verificados | F-01, F-02, F-03, F-04 | Base de toda a jornada e IA no fluxo principal |
| 2. Rotina diária gamificada | F-05, F-09, F-10 e parte de F-12 (dias estudados, tempo dedicado, cartões dominados, XP e sequência) | O diferencial do produto |
| 3. Chat com os materiais | F-06 | Demonstração direta do RAG exigido pela disciplina; reaproveita a indexação de F-03 |

### Ordem

```text
F-01 -> F-02/F-03 -> em paralelo: [F-04]  e  [F-05 + F-09 + F-10 + F-12 parcial] -> F-06
```

A criação manual de cartões (parte de F-04) permite construir e testar a revisão gamificada **sem esperar o pipeline de IA**. Isso viabiliza as duas frentes paralelas com quatro pessoas.

Se algo precisar sair por prazo, o primeiro corte é o painel de evolução, reduzido a dias estudados e XP.

### Fora do MVP

| Item | Motivo |
|---|---|
| F-07 Rota de progressão | A rotina diária entrega o ritmo no MVP; a rota ganha sentido com o edital no projeto final |
| F-08 Questões de escolha única | Absorvida pelos flashcards |
| F-11 Conquistas | Não é essencial à hipótese de valor |
| F-12, restante | Históricos e filtros além do painel mínimo |
| F-13 e F-14 Edital, plano e lacunas | Diferencial do projeto final |
| F-15 Flashcard a partir do chat | Depende de F-04 e F-06 estáveis |

### Incrementos pós-MVP de funcionalidades do MVP

| Funcionalidade | Incremento |
|---|---|
| F-02 | Formatos DOCX, PPTX, SRT e VTT; envio em lote |
| F-03 | OCR de PDF digitalizado (ferramenta a definir, ex.: Docling) |
| F-05 | Desfazer revisão |
| F-10 | Congelamento da sequência |
| F-01 | Sessão no padrão BFF antes do deploy ([QA-25](pendencias.md#qa-25-sessão-no-navegador-migração-para-bff)) |
