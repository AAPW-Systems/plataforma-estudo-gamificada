# Rastreabilidade

**Funcionalidade:** 002-materias-fontes (matérias, envio e processamento de fontes)  
**Data:** 13/10/2026 ([registro](../../prompts/2026-10-13-002-materias-fontes-plano.md)); nomes reais dos testes consolidados em 15/10/2026 (T051, [registro](../../prompts/2026-10-15-002-materias-fontes-implementacao-2.md))  
**Status:** aprovada em 13/10/2026 por Artur Lins (equipe), junto com as [tarefas](tasks.md)

Esta matriz mostra que requisito, cenário, teste e tarefa descrevem o mesmo comportamento. Os nomes de teste abaixo são os **reais** (T051): cada `arquivo::função` existe em `backend/tests/` e é conferido por um script na sessão de fechamento (ver o registro). Os caminhos são relativos a `backend/tests/`, salvo os do frontend, que ficam em `frontend/src/` e são citados pelo arquivo. A coluna de tarefas é a da matriz aprovada.

## Requisitos funcionais

| Requisito | Cenário ou caso de borda | Testes | Tarefas |
|---|---|---|---|
| RF-001 | US1-1, US3-1, US3-2; duas criações com o mesmo nome em caixas diferentes | `unit/materias/test_dominio.py::test_nomes_de_1_a_60_caracteres_sao_aceitos`, `::test_nome_com_61_caracteres_e_recusado`; `functional/fontes/test_us1_materia_fonte.py::test_cria_materia`, `::test_nome_repetido_sem_diferenciar_caixa_e_recusado`, `::test_nome_invalido_e_recusado_com_o_erro_junto_do_campo`; `functional/materias/test_us3_organizar.py::test_renomear_para_nome_livre_aparece_na_lista_e_na_consulta`, `::test_nome_de_outra_materia_e_recusado_sem_diferenciar_caixa`, `::test_nome_invalido_na_renomeacao_e_422_junto_do_campo`; `adversarial/fontes/test_envio_adversarial.py::test_materias_mesmo_nome_simultaneas`; `adversarial/materias/test_organizar_adversarial.py::test_duas_renomeacoes_para_o_mesmo_nome_uma_e_recusada`; `integration/fontes/test_restricoes.py::test_nome_da_materia_e_unico_por_estudante_sem_diferenciar_caixa`; frontend `FormularioMateria.test.tsx`, `RenomearMateria.test.tsx` | T008 T014 T019 T022 T023 T040 T043 |
| RF-002 | US1-1; lista com contagens | `functional/fontes/test_us1_materia_fonte.py::test_lista_materias_ordenada_por_nome_com_contagens`; `unit/nucleo/test_participantes_acervo.py::test_contar_por_materia_soma_os_participantes_e_materias_ausentes_valem_zero`; `functional/materias/test_us3_organizar.py::test_impacto_mostra_o_nome_e_as_contagens_com_suspensos_somados` (a lista mostra só os ativos); frontend `ListaMaterias.test.tsx` | T005 T019 T023 T025 T029 T030 |
| RF-003 | US1-2; título ausente; nome vazio depois da sanitização | `unit/fontes/test_dominio.py::test_titulo_padrao_e_o_nome_sem_a_extensao`, `::test_titulo_padrao_vazio_ou_invisivel_vira_fonte_sem_titulo`; `functional/fontes/test_us1_materia_fonte.py::test_envia_pdf_sem_titulo_usa_o_nome_do_arquivo_sem_a_extensao`, `::test_titulo_fora_dos_limites_e_recusado` | T015 T019 T024 T025 T027 |
| RF-004 | US1-4; arquivo vazio, codificação inválida, PDF protegido, tipo trocado | `unit/fontes/test_validacao.py` (uma linha por verificação da DTEC 028, ex.: `::test_a_ordem_das_verificacoes_e_a_da_dtec_028`); `functional/fontes/test_us1_materia_fonte.py::test_cs002_invalidos_recusados`, `::test_extensao_nao_aceita_e_formato_nao_aceito`, `::test_pdf_com_501_paginas_e_recusado`; `adversarial/fontes/test_envio_adversarial.py::test_disfarcados_zip_com_extensao_md_e_pdf_com_extensao_txt`, `::test_corpo_acima_do_limite_pelo_content_length_vira_413_sem_ler_o_corpo`, `::test_corpo_acima_do_limite_sem_content_length_tambem_vira_413`; `unit/nucleo/test_middlewares.py::test_rota_de_envio_acima_do_limite_pelo_content_length_vira_413_arquivo_muito_grande` | T006 T016 T019 T022 T024 T027 |
| RF-005 | US1-2; atualização sem recarregar | `integration/fontes/test_processar_fonte.py::test_estados_sucesso_grava_trechos_e_conclui_na_mesma_transacao`, `::test_estados_a_fonte_fica_processando_enquanto_o_arquivo_e_extraido`; `functional/fontes/test_us1_materia_fonte.py::test_envia_pdf_e_acompanha_ate_concluido_com_trechos_e_paginas`, `::test_a_listagem_traz_o_estado_de_cada_fonte_para_o_acompanhamento`; frontend `AcervoFontes.test.tsx` (polling e anúncio), `src/api/acompanhamento.test.ts` | T012 T020 T026 T029 T030 |
| RF-006 | US1-3; página só quando conhecida | `unit/fontes/test_divisao.py` (`::test_invariantes_em_pdf_nenhum_trecho_atravessa_paginas`, `::test_pdf_um_trecho_por_pagina_com_a_pagina_fisica`, `::test_invariantes_em_texto_com_parametros_padrao`); `integration/fontes/test_extracao.py::test_paginas_fisicas_dos_trechos_conferem_com_a_fabrica`, `::test_txt_nao_tem_pagina_nem_total_de_paginas`; `functional/fontes/test_us1_materia_fonte.py::test_cs001_validos_concluem_com_paginas` | T017 T018 T019 T024 T026 |
| RF-007 | US1-5, US1-6 | `unit/fontes/test_dominio.py::test_catalogo_falhas_tem_uma_mensagem_em_portugues_por_codigo`, `::test_catalogo_falhas_so_a_falha_tecnica_permite_nova_tentativa`; `functional/fontes/test_us1_materia_fonte.py::test_pdf_sem_texto_falha_com_explicacao_e_sem_nova_tentativa`, `::test_nova_tentativa_apos_falha_tecnica_nao_duplica_trechos`; `integration/fontes/test_processar_fonte.py::test_pdf_sem_texto_vira_falhou_sem_texto_e_nao_gera_trecho`, `::test_tentativas_esgotadas_gravam_falha_tecnica_sem_relancar`; frontend `AcervoFontes.test.tsx` ("Tentar novamente" só com `podeTentarNovamente`), `PainelFonte.test.tsx` | T015 T018 T019 T020 T025 T026 T029 |
| RF-008 | US1-6; duas novas tentativas paralelas; reexecução de fonte concluída | `integration/fontes/test_processar_fonte.py::test_reexecucao_concluida_sem_efeito_nao_substitui_os_trechos`, `::test_execucao_anterior_incompleta_nao_deixa_trechos_duplicados`, `::test_erro_transitorio_seguido_de_sucesso_conclui_na_tentativa_seguinte`; `integration/nucleo/test_tarefas_travadas.py::test_job_de_worker_sem_sinal_de_vida_volta_para_a_fila`; `adversarial/fontes/test_envio_adversarial.py::test_novas_tentativas_paralelas` | T007 T020 T022 T025 T026 |
| RF-009 | US1-3 | `functional/fontes/test_us1_materia_fonte.py::test_envia_pdf_e_acompanha_ate_concluido_com_trechos_e_paginas` (título, arquivo, tipo, tamanho, páginas e trechos); frontend `PainelFonte.test.tsx` | T019 T025 T027 T029 T030 |
| RF-010 | US2-1 a US2-6 | `functional/fontes/test_us2_exclusao_fonte.py` (cenários 1 a 6); `adversarial/fontes/test_exclusao_fonte_adversarial.py`; `unit/fontes/test_exclusao.py`; frontend `DialogoExclusaoFonte.test.tsx` | T005 T032 T033 T036 T037 T038 |
| RF-011 | US3-3, US3-4; matéria com fontes em processamento | `functional/materias/test_us3_organizar.py::test_exclusao_exige_o_nome_digitado_e_recusa_com_422_sem_apagar_nada`, `::test_exclusao_apaga_materia_fontes_trechos_e_objetos_e_chama_os_participantes_na_ordem`; `adversarial/materias/test_organizar_adversarial.py` (exclusão durante o processamento, durante um envio, impacto alterado, paralelas, falhas e confirmação por caixa e extremidades); `unit/materias/test_dominio.py::test_confirmacao_diferencia_caixa_e_exige_o_nome_inteiro`; frontend `DialogoExclusaoMateria.test.tsx`, `CabecalhoMateria.test.tsx` | T040 T041 T043 T044 T045 |
| RF-012 | Cota atingida (50, 30, 100 MB); `falhou` ocupa cota; envios simultâneos acima da cota | `functional/fontes/test_us1_materia_fonte.py::test_cota_de_materias_atingida`, `::test_cota_de_fontes_da_materia_conta_a_fonte_que_falhou`, `::test_cota_de_armazenamento_soma_todas_as_fontes_do_estudante`; `adversarial/fontes/test_envio_adversarial.py::test_cota_simultanea_de_fontes_aceita_so_uma`, `::test_cota_simultanea_de_armazenamento_aceita_so_uma`, `::test_cota_simultanea_de_materias_aceita_so_uma`; `functional/fontes/test_us2_exclusao_fonte.py::test_fonte_em_qualquer_estado_pode_ser_excluida`; frontend `DialogoExclusaoFonte.test.tsx` (ação em `falhou`) | T002 T019 T022 T023 T025 T038 |
| RF-013 | Fonte excluída durante o processamento (CB-16) | `integration/fontes/test_processar_fonte.py::test_fonte_apagada_antes_da_gravacao_termina_sem_trechos`; `adversarial/fontes/test_exclusao_fonte_adversarial.py::test_excluir_durante_a_extracao_nao_deixa_trecho_nenhum`, `::test_job_que_sobrou_na_fila_termina_sem_efeito_e_sem_erro`; `adversarial/materias/test_organizar_adversarial.py::test_excluir_a_materia_durante_a_extracao_nao_deixa_trecho_nenhum` | T020 T026 T034 T036 |
| RF-014 | US1-7; mesmo arquivo em outra matéria; envios simultâneos do mesmo arquivo | `functional/fontes/test_us1_materia_fonte.py::test_fonte_duplicada_na_mesma_materia_e_recusada_com_o_titulo_existente`, `::test_mesmo_arquivo_em_outra_materia_e_aceito`, `::test_conteudo_igual_com_nome_diferente_tambem_e_duplicata`; `adversarial/fontes/test_envio_adversarial.py::test_envios_simultaneos_mesmo_arquivo`, `::test_rajada_do_mesmo_arquivo_aceita_so_uma_copia`; `integration/fontes/test_restricoes.py::test_conteudo_identico_na_mesma_materia_e_recusado_mas_vale_em_outra` | T008 T019 T022 T025 |
| RF-015 | US3-5 | `functional/materias/test_us3_organizar.py::test_renomear_a_fonte_altera_so_o_titulo`, `::test_titulo_de_1_a_120_caracteres_e_aceito`, `::test_titulo_invalido_e_422_junto_do_campo`, `::test_renomear_fonte_que_falhou_e_permitido`; frontend `RenomearFonte.test.tsx` | T040 T043 T044 T045 |
| RF-016 | US1-8 | `functional/fontes/test_us1_materia_fonte.py::test_pouco_texto_conclui`; `integration/fontes/test_extracao.py::test_um_paragrafo_gera_um_trecho_e_chega_a_ser_processado`; `unit/fontes/test_divisao.py::test_um_paragrafo_curto_e_um_so_trecho_sem_pagina` | T017 T019 T024 |

