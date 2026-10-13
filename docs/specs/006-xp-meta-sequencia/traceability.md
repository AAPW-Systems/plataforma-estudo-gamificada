# Rastreabilidade

**Funcionalidade:** 006-xp-meta-sequencia (XP, meta diária e sequência)  
**Data:** 13/10/2026 ([registro](../../prompts/2026-10-13-006-xp-meta-sequencia-plano.md))  
**Status:** aprovada em 13/10/2026 por Artur Lins (equipe), junto com as [tarefas](tasks.md)

Esta matriz mostra que requisito, cenário, teste e tarefa descrevem o mesmo comportamento. Os nomes de teste são planejados e passam a ser links quando a implementação existir (T045). Os caminhos de teste são relativos a `backend/tests/`, salvo os do frontend. Todo teste com instante usa o relógio injetável (T007 da 005).

## Requisitos funcionais

| Requisito | Cenário ou caso de borda | Teste planejado | Tarefas |
|---|---|---|---|
| RF-001 | US1-1, US1-2, US1-4; duas abas (CB-24) | `unit/gamificacao/test_xp.py::test_xp_por_combinacao`; `integration/gamificacao/test_concessao_xp.py::test_concorrencia_*`, `::test_reenvio_registra_uma_vez`; `functional/gamificacao/test_us1_xp.py::test_cenario_1_*`, `::test_cenario_2_*`, `::test_cenario_4_*`, `::test_teste_independente_50_xp` | T014 T015 T016 T017 T018 |
| RF-002 | US1-3 | `unit/gamificacao/test_xp.py::test_bonus_dominado`; `functional/gamificacao/test_us1_xp.py::test_cenario_3_bonus_unico`, `::test_bonus_nao_repete_apos_queda` | T014 T016 T017 |
| RF-003 | US1-5; exclusão da conta | `integration/gamificacao/test_restricoes.py::test_set_null_preserva_evento`, `::test_fk_composta_*`; `integration/gamificacao/test_concessao_xp.py::test_campos_copiados`; `arquitetura/test_camadas.py::test_eventos_xp_sem_update`; `functional/gamificacao/test_us1_xp.py::test_cenario_5_xp_apos_excluir_cartao`; teste de catálogo da 001 | T004 T005 T009 T011 T015 T016 T017 |
| RF-004 | US2-1, US2-4 | `unit/gamificacao/test_meta.py::test_revisados_so_primeira_do_dia`; `functional/gamificacao/test_us2_meta.py::test_cenario_1_*`, `::test_cenario_4_reapresentacao_nao_conta` | T022 T024 T025 |
| RF-005 | US2-2; cartões aceitos ou criados no meio do dia; excluídos ou suspensos | `unit/gamificacao/test_meta.py::test_meta_efetiva_*`; `integration/revisao/test_provedor_disponibilidade.py`; `functional/gamificacao/test_us2_meta.py::test_teste_independente_meta_8`, `::test_aceitos_no_meio_do_dia`, `::test_suspensos_saem_dos_restantes` | T006 T022 T023 T024 T025 T027 |
| RF-006 | US2-2, US2-3; meta já cumprida com novos disponíveis; retirada que completa a meta | `unit/gamificacao/test_meta.py::test_transicoes_linha_dia`; `integration/gamificacao/test_meta_dia.py::test_depois_de_alterar_*`, `::test_concorrencia_uma_marcacao`; `functional/gamificacao/test_us2_meta.py::test_cenario_3_extra_nao_cria_dia`, `::test_meta_cumprida_e_novos_depois` | T022 T023 T024 T025 T026 |
| RF-007 | US3-2 (CB-13); data pulada pela mudança de fuso | `unit/gamificacao/test_sequencia.py::test_liquidar_neutro_*`, `::test_liquidar_contra_oraculo`; `integration/gamificacao/test_liquidacao.py::test_brecha_*`, `::test_reativar_nao_quebra`; `functional/gamificacao/test_us3_sequencia.py::test_cenario_2_dia_neutro`, `::test_data_pulada_neutra` | T006 T031 T032 T033 T034 T035 |
| RF-008 | US3-1, US3-3, US3-5 | `unit/gamificacao/test_sequencia.py::test_teste_independente_atual_1_recorde_3`, `::test_aplicar_sequencia_*`; `integration/gamificacao/test_liquidacao.py::test_leitura_nao_grava`, `::test_sequencia_longa`; `functional/gamificacao/test_us3_sequencia.py::test_cenario_1_*`, `::test_cenario_3_*`, `::test_cenario_5_hoje_falta` | T031 T032 T033 T034 T035 T036 |
| RF-009 | US3-4 (CB-25); mudança de fuso; horário de verão | `unit/gamificacao/test_sequencia.py::test_datas_puladas_*`; `functional/gamificacao/test_us3_sequencia.py::test_cenario_4_3h50_dia_anterior`, `::test_fuso_vivido_em_parte`, `::test_data_repetida_conta_uma_vez`, `::test_horario_verao_*`; `unit/nucleo/test_dia_estudo.py` (005) | T031 T033 T035 |
| RF-010 | US1-1 (valor do servidor); US2-1; US3-5 | `integration/test_contrato_openapi.py::test_contrato_006_*`; `functional/gamificacao/test_us1_xp.py::test_xp_ganho_na_resposta`; `functional/gamificacao/test_us2_meta.py::test_trilha_mostra_progresso`; `integration/gamificacao/test_consultas.py`; `frontend/.../PainelProgresso.test.tsx`, `FechamentoLicao.test.tsx` | T010 T012 T018 T019 T020 T027 T028 T029 T036 T037 T038 |
| RF-011 | — (FSRS soberano, RN-26) | `integration/gamificacao/test_concessao_xp.py::test_fsrs_identico_com_e_sem_ouvinte`; `arquitetura/test_camadas.py::test_gamificacao_nao_importa_cartoes_nem_revisao` | T009 T015 T017 |

