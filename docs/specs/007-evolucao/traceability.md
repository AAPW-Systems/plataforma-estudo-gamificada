# Rastreabilidade

**Funcionalidade:** 007-evolucao (evolução mínima)  
**Data:** 13/10/2026 ([registro](../../prompts/2026-10-13-007-evolucao-plano.md))  
**Status:** aprovada em 13/10/2026 por Artur Lins (equipe), junto com as [tarefas](tasks.md)

Esta matriz mostra que requisito, cenário, teste e tarefa descrevem o mesmo comportamento. Os nomes de teste são planejados e viram links quando a implementação existir (T026). Os caminhos de teste são relativos a `backend/tests/`, salvo os do frontend. Todo teste com instante usa o relógio injetável (T007 da 005).

## Requisitos funcionais

| Requisito | Cenário ou caso de borda | Teste planejado | Tarefas |
|---|---|---|---|
| RF-001 (calendário, situações, total) | US1-1; dias antes da conta; hoje em andamento; mudança de fuso | `unit/evolucao/test_dominio.py::test_periodo_*`, `::test_situacao_exibida_*`, `::test_total_estudados`; `integration/evolucao/test_dias_no_intervalo.py`; `functional/evolucao/test_us1_evolucao.py::test_cenario_1_calendario`, `::test_conta_criada_ha_10_dias`, `::test_hoje_em_andamento_e_cumprido`, `::test_fuso_data_pulada_e_repetida`; `frontend/.../CalendarioEstudo.test.tsx` | T006 T009 T010 T011 T014 T017 T018 |
| RF-002 (XP, sequência e recorde iguais à 006) | US1-2 | `functional/evolucao/test_us1_evolucao.py::test_cenario_2_igual_a_trilha`, `::test_igual_a_trilha_com_dias_nao_liquidados`; `integration/test_contrato_openapi.py::test_resumo_gamificacao_igual_006`; `frontend/.../TelaEvolucao.test.tsx::indicadores` | T011 T014 T015 T019 T020 |
| RF-003 (dominados atuais, total e por matéria) | US1-2, US1-4; perdeu estabilidade; suspensos; matéria excluída | `integration/evolucao/test_consultas_donos.py::test_contar_dominados_*`, `::test_dominados_limiar_vigente`, `::test_dominado_em_sem_estabilidade_nao_conta`; `unit/evolucao/test_dominio.py::test_juntar_dominados_*`; `functional/evolucao/test_us1_evolucao.py::test_cenario_4_excluido_sai_xp_fica`, `::test_suspenso_dominado_conta`, `::test_materia_excluida_some`; `frontend/.../TelaEvolucao.test.tsx::lista_por_materia` | T004 T005 T009 T010 T011 T014 T019 T020 |
| RF-004 (no servidor e em texto; só o calendário é gráfico) | US1-1, US1-2 | `functional/evolucao/test_us1_evolucao.py` (valores na resposta); `frontend/.../TelaEvolucao.test.tsx::indicadores`, `::carregando_sem_numeros`; `frontend/.../CalendarioEstudo.test.tsx::total_em_texto` | T011 T014 T017 T019 T020 |
| RF-005 (estado vazio com acesso à trilha) | US1-3 | `integration/evolucao/test_consultas_donos.py::test_existe_revisao_*`; `functional/evolucao/test_us1_evolucao.py::test_cenario_3_estado_vazio`; `frontend/.../TelaEvolucao.test.tsx::estado_vazio` | T004 T005 T011 T014 T019 T020 |

## Requisitos de qualidade

| Requisito | Teste planejado | Tarefas |
|---|---|---|
| RQ-001 (teclado, leitor de tela, 3:1, além da cor) | `frontend/.../CalendarioEstudo.test.tsx` (grid, anúncio, teclado, glifos, legenda, axe); `frontend/src/estilos/contraste.test.ts` (razões a, b e c); evidência manual com leitor de tela e acromatopsia | T016 T017 T018 T024 |
| RQ-002 (320 px sem rolagem horizontal) | `frontend/.../TelaEvolucao.test.tsx::largura_320`; evidência manual no quickstart | T019 T020 T024 |
| RQ-003 (isolamento) | `security/evolucao/test_evolucao_seguranca.py::test_isolamento_*`; filtros de dono em `integration/evolucao/test_consultas_donos.py` | T004 T005 T012 T014 |

