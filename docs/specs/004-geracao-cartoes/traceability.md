# Rastreabilidade

**Funcionalidade:** 004-geracao-cartoes (geração de cartões pela IA e revisão dos gerados)  
**Data:** 13/10/2026 ([registro](../../prompts/2026-10-13-004-geracao-cartoes-plano.md))  
**Status:** aprovada em 13/10/2026 por Artur Lins (equipe), junto com as [tarefas](tasks.md)

Esta matriz mostra que requisito, cenário, teste e tarefa descrevem o mesmo comportamento. Os nomes de teste são planejados e passam a ser links quando a implementação existir (T059). Os caminhos de teste são relativos a `backend/tests/`, salvo os do frontend. Os testes da suíte principal usam o provedor simulado (`FunctionModel`). Os critérios que dependem do modelo real são medidos no conjunto de avaliação (Fase 7).

## Requisitos funcionais

| Requisito | Cenário ou caso de borda | Teste planejado | Tarefas |
|---|---|---|---|
| RF-001 | US1-2; fonte `pendente`, `processando` ou `falhou`; resposta com mais de 10 cartões | `functional/geracao/test_us1_gerar_revisar.py::test_pede_cartoes_fonte_concluida`, `::test_fonte_nao_concluida_409`; `functional/geracao/test_us4_falhas.py::test_quinze_cartoes_mantem_dez`; `unit/geracao/test_validacao.py::test_excedente_*`; `frontend/.../BotaoPedirCartoes.test.tsx` | T013 T019 T023 T026 T030 T031 T033 |
| RF-002 | US1-1; troca de provedor | `unit/ia/test_aviso.py`; `functional/ia/test_aviso.py::test_ciencia_*`, `::test_versao_antiga_409`, `::test_troca_de_provedor_pede_ciencia`; `security/geracao/test_geracao_seguranca.py::test_sem_ciencia_nenhuma_chamada`; `frontend/.../DialogoAvisoIa.test.tsx` | T003 T015 T021 T024 T030 T031 |
| RF-003 | US1-2 | `integration/geracao/test_tarefa_gerar_cartoes.py::test_pendente_ate_concluida`; `functional/geracao/test_us1_gerar_revisar.py::test_estados_visiveis_e_retorno`; `frontend/.../EstadoGeracao.test.tsx` (polling e `aria-live`) | T016 T019 T025 T026 T030 T031 |
| RF-004 | Envio duplo; novo pedido com geração em andamento; chave reutilizada para outra fonte | `integration/geracao/test_pedido_concorrencia.py::test_mesma_chave_em_paralelo`, `::test_mesma_fonte_em_paralelo`; `functional/geracao/test_us1_gerar_revisar.py::test_reenvio_mesma_geracao`, `::test_em_andamento_devolve_existente`; `adversarial/geracao/test_revisao_adversarial.py::test_chave_outra_fonte_409` | T004 T017 T019 T022 T026 |
| RF-005 | Fonte de outro estudante; instrução para usar outro assunto | `unit/geracao/test_janela.py::test_so_trechos_da_fonte`; `security/geracao/test_geracao_seguranca.py::test_fonte_alheia_*`; `adversarial/geracao/test_injecao.py` | T005 T012 T021 T023 T025 T034 |
| RF-006 | US4-2, US4-3 | `unit/geracao/test_validacao.py` (portões 1 a 4); `integration/geracao/test_falhas.py::test_juiza_*`; `functional/geracao/test_us4_falhas.py::test_sem_trecho_*`, `::test_citacao_inventada_*`, `::test_fora_do_assunto_*` | T013 T023 T033 T035 T036 |
| RF-007 | US4-2, US4-3, US4-6 | `integration/geracao/test_tarefa_gerar_cartoes.py::test_descartados_com_motivo`; `functional/geracao/test_us4_falhas.py::test_todos_descartados_*` | T004 T016 T025 T033 T036 |
| RF-008 | US3-3; explicação obrigatória | `unit/geracao/test_validacao.py::test_explicacao_obrigatoria`, `::test_cobertura_explicacao_*`; `integration/geracao/test_restricoes.py::test_check_explicacao_gerado`; `functional/geracao/test_us3_evidencia.py::test_explicacao_com_citacao` | T004 T013 T023 T040 T042 |
| RF-009 | US1-3, US3-1 | `integration/geracao/test_tarefa_gerar_cartoes.py::test_evidencias_com_copias_e_deslocamentos`; `functional/geracao/test_us1_gerar_revisar.py::test_revisao_mostra_evidencia`; `frontend/componentes/ui/PainelEvidencia.test.tsx` | T010 T016 T019 T025 T040 |
| RF-010 | US1-4 a US1-8; "Aceitar todos" duas vezes | `unit/geracao/test_revisao.py`; `functional/geracao/test_us1_gerar_revisar.py::test_cenario_4_*` a `::test_cenario_8_*`, `::test_aceitar_todos_duas_vezes`; `adversarial/geracao/test_revisao_adversarial.py::test_aceitar_e_recusar_em_paralelo`, `::test_aceitar_todos_com_recusa_em_paralelo`; `frontend/.../RevisaoGeracao.test.tsx` | T014 T019 T022 T023 T027 T030 T031 |
| RF-011 | US1-4, US1-7 (ordem de aceitação) | `unit/geracao/test_revisao.py::test_ordem_aceitar_todos`; `functional/geracao/test_us1_gerar_revisar.py::test_ordem_de_entrada_no_estudo`. Lição real: reverificação pela 005 | T014 T019 T023 T027 |
| RF-012 | US2-1 | `functional/geracao/test_us2_gerar_mais.py::test_resumo_*`; `frontend/.../ResumoGeracao.test.tsx` | T046 T048 T049 T050 |
| RF-013 | US2-2, US2-3; nova geração com cartões aguardando revisão | `unit/geracao/test_repeticao.py`; `unit/geracao/test_janela.py`; `integration/geracao/test_tarefa_gerar_cartoes.py::test_repeticao_entre_fontes_concorrentes`; `integration/geracao/test_cobertura.py`; `functional/geracao/test_us2_gerar_mais.py::test_tres_gerar_mais_sem_repeticao`, `::test_fonte_esgotada_409`; CS-007 no conjunto de avaliação | T012 T016 T019 T023 T046 T047 T048 T054 |
| RF-014 | US1-6 | `functional/geracao/test_us1_gerar_revisar.py::test_recusado_some`; `security/geracao/test_geracao_seguranca.py::test_rotas_003_404_para_recusado`; `integration/geracao/test_analise.py` (recusados na taxa) | T019 T021 T027 T053 |
| RF-015 | US4-4 | `unit/geracao/test_agentes.py::test_nonce_*`, `::test_trechos_so_nos_delimitadores`; `adversarial/geracao/test_injecao.py`; `functional/geracao/test_us4_falhas.py::test_instrucao_obedecida_*`; casos adversariais do conjunto de avaliação | T013 T025 T033 T034 T052 T054 |
| RF-016 | US4-1 | `functional/geracao/test_us4_falhas.py::test_provedor_*`; `integration/geracao/test_falhas.py::test_novas_tentativas_*`, `::test_falha_da_juiza_nao_publica` | T033 T035 T036 T037 T038 |
| RF-017 | — (registro para análise) | `integration/geracao/test_tarefa_gerar_cartoes.py::test_registra_provedor_modelo_versao_trechos`; `integration/ia/test_cliente.py::test_consumo_*` | T008 T009 T016 T025 |
| RF-018 | US3-1, US3-2 | `functional/geracao/test_us3_evidencia.py`; `frontend/.../VerOrigem.test.tsx`; reexecução da US2-2 da 003 (`test_us2_editar.py::test_gerado_vira_editado` com geração real) | T020 T040 T041 T042 T043 T044 |
| RF-019 | Limite atingido; falha técnica não conta | `unit/ia/test_orcamento.py::test_dia_de_estudo_*`; `integration/geracao/test_pedido_concorrencia.py::test_vinte_pedidos_simultaneos`, `::test_falhou_nao_conta`; `functional/geracao/test_us1_gerar_revisar.py::test_limite_retry_after`; `functional/geracao/test_us4_falhas.py::test_falha_nao_conta_no_limite` | T003 T008 T017 T019 T026 T033 |
| RF-020 | US1-9 | `functional/geracao/test_us1_gerar_revisar.py::test_cenario_9_motivo_opcional`; `integration/geracao/test_restricoes.py::test_check_motivo_so_em_recusado`; `frontend/.../MotivoRecusa.test.tsx`; distribuição dos motivos em `integration/geracao/test_analise.py` | T004 T014 T019 T027 T030 T031 T053 |