## Requisitos de qualidade

| Requisito | Teste planejado | Tarefas |
|---|---|---|
| RQ-001 (nada antes da resposta) | `frontend/.../AnuncioGamificacao.test.tsx::nada_antes_da_resposta` (MSW atrasado); `PainelProgresso.test.tsx` (valores do cache vindo da resposta) | T019 T020 T028 T029 |
| RQ-002 (mesma transação) | `integration/gamificacao/test_concessao_xp.py::test_falha_no_ouvinte_desfaz_revisao`; `integration/gamificacao/test_meta_dia.py::test_falha_no_gancho_desfaz_acao` | T015 T017 T023 T026 |
| RQ-003 (anúncio discreto) | `frontend/.../AnuncioGamificacao.test.tsx` (textos, foco, movimento reduzido, sem som); verificação manual com leitor de tela | T019 T020 T028 T029 T037 T043 |
| RQ-004 (regra versionada) | `unit/gamificacao/test_regras_publicadas.py`; `functional/gamificacao/test_us1_xp.py::test_nova_versao_nao_altera_concedido` | T005 T016 T017 |

## Critérios de sucesso

| Critério | Teste planejado | Tarefas |
|---|---|---|
| CS-001 (total igual à soma, sem duplicidade) | `integration/gamificacao/test_concessao_xp.py::test_propriedade_cache` (Hypothesis), `::test_concorrencia_*`; `functional/gamificacao/test_us1_xp.py::test_reenvio_100_vezes`; runbook do quickstart | T015 T016 T017 |
| CS-002 (virada, fuso e horário de verão iguais ao cálculo à mão) | `unit/gamificacao/test_sequencia.py::test_liquidar_contra_oraculo`; `functional/gamificacao/test_us3_sequencia.py` (3h50, fusos, horário de verão) | T031 T033 T034 T035 |
| CS-003 (errar várias vezes = acertar uma vez) | `unit/gamificacao/test_xp.py::test_qualquer_sequencia_de_notas` (Hypothesis); `functional/gamificacao/test_us1_xp.py::test_errar_50_vezes` | T014 T016 |

## Casos de borda

