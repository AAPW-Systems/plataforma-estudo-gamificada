# Rastreabilidade

**Funcionalidade:** 003-cartoes-manuais (cartões criados e gerenciados pelo estudante)  
**Data:** 13/10/2026 ([registro](../../prompts/2026-10-13-003-cartoes-manuais-plano.md))  
**Status:** aprovada em 13/10/2026 por Artur Lins (equipe), junto com as [tarefas](tasks.md); nomes reais dos testes consolidados em 29/10/2026 (T045)

Esta matriz mostra que requisito, cenário, teste e tarefa descrevem o mesmo comportamento. Os nomes de teste foram planejados em 13/10/2026 e **substituídos pelos nomes reais na T045 (29/10/2026)**; um script conferiu cada referência `arquivo::função` contra o código. Os caminhos de teste são relativos a `backend/tests/`, salvo os do frontend, relativos a `frontend/src/`.

## Requisitos funcionais

| Requisito | Cenário ou caso de borda | Teste | Tarefas |
|---|---|---|---|
| RF-001 | US1-1, US1-2; frente, verso ou explicação só com espaços; teto mais um | `unit/cartoes/test_dominio.py::test_aceita_de_1_ate_o_maximo_em_code_points`, `::test_recusa_um_acima_do_maximo_com_a_mensagem_do_campo`, `::test_frente_e_verso_vazios_ou_invisiveis_sao_recusados`, `::test_os_limites_vigentes_mandam_nao_os_padroes`; `functional/cartoes/test_us1_criar.py::test_cria_cartao_ativo_criado_por_voce_e_ele_aparece_na_lista`, `::test_texto_vazio_ou_acima_do_limite_nao_cria_nada_e_aponta_o_campo`, `::test_textos_nos_limites_exatos_sao_aceitos`, `::test_limites_vigentes_vem_da_configuracao_e_nao_do_cache`, `::test_limite_configurado_vale_na_criacao`; `adversarial/cartoes/test_criar_adversarial.py::test_payload_no_teto_mais_um_e_recusado_pelo_dto`; `unit/nucleo/test_configuracao.py::test_cartoes_tem_os_padroes_do_plano`; `funcionalidades/cartoes/PainelCartao.test.tsx` (contador e erro por campo) | T001 T003 T006 T008 T010 T013 T014 T015 T017 T018 |
| RF-002 | US1-3; fonte em `pendente` ou `falhou`; fonte de outra matéria ou de outro dono | `integration/cartoes/test_repositorio.py::test_copia_da_referencia_vem_do_titulo_do_nome_e_da_data_do_envio`, `::test_buscar_fonte_para_referencia_so_devolve_fonte_do_dono_e_da_materia`; `functional/cartoes/test_us1_criar.py::test_cartao_com_referencia_mostra_a_fonte_sem_selo_de_verificado`, `::test_fonte_em_qualquer_estado_serve_de_referencia`, `::test_renomear_a_fonte_nao_muda_a_descricao_copiada`; `security/cartoes/test_cartoes_seguranca.py::test_fonte_alheia_de_outra_materia_ou_inexistente_dao_o_mesmo_422`; `integration/cartoes/test_restricoes.py::test_referencia_a_fonte_de_outra_materia_e_recusada`, `::test_referencia_a_fonte_de_outro_dono_e_recusada` | T003 T009 T010 T012 T015 T017 T018 |
| RF-003 | US1-1 (cartão novo na ordem de criação) | `unit/cartoes/test_dominio.py::test_estado_inicial_espelha_o_card_novo_da_biblioteca_fixada`; `functional/cartoes/test_us1_criar.py::test_cartao_novo_tem_o_estado_gravado_de_cartao_novo_na_ordem_de_criacao`. Lição real: reverificação pela 005 | T008 T010 T014 T015 |
| RF-004 | US1-1, US3-1; matéria sem cartões | `integration/cartoes/test_repositorio.py::test_lista_so_ativos_e_suspensos_do_mais_recente_para_o_mais_antigo`, `::test_paginacao_percorre_tudo_sem_repetir_nem_pular`, `::test_criacao_e_exclusao_entre_as_paginas_nao_repetem_nem_pulam_o_resto`; `functional/cartoes/test_us1_criar.py::test_lista_do_mais_recente_ao_mais_antigo_com_cursor_e_total`; `functional/cartoes/test_us3_suspender_excluir.py::test_suspender_um_cartao_ativo_preserva_o_agendamento_e_aparece_como_suspenso`; `functional/cartoes/test_us4_encontrar.py::test_suspenso_aparece_como_suspenso_na_lista_filtrada`; `funcionalidades/cartoes/AbaCartoes.test.tsx` | T009 T010 T015 T017 T018 T028 T035 |
| RF-005 | US2-1; edição concorrente com revisão | `integration/cartoes/test_edicao_fsrs.py::test_todas_as_colunas_do_fsrs_ficam_iguais_depois_da_edicao`, `::test_o_update_da_edicao_nao_cita_nenhuma_coluna_do_fsrs`, `::test_agendamento_e_edicao_em_paralelo_as_duas_sobrevivem`; `functional/cartoes/test_us2_editar.py::test_editar_a_frente_muda_o_texto_e_nao_o_agendamento`, `::test_cs002_vinte_edicoes_nao_mudam_vencimento_nem_estabilidade` | T021 T022 T024 |
| RF-006 | US2-2, US2-3 | `unit/cartoes/test_edicao.py::test_tabela_da_origem_depois_da_edicao`, `::test_a_origem_nunca_volta_a_gerado_e_verificado`; `functional/cartoes/test_us2_editar.py::test_editar_um_gerado_e_verificado_vira_editado_por_voce`, `::test_edicao_sem_mudanca_nao_muda_a_origem_nem_a_data`, `::test_edicao_mantem_a_referencia_copiada`; `funcionalidades/cartoes/EdicaoCartao.test.tsx` (selo trocado). Evidência mantida: reverificação pela 004 | T004 T020 T022 T024 T025 T026 |
| RF-007 | US3-1, US3-2; reativação com vencimento passado | `functional/cartoes/test_us3_suspender_excluir.py::test_suspender_um_cartao_ativo_preserva_o_agendamento_e_aparece_como_suspenso`, `::test_suspender_e_reativar_mantem_as_colunas_do_fsrs_em_qualquer_estado`, `::test_reativar_devolve_o_cartao_com_o_vencimento_de_antes`, `::test_suspender_ou_reativar_de_novo_nao_escreve_nada`; `funcionalidades/cartoes/SituacaoCartao.test.tsx`. Fora da lição: reverificação pela 005 | T028 T030 T031 T032 |
| RF-008 | US3-3; exclusão repetida | `functional/cartoes/test_us3_suspender_excluir.py::test_excluir_remove_o_cartao_e_um_segundo_pedido_e_404`, `::test_excluir_um_cartao_suspenso_tambem_funciona`; `adversarial/cartoes/test_situacao_adversarial.py::test_exclusao_repetida_em_paralelo_da_um_204_e_o_resto_404`; `funcionalidades/cartoes/SituacaoCartao.test.tsx` (diálogo de exclusão). Revisões e XP preservados: reverificação pela 005 e pela 006 | T028 T030 T031 T032 |
| RF-009 | US1-1, US1-3, US2-2; "Fonte apagada" (D-006) | `unit/cartoes/test_dominio.py::test_rotulo_e_selo_de_verificado_pela_origem`, `::test_fonte_apagada_deriva_das_copias_e_da_fonte_nula`; `functional/fontes/test_us2_exclusao_fonte.py::test_excluir_a_fonte_mantem_os_cartoes_de_referencia_com_fonte_apagada`; `componentes/ui/SeloOrigem.test.tsx`; `funcionalidades/cartoes/SituacaoCartao.test.tsx` ("Fonte apagada" junto da origem) | T006 T008 T010 T011 T014 T022 T031 |
| RF-010 | US4-1, US4-2, US4-3 | `integration/cartoes/test_busca.py::test_busca_sem_diferenciar_maiusculas_e_acentos_na_frente_e_no_verso`, `::test_curingas_e_barra_invertida_sao_literais`, `::test_busca_combina_com_situacao_e_origem`; `functional/cartoes/test_us4_encontrar.py::test_busca_encontra_frente_ou_verso_sem_diferenciar_maiusculas_e_acentos`, `::test_filtros_de_situacao_e_origem_combinam_com_a_busca`, `::test_busca_sem_resultado_tem_total_zero_mas_a_materia_continua_com_cartoes`; `adversarial/cartoes/test_busca_adversarial.py`; `funcionalidades/cartoes/BuscaCartoes.test.tsx` | T034 T035 T036 T037 T038 T039 |
| RF-011 | Quebras de linha preservadas; texto puro | `unit/cartoes/test_dominio.py::test_nenhuma_quebra_interna_e_perdida` (Hypothesis), `::test_normalizacao_de_texto`; `functional/cartoes/test_us1_criar.py::test_texto_e_normalizado_e_a_explicacao_vazia_vira_nula`; `funcionalidades/cartoes/AbaCartoes.test.tsx` (quebras e marcação literal) | T008 T014 T017 |