## Requisitos de qualidade

| Requisito | Teste ou evidência planejada | Tarefas |
|---|---|---|
| RQ-001 | `unit/ia/test_provedores.py` (`gemini`, `groq` e `teste` sem mudar regra); `arquitetura/test_camadas.py` (`pydantic_ai` só em `ia/` e `agentes.py`); runbook da troca de provedor | T007 T008 T009 T058 |
| RQ-002 | `unit/ia/test_orcamento.py`; `integration/ia/test_cliente.py::test_orcamento_impede_chamada`; `integration/geracao/test_falhas.py::test_orcamento_entre_gerador_e_juiza`; `functional/geracao/test_us4_falhas.py::test_orcamento_esgotado_429` | T003 T008 T009 T033 T035 |
| RQ-003 | `security/geracao/test_geracao_seguranca.py::test_logs_e_consumo_sem_conteudo`; `integration/ia/test_cliente.py::test_consumo_sem_conteudo`; revisão dos logs | T008 T021 T041 T056 |
| RQ-004 | axe nos testes de componente; foco no próximo cartão; "Aceitar todos" depois da lista; sem atalhos de uma letra; verificação manual de teclado, leitor de tela e 320 px | T010 T030 T037 T043 T049 T056 |
| RQ-005 | `functional/geracao/test_us4_falhas.py::test_mensagem_sem_detalhe_do_provedor`; `security/geracao/test_geracao_seguranca.py::test_erros_sem_detalhe_do_provedor`; `frontend/.../FalhaGeracao.test.tsx` | T021 T033 T036 T037 |
| RQ-006 | Relatório de avaliação com provedor, modelo e versão (`tests/avaliacao_ia/test_avaliacao.py`); versão gravada em `geracoes` e `consumo_ia` | T016 T053 T054 |
| RQ-007 | Nome da pessoa responsável no plano (T001); revisão humana do relatório (T054) | T001 T052 T054 |

