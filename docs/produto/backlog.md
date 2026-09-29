# Backlog de funcionalidades

**Data:** 29/09/2026
**Status:** candidatas, sem priorização aprovada
**Base:** [visão do produto](visao.md) e [constituição](../constitution.md)

Cada linha é uma **funcionalidade candidata**, ou seja, uma jornada que pode virar uma pasta `docs/specs/NNN-nome-curto/`. O identificador `F-xx` é estável e serve para referência no planejamento. O número `NNN` da pasta só é atribuído quando a spec é criada, na ordem de execução (ver [`../specs/README.md`](../specs/README.md)).

A coluna "Origem no init" preserva a rastreabilidade com o brainstorming inicial: ao escrever a spec, os requisitos, casos de borda e regras citados devem ser revisados e reaproveitados, e não reescritos do zero.

## Funcionalidades candidatas

| ID | Funcionalidade | Pilar | Origem no init | Questões que bloqueiam | Spec |
|---|---|---|---|---|---|
| F-01 | Conta e isolamento de dados | Base | HU-01, RF-01, RN-01, CB-11 | QA-02 | — |
| F-02 | Envio e gestão de materiais | Materiais | HU-02, HU-10, RF-02, RF-03, RN-02, RN-09, CB-01 a CB-03, CB-12 | QA-03, QA-05 | — |
| F-03 | Processamento e indexação de materiais | Materiais | HU-03, RF-04, RN-03, CB-04, CB-06, CB-14 | QA-04, QA-22 | — |
| F-04 | Geração de flashcards por IA com fontes rastreáveis | Flashcards | HU-07, HU-14, RF-08, RF-15, RN-04, RN-11, RN-13, CB-05, CB-16 | QA-04, QA-10, QA-20 | — |
| F-05 | Revisão com repetição espaçada | Flashcards | Nova (fora do escopo no init) | QA-13, QA-20 | — |
| F-06 | Chat com os materiais (RAG com citações) | Chat | Nova; aplica RN-11 e CB-14 | QA-16, QA-22 | — |
| F-07 | Rota de progressão | Rota | HU-04, HU-11, RF-05, RF-10, RN-07, CB-09 | QA-06, QA-15 | — |
| F-08 | Questões de escolha única com correção | Complemento | HU-05, HU-06, RF-06, RF-07, RN-05, RN-06, CB-07, CB-08 | QA-07, QA-17 | — |
| F-09 | XP e meta diária | Ritmo | HU-06, RF-09, RN-06 | QA-07, QA-14 | — |
| F-10 | Sequência diária (*streak*) | Ritmo | Nova (fora do escopo no init); aplica RN-10 e CB-10 | QA-09, QA-14 | — |
| F-11 | Conquistas | Ritmo | HU-09, RF-11, RN-08 | QA-08 | — |
| F-12 | Painel de evolução | Evolução | HU-08, RF-12, RN-07, RN-10 | QA-06, QA-09 | — |
| F-13 | Cobertura de assuntos e lacunas de material | Materiais | HU-13, RF-14, RN-12, CB-15 | QA-04, QA-06 | — |

## Requisitos transversais

Os itens abaixo não são funcionalidades isoladas. Eles se aplicam a todas as specs e estão cobertos pela [constituição](../constitution.md).

| Tema | Origem no init | Onde está |
|---|---|---|
| API documentada por OpenAPI | HU-12, RF-13 | Princípio V |
| Acessibilidade e responsividade | RQ-03, CS-05, CB-13 | Princípio V e [`../skills/padroes-interface.md`](../skills/padroes-interface.md) |
| Segurança, isolamento e logs | RQ-01, RQ-06 | Princípio II |
| Consistência sob falha e concorrência | RQ-02, CS-02 | Princípio IV |
| Desempenho, capacidade e recuperação | RQ-04, RQ-08, QA-11 | A definir no primeiro plano |
| Execução em contêineres | — | Restrições do projeto |

## Recorte do MVP

A definir no brainstorming aprofundado (QA-12). O recorte registra quais `F-xx` entram, a ordem e o motivo de cada exclusão.