## Requisitos de qualidade

| Requisito | Teste ou evidência | Tarefas |
|---|---|---|
| RQ-001 | `functional/cartoes/test_us1_criar.py::test_marcacao_e_script_voltam_literalmente_como_texto`; `adversarial/cartoes/test_criar_adversarial.py::test_bidirecional_e_largura_zero_no_meio_do_texto_voltam_literais`; `adversarial/cartoes/test_editar_adversarial.py::test_marcacao_e_invisiveis_no_meio_voltam_literais_na_edicao`; `funcionalidades/cartoes/AbaCartoes.test.tsx`; regra de lint contra `dangerouslySetInnerHTML` (`eslint.config.js`); verificação no navegador (T019) | T002 T010 T013 T017 T041 |
| RQ-002 | `security/test_isolamento_rotas.py` (8 rotas da 003, cada uma com o teste do arquivo de segurança que a cobre); `security/cartoes/test_cartoes_seguranca.py`, `test_editar_seguranca.py`, `test_situacao_seguranca.py`; FKs compostas em `integration/cartoes/test_restricoes.py::test_cartao_numa_materia_de_outro_dono_e_recusado`; exclusão da conta em `security/cartoes/test_situacao_seguranca.py::test_excluir_a_conta_apaga_os_cartoes_dela_e_preserva_os_de_outra_conta` e `integration/cartoes/test_participante.py::test_exclusao_da_conta_apaga_todos_os_cartoes_do_usuario_e_so_os_dele` | T003 T012 T023 T029 |
| RQ-003 | `vitest-axe` em `PainelCartao`, `AbaCartoes`, `EdicaoCartao`, `SituacaoCartao`, `BuscaCartoes` e `AbasMateria`; `SeloOrigem` com texto e ícone; verificação no Chromium (T019, T027, T033 e T040: teclado, axe WCAG 2.2 AA nos dois temas, 320 px sem rolagem horizontal). Leitor de tela: rodada final do projeto (decisão de 15/10/2026) | T006 T017 T025 T031 T038 T042 |