## Critérios de sucesso

| Critério | Verificação planejada | Tarefas |
|---|---|---|
| CS-001 | Cálculo automático no conjunto de avaliação: 100% dos publicados apontam para um trecho existente da fonte do caso. Reforçado por construção pelo portão de vínculo (`unit/geracao/test_validacao.py::test_rotulo_inexistente`) | T013 T053 T054 |
| CS-002 | Revisão humana dos casos sem evidência e adversariais; `adversarial/geracao/test_injecao.py` com o provedor simulado | T034 T052 T054 |
| CS-003 | Revisão humana dos casos com contradição; `functional/geracao/test_us4_falhas.py::test_contradicao_reprovada` | T033 T052 T054 |
| CS-004 | Revisão humana: pelo menos 90% sustentados e 0 com afirmação ausente (D-006); precisão com e sem a juíza | T052 T053 T054 |
| CS-005 | `integration/geracao/test_analise.py` (taxa por geração, fonte e total); exibida no relatório | T053 T054 |
| CS-006 | Medição com o provedor real e a fonte de 2 MB da fábrica (quickstart, CS-006) | T006 T057 |
| CS-007 | Caso de três "Gerar mais" no conjunto, revisado por pessoa; `functional/geracao/test_us2_gerar_mais.py::test_tres_gerar_mais_sem_repeticao` com o provedor simulado | T046 T052 T054 |

## Casos de borda

| Caso de borda | Teste planejado | Tarefas |
|---|---|---|
| Mesmo pedido enviado duas vezes | `test_us1_gerar_revisar.py::test_reenvio_mesma_geracao`; `test_pedido_concorrencia.py::test_mesma_chave_em_paralelo`; `BotaoPedirCartoes.test.tsx` (chave única por intenção) | T017 T019 T030 |
| Novo pedido com geração em andamento | `test_us1_gerar_revisar.py::test_em_andamento_devolve_existente`; `test_pedido_concorrencia.py::test_mesma_fonte_em_paralelo`; índice parcial em `test_restricoes.py` | T004 T017 T019 |
| Fonte excluída durante a geração | `test_tarefa_gerar_cartoes.py::test_fonte_apagada_entre_a_e_b`, `::test_exclusao_paralela_a_publicacao`; `test_participante.py::test_geracao_em_andamento_interrompida` | T016 T018 |
| Fonte `pendente`, `processando` ou `falhou` | `test_us1_gerar_revisar.py::test_fonte_nao_concluida_409`; `BotaoPedirCartoes.test.tsx` (ação ausente) | T019 T030 |
| Fonte com pouco texto | `test_us4_falhas.py::test_fonte_um_paragrafo` | T033 |
| Limite diário atingido; falha técnica não conta | `test_us1_gerar_revisar.py::test_limite_retry_after`; `test_us4_falhas.py::test_falha_nao_conta_no_limite`; `test_pedido_concorrencia.py::test_falhou_nao_conta` | T017 T019 T033 |
| Nova geração com cartões aguardando revisão | `test_us1_gerar_revisar.py::test_nova_geracao_com_aguardando`; `unit/geracao/test_repeticao.py::test_compara_aguardando` | T012 T019 |
| "Aceitar todos" duas vezes | `test_us1_gerar_revisar.py::test_aceitar_todos_duas_vezes` | T019 |
| Editar e aceitar com frente ou verso vazios | `test_us1_gerar_revisar.py::test_editar_aceitar_frente_vazia_422` | T019 T027 |
| Resposta com mais de 10 cartões | `test_us4_falhas.py::test_quinze_cartoes_mantem_dez`; `unit/geracao/test_validacao.py::test_excedente_*` | T013 T033 |

