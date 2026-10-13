# Rastreabilidade

**Funcionalidade:** 005-licao-trilha (lição com repetição espaçada e trilha de progressão)  
**Data:** 13/10/2026 ([registro](../../prompts/2026-10-13-005-licao-trilha-plano.md))  
**Status:** aprovada em 13/10/2026 por Artur Lins (equipe), junto com as [tarefas](tasks.md)

Esta matriz mostra que requisito, cenário, teste e tarefa descrevem o mesmo comportamento. Os nomes de teste são planejados e passam a ser links quando a implementação existir (T049). Os caminhos de teste são relativos a `backend/tests/`, salvo os do frontend. Todo teste com instante usa o relógio injetável (T007).

## Requisitos funcionais

| Requisito | Cenário ou caso de borda | Teste planejado | Tarefas |
|---|---|---|---|
| RF-001 | US1-1; menos disponíveis que o tamanho; cartão aceito durante a lição | `unit/revisao/test_montagem.py::test_ordem_devidos_*`, `::test_ordem_novos_*`, `::test_menos_disponiveis`; `integration/cartoes/test_consultas_licao.py::test_so_ativo_*`; `functional/revisao/test_us1_licao.py::test_cenario_1_*`, `::test_aceito_durante_licao_fica_fora`; `functional/revisao/test_reverificacoes.py` | T005 T014 T017 T018 T021 T022 |
| RF-002 | Limite zero; lição de dia anterior com novos não revisados; limite reduzido durante a lição | `unit/revisao/test_montagem.py::test_vagas_de_novos_*`, `::test_limite_zero`; `integration/revisao/test_concorrencia.py::test_limite_uma_vaga_em_paralelo`; `functional/revisao/test_us1_licao.py::test_dia_anterior_nao_consome_limite`; `adversarial/revisao/test_licao_adversarial.py::test_limite_zero_em_paralelo` | T004 T014 T016 T017 T020 T021 T023 |
| RF-003 | US1-2; CB-22 | `functional/revisao/test_us1_licao.py::test_cenario_2_sem_verso`, `::test_avaliar_sem_revelar_409`; `security/revisao/test_licao_seguranca.py::test_verso_so_na_revelacao`; `integration/revisao/test_restricoes.py::test_check_avaliada_exige_revelada`; `frontend/.../BotoesAvaliacao.test.tsx` | T004 T017 T019 T023 T026 T027 |
| RF-004 | US1-3 | `contrato/fsrs/test_mapeamento.py::test_notas_rating`; `adversarial/revisao/test_licao_adversarial.py::test_nota_fora_do_enum`; `frontend/.../BotoesAvaliacao.test.tsx` (atalhos 1 a 4) | T009 T010 T020 T026 |
| RF-005 | US1-3; retenção alterada durante a lição | `contrato/fsrs/test_cs001_reproducao.py`; `functional/revisao/test_us1_licao.py::test_retencao_alterada_vale_na_proxima`; `arquitetura/test_camadas.py::test_fsrs_so_no_agendador` | T008 T009 T010 T017 T023 |
| RF-006 | US1-4, US1-5, US1-6; Errei repetido | `unit/revisao/test_licao.py::test_proximo_*`, `::test_termino_*`, `::test_errei_repetido_conclui`; `functional/revisao/test_us1_licao.py::test_cenario_4_revendo`, `::test_cenario_5_*`, `::test_cenario_6_passo_nao_vencido` | T015 T017 T021 T023 |
| RF-007 | — (registro imutável) | `functional/revisao/test_us1_licao.py::test_revisao_registra_estados_e_versao`; `arquitetura/test_camadas.py::test_revisoes_sem_update`; `integration/revisao/test_cascata.py::test_revisao_sobrevive_ao_cartao` | T004 T008 T016 T017 T023 |
| RF-008 | CB-24 (reenvio, duas abas, nota diferente) | `integration/revisao/test_concorrencia.py::test_mesma_chave_em_paralelo`, `::test_duas_abas_mesma_apresentacao`; `functional/revisao/test_us1_licao.py::test_reenvio_*`, `::test_mesma_chave_outra_nota_409`, `::test_duas_abas_*`; `frontend/.../BotoesAvaliacao.test.tsx` (chave única) | T004 T016 T017 T020 T023 T026 |
| RF-009 | US2-1, US2-2, US2-3 | `functional/revisao/test_us2_explicacao.py`; `security/revisao/test_licao_seguranca.py::test_explicacao_so_em_errei`; `frontend/.../ExplicacaoErro.test.tsx` | T019 T029 T030 T031 T032 |
| RF-010 | US3-1, US3-2; US1-5 (nó acende) | `unit/revisao/test_trilha.py::test_estado_no_atual_*`; `functional/revisao/test_us3_trilha.py`; `security/revisao/test_trilha_seguranca.py` (isolamento, cursor e limite); `frontend/.../Trilha.test.tsx` | T022 T034 T035 T036 T037 T038 |
| RF-011 | CB-28; D-005 | `functional/revisao/test_us1_licao.py::test_aba_fechada_retoma`, `::test_dia_anterior_encerrada_sem_no`; `unit/revisao/test_trilha.py::test_aberta_dia_anterior_como_comecar`; `frontend/.../Licao.test.tsx` (`POST /licoes` ao carregar) | T017 T022 T026 T034 |
| RF-012 | US4-1; cartões não vencidos fora das extras | `functional/revisao/test_us4_extras.py`; `unit/revisao/test_montagem.py::test_nenhum_elegivel_depois_da_virada` | T014 T040 T041 |
| RF-013 | US3-3; US4-2; CB-13, CB-30 | `functional/revisao/test_us3_trilha.py::test_sem_disponiveis_proximo_vencimento`; `functional/revisao/test_us1_licao.py::test_sem_cartoes_409`; `functional/revisao/test_us4_extras.py::test_cenario_2_*`; `frontend/.../Trilha.test.tsx`, `FechamentoLicao.test.tsx` | T017 T034 T036 T037 T040 T041 T042 |
| RF-014 | US1-5 | `unit/revisao/test_licao.py::test_fechamento_*`, `::test_dominado_*`; `functional/revisao/test_us1_licao.py::test_cenario_5_fechamento_com_dominados`; `frontend/.../FechamentoLicao.test.tsx` | T015 T017 T021 T026 T027 |
| RF-015 | — (teclado) | `frontend/.../BotoesAvaliacao.test.tsx` (Espaço, Enter, 1 a 4); `frontend/.../ExplicacaoErro.test.tsx` (Enter); `frontend/componentes/ui/AtalhoTeclado.test.tsx`; lição só com teclado (T047) | T012 T026 T027 T031 T047 |

