# Rastreabilidade

**Funcionalidade:** 001-conta-acesso (conta, sessão, isolamento e preferências)  
**Data:** 12/10/2026 ([registro](../../prompts/2026-10-12-001-conta-acesso-plano.md)); nomes reais dos testes consolidados em 14/10/2026 (T065, [registro](../../prompts/2026-10-13-001-conta-acesso-implementacao-4.md))  
**Status:** aprovada em 13/10/2026 por Artur Lins (equipe)

Esta matriz mostra que requisito, cenário, teste e tarefa descrevem o mesmo comportamento. Os nomes abaixo são os **reais**, conferidos contra o código em 14/10/2026 (backend: 748 testes; frontend: 75). Os caminhos de teste do backend são relativos a `backend/tests/`; os do frontend começam por `frontend/src/`. Onde um grupo tem vários testes parecidos, o prefixo comum aparece seguido de `*` e o arquivo é a referência exata.

## Requisitos funcionais

| Requisito | Cenário ou caso de borda | Testes | Tarefas |
|---|---|---|---|
| RF-001 | US1-1; bordas de nome e e-mail | `unit/identidade/test_dominio.py::test_nome_*` e `::test_email_*` (NFC, 100/101 caracteres, controle e direção, 254 caracteres); `functional/identidade/test_us1_conta_entrada.py::test_cenario1_cadastro_cria_estudante_com_padroes_e_ja_entra`, `::test_cenario1_normaliza_nome_e_email`; `adversarial/identidade/test_autenticacao_adversarial.py::test_nome_com_unicode_malicioso_e_recusado`, `::test_emails_hostis_sao_recusados_no_cadastro`, `::test_nome_de_100_caracteres_aceito_e_de_101_recusado` | T029 T030 T033 T036 |
| RF-002 | US1-2; senha com mais de 128 caracteres ou só com espaços | `unit/identidade/test_dominio.py::test_senha_*` (8 e 128, curta, acima de 128, só espaços, lista comum em qualquer caixa); `functional/.../test_us1_conta_entrada.py::test_cenario2_senha_curta_ou_comum_e_recusada_junto_do_campo`, `::test_cenario2_lista_todos_os_campos_invalidos_de_uma_vez`; `adversarial/.../test_autenticacao_adversarial.py::test_senha_com_substituto_isolado_e_recusada_no_cadastro_sem_erro_500` | T028 T029 T030 T033 |
| RF-003 | US1-1 | `security/identidade/test_autenticacao.py::test_todo_cadastro_publico_cria_estudante`, `::test_nenhum_campo_extra_e_aceito_no_cadastro`; `adversarial/identidade/test_perfil_adversarial.py::test_campos_extras_sao_recusados_e_nada_muda` (o papel não é campo alterável) | T031 T036 T048 T049 |
| RF-004 | US1-3, US1-4 | `functional/.../test_us1_conta_entrada.py::test_cenario3_*`, `::test_cenario4_senha_errada_e_email_inexistente_tem_a_mesma_resposta`; `security/identidade/test_autenticacao.py::test_entrada_tem_corpo_e_status_identicos_para_conta_inexistente_e_senha_errada`, `::test_entrada_com_senha_de_substituto_isolado_nao_quebra_nem_distingue` | T030 T031 T035 T036 |
| RF-005 | US1-6; tentativas distribuídas a partir do mesmo endereço | `unit/identidade/test_limites.py::test_*` (janela, bloqueio, borda, cadastro); `security/.../test_autenticacao.py::test_bloqueio_por_conta_nao_afeta_outras_contas`, `::test_bloqueio_por_endereco_apos_20_falhas_mesmo_com_senha_certa`, `::test_endereco_bloqueado_nao_afeta_outro_endereco`; `functional/.../test_us1_conta_entrada.py::test_cenario6_*`; `adversarial/.../test_autenticacao_adversarial.py::test_rajada_paralela_de_entradas_erradas_respeita_o_limite_da_conta`, `::test_rajada_com_a_senha_certa_no_meio_nao_burla_o_bloqueio`, `::test_rajada_de_limite_por_endereco_nao_ultrapassa_20_falhas`, `::test_x_forwarded_for_forjado_nao_contorna_o_limite_por_endereco`; `unit/nucleo/test_rede.py::test_*` | T012 T031 T032 T034 T035 |
| RF-006 | US1-5; sair numa aba invalida as duas | `unit/nucleo/test_seguranca.py::test_sessao_expira_por_inatividade_em_14_dias`, `::test_sessao_expira_no_limite_absoluto_mesmo_com_uso_constante`, `::test_sessao_revogada_nunca_volta_a_valer`; `functional/.../test_us1_conta_entrada.py::test_cenario5_sair_invalida_a_sessao_no_servidor`, `::test_sessao_expira_apos_14_dias_sem_uso`, `::test_sessao_expira_30_dias_apos_a_entrada_mesmo_com_uso`; `security/.../test_autenticacao.py::test_sair_apaga_os_cookies_e_revoga_no_servidor`, `::test_resposta_401_apaga_os_cookies` | T020 T030 T035 |
| RF-007 | US2-1, US2-2; recurso de outro estudante em qualquer operação | `security/test_isolamento_rotas.py::test_toda_rota_com_identificador_no_caminho_tem_caso_de_isolamento`, `::test_o_detector_acusa_rota_nova_com_identificador_sem_caso`, `::test_toda_rota_protegida_responde_401_sem_dados_sem_sessao`, `::test_perfil_e_saida_de_uma_conta_nao_afetam_a_outra`, `::test_alteracao_do_perfil_de_uma_conta_nao_afeta_a_outra`, `::test_senha_e_exclusao_de_uma_conta_nao_afetam_a_outra`, `::test_recurso_de_outro_dono_responde_404_identico_ao_inexistente`; `adversarial/.../test_perfil_adversarial.py::test_conta_nao_altera_o_perfil_de_outra` | T041 T043 |
| RF-008 | US3-1, US3-2 | `unit/identidade/test_preferencias.py::test_*`; `functional/identidade/test_us3_perfil.py::test_cenario1_*`, `::test_cenario2_*`; `adversarial/.../test_perfil_adversarial.py::test_alteracoes_simultaneas_de_campos_diferentes_nao_se_perdem`, `::test_inteiros_com_tipos_estranhos_sao_recusados`; `frontend/src/funcionalidades/identidade/FormularioPerfil.test.tsx` | T046 T047 T049 T051 |
| RF-009 | US1-1; fuso IANA inválido | `unit/identidade/test_dominio.py::test_fuso_*`, `::test_cadastro_com_fuso_*`; `functional/.../test_us1_conta_entrada.py::test_cenario1_fuso_ausente_ou_invalido_vira_sao_paulo`; `functional/.../test_us3_perfil.py::test_cenario4_fuso_novo_nao_mexe_em_dados_anteriores`; `adversarial/.../test_perfil_adversarial.py::test_fuso_hostil_e_recusado_sem_alterar_nada`; `frontend/src/funcionalidades/identidade/FormularioCadastro.test.tsx` ("envia os dados com o fuso detectado no navegador") | T029 T030 T033 T039 |
| RF-010 | US3-3 | `unit/revisao/test_parametros_fsrs.py::test_*`; `functional/.../test_us3_perfil.py::test_cenario3_*` (nova versão, mesmo valor, sequência, outras preferências, versão vigente); `functional/.../test_us1_conta_entrada.py::test_cenario1_cria_a_versao_1_dos_parametros_do_fsrs`; `adversarial/.../test_perfil_adversarial.py::test_trocas_de_retencao_concorrentes_geram_versoes_sem_lacuna_nem_duplicata`, `::test_trocas_concorrentes_do_mesmo_valor_criam_uma_so_versao`; `integration/test_migracoes.py::test_parametros_fsrs_check_no_banco` | T046 T047 T049 |
| RF-011 | US2-3 | `security/test_csrf_origem.py::test_*`; `unit/nucleo/test_seguranca.py::test_token_csrf_*`, `::test_origin_*`, `::test_sec_fetch_site_*`; `security/.../test_autenticacao.py::test_cadastro_e_entrada_exigem_o_token_anti_csrf`, `::test_origem_estranha_e_recusada_no_cadastro`; `adversarial/.../test_perfil_adversarial.py::test_alteracao_exige_csrf`; `frontend/src/api/cliente.test.ts` (renovação do token) | T020 T042 |
| RF-012 | US1-7; e-mail com outra caixa ou espaços | `functional/.../test_us1_conta_entrada.py::test_cenario7_email_em_uso_sem_diferenciar_caixa`; `adversarial/.../test_autenticacao_adversarial.py::test_dois_cadastros_simultaneos_com_o_mesmo_email_criam_uma_conta`, `::test_cadastro_reenviado_depois_do_sucesso_responde_409`, `::test_email_com_espacos_e_caixa_mista_e_o_mesmo_email`; `integration/test_migracoes.py::test_email_unico_sem_caixa`; `integration/identidade/test_repositorios.py::test_corrida_de_cadastros_com_o_mesmo_email_cria_uma_conta` | T030 T032 T034 |
| RF-013 | US1-8 | `frontend/src/funcionalidades/identidade/FormularioCadastro.test.tsx` ("RF-013 / cenário 8: mostra o aviso de privacidade, sem caixa de aceite"); `frontend/src/testes/fluxo-identidade.test.tsx` ("as telas públicas se ligam e têm o título e o aviso de privacidade esperados") | T038 T039 |
| RF-014 | US4-1, US4-2 | `functional/identidade/test_us4_senha_exclusao.py::test_cenario1_*`, `::test_cenario2_*`, `::test_troca_de_senha_exige_sessao`; `adversarial/identidade/test_exclusao_adversarial.py::test_trocas_de_senha_concorrentes_deixam_uma_unica_senha_valida`, `::test_troca_de_senha_revoga_as_outras_sessoes_mesmo_com_rajada`, `::test_corpos_hostis_na_troca_de_senha_sao_recusados`; `frontend/src/funcionalidades/identidade/FormularioSenha.test.tsx` | T053 T055 T056 T057 T058 |
| RF-015 | US4-3, US4-4; exclusão pedida duas vezes; processamento em andamento | `functional/.../test_us4_senha_exclusao.py::test_cenario4_*`; `security/identidade/test_exclusao_completa.py::test_*`; `adversarial/.../test_exclusao_adversarial.py::test_exclusao_pedida_duas_vezes_em_paralelo_tem_um_unico_efeito`, `::test_exclusao_pedida_de_duas_sessoes_da_mesma_conta_em_paralelo`, `::test_exclusao_com_a_conta_bloqueada_responde_429_e_nao_apaga`, `::test_corpos_hostis_na_exclusao_nunca_apagam_nada`; `unit/nucleo/test_exclusao.py::test_*`; `integration/identidade/test_tarefas.py::test_*`; `integration/nucleo/test_fila_transacao.py::test_*`, `integration/nucleo/test_worker.py::test_o_worker_registra_as_tarefas_da_identidade_num_processo_novo`; `frontend/src/funcionalidades/identidade/DialogoExclusao.test.tsx` (cenário 3 na interface) | T053 T054 T055 T056 T057 T058 |