## Decisões técnicas

| Decisão | Teste que a sustenta | Tarefas |
|---|---|---|
| DTEC 039 (aviso e ciência) | `unit/ia/test_aviso.py`; `functional/ia/test_aviso.py`; `test_sem_ciencia_nenhuma_chamada`; `unit/ia/test_configuracao.py` (aviso por provedor) | T003 T015 T021 T024 |
| DTEC 040 (consumo e orçamento) | `unit/ia/test_orcamento.py`; `unit/ia/test_classificacao_erros.py`; `integration/ia/test_cliente.py`; `test_falhas.py::test_orcamento_*` | T008 T009 T035 |
| DTEC 041 (janela, cobertura e repetição) | `unit/geracao/test_janela.py`; `unit/geracao/test_repeticao.py`; `integration/geracao/test_cobertura.py`; `test_us2_gerar_mais.py` | T012 T016 T046 T047 |
| DTEC 042 (validação) | `unit/geracao/test_validacao.py`; `integration/geracao/test_falhas.py::test_juiza_*`; relatório com e sem a juíza | T013 T035 T054 |
| DTEC 043 (execução e falhas) | `integration/geracao/test_tarefa_gerar_cartoes.py`; `integration/geracao/test_falhas.py`; `test_us4_falhas.py` | T016 T033 T035 |
| DTEC 044 (pedido sob concorrência) | `integration/geracao/test_pedido_concorrencia.py`; índices em `test_restricoes.py` | T004 T017 |
| DTEC 045 (revisão) | `unit/geracao/test_revisao.py`; `adversarial/geracao/test_revisao_adversarial.py`; testes da 003 verdes com o selo derivado | T014 T022 T027 |
| DTEC 046 (participante e descartes) | `integration/geracao/test_participante.py`; reexecução da 002 (T020); catálogo da exclusão da conta | T018 T020 T028 |
| DTEC 047 (injeção, contradição e avaliação) | `unit/geracao/test_agentes.py`; `adversarial/geracao/test_injecao.py`; `tests/avaliacao_ia/` | T006 T013 T034 T052 T053 |

## Tarefas de suporte

Tarefas que não implementam um requisito isolado, mas sustentam todos ou produzem a evidência de uma história.

| Tarefas | Papel | Requisitos sustentados |
|---|---|---|
| T001 | Pessoa responsável registrada antes da implementação | RQ-007 |
| T002, T003, T004, T005, T006, T007, T011 | Dependências, configuração, migração, leitura de fontes, fábricas e cenários do provedor, arquitetura e verificação da base | Todos os RF |
| T020 | Reexecuções obrigatórias da 002 e da 003 com dados reais (DTEC 027 e 038) | RF-009, RF-018; CS-004 da 002; RF-006 da 003 |
| T029 | Contrato gerado e tipos do frontend | Todos os RF expostos pela API |
| T032, T039, T045, T051 | Evidência do teste independente de cada história | Cenários de cada história |
| T055, T056, T057, T058, T059 | Suítes completas, evidências, medições, documentação e atualização desta matriz | Regra 17; RQ-003, RQ-004; CS-006; metas de desempenho do plano |

## Análise de consistência (etapa 7)

Conferência feita em 13/10/2026 entre spec, plano, pesquisa, modelo de dados, contrato, quickstart e tarefas.