## Requisitos de qualidade

| Requisito | Teste ou evidência planejada | Tarefas |
|---|---|---|
| RQ-001 | `integration/revisao/test_concorrencia.py` (abertura, limite, duas abas, mesma chave, escritas disjuntas, sem *deadlock*); `adversarial/revisao/test_licao_adversarial.py` (concorrência); banco indisponível com reenvio da mesma chave | T016 T020 T023 |
| RQ-002 | `unit/nucleo/test_dia_estudo.py` (Hypothesis, horário de verão); `functional/revisao/test_us1_licao.py::test_licao_atravessa_virada` | T002 T003 T017 |
| RQ-003 | axe em todos os testes de componente; foco, `aria-live`, movimento reduzido e estados de nó sem depender de cor; verificação manual de teclado, leitor de tela e 320 px | T012 T026 T031 T037 T042 T046 |
| RQ-004 | `contrato/fsrs/test_cs001_reproducao.py`; `functional/revisao/test_us1_licao.py::test_reproduz_revisoes_gravadas`; `app/revisao/reproduzir.py` | T009 T010 T017 T024 |

## Critérios de sucesso

| Critério | Verificação planejada | Tarefas |
|---|---|---|
| CS-001 | `contrato/fsrs/test_cs001_reproducao.py`: 20 revisões de referência pelo adaptador e pela biblioteca isolada em subprocesso, com a mesma semente e os mesmos parâmetros | T009 T010 |
| CS-002 | `integration/revisao/test_concorrencia.py::test_mesma_chave_em_paralelo`, `::test_duas_abas_mesma_apresentacao`; `functional/revisao/test_us1_licao.py::test_reenvio_*`, `::test_duas_abas_*`; índices únicos em `test_restricoes.py` | T004 T016 T017 |
| CS-003 | `unit/revisao/test_montagem.py::test_nenhum_elegivel_depois_da_virada` (Hypothesis), `::test_revisao_na_virada`; reverificação US3-1 e CS-003 da 003 | T014 T018 |
| CS-004 | `functional/desempenho/test_transicao.py` (servidor, 150 ms); roteiro do quickstart com `transicao-cartao` (navegador, 300 ms) e lição só com teclado | T026 T027 T047 |