## Requisitos de qualidade

| Requisito | Testes ou evidência | Tarefas |
|---|---|---|
| RQ-001 | `security/identidade/test_autenticacao.py::test_atributos_dos_cookies_de_sessao_e_csrf`, `::test_identificador_tem_256_bits_e_o_banco_guarda_so_o_sha256`, `::test_tentativas_guardam_so_a_chave_hmac_e_nunca_o_email`; `functional/.../test_us1_conta_entrada.py::test_o_banco_nao_guarda_a_senha_em_texto_legivel`; `functional/.../test_us4_senha_exclusao.py::test_cenario1_a_nova_senha_fica_guardada_so_como_hash`; `unit/nucleo/test_seguranca.py::test_hash_usa_o_perfil_de_pouca_memoria_da_rfc_9106` | T020 T031 |
| RQ-002 | `unit/nucleo/test_logs.py::test_chaves_sensiveis_sao_mascaradas`, `::test_mascaramento_alcanca_estruturas_aninhadas`, `::test_saida_json_numa_linha_sem_dados_sensiveis`; `security/.../test_autenticacao.py::test_logs_nao_registram_senha_email_cookie_nem_corpo`; revisão dos logs do ensaio real (T061, 14/10/2026: 212 linhas da `api` e 13 do `worker`, zero ocorrências) | T011 T031 T061 |
| RQ-003 | `security/.../test_autenticacao.py::test_bloqueio_por_conta_vale_igual_para_email_com_e_sem_conta`, `::test_limite_de_10_cadastros_por_hora_por_endereco`, `::test_cadastro_recusado_por_validacao_nao_consome_o_limite`; `functional/.../test_us4_senha_exclusao.py::test_cenario2_senha_atual_errada_nao_muda_nada_e_conta_para_o_limite`; `adversarial/.../test_exclusao_adversarial.py::test_rajada_de_exclusoes_erradas_nao_ultrapassa_o_limite_da_conta`; `unit/nucleo/test_configuracao.py::test_nao_sobe_com_limite_invalido` | T009 T031 T032 T034 |
| RQ-004 | Axe nos testes de componente: `frontend/src/funcionalidades/identidade/{FormularioCadastro,FormularioEntrada,FormularioPerfil,FormularioSenha,DialogoExclusao}.test.tsx` ("RQ-004: não tem violações do axe…") e `frontend/src/testes/fluxo-identidade.test.tsx` ("T039 / RQ-004", "T051 / RQ-004"); axe com contraste no navegador real (T061): 8 telas e estados nos dois temas, 0 violações; 320 px sem rolagem horizontal (T040, T052, T059); teclado: ordem de tabulação (T040), foco preso e `Esc` no diálogo (T059, `DialogoExclusao.test.tsx`, `componentes/ui/ui.test.tsx`). **Pendente:** leitor de tela (não executado; depende de pessoa, ver lacunas) | T024 T038 T050 T057 T061 |
| RQ-005 | `integration/test_contrato_openapi.py::test_*` (documentos válidos, `openapi.json` atualizado, operações, respostas, esquemas, códigos de erro); etapas "Contrato OpenAPI atualizado" e "Tipos da API atualizados" do CI | T037 |

