# Tarefas da consulta de prazos acadêmicos

**Entrada:** spec, plano e artefatos de design revisados  
**Formato:** `[ID] [P?] [US?] descrição com caminho exato`

## Fase 1 Preparação

- [ ] T001 Criar a estrutura `backend/src`, `backend/tests`, `frontend/src`, `frontend/tests` e `data/corpus` conforme `plan.md`.
- [ ] T002 [P] Configurar Python 3.12, FastAPI, SQLAlchemy, Alembic e pytest em `backend/pyproject.toml`.
- [ ] T003 [P] Configurar lint e formatação em `backend/pyproject.toml`.
- [ ] T004 [P] Criar `backend/.env.example` com `ACADEMIC_SUPPORT_URL` sem valor real.

## Fase 2 Base compartilhada

- [ ] T005 Criar entidades e estados descritos em `backend/src/domain/models.py`.
- [ ] T006 Criar migração de `source_documents`, `passages` e `query_executions` em `backend/migrations/versions/`.
- [ ] T007 [P] Definir a interface `Retriever` em `backend/src/ports/retriever.py`.
- [ ] T008 [P] Criar validação de entrada em `backend/src/domain/input_policy.py`.
- [ ] T009 Implementar ingestão que rejeita fonte sem versão ou seção em `backend/src/adapters/ingest.py`.
- [ ] T010 Implementar o índice FTS5 em `backend/src/adapters/sqlite_retriever.py`.
- [ ] T011 Criar log estruturado sem pergunta bruta em `backend/src/repositories/query_log.py`.

## Fase 3 História de usuário 1 Consultar prazo com fonte

**Objetivo:** responder uma consulta sustentada e apresentar referência verificável.  
**Teste independente:** executar o primeiro cenário da US1 com um calendário fictício.

- [ ] T012 [P] [US1] Criar testes unitários de referência e resposta em `backend/tests/unit/test_answer_builder.py`.
- [ ] T013 [P] [US1] Criar teste de contrato do estado `answered` em `backend/tests/contract/test_queries_api.py`.
- [ ] T014 [US1] Implementar montagem extrativa da resposta em `backend/src/adapters/extractive_answer.py`.
- [ ] T015 [US1] Implementar orquestração da consulta em `backend/src/domain/query_service.py`.
- [ ] T016 [US1] Implementar `POST /api/v1/queries` em `backend/src/api/routes/queries.py`.
- [ ] T017 [US1] Criar formulário e apresentação de fontes em `frontend/src/query-form.js` e `frontend/index.html`.
- [ ] T018 [US1] Criar jornada acessível da US1 em `frontend/tests/query-flow.spec.js`.

## Fase 4 História de usuário 2 Reconhecer ausência

**Objetivo:** não afirmar dados ausentes do corpus.  
**Teste independente:** perguntar por taxa de diploma e verificar estado e mensagem.

- [ ] T019 [P] [US2] Criar testes de limiar e ausência em `backend/tests/unit/test_query_service.py`.
- [ ] T020 [P] [US2] Criar teste de contrato `insufficient_evidence` em `backend/tests/contract/test_queries_api.py`.
- [ ] T021 [US2] Implementar limiar configurável e estado de ausência em `backend/src/domain/query_service.py`.
- [ ] T022 [US2] Apresentar orientação de continuidade sem fato inventado em `frontend/src/query-form.js`.

## Fase 5 História de usuário 3 Esclarecer pergunta

**Objetivo:** solicitar o assunto ausente antes da busca.  
**Teste independente:** enviar “qual é o prazo?” e confirmar que o recuperador não é chamado.

- [ ] T023 [P] [US3] Criar teste com `Retriever` simulado em `backend/tests/unit/test_query_service.py`.
- [ ] T024 [US3] Implementar detecção mínima de ambiguidade em `backend/src/domain/input_policy.py`.
- [ ] T025 [US3] Apresentar pergunta de esclarecimento em `frontend/src/query-form.js`.

## Fase 6 Falhas e qualidade transversal

- [ ] T026 Criar detecção de conflito entre fontes em `backend/src/domain/query_service.py`.
- [ ] T027 Criar estado `unavailable` e timeout em `backend/src/domain/query_service.py`.
- [ ] T028 [P] Implementar `GET /health` em `backend/src/api/routes/health.py`.
- [ ] T029 Executar os 18 casos de avaliação e registrar resultados em `docs/ia/eval-consulta-prazos.md`.
- [ ] T030 Verificar os requisitos RQ-001 a RQ-004 e registrar evidências em `docs/qualidade/consulta-prazos.md`.
- [ ] T031 Atualizar `quickstart.md` com os comandos que funcionaram no ambiente limpo.
- [ ] T032 Conferir `traceability.md` e corrigir requisitos sem teste ou tarefa.

## Dependências

- T005 a T011 bloqueiam as histórias de usuário.
- US1 pode ser demonstrada antes de US2 e US3.
- T026 e T027 dependem do serviço criado em T015.
- T029 a T032 dependem das três histórias concluídas.

## Pontos de paralelismo

- T002, T003 e T004 alteram arquivos distintos.
- Em cada história, testes de unidade e contrato podem ser escritos em paralelo.
- Depois de T016, frontend e testes adicionais do backend podem avançar em paralelo.