## Requisitos de qualidade

| Requisito | Testes ou evidência | Tarefas |
|---|---|---|
| RQ-001 | `unit/fontes/test_dominio.py::test_nome_exibido_nunca_tem_caminho_controle_nem_passa_de_255`; `security/fontes/test_acervo_seguranca.py::test_chave_sem_nome_enviado`, `::test_chave_do_objeto_pertence_ao_prefixo_do_dono_e_a_api_nunca_a_expoe`; `adversarial/fontes/test_envio_adversarial.py::test_nomes_maliciosos_sao_so_exibidos_e_nunca_viram_caminho` | T004 T015 T021 T022 |
| RQ-002 | `security/fontes/test_acervo_seguranca.py::test_logs_sem_conteudo`, `::test_logs_da_falha_e_da_recusa_nao_trazem_caminho_nem_excecao_com_dados`; revisão dos logs reais de `api` e `worker` (T048) | T021 T048 |
| RQ-003 | `security/test_isolamento_rotas.py` (11 rotas da 002 com identificador, cada uma com o seu teste de duas contas em `security/fontes/test_acervo_seguranca.py`); `integration/fontes/test_restricoes.py::test_fonte_numa_materia_de_outro_dono_e_recusada_pela_fk_composta`; `security/identidade/test_exclusao_completa.py::test_excluir_a_conta_apaga_materias_fontes_trechos_e_objetos_e_preserva_a_outra_conta` | T008 T021 T035 T042 |
| RQ-004 | axe nos testes de componente (`acervo.test.tsx` e os de cada tela e diálogo); axe no Chromium real em 2 temas e a 320 px, com os dois diálogos abertos (T048); leitor de tela: rodada única no final do projeto (decisão de 15/10/2026) | T012 T029 T037 T044 T048 |
| RQ-005 | `unit/nucleo/test_configuracao.py::test_nao_sobe_com_cota_ou_limite_menor_que_1`; `functional/fontes/test_us1_materia_fonte.py::test_uso_acervo_traz_os_limites_vigentes_e_o_uso`, `::test_o_limite_de_tamanho_configurado_vale_para_o_envio`; `integration/test_contrato_openapi.py`; frontend `EnvioFonte.test.tsx` (limites vindos da API) | T002 T019 T027 T028 T029 |