## Casos de borda

| Caso de borda | Teste planejado | Tarefas |
|---|---|---|
| Avaliação sem revelação (CB-22) | `test_us1_licao.py::test_avaliar_sem_revelar_409` | T017 T023 |
| Reenvio, duas abas e nota diferente (CB-24) | `test_concorrencia.py::test_mesma_chave_em_paralelo`, `::test_duas_abas_mesma_apresentacao`; `test_us1_licao.py::test_reenvio_*`, `::test_mesma_chave_outra_nota_409` | T016 T017 |
| Lição interrompida com passo curto (CB-28) | `test_us1_licao.py::test_aba_fechada_retoma` | T017 T022 |
| Lição aberta de dia anterior (D-005) | `test_us1_licao.py::test_dia_anterior_encerrada_sem_no`; `test_trilha.py::test_nos_sem_buracos` | T017 T022 T034 |
| Lição atravessando as 4h (CB-25) | `test_us1_licao.py::test_licao_atravessa_virada`; `test_licao.py::test_primeira_do_dia_na_virada` | T015 T017 |
| Cartão excluído, suspenso ou com fonte excluída (CB-27) | `test_cascata.py`; `test_us1_licao.py::test_suspenso_durante_licao`; `test_licao_adversarial.py::test_avaliar_depois_da_exclusao_404` | T016 T017 T020 |
| Cartão aceito durante a lição | `test_us1_licao.py::test_aceito_durante_licao_fica_fora` | T017 |
| Retenção alterada durante a lição (CB-29) | `test_us1_licao.py::test_retencao_alterada_vale_na_proxima` | T017 |
| Menos disponíveis que o tamanho | `test_montagem.py::test_menos_disponiveis`; `test_us4_extras.py::test_cenario_2_*` | T014 T040 |
| Limite de novos igual a zero | `test_montagem.py::test_limite_zero`; `test_us1_licao.py::test_limite_zero_so_devidos` | T014 T017 |
| Novos não revisados de lição encerrada voltam a ser elegíveis (D-007) | `test_us1_licao.py::test_dia_anterior_nao_consome_limite` | T017 |
| Tamanho alterado durante a lição | `test_us1_licao.py::test_tamanho_alterado_vale_na_proxima` | T017 |
| Errei repetido (D-004) | `test_licao.py::test_errei_repetido_conclui`; `test_us1_licao.py::test_errei_repetido` | T015 T017 |

## Decisões técnicas

