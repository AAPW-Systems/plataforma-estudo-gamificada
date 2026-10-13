# Rastreabilidade

**Funcionalidade:** 001-conta-acesso (conta, sessão, isolamento e preferências)  
**Data:** 12/10/2026 ([registro](../../prompts/2026-10-12-001-conta-acesso-plano.md))  
**Status:** em revisão (portão "Tarefas aprovadas")

Esta matriz mostra que requisito, cenário, teste e tarefa descrevem o mesmo comportamento. Os nomes de teste são planejados e passam a ser links quando a implementação existir (T065). Os caminhos de teste são relativos a `backend/tests/`, salvo os do frontend.

## Requisitos funcionais

| Requisito | Cenário ou caso de borda | Teste planejado | Tarefas |
|---|---|---|---|
| RF-001 | US1-1; bordas de nome e e-mail | `unit/identidade/test_dominio.py::test_nome_*`, `::test_email_*`; `functional/identidade/test_us1_conta_entrada.py::test_cadastro_cria_conta` | T029 T030 T033 T036 |
| RF-002 | US1-2; senha com mais de 128 caracteres ou só com espaços | `unit/identidade/test_dominio.py::test_politica_senha_*`; `functional/.../test_us1_conta_entrada.py::test_cadastro_recusa_senha_comum` | T028 T029 T030 T033 |
| RF-003 | US1-1 | `security/identidade/test_autenticacao.py::test_papel_estudante_e_imutavel`; `adversarial/identidade/test_perfil_adversarial.py::test_campos_extras_recusados` | T031 T036 T048 T049 |
| RF-004 | US1-3, US1-4 | `functional/.../test_us1_conta_entrada.py::test_entrada_*`; `security/identidade/test_autenticacao.py::test_mensagem_neutra_*` | T030 T031 T035 T036 |
| RF-005 | US1-6; tentativas distribuídas a partir do mesmo endereço | `security/identidade/test_autenticacao.py::test_limite_*`; `adversarial/identidade/test_autenticacao_adversarial.py::test_rajada_paralela_*` | T012 T031 T032 T034 T035 |
| RF-006 | US1-5; sair numa aba invalida as duas | `unit/nucleo/test_seguranca.py::test_validade_sessao_*`; `functional/.../test_us1_conta_entrada.py::test_saida_revoga_sessao` | T020 T030 T035 |
| RF-007 | US2-1, US2-2; recurso de outro estudante em qualquer operação | `security/test_isolamento_rotas.py` | T041 T043 |
| RF-008 | US3-1, US3-2 | `unit/identidade/test_preferencias.py`; `functional/identidade/test_us3_perfil.py::test_alteracao_*` | T046 T047 T049 T051 |
| RF-009 | US1-1; fuso IANA inválido | `unit/identidade/test_dominio.py::test_fuso_*`; `functional/.../test_us1_conta_entrada.py::test_cadastro_fuso_*` | T029 T030 T033 T039 |
| RF-010 | US3-3 | `unit/revisao/test_parametros_fsrs.py`; `functional/identidade/test_us3_perfil.py::test_retencao_cria_versao` | T046 T047 T049 |
| RF-011 | US2-3 | `security/test_csrf_origem.py`; `unit/nucleo/test_seguranca.py::test_csrf_*` | T020 T042 |
| RF-012 | US1-7; e-mail com outra caixa ou espaços | `functional/.../test_us1_conta_entrada.py::test_email_em_uso`; `adversarial/.../test_autenticacao_adversarial.py::test_cadastros_simultaneos_mesmo_email` | T030 T032 T034 |
| RF-013 | US1-8 | `frontend/src/funcionalidades/identidade/FormularioCadastro.test.tsx` (aviso de privacidade) | T038 T039 |
| RF-014 | US4-1, US4-2 | `functional/identidade/test_us4_senha_exclusao.py::test_troca_senha_*` | T053 T055 T056 T057 T058 |
| RF-015 | US4-3, US4-4; exclusão pedida duas vezes; processamento em andamento | `functional/.../test_us4_senha_exclusao.py::test_exclusao_*`; `security/identidade/test_exclusao_completa.py`; `adversarial/identidade/test_exclusao_adversarial.py` | T053 T054 T055 T056 T057 T058 |

## Requisitos de qualidade

| Requisito | Teste ou evidência planejada | Tarefas |
|---|---|---|
| RQ-001 | `security/identidade/test_autenticacao.py::test_senha_nunca_gravada`, `::test_cookie_sessao_httponly` | T020 T031 |
| RQ-002 | `unit/nucleo/test_logs.py::test_mascaramento_*`; revisão dos logs | T011 T031 T061 |
| RQ-003 | `security/identidade/test_autenticacao.py::test_limite_conta`, `::test_limite_ip`, `::test_limite_cadastro`; variáveis configuráveis em `test_configuracao.py` | T009 T031 T032 T034 |
| RQ-004 | axe nos testes de componente; verificação manual de teclado, leitor de tela e 320 px | T024 T038 T050 T057 T061 |
| RQ-005 | `integration/test_contrato_openapi.py` | T037 |

## Critérios de sucesso