## Critérios de sucesso

| Critério | Verificação | Tarefas |
|---|---|---|
| CS-001 | Teste guiado com três pessoas, até 2 minutos sem ajuda. **Não executado:** depende de pessoas | T063 |
| CS-002 | `security/test_isolamento_rotas.py::test_toda_rota_com_identificador_no_caminho_tem_caso_de_isolamento` (falha com rota nova sem caso), `::test_o_detector_acusa_rota_nova_com_identificador_sem_caso`, `::test_a_verificacao_de_401_acusa_uma_rota_esquecida_sem_autenticacao`, `::test_a_enumeracao_de_rotas_cobre_tudo_o_que_o_openapi_publica` | T041 |
| CS-003 | `security/identidade/test_autenticacao.py::test_entrada_tem_corpo_e_status_identicos_para_conta_inexistente_e_senha_errada`, `::test_tempo_de_resposta_nao_revela_se_o_email_tem_conta`, `::test_bloqueio_por_conta_vale_igual_para_email_com_e_sem_conta`; `unit/nucleo/test_seguranca.py::test_hash_ficticio_recusa_sempre_e_e_calculado_uma_vez` | T031 |
| CS-004 | `security/identidade/test_exclusao_completa.py::test_nenhuma_tabela_com_usuario_id_guarda_linhas_da_conta_excluida` (catálogo do PostgreSQL), `::test_o_catalogo_acusa_uma_tabela_de_dominio_que_esqueceu_de_se_registrar`, `::test_nenhum_objeto_resta_sob_o_prefixo_do_usuario_depois_da_tarefa` (armazenamento) | T054 |