## Critérios de sucesso

| Critério | Teste planejado | Tarefas |
|---|---|---|
| CS-001 (30 dias iguais ao cálculo à mão) | `functional/evolucao/test_us1_evolucao.py::test_teste_independente_trinta_dias` (tabela escrita à mão, cenário `trinta-dias`); passo 2 do quickstart | T008 T011 T014 T021 |
| CS-002 (1 s no p95 com um ano) | `functional/desempenho/test_evolucao.py` (servidor abaixo de 300 ms); medida `evolucao-carregada` no quickstart (tela abaixo de 1 s) | T008 T019 T020 T022 T024 |

## Casos de borda

| Caso de borda da spec | Teste planejado | Tarefas |
|---|---|---|
| Dias anteriores à criação da conta não aparecem como não estudados | `test_us1_evolucao.py::test_conta_criada_ha_10_dias`; `test_dias_no_intervalo.py::test_recorte_primeiro_dia`; `CalendarioEstudo.test.tsx::celulas_vazias_fora_do_foco` | T006 T011 T017 |
| Dia de hoje aparece "em andamento", nunca como não estudado | `test_dominio.py::test_hoje_nunca_nao_estudado`; `test_us1_evolucao.py::test_hoje_em_andamento_e_cumprido` | T009 T011 |
| Cartão dominado que perdeu estabilidade deixa de contar, sem perder o bônus | `test_consultas_donos.py::test_dominado_em_sem_estabilidade_nao_conta`; `test_us1_evolucao.py::test_perdeu_estabilidade_mantem_bonus` | T004 T011 |
| Cartões suspensos dominados contam | `test_consultas_donos.py::test_contar_dominados_suspenso`; `test_us1_evolucao.py::test_suspenso_dominado_conta` | T004 T011 |
| Matéria excluída some da lista; o XP permanece | `test_us1_evolucao.py::test_materia_excluida_some` | T011 |
| Mudança de fuso usa as datas já atribuídas | `test_us1_evolucao.py::test_fuso_data_pulada_e_repetida`; `test_dominio.py::test_data_pulada_neutro` | T009 T011 |

## Decisões técnicas

| Decisão | Teste que a sustenta | Tarefas |
|---|---|---|
| DTEC 064 (rota única, transação de leitura, dependências) | `integration/nucleo/test_transacao_leitura.py`; `test_us1_evolucao.py::test_sem_efeito_colateral`; `arquitetura/test_camadas.py::test_evolucao_*`; `adversarial/.../test_concorrencia_coerente` | T002 T003 T007 T011 T013 T014 |
| DTEC 065 (período e situações) | `unit/evolucao/test_dominio.py`; `integration/evolucao/test_dias_no_intervalo.py` | T006 T009 T010 |
| DTEC 066 (dominados atuais pela regra vigente) | `integration/evolucao/test_consultas_donos.py`; `arquitetura/test_camadas.py::test_limiar_so_em_revisao`; `functional/desempenho/test_evolucao.py` (sem índice novo) | T004 T005 T007 T022 |
| DTEC 067 (calendário acessível e responsivo) | `CalendarioEstudo.test.tsx`; `contraste.test.ts`; `TelaEvolucao.test.tsx::largura_320` | T016 T017 T018 T019 T020 |

## Tarefas de suporte

Tarefas que não implementam um requisito isolado, mas sustentam todos ou produzem a evidência da história.

| Tarefas | Papel | Requisitos sustentados |
|---|---|---|
| T001 | Pessoa responsável registrada antes da implementação | Processo (regra 1) |
| T008 | Fábricas dos cenários de 30 dias e de um ano | CS-001, CS-002 |
| T015 | Contrato gerado, comparação com a 006 e tipos do frontend | Princípio V; RF-002 |
| T021 | Evidência do teste independente | Cenários US1-1 a US1-4; CS-001 |
| T023, T024, T025, T026 | Suítes completas, evidências manuais, documentação e atualização desta matriz | Regra 17; RQ-001, RQ-002, CS-002 |

