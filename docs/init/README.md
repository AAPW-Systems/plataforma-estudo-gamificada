# Brainstorming inicial (registro histórico)

**Status:** substituído, somente leitura
**Data original:** 25/09/2026
**Migrado em:** 29/09/2026 ([registro da sessão](../prompts/2026-09-29-estruturacao-projeto.md))

Esta pasta preserva o brainstorming inicial da equipe **sem alterações**, seguindo o modelo de spec ancorado das guidelines ("não reescreva o histórico"). O conteúdo foi redistribuído para o padrão SDD do projeto. **Não edite estes arquivos**: novas decisões vão para os destinos abaixo.

## Para onde foi cada parte

| Arquivo original | Conteúdo | Destino atual |
|---|---|---|
| `SKILL.md` | Princípios (fontes exclusivas, isolamento, consistência, MVC, nomenclatura) | [`../constitution.md`](../constitution.md) |
| `SKILL.md` | Padrões técnicos (textos, datas, validações, erros, OpenAPI, IA, gamificação) | [`../skills/padroes-implementacao.md`](../skills/padroes-implementacao.md) |
| `SKILL.md` | Tabela de configuração `[PREENCHER]` e comandos | Questões QA-01 e QA-18 em [`../produto/visao.md`](../produto/visao.md); comandos no `quickstart.md` de cada spec |
| `DESIGN.md` | Componentes, estados, validações, acessibilidade e responsividade | [`../skills/padroes-interface.md`](../skills/padroes-interface.md) |
| `DESIGN.md` | Tecnologia e identidade visual (React, tema claro, azul `#2563EB`) | Não adotados; questões QA-18 e QA-19 |
| `DESIGN.md` | Telas (Início, Materiais, Trilhas, Questões, Flashcards, Evolução) | Insumo para as specs das funcionalidades F-02, F-04, F-07, F-08 e F-12 |
| `Spec.md` | Problema, escopo e entidades | [`../produto/visao.md`](../produto/visao.md) (escopo revisto: repetição espaçada, sequência diária e chat RAG entram) |
| `Spec.md` | HU, RF, RN, CB e RQ | Mapeados para as funcionalidades F-01 a F-13 em [`../produto/backlog.md`](../produto/backlog.md), com IDs preservados para reuso nas specs |
| `Spec.md` | Questões QA-01 a QA-11 | Continuam válidas; complementadas por QA-12 a QA-22 em [`../produto/visao.md`](../produto/visao.md) |
| `Plan.md` | Abordagem técnica, riscos e estratégia de testes | Insumo para o `plan.md` e o `research.md` de cada spec, depois da decisão da stack |
| `Tasks.md` | Fases e tarefas | Não reaproveitado diretamente: as tarefas são geradas por funcionalidade e por história, depois do plano aprovado |

## Problemas conhecidos nos originais

- `Spec.md`, seção 3: a linha HU-12 da tabela está mesclada com o conteúdo do RF-14, e o RF-13 aparece solto.
- O escopo exclui a repetição espaçada e a sequência diária, o que foi revisto pelo PO em 29/09/2026.
- `SKILL.md` e `DESIGN.md` misturam princípios estáveis com configuração e detalhes de interface. Isso foi separado na migração.
