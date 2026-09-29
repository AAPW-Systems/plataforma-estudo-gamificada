# Plano de implementação da consulta de prazos acadêmicos

**Spec:** [spec.md](spec.md)  
**Data:** 24 de setembro de 2026  
**Responsáveis:** equipe do exemplo didático

## Resumo técnico

A funcionalidade será um serviço web em Python. A API valida a pergunta, consulta somente trechos ativos em um índice SQLite FTS5 e monta uma resposta extrativa com referência. Interfaces para recuperação e geração preservam a possibilidade de substituir esses componentes. Estados de ausência, ambiguidade, conflito e indisponibilidade serão respostas explícitas do domínio, não exceções convertidas em texto genérico.

## Contexto técnico

- **Linguagem e versão:** Python 3.12.
- **Dependências principais:** FastAPI, Pydantic, SQLAlchemy e Alembic.
- **Persistência:** SQLite com FTS5 no primeiro incremento.
- **Testes:** pytest, testes HTTP do FastAPI e Playwright para a jornada prioritária.
- **Plataforma:** container Linux e navegador atual.
- **Desempenho:** percentil 95 abaixo de três segundos em 20 consultas sequenciais no ambiente local de referência.
- **Escala:** até 20 documentos curtos e uso simultâneo de uma turma.

## Verificação da constituição

| Princípio | Como o plano atende | Evidência prevista |
|---|---|---|
| Evidência antes de afirmação | Resposta factual exige objeto `Citation` | Testes de integração e conjunto de avaliação |
| Proteção de dados | Validação bloqueia padrões definidos e logs omitem texto bruto | Testes de log e revisão de configuração |
| Verificação humana | Conflitos e ausências encaminham ao canal acadêmico | Cenários US2 e contrato HTTP |
| Qualidade verificável | Cada história possui testes independentes | Suíte por história e matriz de rastreabilidade |
| Entrega incremental | US1 funciona com resposta extrativa antes das histórias posteriores | Quickstart e teste de jornada P1 |

Não há exceção conhecida aos princípios.

## Arquitetura e fluxo

```text
navegador -> API de consultas -> validação -> serviço de consulta
                                            |-> Retriever -> SQLite FTS5
                                            |-> AnswerBuilder
                                            |-> repositório de execuções
```

A API converte HTTP em comandos do domínio. O serviço de consulta decide os estados e não depende de FastAPI. `Retriever` devolve evidências com metadados. `AnswerBuilder` recebe somente evidências aprovadas. O repositório registra estado, IDs de fonte, versão do corpus e duração.

## Estrutura do repositório

```text
backend/
├── pyproject.toml
├── migrations/
├── src/
│   ├── api/routes/queries.py
│   ├── domain/models.py
│   ├── domain/query_service.py
│   ├── ports/retriever.py
│   ├── adapters/sqlite_retriever.py
│   ├── adapters/extractive_answer.py
│   └── repositories/query_log.py
└── tests/
    ├── contract/test_queries_api.py
    ├── integration/test_query_flow.py
    └── unit/test_query_service.py
frontend/
├── src/query-form.js
└── tests/query-flow.spec.js
```

**Decisão de estrutura:** frontend e backend ficam separados porque serão implantados como unidades distintas no projeto integrador. O domínio permanece independente do framework HTTP.

## Contratos

- `POST /api/v1/queries` recebe a pergunta e devolve um dos estados `answered`, `insufficient_evidence`, `needs_clarification`, `source_conflict` ou `unavailable`.
- `GET /health` informa disponibilidade do processo e do banco, sem consultar fontes externas.
- Erros de formato usam HTTP 422. Estados válidos do domínio retornam HTTP 200 com campo `status`.
- A versão inicial do contrato está em `contracts/openapi.yaml`.

## Dados

- `SourceDocument` e `Passage` guardam o corpus aprovado e sua versão.
- `QueryExecution` guarda identificador, estado, duração, versão do corpus e IDs de fonte.
- A pergunta bruta não será persistida nesta versão.
- O canal acadêmico será configuração de ambiente não secreta.

## Estratégia de testes

- **Unitários:** validação de ambiguidade, limiar, conflito e montagem de referência.
- **Integração:** ingestão, busca FTS5, persistência do estado e atualização de versão.
- **Contrato:** corpo de entrada, todos os estados e erros 422.
- **Jornada:** pergunta respondível com abertura da fonte pelo teclado.
- **Avaliação:** 10 casos respondíveis, cinco ausentes e três ambíguos.

## Observabilidade e operação

- Log estruturado com `query_id`, `status`, `source_ids`, `corpus_version` e `duration_ms`.
- Endpoint de saúde e contagem de consultas por estado.
- Timeout interno de dois segundos para recuperação.
- Falha de armazenamento impede resposta factual e produz estado `unavailable`.

## Riscos técnicos

| Risco | Consequência | Mitigação | Como verificar |
|---|---|---|---|
| Vocabulário diferente | Fonte correta não aparece | Interface de busca e preservação dos casos falhos | Avaliação de recuperação |
| Metadado incompleto | Referência não verificável | Ingestão rejeita trecho sem seção ou versão | Teste de integração |
| Fonte vencida ativa | Orientação desatualizada | Estado e vigência obrigatórios | Teste de atualização |
| Log com dado pessoal | Exposição indevida | Não persistir pergunta bruta e testar redaction | Teste de log |

## Saídas do planejamento

As decisões estão em `research.md`, entidades em `data-model.md`, contrato em `contracts/openapi.yaml`, validação local em `quickstart.md` e execução em `tasks.md`.