## Critérios de sucesso

| Critério | Verificação | Tarefas |
|---|---|---|
| CS-001 | `functional/fontes/test_us1_materia_fonte.py::test_cs001_validos_concluem_com_paginas` (10 arquivos gerados) | T010 T019 |
| CS-002 | `functional/fontes/test_us1_materia_fonte.py::test_cs002_dez_invalidos_nenhum_gera_trecho_e_todos_tem_explicacao_especifica` (10 arquivos gerados) | T010 T019 |
| CS-003 | `functional/fontes/test_us1_materia_fonte.py::test_cs003_pdf_de_2mb_chega_a_concluido_em_menos_de_60_segundos`; medição no Chromium e na API (T049): cerca de 9 s | T019 T031 T049 |
| CS-004 | `functional/fontes/test_us2_exclusao_fonte.py::test_cs004_contagens_exibidas_iguais_as_recebidas_e_ao_apagado`; `functional/materias/test_us3_organizar.py::test_cs004_contagens_exibidas_sao_as_apagadas_na_exclusao_da_materia`; `adversarial/fontes/test_exclusao_fonte_adversarial.py::test_impacto_alterado_devolve_409_e_nao_apaga_nada`, `adversarial/materias/test_organizar_adversarial.py::test_impacto_alterado_devolve_409_e_nao_apaga_nada` | T033 T034 T040 T041 |

