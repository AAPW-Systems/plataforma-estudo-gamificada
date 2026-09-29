# Rastreabilidade da consulta de prazos

Esta matriz demonstra que requisito, cenário, teste e tarefa descrevem o mesmo comportamento. Os nomes de teste são planejados; passam a ser links quando a implementação existir.

| Requisito | Cenário | Teste planejado | Tarefas |
|---|---|---|---|
| RF-001 | entrada válida e limites | `test_query_validation.py` | T008 T016 |
| RF-002 | consulta usa fonte ativa | `test_ingestion_and_search.py` | T009 T010 |
| RF-003 | US1 cenário 1 | `test_queries_api.py::test_answered_has_citation` | T012 T013 T014 T016 |
| RF-004 | US2 cenários 1 e 2 | `test_query_service.py::test_insufficient_evidence` | T019 T020 T021 T022 |
| RF-005 | US3 cenários 1 e 2 | `test_query_service.py::test_ambiguous_skips_retrieval` | T023 T024 T025 |
| RF-006 | caso de borda fontes divergentes | `test_query_service.py::test_source_conflict` | T026 |
| RF-007 | casos de borda de entrada | `test_query_validation.py` | T008 T016 |
| RF-008 | caso serviço indisponível | `test_query_service.py::test_unavailable` | T027 |
| RF-009 | RQ-003 e RQ-004 | `test_query_log.py` | T011 T030 |

## Lacunas aceitas antes da implementação

- O nome final do arquivo de avaliação será confirmado na T029.
- O link do canal acadêmico continua configurável até a confirmação do PO.