## Decisões técnicas

| Decisão | Teste que a sustenta | Tarefas |
|---|---|---|
| Emenda da DTEC 002 (psycopg 3) | `integration/nucleo/test_fila_transacao.py::test_rollback_nao_deixa_tarefa_na_fila`, `::test_commit_deixa_tarefa_na_fila`, `::test_queueing_lock_impede_duplicata_na_fila` | T013 T014 T017 |
| DTEC 015 (rotas e estado do servidor) | `frontend/src/api/cliente.test.ts`; `frontend/src/testes/roteamento.test.tsx` (rota protegida redireciona, 401 global) | T025 T026 T044 |
| DTEC 016 (React Aria) | `frontend/src/componentes/ui/ui.test.tsx`; axe dos formulários | T024 |
| DTEC 017 (integração contínua) | Execuções do fluxo na `develop`: 5, 7, 9, 12 e 13 verdes (a 13 é a de `9232f70`, com todo o código da spec); falhas anteriores corrigidas e descritas no registro da sessão | T007 T027 T060 |
| DTEC 018 (camadas) | `arquitetura/test_camadas.py::test_camadas_respeitam_dtec018`, `::test_detector_recusa_importacao_proibida`; `unit/nucleo/test_erros.py::test_*` | T010 T023 |
| DTEC 019 (isolamento) | `security/test_isolamento_rotas.py::test_*` | T041 T043 |
| DTEC 020 (tentativas) | `unit/identidade/test_limites.py::test_*`; `unit/nucleo/test_rede.py::test_*`; `integration/identidade/test_repositorios.py::test_trava_por_chave_exclui_transacoes_concorrentes`; rajadas em `adversarial/identidade/` | T031 T032 T034 |
| DTEC 021 (exclusão e chaves) | `security/identidade/test_exclusao_completa.py::test_*`; `integration/nucleo/test_armazenamento_contrato.py::test_*` | T018 T019 T054 T056 |
| DTEC 022 (senhas comuns) | `unit/identidade/test_dominio.py::test_senha_da_lista_comum_e_recusada_em_qualquer_caixa`, `::test_lista_empacotada_tem_ncsc_e_lista_em_portugues`, `::test_lista_ausente_impede_o_carregamento` | T028 T029 |
| DTEC 023 (sessão, CSRF, Argon2) | `unit/nucleo/test_seguranca.py::test_*` | T020 |