## Casos de borda

| Caso de borda | Testes | Tarefas |
|---|---|---|
| Envio interrompido (CB-04) | `adversarial/fontes/test_envio_adversarial.py::test_envio_interrompido_no_meio_nao_guarda_nada_e_apaga_o_temporario` | T022 |
| Fonte excluída durante o processamento (CB-16) | ver RF-013 | T020 T034 |
| Matéria excluída com fontes em processamento | `adversarial/materias/test_organizar_adversarial.py::test_excluir_a_materia_durante_a_extracao_nao_deixa_trecho_nenhum`; durante um envio: `::test_excluir_a_materia_durante_um_envio_da_404_e_o_objeto_e_compensado` | T041 |
| Matéria excluída com geração em andamento | Coberto pela 004 (participante das gerações, DTEC 027); na 002, os participantes falsos confirmam a chamada: `functional/materias/test_us3_organizar.py::test_exclusao_apaga_materia_fontes_trechos_e_objetos_e_chama_os_participantes_na_ordem` | T040 |
| Exclusão com cartões numa lição aberta (CB-27) | Na 002, a exclusão não toca revisões, XP nem sequência (tabelas da 005 e da 006); a verificação de ponta a ponta fica com a 005 | T033 T040 |
| Arquivo vazio, codificação inválida, PDF com senha | `unit/fontes/test_validacao.py`; `functional/fontes/test_us1_materia_fonte.py::test_cs002_dez_invalidos_nenhum_gera_trecho_e_todos_tem_explicacao_especifica` | T016 T019 |
| Nome com caminho, controles ou mais de 255 caracteres | ver RQ-001 | T015 T022 |
| Mesmo arquivo duas vezes; em matérias diferentes; simultâneo | ver RF-014 | T019 T022 |
| Cota atingida; `falhou` ocupa cota; envios simultâneos acima da cota | ver RF-012 | T019 T022 |
| Texto com instruções à IA (CB-15) | `adversarial/fontes/test_envio_adversarial.py::test_instrucoes_guardadas_como_conteudo`; `integration/fontes/test_extracao.py::test_instrucoes_a_ia_no_texto_viram_trecho_comum` | T022 |

