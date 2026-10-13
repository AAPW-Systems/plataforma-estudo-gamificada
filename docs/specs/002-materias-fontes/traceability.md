# Rastreabilidade

**Funcionalidade:** 002-materias-fontes (matérias, envio e processamento de fontes)  
**Data:** 13/10/2026 ([registro](../../prompts/2026-10-13-002-materias-fontes-plano.md))  
**Status:** aguardando o portão "Tarefas aprovadas", junto com as [tarefas](tasks.md)

Esta matriz mostra que requisito, cenário, teste e tarefa descrevem o mesmo comportamento. Os nomes de teste são planejados e passam a ser links quando a implementação existir (T051). Os caminhos de teste são relativos a `backend/tests/`, salvo os do frontend.

## Requisitos funcionais

| Requisito | Cenário ou caso de borda | Teste planejado | Tarefas |
|---|---|---|---|
| RF-001 | US1-1, US3-1, US3-2; duas criações com o mesmo nome em caixas diferentes | `unit/materias/test_dominio.py`; `functional/fontes/test_us1_materia_fonte.py::test_cria_materia`; `functional/materias/test_us3_organizar.py::test_renomeia_*`, `::test_nome_repetido_*`; `adversarial/fontes/test_envio_adversarial.py::test_materias_mesmo_nome_simultaneas` | T008 T014 T019 T022 T023 T040 T043 |
| RF-002 | US1-1; lista com contagens | `functional/.../test_us1_materia_fonte.py::test_lista_materias_contagens`; `unit/nucleo/test_participantes_acervo.py::test_soma_contagens`; `frontend/.../ListaMaterias.test.tsx` | T005 T019 T023 T025 T029 T030 |
| RF-003 | US1-2; título ausente; nome vazio depois da sanitização | `unit/fontes/test_dominio.py::test_titulo_padrao_*`; `functional/.../test_us1_materia_fonte.py::test_envia_pdf_*` | T015 T019 T024 T025 T027 |
| RF-004 | US1-4; arquivo vazio, codificação inválida, PDF protegido, tipo trocado | `unit/fontes/test_validacao.py`; `functional/.../test_us1_materia_fonte.py::test_cs002_*`; `adversarial/fontes/test_envio_adversarial.py::test_disfarcados_*`, `::test_corpo_acima_*` | T006 T016 T019 T022 T024 T027 |
| RF-005 | US1-2; atualização sem recarregar | `integration/fontes/test_processar_fonte.py::test_estados_*`; `frontend/.../Acervo.test.tsx::polling_*`; `frontend/src/api/acompanhamento.test.ts` | T012 T020 T026 T029 T030 |
| RF-006 | US1-3; página só quando conhecida | `unit/fontes/test_divisao.py` (invariantes); `integration/fontes/test_extracao.py::test_paginas_fisicas`; `functional/.../test_us1_materia_fonte.py::test_cs001_*` | T017 T018 T019 T024 T026 |
| RF-007 | US1-5, US1-6 | `unit/fontes/test_dominio.py::test_catalogo_falhas_*`; `functional/.../test_us1_materia_fonte.py::test_pdf_sem_texto_*`, `::test_nova_tentativa_*`; `frontend/.../Acervo.test.tsx::tentar_novamente_*` | T015 T018 T019 T020 T025 T026 T029 |
| RF-008 | US1-6; duas novas tentativas paralelas; reexecução de fonte concluída | `integration/fontes/test_processar_fonte.py::test_reexecucao_concluida_sem_efeito`, `::test_tentativas_*`; `adversarial/.../test_envio_adversarial.py::test_novas_tentativas_paralelas` | T007 T020 T022 T025 T026 |
| RF-009 | US1-3 | `functional/.../test_us1_materia_fonte.py::test_consulta_fonte`; `frontend/.../PainelFonte.test.tsx` | T019 T025 T027 T029 T030 |
| RF-010 | US2-1 a US2-6 | `functional/fontes/test_us2_exclusao_fonte.py`; `frontend/.../DialogoExclusaoFonte.test.tsx` | T005 T032 T033 T036 T037 T038 |
| RF-011 | US3-3, US3-4; matéria com fontes em processamento | `functional/materias/test_us3_organizar.py::test_exclui_materia_*`; `adversarial/materias/test_organizar_adversarial.py`; `frontend/.../DialogoExclusaoMateria.test.tsx` | T040 T041 T043 T044 T045 |
| RF-012 | Cota atingida (50, 30, 100 MB); `falhou` ocupa cota; envios simultâneos acima da cota | `functional/.../test_us1_materia_fonte.py::test_cota_*`; `adversarial/.../test_envio_adversarial.py::test_cota_simultanea_*`; `frontend/.../DialogoExclusaoFonte.test.tsx` (ação em `falhou`) | T002 T019 T022 T023 T025 T038 |
| RF-013 | Fonte excluída durante o processamento (CB-16) | `integration/fontes/test_processar_fonte.py::test_fonte_apagada_antes_da_gravacao`; `adversarial/fontes/test_exclusao_fonte_adversarial.py::test_exclusao_durante_processamento` | T020 T026 T034 T036 |
| RF-014 | US1-7; mesmo arquivo em outra matéria; envios simultâneos do mesmo arquivo | `functional/.../test_us1_materia_fonte.py::test_fonte_duplicada_*`; `adversarial/.../test_envio_adversarial.py::test_envios_simultaneos_mesmo_arquivo` | T008 T019 T022 T025 |
| RF-015 | US3-5 | `functional/materias/test_us3_organizar.py::test_renomeia_fonte_*` | T040 T043 T044 T045 |
| RF-016 | US1-8 | `functional/.../test_us1_materia_fonte.py::test_pouco_texto_conclui` | T017 T019 T024 |