## Tarefas de suporte

Tarefas que não implementam um requisito isolado, mas sustentam todos ou produzem a evidência de uma história.

| Tarefas | Papel | Requisitos sustentados |
|---|---|---|
| T001 a T006, T008 | Estrutura base: projetos, Dockerfiles, Compose e ganchos locais | Regra 11 (Docker), RQ-005 (Swagger) e todos os demais, indiretamente |
| T015, T016, T021, T022 | Migrações, infraestrutura de testes, entidades e aplicação | Todos os RF; RQ-005 (`integration/test_migracoes.py`, `integration/test_saude.py`) |
| T040, T045, T052, T059 | Evidência do teste independente de US1, US2, US3 e US4 | Cenários de cada história |
| T060 | Execução completa das suítes e da qualidade, e CI verde | Regra 17 |
| T062 | Medição da entrada e do pico de memória | Limites de desempenho do plano (DTEC 023) |
| T064 | Documentação dos comandos verificados | Quickstart e regra 11 |
| T065 | Esta matriz | Todos |

## Análise de consistência (etapa 7)

Conferência feita em 12/10/2026 entre spec, plano, pesquisa, modelo de dados, contrato, quickstart e tarefas, e revisada em 14/10/2026 contra o código.

| Verificação | Resultado |
|---|---|
| Todo RF, RQ e CS da spec tem teste e tarefa | Sim: RF-001 a RF-015, RQ-001 a RQ-005 e CS-001 a CS-004. **Sem teste automatizado completo:** CS-001 (teste guiado, T063) e a parte de leitor de tela do RQ-004 (T061) |
| Todo cenário de aceitação (US1-1 a US4-4) tem teste funcional | Sim. Os cenários da US2 estão em `security/` (isolamento e CSRF), não em `functional/`; o cenário 8 da US1 e o 3 da US4 são testes de interface |
| Todo caso de borda da spec tem teste | Sim. A borda "exclusão com processamento em andamento" é coberta na 001 só pelo enfileiramento atômico (`test_falha_no_meio_da_exclusao_desfaz_tudo_e_nao_enfileira_a_tarefa`, `test_exclusao_pedida_duas_vezes_em_paralelo_tem_um_unico_efeito`). O comportamento das tarefas de processamento cabe às specs 002 e 004 (DTEC 021) |
| Toda tarefa cita caminho exato e resultado verificável | Sim |
| Toda tarefa aparece na matriz | Sim: T001 a T065, nas tabelas acima ou em "Tarefas de suporte" |
| Tarefas organizadas por história, não por camada | Sim: Fases 3 a 6, uma por história; a base compartilhada só tem o que todas as histórias usam |
| Contrato coerente com a spec e o plano | Sim, com as lacunas registradas abaixo (`413` e `securitySchemes`). Todo erro usa o esquema `Erro`. O `409 email_em_uso` é a única distinção de e-mail permitida (D-005) |
| Modelo de dados coerente com o esquema | Sim: o esquema foi atualizado com `tentativas_acesso` e `nome` de 100 caracteres. As colunas de gamificação de `usuarios` são da spec 006 (exceção registrada no plano) |
| Requisito enfraquecido no plano | Nenhum |
| Tecnologia fora da stack aprovada | Nenhuma. As decisões novas estão registradas como DTEC 015 a 023 e foram aprovadas com o plano |

