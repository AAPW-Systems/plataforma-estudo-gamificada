# Rastreabilidade

**Funcionalidade:** 003-cartoes-manuais (cartões criados e gerenciados pelo estudante)  
**Data:** 13/10/2026 ([registro](../../prompts/2026-10-13-003-cartoes-manuais-plano.md))  
**Status:** aguardando o portão "Tarefas aprovadas", junto com as [tarefas](tasks.md)

Esta matriz mostra que requisito, cenário, teste e tarefa descrevem o mesmo comportamento. Os nomes de teste são planejados e passam a ser links quando a implementação existir (T045). Os caminhos de teste são relativos a `backend/tests/`, salvo os do frontend.

## Requisitos funcionais

| Requisito | Cenário ou caso de borda | Teste planejado | Tarefas |
|---|---|---|---|
| RF-001 | US1-1, US1-2; frente, verso ou explicação só com espaços; teto mais um | `unit/cartoes/test_dominio.py::test_limites_*`, `::test_normalizacao_*`; `functional/cartoes/test_us1_criar.py::test_cria_cartao`, `::test_campos_invalidos_*`, `::test_limites_vigentes`; `adversarial/cartoes/test_criar_adversarial.py::test_teto_*`; `frontend/.../PainelCartao.test.tsx` (contador e erro por campo) | T001 T003 T006 T008 T010 T013 T014 T015 T017 T018 |
| RF-002 | US1-3; fonte em `pendente` ou `falhou`; fonte de outra matéria ou de outro dono | `integration/cartoes/test_repositorio.py::test_referencia_copia_*`; `functional/cartoes/test_us1_criar.py::test_referencia_sem_selo`, `::test_referencia_qualquer_estado`; `security/cartoes/test_cartoes_seguranca.py::test_fonte_alheia_mesma_mensagem`; `integration/cartoes/test_restricoes.py::test_fk_referencia_*` | T003 T009 T010 T012 T015 T017 T018 |
| RF-003 | US1-1 (cartão novo na ordem de criação) | `unit/cartoes/test_dominio.py::test_estado_inicial_espelha_card`; `functional/cartoes/test_us1_criar.py::test_estado_de_cartao_novo`, `::test_ordem_de_entrada`. Lição real: reverificação pela 005 | T008 T010 T014 T015 |
| RF-004 | US1-1, US3-1; matéria sem cartões | `integration/cartoes/test_repositorio.py::test_lista_visiveis_*`, `::test_paginacao_estavel`; `functional/cartoes/test_us1_criar.py::test_lista_*`; `functional/cartoes/test_us3_suspender_excluir.py::test_lista_mostra_suspenso`; `frontend/.../ListaCartoes.test.tsx` | T009 T010 T015 T017 T018 T028 |
| RF-005 | US2-1; edição concorrente com revisão | `integration/cartoes/test_edicao_fsrs.py`; `functional/cartoes/test_us2_editar.py::test_cs002_*` | T021 T022 T024 |
| RF-006 | US2-2, US2-3 | `unit/cartoes/test_edicao.py::test_origem_apos_edicao_*`; `functional/cartoes/test_us2_editar.py::test_gerado_vira_editado`, `::test_sem_mudanca_mantem_origem`. Evidência mantida: reverificação pela 004 | T004 T020 T022 T024 T025 T026 |
| RF-007 | US3-1, US3-2; reativação com vencimento passado | `functional/cartoes/test_us3_suspender_excluir.py::test_suspende_*`, `::test_reativa_*`, `::test_reativado_vencido_fica_devido`. Fora da lição: reverificação pela 005 | T028 T030 T031 T032 |
| RF-008 | US3-3; exclusão repetida | `functional/cartoes/test_us3_suspender_excluir.py::test_exclui_*`; `frontend/.../DialogoExclusaoCartao.test.tsx`. Revisões e XP preservados: reverificação pela 005 e pela 006 | T028 T030 T031 T032 |
| RF-009 | US1-1, US1-3, US2-2; "Fonte apagada" (D-006) | `unit/cartoes/test_dominio.py::test_derivados_*`; `functional/fontes/test_us2_exclusao_fonte.py` com cartões reais; `frontend/componentes/ui/SeloOrigem.test.tsx` | T006 T008 T010 T011 T014 T022 T031 |
| RF-010 | US4-1, US4-2, US4-3 | `integration/cartoes/test_busca.py`; `functional/cartoes/test_us4_encontrar.py`; `adversarial/cartoes/test_busca_adversarial.py`; `frontend/.../FiltrosCartoes.test.tsx` | T034 T035 T036 T037 T038 T039 |
| RF-011 | Quebras de linha preservadas; texto puro | `unit/cartoes/test_dominio.py::test_normalizacao_preserva_quebras` (Hypothesis); `frontend/.../ListaCartoes.test.tsx::quebras_de_linha` | T008 T014 T017 |

