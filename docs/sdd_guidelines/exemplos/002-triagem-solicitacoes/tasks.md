# Tarefas da triagem de solicitações

## Preparação e base

- [ ] T001 Criar diretórios previstos em `plan.md`.
- [ ] T002 [P] Configurar dependências e testes em `backend/pyproject.toml`.
- [ ] T003 [P] Criar mapa versionado em `config/sectors.yaml`.
- [ ] T004 [P] Criar 15 casos de desenvolvimento e cinco reservados em `evals/triage_cases.jsonl`.
- [ ] T005 Definir `Classifier` e os objetos de entrada e saída em `backend/src/ports/classifier.py` e `backend/src/domain/models.py`.
- [ ] T006 Implementar política de entrada sem persistência em `backend/src/domain/input_policy.py`.

## História 1 Sugestão e confirmação

- [ ] T007 [P] [US1] Criar testes de categoria válida e desconhecida em `backend/tests/unit/test_triage_service.py`.
- [ ] T008 [P] [US1] Criar teste de contrato da resposta em `backend/tests/contract/test_triage_api.py`.
- [ ] T009 [US1] Implementar adaptador de modelo com schema em `backend/src/adapters/llm_classifier.py`.
- [ ] T010 [US1] Implementar regras do domínio em `backend/src/domain/triage_service.py`.
- [ ] T011 [US1] Implementar endpoint em `backend/src/api/routes/triage.py`.
- [ ] T012 [US1] Criar interface de confirmação e correção em `frontend/src/triage-form.js`.
- [ ] T013 [US1] Verificar que nenhuma ação de envio existe no teste `frontend/tests/triage-flow.spec.js`.

## História 2 Baixa confiança e contingência

- [ ] T014 [P] [US2] Criar testes de baixa confiança e indisponibilidade em `backend/tests/unit/test_triage_service.py`.
- [ ] T015 [US2] Implementar limiar e pedido de contexto em `backend/src/domain/triage_service.py`.
- [ ] T016 [US2] Implementar adaptador de regras em `backend/src/adapters/rule_classifier.py`.
- [ ] T017 [US2] Exibir escolha manual na interface em `frontend/src/triage-form.js`.

## Qualidade e entrega

- [ ] T018 Criar logger de métricas sem texto em `backend/src/observability/triage_metrics.py`.
- [ ] T019 Criar teste que inspeciona logs em `backend/tests/integration/test_triage_logs.py`.
- [ ] T020 Executar os 15 casos de desenvolvimento e definir limiar em `docs/ia/triage-development.md`.
- [ ] T021 Congelar a versão e executar os cinco casos reservados em `docs/ia/triage-final.md`.
- [ ] T022 Revisar a correspondência entre RF-001 a RF-007, testes e tarefas.