| Decisão | Teste que a sustenta | Tarefas |
|---|---|---|
| DTEC 048 (dia de estudo) | `unit/nucleo/test_dia_estudo.py` | T002 T003 |
| DTEC 049 (modelo da lição) | `integration/revisao/test_restricoes.py`; `test_cascata.py` | T004 T016 |
| DTEC 050 (abertura e encerramento) | `test_concorrencia.py::test_dez_aberturas_simultaneas`; `test_us1_licao.py::test_dia_anterior_*`, `::test_licao_atravessa_virada`; `test_trilha.py::test_get_nao_escreve` | T016 T017 T022 T034 |
| DTEC 051 (elegibilidade e limite) | `unit/revisao/test_montagem.py`; `integration/cartoes/test_consultas_licao.py`; `test_concorrencia.py::test_limite_uma_vaga_em_paralelo` | T005 T014 T016 |
| DTEC 052 (revelação, avaliação e duração) | `test_us1_licao.py` (códigos `409`); `test_licao.py::test_duracao_*`; `test_concorrencia.py::test_sem_deadlock` | T015 T016 T017 T023 |
| DTEC 053 (agendamento reprodutível) | `tests/contrato/fsrs/`; `arquitetura/test_camadas.py::test_fsrs_so_no_agendador` | T008 T009 T010 |
| DTEC 054 (próximo, término e transição) | `unit/revisao/test_licao.py::test_proximo_*`, `::test_termino_*`; `functional/desempenho/test_transicao.py` | T015 T021 T047 |
| DTEC 055 (dominado e evento) | `test_licao.py::test_dominado_*`, `::test_primeira_do_dia_*`; `unit/nucleo/test_eventos_revisao.py`; `integration/revisao/test_evento.py` | T010 T011 T015 T016 |
| DTEC 056 (trilha) | `unit/revisao/test_trilha.py`; `functional/revisao/test_us3_trilha.py`; `security/revisao/test_trilha_seguranca.py` | T034 T035 T036 |

## Tarefas de suporte

Tarefas que não implementam um requisito isolado, mas sustentam todos ou produzem a evidência de uma história.

| Tarefas | Papel | Requisitos sustentados |
|---|---|---|
| T001 | Pessoa responsável registrada antes da implementação | Processo (regra 1) |
| T004, T005, T006, T007, T008, T011, T013 | Migração, consultas e escrita dos cartões, existência de matérias, fábricas e relógio, arquitetura, evento e verificação da base | Todos os RF |
| T018 | Reverificações obrigatórias da 003 e da 004 com lições reais | RF-001; US1-1, US3-1, US3-2 e CS-003 da 003; US1-4, RF-010 e RF-014 da 004 |
| T024 | Exclusão da conta e runbook da reprodução | RQ-004; CS-004 da 001 (catálogo) |
| T025 | Contrato gerado e tipos do frontend | Todos os RF expostos pela API |
| T028, T033, T039, T044 | Evidência do teste independente de cada história | Cenários de cada história |
| T045, T046, T047, T048, T049 | Suítes completas, evidências, medições, documentação e atualização desta matriz | Regra 17; RQ-003; CS-004; metas de desempenho do plano |

## Análise de consistência (etapa 7)

Conferência feita em 13/10/2026 entre spec, plano, pesquisa, modelo de dados, contrato, quickstart e tarefas.