## Requisitos de qualidade

| Requisito | Teste ou evidência planejada | Tarefas |
|---|---|---|
| RQ-001 | `unit/fontes/test_dominio.py::test_nome_exibido_*`; `security/fontes/test_acervo_seguranca.py::test_chave_sem_nome_enviado`; `adversarial/.../test_envio_adversarial.py::test_nomes_maliciosos` | T004 T015 T021 T022 |
| RQ-002 | `security/fontes/test_acervo_seguranca.py::test_logs_sem_conteudo`; revisão dos logs | T021 T048 |
| RQ-003 | `security/test_isolamento_rotas.py` (11 rotas da 002); FK composta em `integration/fontes/test_restricoes.py`; `security/identidade/test_exclusao_completa.py` | T008 T021 T035 T042 |
| RQ-004 | axe nos testes de componente; verificação manual de teclado, leitor de tela e 320 px | T012 T029 T037 T044 T048 |
| RQ-005 | `unit/nucleo/test_configuracao.py`; `GET /acervo/uso` em `functional/.../test_us1_materia_fonte.py::test_uso_acervo`; `frontend/.../EnvioFonte.test.tsx` (limites vindos da API); `integration/test_contrato_openapi.py` | T002 T019 T027 T028 T029 |

## Critérios de sucesso

| Critério | Verificação planejada | Tarefas |
|---|---|---|
| CS-001 | `functional/fontes/test_us1_materia_fonte.py::test_cs001_validos_concluem_com_paginas` (10 arquivos gerados) | T010 T019 |
| CS-002 | `functional/fontes/test_us1_materia_fonte.py::test_cs002_invalidos_recusados` (10 arquivos gerados) | T010 T019 |
| CS-003 | `functional/fontes/test_us1_materia_fonte.py::test_cs003_pdf_2mb_em_60s`; medição no quickstart | T019 T031 T049 |
| CS-004 | `functional/fontes/test_us2_exclusao_fonte.py::test_cs004_*`; `functional/materias/test_us3_organizar.py::test_cs004_*`; testes de `409 impacto_alterado` | T033 T034 T040 T041 |

## Casos de borda

