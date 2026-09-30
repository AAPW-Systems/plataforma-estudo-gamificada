# Backlog de funcionalidades

**Data:** 29/09/2026 (atualizado no brainstorming aprofundado e com as exigências do PO)
**Status:** recorte do MVP proposto por Artur Lins, pendente de validação com o professor ([VAL-01](pendencias.md#val-01-validação-do-mvp-com-o-professor))
**Base:** [visão do produto](visao.md), [constituição](../constitution.md), [exigências do PO](exigencias_po.md) e [pendências](pendencias.md)

Cada linha é uma **funcionalidade candidata**, ou seja, uma jornada que pode virar uma pasta `docs/specs/NNN-nome-curto/`. O identificador `F-xx` é estável e serve para referência no planejamento. O número `NNN` da pasta só é atribuído quando a spec é criada, na ordem de execução (ver [`../specs/README.md`](../specs/README.md)).

A coluna "Origem no init" preserva a rastreabilidade com o brainstorming inicial: ao escrever a spec, os requisitos, casos de borda e regras citados devem ser revisados e reaproveitados, e não reescritos do zero.

## Funcionalidades candidatas

| ID | Funcionalidade | Pilar | MVP | Origem no init | Questões que bloqueiam | Spec |
|---|---|---|---|---|---|---|
| F-01 | Conta e isolamento de dados | Base | Sim | HU-01, RF-01, RN-01, CB-11 | — (QA-25 só para o deploy final) | — |
| F-02 | Envio e gestão de materiais (inclui matérias) | Materiais | Sim | HU-02, HU-10, RF-02, RF-03, RN-02, RN-09, CB-01 a CB-03, CB-12 | — | — |
| F-03 | Processamento e indexação de materiais | Materiais | Sim | HU-03, RF-04, RN-03, CB-04, CB-06, CB-14 | QA-04, QA-22 | — |
| F-04 | Geração de flashcards por IA com fontes rastreáveis, e cartões manuais. Inclui gerar novos cartões sob demanda (EX-02), explicação curta com citação em cada cartão gerado (EX-03) e nível de dificuldade (EX-05) | Flashcards | Sim | HU-07, HU-14, RF-08, RF-15, RN-04, RN-11, RN-13, CB-05, CB-16 | QA-04, QA-22, QA-23, QA-26 | — |
| F-05 | Revisão com repetição espaçada numa rotina diária unificada. Ao errar, exibe a explicação curta do cartão (EX-03) | Flashcards | Sim | Nova (fora do escopo no init) | QA-23, QA-24 | — |
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
| F-16 | Tira-dúvidas a partir de um flashcard: durante a revisão, o estudante abre um chat com o cartão como contexto e pede explicações adicionais, com referência (EX-04). Na versão final, pode acionar uma consulta externa (EX-01). Caminho opcional: não faz parte do fluxo principal | Chat | **Parcial**: consulta aos materiais no MVP; consulta externa só na versão final | Nova (exigências do PO); aplica RN-11 e CB-14 | QA-16, QA-22; QA-27 para a consulta externa | — |

## Exigências do PO

As exigências de [`exigencias_po.md`](exigencias_po.md) foram incorporadas ao backlog em 29/09/2026. A spec de cada funcionalidade de destino cita o `EX-xx` e o cobre com requisitos ou com uma questão `Q-xxx`.

| Exigência | Resumo | Destino | MVP | Observações |
|---|---|---|---|---|
| EX-01 | Pesquisa externa sobre o assunto | F-16 (incremento) | Não, só na versão final | Acionada pelo estudante no tira-dúvidas de um cartão. Exige o ajuste do Princípio I da constituição (v0.3) e as regras de [QA-27](pendencias.md#qa-27-regras-da-consulta-externa) |
| EX-02 | Gerar novos flashcards (incrementar) | F-04 | Sim | O estudante pede mais cartões de um material ou matéria já processados. Os novos cartões não repetem os existentes e seguem a mesma verificação |
| EX-03 | Explicação curta do motivo do erro | F-04 e F-05 | Sim | F-04 gera a explicação com citação do trecho; F-05 a exibe quando o estudante marca "Errei". A regra para cartões criados pelo usuário fica na spec de F-04 |
| EX-04 | Pedir explicações adicionais, com referência | F-16 | Sim, restrito aos materiais | Reaproveita a busca e as citações de F-06 |
| EX-05 | Níveis de dificuldade (fácil, médio, difícil) | F-04 | Sim, conforme [QA-26](pendencias.md#qa-26-níveis-de-dificuldade) | O significado dos níveis está em aberto. Não confundir com os botões de autoavaliação da revisão |

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
- **Jornada (caminho principal):** enviar materiais, receber flashcards verificados, cumprir a rotina diária gamificada e tirar dúvidas no chat. O tira-dúvidas a partir de um cartão (F-16) é um caminho opcional da revisão e não altera o caminho principal.
- **Hipótese de valor:** ver a [visão](visao.md#diferencial).

### Capacidades

| Capacidade | Funcionalidades | Motivo |
|---|---|---|
| 1. Materiais → flashcards verificados | F-01, F-02, F-03, F-04 | Base de toda a jornada e IA no fluxo principal |
| 2. Rotina diária gamificada | F-05, F-09, F-10 e parte de F-12 (dias estudados, tempo dedicado, cartões dominados, XP e sequência) | O diferencial do produto |
| 3. Chat com os materiais | F-06 e F-16 restrito aos materiais | Demonstração direta do RAG exigido pela disciplina; reaproveita a indexação de F-03. F-16 atende EX-04 com o mesmo mecanismo |

### Ordem

```text
F-01 -> F-02/F-03 -> em paralelo: [F-04]  e  [F-05 + F-09 + F-10 + F-12 parcial] -> F-06 -> F-16 (materiais)
```

A criação manual de cartões (parte de F-04) permite construir e testar a revisão gamificada **sem esperar o pipeline de IA**. Isso viabiliza as duas frentes paralelas com cinco pessoas.

Se algo precisar sair por prazo, o primeiro corte é o painel de evolução, reduzido a dias estudados e XP. O segundo é F-16, por estar fora do caminho principal; nesse caso, EX-04 precisa ser renegociada com o professor.

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
| F-16 | Consulta externa acionada pelo estudante (EX-01), conforme [QA-27](pendencias.md#qa-27-regras-da-consulta-externa) |
| F-01 | Sessão no padrão BFF antes do deploy ([QA-25](pendencias.md#qa-25-sessão-no-navegador-migração-para-bff)) |