## Requisitos de qualidade

| Requisito | Teste ou evidência planejada | Tarefas |
|---|---|---|
| RQ-001 | `functional/cartoes/test_us1_criar.py::test_marcacao_literal`; `adversarial/cartoes/test_criar_adversarial.py::test_script_*`; `frontend/.../ListaCartoes.test.tsx::marcacao_literal`; regra de lint contra `dangerouslySetInnerHTML` | T002 T010 T013 T017 T041 |
| RQ-002 | `security/test_isolamento_rotas.py` (6 rotas da 003); FKs compostas em `integration/cartoes/test_restricoes.py`; `security/cartoes/*`; `security/identidade/test_exclusao_completa.py` com cartões | T003 T012 T023 T029 |
| RQ-003 | axe nos testes de componente; `SeloOrigem` com texto e ícone; verificação manual de teclado, leitor de tela e 320 px | T006 T017 T025 T031 T038 T042 |

## Critérios de sucesso

| Critério | Verificação planejada | Tarefas |
|---|---|---|
| CS-001 | Medição cronometrada só com teclado no quickstart (5 cartões em até 3 min); `PainelCartao.test.tsx` (atalhos e foco) | T017 T019 |
| CS-002 | `integration/cartoes/test_edicao_fsrs.py`; `functional/cartoes/test_us2_editar.py::test_cs002_20_edicoes` | T004 T021 T022 |
| CS-003 | Na 003, situação `suspenso` e agendamento preservado (`test_us3_suspender_excluir.py::test_suspende_*`). Ausência em todas as lições: reverificação pela 005 (obrigação no plano) | T028 |

## Casos de borda

| Caso de borda | Teste planejado | Tarefas |
|---|---|---|
| Frente, verso ou explicação só com espaços | `functional/cartoes/test_us1_criar.py::test_so_espacos_*`; `unit/cartoes/test_dominio.py` | T008 T010 |
| Texto com marcação ou script | ver RQ-001 | T010 T013 T017 |
| Suspenso ou excluído durante uma lição aberta (CB-27) | A 003 não guarda estado de lição; a verificação de ponta a ponta fica com a 005 (obrigação no plano) | — |
| Edição concorrente em duas abas | `adversarial/cartoes/test_editar_adversarial.py::test_duas_edicoes_ultima_vale`; `integration/cartoes/test_edicao_fsrs.py::test_edicao_e_agendamento_concorrentes` | T021 T023 |
| Fonte de referência excluída, inclusive com "Excluir os cartões junto" (D-006) | `functional/fontes/test_us2_exclusao_fonte.py` com cartões reais; `integration/cartoes/test_participante.py::test_ao_excluir_fonte_*`; `adversarial/cartoes/test_criar_adversarial.py::test_criacao_durante_exclusao_da_fonte` | T009 T011 T013 |
| Cartão aguardando revisão fora da lista | `security/cartoes/test_editar_seguranca.py::test_aguardando_revisao_404`; reexecução pela 004 com dados reais | T023 |

## Decisões técnicas

| Decisão | Teste que a sustenta | Tarefas |
|---|---|---|
| DTEC 027, emenda (`cartoes_suspensos`) | `integration/cartoes/test_participante.py::test_contar_por_materia_*`; T011 (lista só com ativos; impacto com ativos e suspensos) | T009 T011 T015 |
| DTEC 033 (busca com `unaccent`) | `integration/cartoes/test_busca.py`; migração em `test_migracoes.py`; medição da T043 | T003 T034 T037 T043 |
| DTEC 034 (paginação por cursor) | `unit/cartoes/test_cursor.py`; `integration/cartoes/test_repositorio.py::test_paginacao_estavel`; `test_us4_encontrar.py::test_cursor_outros_filtros` | T008 T009 T035 |
| DTEC 035 (referência à fonte) | `integration/cartoes/test_restricoes.py`; `test_participante.py`; `test_criar_adversarial.py::test_criacao_durante_exclusao_da_fonte` | T003 T009 T013 |
| DTEC 036 (texto e limites) | `unit/nucleo/test_configuracao.py`; `unit/cartoes/test_dominio.py`; `CampoTextoLongo.test.tsx`; regra de lint | T001 T002 T006 T008 |
| DTEC 037 (agendamento, edição e situação) | `test_estado_inicial_espelha_card`; `integration/cartoes/test_edicao_fsrs.py`; testes de idempotência da US3 | T008 T021 T028 |
| DTEC 038 (fronteira com a 004) | `unit/cartoes/test_edicao.py`; `test_aguardando_revisao_404`; `test_participante.py`; `arquitetura/test_camadas.py` | T005 T009 T020 T023 |