## Critérios de sucesso

| Critério | Verificação | Tarefas |
|---|---|---|
| CS-001 | `funcionalidades/cartoes/PainelCartao.test.tsx` (atalhos e foco); cinco cartões só com o teclado no navegador (T019). O tempo de uma pessoa (3 min) fica para o teste guiado com pessoas | T017 T019 |
| CS-002 | `integration/cartoes/test_edicao_fsrs.py`; `functional/cartoes/test_us2_editar.py::test_cs002_vinte_edicoes_nao_mudam_vencimento_nem_estabilidade`; 24 edições conferidas no banco (T027) | T004 T021 T022 T027 |
| CS-003 | Na 003, situação `suspenso` e agendamento preservado (`functional/cartoes/test_us3_suspender_excluir.py::test_suspender_e_reativar_mantem_as_colunas_do_fsrs_em_qualquer_estado`). Ausência em todas as lições: reverificação pela 005 (obrigação no plano) | T028 |

## Casos de borda

| Caso de borda | Teste | Tarefas |
|---|---|---|
| Frente, verso ou explicação só com espaços | `unit/cartoes/test_dominio.py::test_frente_e_verso_vazios_ou_invisiveis_sao_recusados`, `::test_explicacao_vazia_vira_none`; `adversarial/cartoes/test_criar_adversarial.py::test_texto_so_de_caracteres_invisiveis_ou_proibidos_vale_como_vazio` | T008 T010 |
| Texto com marcação ou script | ver RQ-001 | T010 T013 T017 |
| Suspenso ou excluído durante uma lição aberta (CB-27) | A 003 não guarda estado de lição; a verificação de ponta a ponta fica com a 005 (obrigação no plano) | — |
| Edição concorrente em duas abas | `adversarial/cartoes/test_editar_adversarial.py::test_duas_edicoes_simultaneas_a_ultima_vale_sem_erro`; `integration/cartoes/test_edicao_fsrs.py::test_duas_edicoes_simultaneas_de_campos_diferentes_nao_se_desfazem`, `::test_agendamento_e_edicao_em_paralelo_as_duas_sobrevivem` | T021 T023 |
| Fonte de referência excluída, inclusive com "Excluir os cartões junto" (D-006) | `functional/fontes/test_us2_exclusao_fonte.py::test_excluir_a_fonte_mantem_os_cartoes_de_referencia_com_fonte_apagada`; `integration/cartoes/test_participante.py::test_excluir_fonte_anula_fonte_id_nos_dois_modos_e_mantem_a_copia`; `adversarial/cartoes/test_criar_adversarial.py::test_criar_com_referencia_durante_a_exclusao_da_fonte_nunca_cita_fonte_inexistente` | T009 T011 T013 |
| Cartão aguardando revisão fora da lista | `functional/cartoes/test_us1_criar.py::test_cartao_aguardando_revisao_nao_aparece_na_lista_nem_no_total`; `security/cartoes/test_editar_seguranca.py::test_cartao_aguardando_revisao_ou_recusado_e_404_na_consulta_e_na_edicao`; `security/cartoes/test_situacao_seguranca.py::test_cartao_aguardando_revisao_ou_recusado_nao_e_suspenso_reativado_nem_excluido`; reexecução pela 004 com dados reais | T010 T023 T029 |