## Decisões técnicas

| Decisão | Testes que a sustentam | Tarefas |
|---|---|---|
| DTEC 024 (isolamento) | `integration/nucleo/test_isolamento.py`; `integration/fontes/test_extracao.py::test_pdf_que_estoura_o_tempo_devolve_conteudo_invalido` | T003 T018 |
| DTEC 025 (armazenamento e banco) | `integration/nucleo/test_armazenamento_contrato.py`; `integration/fontes/test_processar_fonte.py::test_rollback_compensa_objeto_e_nao_deixa_linha_nem_job`, `::test_reconciliacao_apaga_so_orfaos_mais_antigos_que_a_margem` | T004 T020 T025 T026 |
| DTEC 026 (acompanhamento) | `frontend/src/api/acompanhamento.test.ts`; `AcervoFontes.test.tsx` | T012 T029 |
| DTEC 027 (participantes) | `unit/nucleo/test_participantes_acervo.py` (inclui o gancho opcional `travar_materia`); testes da US2 e da US3 com os participantes falsos; `arquitetura/test_camadas.py::test_camadas_respeitam_dtec018` | T005 T009 T033 T040 |
| DTEC 028 (validação) | `unit/fontes/test_validacao.py`; `unit/nucleo/test_middlewares.py::test_rota_de_envio_aceita_ate_o_seu_limite` | T006 T016 |
| DTEC 029 (extração e divisão) | `unit/fontes/test_divisao.py`; `integration/fontes/test_extracao.py` (hifenização desfeita: `::test_hifenizacao_do_pdf_e_desfeita_depois_da_extracao` e `unit/fontes/test_extracao.py`, emenda de 15/10/2026) | T017 T018 |
| DTEC 030 (estados e tentativas) | `integration/fontes/test_processar_fonte.py`; `integration/nucleo/test_tarefas_travadas.py`; `integration/nucleo/test_worker.py` | T007 T020 T026 |
| DTEC 031 (impacto sob concorrência) | `adversarial/fontes/test_exclusao_fonte_adversarial.py::test_impacto_alterado_devolve_409_e_nao_apaga_nada`; `adversarial/materias/test_organizar_adversarial.py::test_impacto_alterado_devolve_409_e_nao_apaga_nada`, `::test_a_fonte_travada_por_outra_transacao_faz_a_exclusao_esperar_e_recalcular` | T034 T041 |
| DTEC 032 (cotas e duplicatas) | `adversarial/fontes/test_envio_adversarial.py::test_cota_simultanea_de_fontes_aceita_so_uma`, `::test_envios_simultaneos_mesmo_arquivo` | T022 T023 T025 |

## Tarefas de suporte

Tarefas que não implementam um requisito isolado, mas sustentam todos ou produzem a evidência de uma história.

| Tarefas | Papel | Requisitos sustentados |
|---|---|---|
| T001, T002 | Dependências e configuração | Todos; RQ-005 |
| T008, T010, T011 | Migração, fábricas de arquivos e saúde do armazenamento | Todos os RF; CS-001 e CS-002 |
| T013, T031, T039, T046 | Evidência da base e do teste independente de cada história | Cenários de cada história |
| T028 | Contrato gerado e tipos do frontend | RQ-005 e todos os RF expostos pela API |
| T047, T049, T050, T051 | Suítes completas, medições, documentação e atualização desta matriz | Regra 17; CS-003; quickstart |