## Análise de consistência (etapa 7)

Conferência feita em 13/10/2026 entre spec, plano, pesquisa, modelo de dados, contrato, quickstart e tarefas.

| Verificação | Resultado |
|---|---|
| Todo RF, RQ e CS da spec tem teste planejado e tarefa | Sim: RF-001 a RF-005, RQ-001 a RQ-003 e CS-001 e CS-002 |
| Todo cenário de aceitação tem teste funcional | Sim: US1-1 a US1-4 (T011) e o teste independente (T011 e T021) |
| Todo caso de borda da spec tem teste | Sim: os 6 casos, na tabela acima |
| Toda tarefa cita caminho exato e resultado verificável | Sim |
| Toda tarefa aparece na matriz | Sim: T001 a T026, nas tabelas acima ou em "Tarefas de suporte" |
| Tarefas organizadas por história, não por camada | Sim: história única (Fase 3), com backend e frontend na mesma fase. A base só tem o que a história usa de outros domínios (transação de leitura, consultas nos donos, recorte de `dias_no_intervalo`, arquitetura e fábricas) |
| Contrato coerente com a spec e o plano | Sim: uma rota, `GET /api/v1/evolucao` (`200`, `401`); esquemas novos para calendário e dominados; `ResumoGamificacao`, `ProgressoMeta` e `Sequencia` idênticos aos da 006 (conferido por script e pela T015); nenhum código de erro novo; validado com `openapi-spec-validator` |
| Modelo de dados coerente com o esquema | Sim: nenhuma tabela, coluna, enum ou índice novo; o [esquema inicial](../../arquitetura/esquema-inicial.dbml) não muda; sem migração `0008` (justificada na DTEC 066, com contingência na T022) |
| Exigências do PO | Nenhuma toca a 007. A EX-05 (PO-01) saiu do MVP (D-009 da 005) e, se aprovada, entra na 013; conferido em 13/10/2026 |
| Requisito enfraquecido no plano | Nenhum, com uma interpretação registrada e aprovada no portão do plano: o contraste de 3:1 "entre as situações" (RQ-001) é verificado por três razões (indicador contra o fundo, preenchimento contra células vazias, glifo contra o preenchimento), com a forma como distinção principal, porque 3:1 entre todos os pares de quatro cores só pela luminância é inatingível (DTEC 067) |
| Tecnologia fora da stack aprovada | Nenhuma. PostgreSQL (`REPEATABLE READ`, `READ ONLY`), SQLAlchemy, React Aria (DTEC 016) e `Intl.DateTimeFormat`. Nenhuma dependência nova |
| Coerência com as specs vizinhas | Obrigação da 006 cumprida: dias e sequência só por `gamificacao/consultas.py` (`resumo` e `dias_no_intervalo`), sem ler `dias_estudo` nem recalcular a sequência (T006, T007, T014). Obrigação da 005 cumprida: dominados e estabilidade pela consulta de `revisao` sobre `cartoes` (T004, T005), e a existência de revisão por `revisao/consultas.py`. `xp_por_dia` não é usado no MVP (DTEC 064) e fica para a 013. O esclarecimento da T036 da 006 foi registrado sem mudança de comportamento e é conferido pela T006. As consultas novas em `cartoes`, `revisao` e `materias` são só de leitura, e as suítes dessas specs continuam verdes (T023) |

## Lacunas aceitas antes da implementação

- **CS-002 da tela com medida manual:** a medida de 1 s na tela é feita no quickstart (T024). A automação com o Playwright entra no final acadêmico (DTEC 014). O servidor tem teste automatizado (T022).
- **Leitor de tela:** a leitura real do calendário é evidência manual (T024). O comportamento verificável (papéis, rótulos, foco e teclado) tem teste automatizado (T017).
- **Dependência da ordem de implementação:** a 007 só começa depois da 006 e da 002 completas.
- **Pessoa responsável:** William Johnson, designado em 13/10/2026; a T001 se conclui com a confirmação dele na sessão de implementação. As aprovações da documentação seguem com Artur Lins.
- **Nomes de teste:** os nomes exatos são confirmados na implementação e consolidados na T026.