## Decisões técnicas

| Decisão | Teste que a sustenta | Tarefas |
|---|---|---|
| DTEC 027, emenda (`cartoes_suspensos`) | `integration/cartoes/test_participante.py::test_conta_ativos_e_suspensos_separados_de_qualquer_origem`; `functional/materias/test_us3_organizar.py::test_exclusao_apaga_todos_os_cartoes_da_materia_e_so_os_dela`; `functional/fontes/test_us2_exclusao_fonte.py::test_cartao_suspenso_que_cita_a_fonte_tambem_conta_e_e_mantido` | T009 T011 T015 |
| DTEC 033 (busca com `unaccent`) | `integration/cartoes/test_busca.py`; `integration/cartoes/test_restricoes.py::test_extensao_unaccent_existe_e_remove_acentos`; `integration/test_migracoes.py::test_migracao_0004_dos_cartoes_sobe_e_desce`; medição da T043 | T003 T034 T037 T043 |
| DTEC 034 (paginação por cursor) | `unit/cartoes/test_cursor.py`; `integration/cartoes/test_repositorio.py::test_paginacao_percorre_tudo_sem_repetir_nem_pular`; `functional/cartoes/test_us4_encontrar.py::test_cursor_reaproveitado_com_outros_filtros_e_422_cursor_invalido` | T008 T009 T035 |
| DTEC 035 (referência à fonte) | `integration/cartoes/test_restricoes.py::test_apagar_fonte_citada_falha_por_restrict`; `integration/cartoes/test_participante.py::test_excluir_fonte_anula_fonte_id_nos_dois_modos_e_mantem_a_copia`; `integration/cartoes/test_repositorio.py::test_a_fonte_de_referencia_fica_travada_com_for_share` | T003 T009 T013 |
| DTEC 036 (texto e limites) | `unit/nucleo/test_configuracao.py::test_limite_de_cartao_aceita_de_1_ate_o_teto`; `unit/cartoes/test_dominio.py`; `componentes/ui/CampoTextoLongo.test.tsx`; regra de lint | T001 T002 T006 T008 |
| DTEC 037 (agendamento, edição e situação) | `unit/cartoes/test_dominio.py::test_estado_inicial_espelha_o_card_novo_da_biblioteca_fixada`; `integration/cartoes/test_edicao_fsrs.py`; `adversarial/cartoes/test_situacao_adversarial.py::test_suspensao_repetida_em_paralelo_tem_um_unico_efeito` | T008 T021 T028 |
| DTEC 038 (fronteira com a 004) | `unit/cartoes/test_edicao.py`; `security/cartoes/test_editar_seguranca.py::test_cartao_aguardando_revisao_ou_recusado_e_404_na_consulta_e_na_edicao`; `integration/cartoes/test_participante.py`; `arquitetura/test_camadas.py` | T005 T009 T020 T023 |

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
- ~~**Nomes de teste:** os nomes exatos são confirmados na implementação e consolidados na T045.~~ Consolidados em 29/10/2026.

## Conferência depois da implementação (T045, 29/10/2026)

- **Referências:** as 80 funções de teste citadas (`::test_...`) e todos os arquivos de teste desta matriz foram conferidos por script contra `backend/tests/` e `frontend/src/`; nenhuma ausente.
- **Requisitos sem teste ou tarefa:** nenhum. A RF-004 ganhou a T035 (o filtro por situação, pedido na T028, chegou com a US4).
- **Divergências registradas na implementação:** a T011 acrescentou testes com cartões reais nos arquivos da 002 em vez de parametrizar os antigos, que seguem com o participante falso dos cartões gerados (da 004); a T028 testou o suspenso na lista sem filtro e deixou o filtro para a T035.
- **Dependem de pessoas:** o tempo do CS-001 (3 minutos, teste guiado) e a parte de leitor de tela do RQ-003 (rodada final do projeto, decisão de 15/10/2026).
- **Dependem das próximas specs:** as lacunas aceitas acima (005, 006 e 004) continuam como obrigações no [plano](plan.md#obrigações-registradas-para-as-próximas-specs).