## Análise de consistência (etapa 7)

Conferência feita em 13/10/2026 entre spec, plano, pesquisa, modelo de dados, contrato, quickstart e tarefas.

| Verificação | Resultado |
|---|---|
| Todo RF, RQ e CS da spec tem teste planejado e tarefa | Sim: RF-001 a RF-016, RQ-001 a RQ-005 e CS-001 a CS-004 |
| Todo cenário de aceitação tem teste funcional | Sim: US1-1 a US1-8 (T019), US2-1 a US2-6 (T033), US3-1 a US3-5 (T040) |
| Todo caso de borda da spec tem teste | Sim. Duas bordas dependem de outras specs e estão registradas como lacunas aceitas: geração em andamento (004) e lição aberta (005) |
| Toda tarefa cita caminho exato e resultado verificável | Sim |
| Toda tarefa aparece na matriz | Sim: T001 a T051, nas tabelas acima ou em "Tarefas de suporte" |
| Tarefas organizadas por história, não por camada | Sim: Fases 3 a 5, uma por história; a base compartilhada só tem o que todas as histórias usam |
| Contrato coerente com a spec e o plano | Sim: 14 operações, 11 com identificador no caminho, todas na tabela de isolamento. Todo erro usa o esquema `Erro`, e os códigos da 001 foram mantidos |
| Modelo de dados coerente com o esquema | Sim: o esquema foi atualizado nesta sessão (`codigo_falha`, `versao_extracao`, `total_trechos`, título com 120 caracteres, índices) |
| Exigências do PO | Nenhuma toca a 002 diretamente (spec, seção "Exigências do PO"); EX-02 e EX-03 dependem das fontes processadas aqui e são cobertas pela 004 |
| Requisito enfraquecido no plano | Nenhum. O CS-004 é reforçado pela conferência das contagens na confirmação (DTEC 031) |
| Tecnologia fora da stack aprovada | Nenhuma. PyMuPDF já estava na DTEC 009; `python-multipart` é exigido pelo FastAPI para formulários; as decisões novas estão nas DTEC 024 a 032, aprovadas com o plano |

## Conferência depois da implementação (T051, 15/10/2026)

| Verificação | Resultado |
|---|---|
| Todo RF, RQ e CS tem teste com nome real | Sim: 130 referências `arquivo::função` das tabelas acima foram conferidas contra os arquivos de `backend/tests/` (nenhuma ausente); os testes do frontend são citados pelo arquivo |
| Requisito sem teste ou sem tarefa | Nenhum |
| Tarefa sem requisito | Nenhuma: as tarefas de suporte continuam na tabela própria |
| Requisito que depende de uma pessoa | RQ-004 (leitor de tela): por decisão de 15/10/2026, a rodada com leitor de tela é única e fica para o final do projeto. A T013 (Compose no Docker Desktop) foi verificada por Artur Lins em 15/10/2026 ([registro](../../prompts/2026-10-15-002-materias-fontes-implementacao-2.md)) |
| Teste que só caracteriza um comportamento | Só o limite conhecido da regra de hifenização (`unit/fontes/test_extracao.py::test_limite_conhecido_composto_com_hifen_no_fim_da_linha_tambem_e_juntado`); o problema do PyMuPDF foi resolvido pela emenda da DTEC 029 |

## Lacunas aceitas antes da implementação

- **Cartões reais na exclusão:** as US2 e US3 são verificadas com um participante falso. A verificação com cartões reais fica nas tarefas da 003 e da 004, que reexecutam estes testes funcionais (DTEC 027).
- **Lição aberta (CB-27):** só é verificável de ponta a ponta com as lições da 005. A 002 garante que a exclusão não toca revisões, XP nem sequência.
- **Geração em andamento:** a interrupção da geração na exclusão é obrigação da 004 (participante das gerações e `FOR SHARE` na fonte, DTEC 031).
- **Nomes de teste:** consolidados na T051 (15/10/2026): as tabelas acima trazem os nomes reais.
- **Parâmetros da divisão:** 1.200, 2.000 e 150 caracteres são valores iniciais (DTEC 029); a avaliação da 004 pode ajustá-los por configuração.