## Lacunas registradas na implementação (14/10/2026)

- **CS-001 e T063:** o teste guiado com três pessoas não foi feito; é uma atividade humana. A spec 001 não deve ser dada como concluída sem ele.
- **RQ-004, leitor de tela:** nenhuma tecnologia assistiva foi usada. A estrutura (rótulos, descrição de erro, papéis, foco) é conferida pelo axe e pelos testes de componente, o que não substitui uma passagem com leitor de tela. Fica para a mesma rodada da T063.
- **Contrato (`contracts/openapi.yaml`):** a resposta `413` (corpo acima de 64 KiB, `test_corpo_acima_de_64_kib_e_recusado_com_413`) não está declarada no contrato de projeto, e o OpenAPI gerado não declara `securitySchemes` (a sessão vai por cookie). O teste de contrato aceita esses desvios; o ajuste do contrato aprovado depende de decisão da equipe e não foi feito.
- **Lista de senhas em português (T028):** revisada pela equipe em 14/10/2026.
- **Tolerância de tempo (CS-003):** calibrada na T031 com a mediana de várias amostras e tolerância de 25%; sem a defesa (hash fictício), o teste falha com 72% de diferença.
- **Cobertura (T060):** backend 94% (instruções e ramos; 1.792 instruções) e frontend 92,6% das instruções e 79,5% dos ramos, medidos em 14/10/2026. A primeira medição do backend dava 91%, porque o *coverage* perdia as linhas executadas depois de cada troca de *greenlet* do SQLAlchemy assíncrono (`identidade/servicos.py` aparecia com 74%); a configuração passou a medir `greenlet` e `thread`. O que continua baixo é código que roda fora dos testes de unidade: `worker.py` (0%, processo próprio, verificado por `integration/nucleo/test_worker.py`), `exportar_openapi.py` (0%, executado pelo CI) e o corpo da tarefa periódica `limpar_registros_expirados` (83% em `tarefas.py`; a lógica, `executar_limpeza`, é testada). Não há limite mínimo de cobertura configurado.
- **Processamento em andamento:** a interrupção dos processamentos na exclusão da conta (borda da spec) só é verificável de ponta a ponta quando existirem tarefas de processamento (specs 002 e 004). Os planos dessas specs herdam a exigência.