| Caso de borda da spec | Teste planejado | Tarefas |
|---|---|---|
| Revisões de duas abas ao mesmo tempo (CB-24) | `test_concessao_xp.py::test_concorrencia_dez_abas`; `test_meta_dia.py::test_concorrencia_uma_marcacao` | T015 T023 |
| Cartões aceitos ou criados no meio do dia | `test_us2_meta.py::test_aceitos_no_meio_do_dia`, `::test_criados_no_meio_do_dia` | T024 T025 |
| Cartões excluídos ou suspensos no meio do dia | `test_us2_meta.py::test_suspensos_saem_dos_restantes`; `test_meta_dia.py::test_depois_de_alterar_*` | T023 T024 T026 |
| Meta efetiva já cumprida e novos disponíveis depois | `test_us2_meta.py::test_meta_cumprida_e_novos_depois` | T024 T025 |
| Mudança da meta diária no meio do dia | `test_us2_meta.py::test_meta_reduzida_marca_dia`, `::test_meta_aumentada_nao_desfaz` | T024 T026 |
| Mudança de fuso (datas puladas e repetidas) | `test_us3_sequencia.py::test_fuso_vivido_em_parte`, `::test_data_pulada_neutra`, `::test_data_repetida_conta_uma_vez`; `test_liquidacao.py::test_trocar_fuso_nao_salva_dia` | T032 T033 T035 |
| Mudança de horário de verão | `test_us3_sequencia.py::test_horario_verao_sao_paulo`, `::test_horario_verao_santiago` | T033 |
| Mudança dos valores de XP | `test_regras_publicadas.py`; `test_us1_xp.py::test_nova_versao_nao_altera_concedido` | T005 T016 |

## Decisões técnicas

| Decisão | Teste que a sustenta | Tarefas |
|---|---|---|
| DTEC 057 (provedor e ganchos no núcleo) | `unit/nucleo/test_disponibilidade.py`; `integration/revisao/test_provedor_disponibilidade.py`; `test_meta_dia.py::test_chamadores_*`; `arquitetura/test_camadas.py` | T002 T003 T006 T009 T023 T026 |
| DTEC 058 (regra de valores versionada) | `unit/gamificacao/test_regras_publicadas.py` | T005 |
| DTEC 059 (concessão e cache) | `integration/gamificacao/test_concessao_xp.py`; `test_restricoes.py::test_indice_revisao_tipo` | T004 T015 T017 |
| DTEC 060 (meta efetiva e dia estudado) | `unit/gamificacao/test_meta.py`; `integration/gamificacao/test_meta_dia.py` | T022 T023 T025 T026 |
| DTEC 061 (liquidação e sequência) | `unit/gamificacao/test_sequencia.py`; `integration/gamificacao/test_liquidacao.py` | T031 T032 T034 T035 T036 |
| DTEC 062 (fuso e horário de verão) | `test_us3_sequencia.py` (fusos); `test_sequencia.py::test_datas_puladas_*` | T031 T033 T035 |
| DTEC 063 (exibição e contrato aditivo) | `test_contrato_openapi.py::test_contrato_006_superconjunto_005`; testes de componente da gamificação | T010 T012 T019 T020 T028 T029 |

## Tarefas de suporte

Tarefas que não implementam um requisito isolado, mas sustentam todos ou produzem a evidência de uma história.

| Tarefas | Papel | Requisitos sustentados |
|---|---|---|
| T001 | Pessoa responsável registrada antes da implementação | Processo (regra 1) |
| T004, T007, T008, T011, T012, T013 | Migração, trava e repositórios, fábricas, exclusão da conta, resumo e campos aditivos, verificação da base | Todos os RF |
| T016 (parte) | Reverificação obrigatória da US3-3 da 003 com XP real | RF-003; US3-3 e RF-008 da 003 |
| T021, T030, T039 | Evidência do teste independente de cada história | Cenários de cada história |
| T040 | Segurança transversal: isolamento do resumo, logs, proteções herdadas, zero chamadas à IA | Princípio II; RF-010 |
| T041 | Medições de desempenho | CS-004 da 005; metas de desempenho do plano |
| T042, T043, T044, T045 | Suítes completas, evidências manuais, documentação e atualização desta matriz | Regra 17; RQ-003 |

## Análise de consistência (etapa 7)