| Verificação | Resultado |
|---|---|
| Todo RF, RQ e CS da spec tem teste planejado e tarefa | Sim: RF-001 a RF-015, RQ-001 a RQ-004 e CS-001 a CS-004 |
| Todo cenário de aceitação tem teste funcional | Sim: US1-1 a US1-6 (T017), US2-1 a US2-3 (T029), US3-1 a US3-3 (T034), US4-1 e US4-2 (T040) |
| Todo caso de borda da spec tem teste | Sim: os 13 casos, na tabela acima |
| Toda tarefa cita caminho exato e resultado verificável | Sim |
| Toda tarefa aparece na matriz | Sim: T001 a T049, nas tabelas acima ou em "Tarefas de suporte". T002 e T003 em RQ-002 e DTEC 048; T009 e T010 em CS-001; T012 em RF-015; T019 e T020 em RF-003, RF-008 e RF-009; T021 a T023 nos RF da US1; T026 e T027 na US1 e no CS-004; T029 a T032 em RF-009; T034 a T038 em RF-010 e RF-013; T040 a T043 em RF-012 e RF-013 |
| Tarefas organizadas por história, não por camada | Sim: Fases 3 a 6, uma por história, na ordem do plano (US1 e US2 como P1 demonstráveis sem IA, depois US3 e US4). A base só tem o que todas usam: dia de estudo, migração, consultas de cartões, agendador, evento e um componente. A numeração dos nós entra na US1, porque a conclusão da lição já acende o nó (US1-5) |
| Contrato coerente com a spec e o plano | Sim: 5 operações, 3 com identificador no caminho, todas na tabela de isolamento (T019). Todo erro usa o esquema `Erro`; os códigos da 001 a 004 foram mantidos, e 6 foram acrescentados. Nenhuma resposta além da revelação contém o verso. Validado com `openapi-spec-validator` |
| Modelo de dados coerente com o esquema | Sim: o [esquema inicial](../../arquitetura/esquema-inicial.dbml) foi atualizado nesta sessão (tabelas, colunas, índices parciais, FKs compostas e `CHECK` da 005) |
| Exigências do PO | EX-03 coberta por RF-009 (US2; T029 a T033), com a explicação gerada na 004 e a evidência pela rota da 004, sem IA. EX-05 fica fora, sem requisito, até a resposta do PO (Q-002, PO-01); a dificuldade do FSRS já fica gravada. EX-01 não toca esta spec. Nenhuma exigência conflita com o plano |
| Requisito enfraquecido no plano | Nenhum. O CB-25 e o D-005 foram conciliados por critério técnico (DTEC 050), sem mudar o comportamento da spec. O RF-002 virou invariante verificado na primeira revisão (DTEC 051) |
| Tecnologia fora da stack aprovada | Nenhuma. Biblioteca `fsrs` (DTEC 012), PostgreSQL (índices parciais, `FOR NO KEY UPDATE`, `SET NULL (coluna)`, *advisory lock*), biblioteca padrão (`zoneinfo`, `secrets`, `contextvars`). Nenhuma dependência nova |
| Coerência com as specs vizinhas | Obrigações da 003 cumpridas: `revisoes.cartao_id` com `set null` (T004), `dominado_em` (T004), lição só com `ativo` e novos por `entrada_estudo_em` (T005, T014), escritas disjuntas (T005, T016) e reverificações (T018). Obrigações da 004 cumpridas: só `ativo` (T005), ordem de aceitação e US1-4 (T018), explicação ao errar com a evidência e sem IA (T029 a T032). A exceção do `cascade` em `licoes_cartoes` e `apresentacoes` está justificada no plano. A 004 passa a usar `nucleo/dia_estudo.py` (DTEC 048), sem mudar comportamento. As obrigações para a 006, a 007, a 012 e a 015 estão no [plano](plan.md#obrigações-registradas-para-as-próximas-specs) e no guia de contexto técnico |

## Lacunas aceitas antes da implementação

- **Q-001 (composição da trilha):** a T038 depende da decisão da equipe (prazo 14/10/2026). A API e os testes do backend da US3 não dependem dela.
- **Medição do CS-004 no navegador:** manual, pelo roteiro do quickstart, porque o Playwright só chega no final acadêmico (DTEC 014). A parte do servidor é automatizada (T047).
- **US2 com evidência real:** depende das T040 a T042 da 004. Sem elas, a T029 usa o cartão gerado da fábrica e verifica `evidenciaDisponivel`; a abertura da evidência é verificada quando a 004 estiver implementada.
- **XP, meta e sequência no fechamento:** da 006, por campos aditivos.
- **Pessoa responsável:** a definir no início da implementação (T001). Até lá, as aprovações da documentação são de Artur Lins.
- **Nomes de teste:** os nomes exatos são confirmados na implementação e consolidados na T049.