| Caso de borda | Teste planejado | Tarefas |
|---|---|---|
| Envio interrompido (CB-04) | `adversarial/fontes/test_envio_adversarial.py::test_envio_interrompido` | T022 |
| Fonte excluída durante o processamento (CB-16) | ver RF-013 | T020 T034 |
| Matéria excluída com fontes em processamento | `adversarial/materias/test_organizar_adversarial.py::test_exclusao_com_processamento` | T041 |
| Matéria excluída com geração em andamento | Coberto pela 004 (participante das gerações, DTEC 027); na 002, o participante falso confirma a chamada | T040 |
| Exclusão com cartões numa lição aberta (CB-27) | Na 002, a exclusão não toca revisões, XP nem sequência (tabelas da 005 e da 006); a verificação de ponta a ponta fica com a 005 | T033 T040 |
| Arquivo vazio, codificação inválida, PDF com senha | `unit/fontes/test_validacao.py`; `test_cs002_*` | T016 T019 |
| Nome com caminho, controles ou mais de 255 caracteres | ver RQ-001 | T015 T022 |
| Mesmo arquivo duas vezes; em matérias diferentes; simultâneo | ver RF-014 | T019 T022 |
| Cota atingida; `falhou` ocupa cota; envios simultâneos acima da cota | ver RF-012 | T019 T022 |
| Texto com instruções à IA (CB-15) | `adversarial/.../test_envio_adversarial.py::test_instrucoes_guardadas_como_conteudo` | T022 |

## Decisões técnicas

| Decisão | Teste que a sustenta | Tarefas |
|---|---|---|
| DTEC 024 (isolamento) | `integration/nucleo/test_isolamento.py`; `integration/fontes/test_extracao.py::test_tempo_esgotado` | T003 T018 |
| DTEC 025 (armazenamento e banco) | suíte de contrato do armazenamento; `test_processar_fonte.py::test_rollback_compensa_objeto`, `::test_reconciliacao_*` | T004 T020 T025 T026 |
| DTEC 026 (acompanhamento) | `frontend/src/api/acompanhamento.test.ts`; `Acervo.test.tsx::polling_*` | T012 T029 |
| DTEC 027 (participantes) | `unit/nucleo/test_participantes_acervo.py`; testes da US2 e da US3 com o participante falso; `arquitetura/test_camadas.py` | T005 T009 T033 T040 |
| DTEC 028 (validação) | `unit/fontes/test_validacao.py`; `unit/nucleo/test_middlewares.py` | T006 T016 |
| DTEC 029 (extração e divisão) | `unit/fontes/test_divisao.py`; `integration/fontes/test_extracao.py` | T017 T018 |
| DTEC 030 (estados e tentativas) | `integration/fontes/test_processar_fonte.py`; `integration/nucleo/test_tarefas_travadas.py` | T007 T020 T026 |
| DTEC 031 (impacto sob concorrência) | testes de `409 impacto_alterado` da US2 e da US3 | T034 T041 |
| DTEC 032 (cotas e duplicatas) | testes de concorrência de `test_envio_adversarial.py` | T022 T023 T025 |

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

## Lacunas aceitas antes da implementação

- **Cartões reais na exclusão:** as US2 e US3 são verificadas com um participante falso. A verificação com cartões reais fica nas tarefas da 003 e da 004, que reexecutam estes testes funcionais (DTEC 027).
- **Lição aberta (CB-27):** só é verificável de ponta a ponta com as lições da 005. A 002 garante que a exclusão não toca revisões, XP nem sequência.
- **Geração em andamento:** a interrupção da geração na exclusão é obrigação da 004 (participante das gerações e `FOR SHARE` na fonte, DTEC 031).
- **Nomes de teste:** os nomes exatos são confirmados na implementação e consolidados na T051.
- **Parâmetros da divisão:** 1.200, 2.000 e 150 caracteres são valores iniciais (DTEC 029); a avaliação da 004 pode ajustá-los por configuração.