Conferência feita em 13/10/2026 entre spec, plano, pesquisa, modelo de dados, contrato, quickstart e tarefas.

| Verificação | Resultado |
|---|---|
| Todo RF, RQ e CS da spec tem teste planejado e tarefa | Sim: RF-001 a RF-011, RQ-001 a RQ-004 e CS-001 a CS-003 |
| Todo cenário de aceitação tem teste funcional | Sim: US1-1 a US1-5 (T016), US2-1 a US2-4 (T024), US3-1 a US3-5 (T033) |
| Todo caso de borda da spec tem teste | Sim: os 8 casos, na tabela acima |
| Toda tarefa cita caminho exato e resultado verificável | Sim |
| Toda tarefa aparece na matriz | Sim: T001 a T045, nas tabelas acima ou em "Tarefas de suporte" |
| Tarefas organizadas por história, não por camada | Sim: Fases 3 a 5, uma por história, na ordem do plano (US1 e US2 como P1, depois US3). A base só tem o que todas usam: núcleo de disponibilidade, migração, regras, provedor, trava, fábricas, arquitetura, contrato e os campos aditivos. Os ganchos são chamados na US2, que precisa do `depois`; o `antes` ganha comportamento na US3 |
| Contrato coerente com a spec e o plano | Sim: nenhuma rota nova; 4 caminhos da 005 redefinidos como superconjunto (conferido por script e pela T010); esquemas `ResumoGamificacao`, `ProgressoMeta` e `Sequencia`; nenhum código de erro novo; validado com `openapi-spec-validator` |
| Modelo de dados coerente com o esquema | Sim: o [esquema inicial](../../arquitetura/esquema-inicial.dbml) foi atualizado nesta sessão (enum `situacao_dia`, `eventos_xp`, `dias_estudo`, colunas de `usuarios` e `revisoes_id_usuario`) |
| Exigências do PO | Nenhuma exigência (EX-01 a EX-05) toca a 006, conferido em 13/10/2026 |
| Requisito enfraquecido no plano | Nenhum. A leitura de "disponível na virada" (RF-007) e de "data pulada" (D-003) segue o texto da spec e foi registrada na sessão (DTEC 061 e 062). O RF-006 é garantido por `CHECK` e pela ausência de transição de volta |
| Tecnologia fora da stack aprovada | Nenhuma. PostgreSQL (`FOR NO KEY UPDATE`, índices únicos, `SET NULL (coluna)`), biblioteca padrão (`zoneinfo`), Hypothesis (DTEC 014). Nenhuma dependência nova |
| Coerência com as specs vizinhas | Obrigações da 005 cumpridas: ouvinte de `RevisaoRegistrada` na mesma transação (T017), XP só com `primeira_do_dia` e bônus só com `tornou_dominado` (T014, T017), campos aditivos de `Fechamento` e da trilha (T012, T018, T027, T036), `nucleo/dia_estudo.py` na meta e na sequência (T025, T035), "extra depois da meta" (T027). Obrigação da 003 cumprida: `eventos_xp.cartao_id` com `SET NULL` (T004) e reverificação da US3-3 (T016). As alterações nos serviços da 001, da 003 e da 005 (T006, T012, T026) não mudam o comportamento delas, e as suítes delas continuam verdes (T042). As obrigações para a 007 e a 012 estão no [plano](plan.md#obrigações-registradas-para-as-próximas-specs) e no guia de contexto técnico |

## Lacunas aceitas antes da implementação

- **US3 sem demonstração manual:** a passagem de dias só é verificada pelos testes com relógio controlado, porque a aplicação não tem relógio ajustável fora deles (quickstart).
- **Dependência da ordem de implementação:** a 006 só começa depois da 005 completa. Se a 001 ou a 003 forem implementadas antes de existir `nucleo/disponibilidade.py`, quem chegar primeiro cria o módulo vazio (DTEC 057), e a T026 insere as chamadas.
- **Pessoa responsável:** a definir no início da implementação (T001). Até lá, as aprovações da documentação são de Artur Lins.
- **Nomes de teste:** os nomes exatos são confirmados na implementação e consolidados na T045.