| Verificação | Resultado |
|---|---|
| Todo RF, RQ e CS da spec tem teste planejado e tarefa | Sim: RF-001 a RF-020, RQ-001 a RQ-007 e CS-001 a CS-007. Os CS-002 a CS-004 e o CS-007 dependem do modelo real e do revisor humano, e são medidos no conjunto de avaliação (T054), além dos testes com o provedor simulado |
| Todo cenário de aceitação tem teste funcional | Sim: US1-1 a US1-9 (T015 e T019), US2-1 a US2-3 (T046), US3-1 a US3-3 (T040), US4-1 a US4-6 (T033) |
| Todo caso de borda da spec tem teste | Sim: os 10 casos da spec, na tabela acima |
| Toda tarefa cita caminho exato e resultado verificável | Sim |
| Toda tarefa aparece na matriz | Sim: T001 a T059, nas tabelas acima ou em "Tarefas de suporte" |
| Tarefas organizadas por história, não por camada | Sim: Fases 3 a 6, uma por história, na ordem do plano (US1 e US4 como P1, depois US3 e US2). A base só tem o que todas usam: migração, domínio `ia`, leitura de fontes, fábricas, arquitetura e dois componentes. O participante da exclusão entra na US1, porque a primeira publicação já torna a exclusão da fonte dependente dele. A juíza entra na US4, porque a US1 já é demonstrável com os portões determinísticos, e a US4 é o critério de pronto dela |
| Contrato coerente com a spec e o plano | Sim: 11 operações, 8 com identificador no caminho, todas na tabela de isolamento (T021 e T041). Todo erro usa o esquema `Erro`; os códigos da 001, da 002 e da 003 foram mantidos, e 8 códigos foram acrescentados. Validado com `openapi-spec-validator` |
| Modelo de dados coerente com o esquema | Sim: o [esquema inicial](../../arquitetura/esquema-inicial.dbml) foi atualizado nesta sessão (tabelas, colunas, enums, índices, FKs e `CHECK` da 004) |
| Exigências do PO | EX-02 coberta por RF-012 e RF-013 (US2; T046 a T051) e pelo CS-007 (T054). EX-03 coberta por RF-006 e RF-008: a explicação é obrigatória, validada pelos portões e com a citação (T013, T040). A exibição ao errar é obrigação registrada para a 005. EX-01 e EX-05 continuam fora do escopo e em pauta com o PO (PO-02 e PO-01). Nenhuma exigência conflita com o plano |
| Requisito enfraquecido no plano | Nenhum. A limitação de cobertura de fontes grandes (DTEC 041) não enfraquece requisito: o CS-006 continua atendido por geração, e a cobertura proporcional ao volume é do final acadêmico (010). Ela está registrada como risco e será explicada ao PO na apresentação |
| Tecnologia fora da stack aprovada | Nenhuma. PydanticAI e pydantic-evals (DTEC 007 e 011), Procrastinate (DTEC 006), PostgreSQL 17 (`SET NULL (coluna)`, índice parcial, *advisory lock*). Nenhuma extensão nova |
| Coerência com as specs vizinhas | A 003 recebeu a propagação da DTEC 045 (README e modelo de dados, com registro no histórico); a mudança no código da 003 é feita pela T027, e os testes da 003 continuam verdes. As obrigações da 003 (reexecução da US2-2 e do caso "aguardando revisão fora da lista") e da 002 (participante e reexecução da US2 e da US3) estão na T020. As obrigações para a 005, a 010 e a 014 estão no [plano](plan.md#obrigações-registradas-para-as-próximas-specs) |

## Lacunas aceitas antes da implementação

- **Lições reais:** a entrada como cartão novo e a ordem de aceitação (US1-4, RF-011) e a ausência dos aguardando revisão e dos recusados nas lições (RF-010, RF-014) só são verificáveis de ponta a ponta com a 005. A 004 verifica o estado gravado que a lição usa.
- **Explicação ao errar (EX-03):** a exibição ao marcar "Errei" é da 005. A 004 garante a explicação obrigatória e o acesso à evidência.
- **Qualidade com o modelo real:** os CS-002 a CS-004 e o CS-007 dependem do provedor real e do revisor humano (T054), fora da suíte que bloqueia o merge (DTEC 011). Sem a chave do provedor, a suíte principal continua completa com o provedor simulado.
- **Repetição por paráfrase:** o filtro é lexical (DTEC 041). Paráfrases sem palavras em comum só serão detectáveis com embeddings, no final acadêmico. O CS-007 mede o efeito real.
- **Pessoa responsável:** a definir no início da implementação (T001). Até lá, as aprovações da documentação são de Artur Lins.
- **Nomes de teste:** os nomes exatos são confirmados na implementação e consolidados na T059.