| Critério | Verificação planejada | Tarefas |
|---|---|---|
| CS-001 | Teste guiado com três pessoas, até 2 minutos sem ajuda | T063 |
| CS-002 | `security/test_isolamento_rotas.py`, que falha com rota não coberta | T041 |
| CS-003 | `security/identidade/test_autenticacao.py::test_mensagem_neutra_*`, `::test_tempo_resposta_*`, `::test_bloqueio_igual_com_e_sem_conta` | T031 |
| CS-004 | `security/identidade/test_exclusao_completa.py` (catálogo do PostgreSQL e armazenamento) | T054 |

## Decisões técnicas

| Decisão | Teste que a sustenta | Tarefas |
|---|---|---|
| Emenda da DTEC 002 (psycopg 3) | `integration/nucleo/test_fila_transacao.py` | T013 T014 T017 |
| DTEC 015 (rotas e estado do servidor) | `frontend/src/api/cliente.test.ts`; teste de redirecionamento da rota protegida | T025 T026 T044 |
| DTEC 016 (React Aria) | testes de componente de `componentes/ui/` com axe | T024 |
| DTEC 017 (integração contínua) | execução do fluxo na `develop` | T007 T027 T060 |
| DTEC 018 (camadas) | `arquitetura/test_camadas.py`; `unit/nucleo/test_erros.py` | T010 T023 |
| DTEC 019 (isolamento) | `security/test_isolamento_rotas.py` | T041 T043 |
| DTEC 020 (tentativas) | testes de limite e de rajada | T031 T032 T034 |
| DTEC 021 (exclusão e chaves) | `security/identidade/test_exclusao_completa.py`; suíte de contrato do armazenamento | T018 T019 T054 T056 |
| DTEC 022 (senhas comuns) | `unit/identidade/test_dominio.py::test_politica_senha_lista_comum` | T028 T029 |
| DTEC 023 (sessão, CSRF, Argon2) | `unit/nucleo/test_seguranca.py` | T020 |

## Tarefas de suporte

Tarefas que não implementam um requisito isolado, mas sustentam todos ou produzem a evidência de uma história.

| Tarefas | Papel | Requisitos sustentados |
|---|---|---|
| T001 a T006, T008 | Estrutura base: projetos, Dockerfiles, Compose e ganchos locais | Regra 11 (Docker), RQ-005 (Swagger) e todos os demais, indiretamente |
| T015, T016, T021, T022 | Migrações, infraestrutura de testes, entidades e aplicação | Todos os RF; RQ-005 |
| T040, T045, T052, T059 | Evidência do teste independente de US1, US2, US3 e US4 | Cenários de cada história |
| T062 | Medição da entrada e do pico de memória | Limites de desempenho do plano (DTEC 023) |
| T064 | Documentação dos comandos verificados | Quickstart e regra 11 |

## Análise de consistência (etapa 7)

Conferência feita em 12/10/2026 entre spec, plano, pesquisa, modelo de dados, contrato, quickstart e tarefas.

| Verificação | Resultado |
|---|---|
| Todo RF, RQ e CS da spec tem teste planejado e tarefa | Sim: RF-001 a RF-015, RQ-001 a RQ-005 e CS-001 a CS-004 |
| Todo cenário de aceitação (US1-1 a US4-4) tem teste funcional | Sim: T030, T041, T042, T047 e T053, um teste por cenário |
| Todo caso de borda da spec tem teste | Sim. A borda "exclusão com processamento em andamento" é coberta na 001 só pelo enfileiramento atômico. O comportamento das tarefas de processamento cabe às specs 002 e 004 (DTEC 021) |
| Toda tarefa cita caminho exato e resultado verificável | Sim |
| Toda tarefa aparece na matriz | Sim: T001 a T065, nas tabelas acima ou em "Tarefas de suporte" |
| Tarefas organizadas por história, não por camada | Sim: Fases 3 a 6, uma por história; a base compartilhada só tem o que todas as histórias usam |
| Contrato coerente com a spec e o plano | Sim: 8 operações e 2 de saúde. Todo erro usa o esquema `Erro`. O `409 email_em_uso` é a única distinção de e-mail permitida (D-005) |
| Modelo de dados coerente com o esquema | Sim: o esquema foi atualizado com `tentativas_acesso` e `nome` de 100 caracteres. As colunas de gamificação de `usuarios` são da spec 006 (exceção registrada no plano) |
| Requisito enfraquecido no plano | Nenhum |
| Tecnologia fora da stack aprovada | Nenhuma. As decisões novas estão registradas como DTEC 015 a 023 e foram aprovadas com o plano |

## Lacunas aceitas antes da implementação

- **Nomes de teste:** os nomes exatos de teste e função são confirmados na implementação e consolidados na T065.
- **Lista de senhas em português:** a lista curta (T028) é definida e revisada pela equipe no pull request.
- **Tolerância de tempo:** a tolerância estatística do teste de tempo de resposta (CS-003) é calibrada na T031, com várias amostras para evitar teste instável.
- **Processamento em andamento:** a interrupção dos processamentos na exclusão da conta (borda da spec) só é verificável de ponta a ponta quando existirem tarefas de processamento (specs 002 e 004). Os planos dessas specs herdam a exigência.