## Tarefas de suporte

Tarefas que não implementam um requisito isolado, mas sustentam todos ou produzem a evidência de uma história.

| Tarefas | Papel | Requisitos sustentados |
|---|---|---|
| T003, T004, T005, T007 | Migração, fábricas, teste de arquitetura e verificação da base | Todos os RF; CS-002 |
| T016 | Contrato gerado e tipos do frontend | Todos os RF expostos pela API |
| T019, T027, T033, T040 | Evidência do teste independente de cada história | Cenários de cada história; CS-001 |
| T041, T042, T043, T044, T045 | Suítes completas, evidências, medições, documentação e atualização desta matriz | Regra 17; RQ-001 a RQ-003; metas de desempenho do plano |

## Análise de consistência (etapa 7)

Conferência feita em 13/10/2026 entre spec, plano, pesquisa, modelo de dados, contrato, quickstart e tarefas.

| Verificação | Resultado |
|---|---|
| Todo RF, RQ e CS da spec tem teste planejado e tarefa | Sim: RF-001 a RF-011, RQ-001 a RQ-003 e CS-001 a CS-003. O CS-003 e partes da RF-003, da RF-007 e da RF-008 dependem de lições e revisões reais e têm a reverificação registrada como obrigação da 005 e da 006 |
| Todo cenário de aceitação tem teste funcional | Sim: US1-1 a US1-3 (T010), US2-1 a US2-3 (T022), US3-1 a US3-3 (T028), US4-1 a US4-3 (T035) |
| Todo caso de borda da spec tem teste | Sim, exceto o CB-27 (lição aberta), que só é verificável com a 005 e está registrado como lacuna aceita |
| Toda tarefa cita caminho exato e resultado verificável | Sim |
| Toda tarefa aparece na matriz | Sim: T001 a T045, nas tabelas acima ou em "Tarefas de suporte" |
| Tarefas organizadas por história, não por camada | Sim: Fases 3 a 6, uma por história. A base só tem o que todas usam (migração, fábricas, arquitetura e dois componentes). O participante da exclusão entra na US1, porque a criação de um cartão com referência já torna a exclusão da fonte dependente dele |
| Contrato coerente com a spec e o plano | Sim: 8 operações, 6 com identificador no caminho, todas na tabela de isolamento (T012, T023, T029). Todo erro usa o esquema `Erro`; os códigos da 001 e da 002 foram mantidos, e `cursor_invalido` foi acrescentado. Validado com `openapi-spec-validator` |
| Modelo de dados coerente com o esquema | Sim: o esquema foi atualizado nesta sessão (referência, `entrada_estudo_em`, índices e a spec que cria cada coluna) |
| Exigências do PO | Só a EX-03 toca a 003: explicação opcional aqui (RF-001), obrigatória na 004 e exibida ao errar na 005. EX-01 e EX-05, em pauta, não tocam a 003 |
| Requisito enfraquecido no plano | Nenhum. O CS-002 é garantido por construção (escritas disjuntas por coluna, DTEC 037) e testado com concorrência |
| Tecnologia fora da stack aprovada | Nenhuma. A extensão `unaccent` está na DTEC 033, aprovada com o plano; a regra de lint é nativa do ESLint; `fsrs` já entra na 001 |
| Coerência com as specs vizinhas | A 002 recebeu a emenda da DTEC 027 (plano, research, T005 e T043, com registro no histórico). As obrigações da 004, da 005, da 006 e da 011 estão no [plano](plan.md#obrigações-registradas-para-as-próximas-specs) |

## Lacunas aceitas antes da implementação

- **Lições reais:** a entrada como cartão novo (US1-1), a ausência dos suspensos nas lições (US3-1, CS-003), a volta do reativado (US3-2) e o CB-27 só são verificáveis de ponta a ponta com a 005. A 003 verifica o estado gravado que a lição usa.
- **Revisões e XP preservados (RF-008):** dependem das FKs `set null` da 005 e da 006, que reverificam a US3-3.
- **Evidência mantida na edição (RF-006):** a tabela de evidências é da 004, que reexecuta a US2-2 com geração real.
- **Aguardando revisão:** até a 004, o valor do enum é criado pela fixture do teste; a 004 reexecuta o caso com dados reais.
- **Nomes de teste:** os nomes exatos são confirmados na implementação e consolidados na T045.
