# Plano de implementação

**Funcionalidade:** 001-conta-acesso (conta, sessão, isolamento e preferências)  
**Spec:** [spec.md](spec.md), aprovada em 12/10/2026  
**Data:** 12/10/2026 ([registro](../../prompts/2026-10-12-001-conta-acesso-plano.md))  
**Responsáveis:** Artur Lins (decisões técnicas); equipe na revisão  
**Status:** aprovado em 12/10/2026 por Artur Lins (equipe), com a emenda da DTEC 002 e as DTEC 015 a 023

Este é o primeiro plano do projeto. Além da spec 001, ele define a **estrutura base do repositório** (pastas, Compose, Dockerfiles, configuração, qualidade e integração contínua), que as specs 002 a 007 reaproveitam sem redefinir.

## Resumo técnico

A conta é implementada no domínio `identidade` de um backend FastAPI, organizado em camadas explícitas (DTO, mapeador, serviço, domínio, repositório e exceções; [DTEC 018](../../research.md#decisão-dtec-018-camadas-do-backend-dto-mapper-repositório-e-exceções)), com PostgreSQL acessado pelo SQLAlchemy assíncrono sobre psycopg 3 ([emenda da DTEC 002](../../research.md#decisão-dtec-002-framework-do-backend)). A autenticação é própria ([DTEC 003](../../research.md#decisão-dtec-003-autenticação)): senha com Argon2id, sessão opaca guardada como hash e entregue em cookie `HttpOnly`, proteção anti-CSRF por *double submit* assinado e limites de tentativas persistidos no banco ([DTEC 020](research.md#decisão-dtec-020-registro-e-limite-das-tentativas-de-acesso) e [DTEC 023](research.md#decisão-dtec-023-detalhes-da-sessão-do-csrf-e-do-hash-de-senha)). O isolamento entre estudantes fica num único ponto, o repositório, e é protegido por um teste que percorre todas as rotas ([DTEC 019](research.md#decisão-dtec-019-garantia-do-isolamento-entre-estudantes)). A exclusão da conta apaga as linhas numa transação e enfileira, de forma atômica, a remoção dos arquivos do prefixo do usuário ([DTEC 021](research.md#decisão-dtec-021-exclusão-da-conta-e-chaves-de-armazenamento-por-usuário)). O frontend React consome o contrato tipado com TanStack Router, TanStack Query e `openapi-fetch` ([DTEC 015](../../research.md#decisão-dtec-015-roteamento-e-estado-do-servidor-no-frontend)), sobre primitivas do React Aria ([DTEC 016](../../research.md#decisão-dtec-016-primitivas-acessíveis-da-interface)).

**Riscos principais:** o prazo (apresentação prevista para 15/10/2026), a enumeração de contas por mensagem ou tempo de resposta, a força bruta e um vazamento entre estudantes. A ordem de entrega (US1 → US2 → US3 → US4) garante que as histórias P1 fiquem demonstráveis primeiro.

## Contexto técnico

- **Linguagem e versão:** Python 3.13 (backend), gerenciado pelo uv. A versão foi alterada de 3.14 para 3.13 em 13/10/2026 por Artur Lins, na aprovação das tarefas, por maturidade do ecossistema de *wheels*. TypeScript em modo *strict* sobre Node 24 LTS com npm (frontend). As versões ficam fixadas em `backend/.python-version`, `frontend/.nvmrc`, no campo `engines` do `package.json` e nas imagens base com *digest*.
- **Dependências principais do backend:** FastAPI, Uvicorn, Pydantic e pydantic-settings, SQLAlchemy 2 (assíncrono) com psycopg 3 (`psycopg[binary,pool]`), Alembic, Procrastinate, `argon2-cffi`, `email-validator`, `tzdata`, `fsrs` (DTEC 012) e structlog. As versões exatas são fixadas no `uv.lock` na tarefa de estrutura.
- **Dependências principais do frontend:** React, Vite, Tailwind CSS, TanStack Router (com o plugin do Vite), TanStack Query, `openapi-fetch` e `openapi-typescript`, React Aria Components, React Hook Form e Zod. Versões fixadas no `package-lock.json`.
- **Persistência:** PostgreSQL na imagem `pgvector/pgvector` (DTEC 005), com as tabelas `usuarios`, `sessoes`, `parametros_fsrs` e `tentativas_acesso` ([modelo de dados](data-model.md)) e o esquema do Procrastinate.
- **Testes:** pytest com pytest-asyncio, httpx (`AsyncClient`), pytest-cov e Hypothesis, contra um Postgres real (DTEC 001 e 014). No frontend, Vitest, Testing Library, MSW e `vitest-axe`.
- **Plataforma de execução:** Docker Compose local, com os serviços `db`, `migrate`, `api`, `worker` e `web`. No final acadêmico, os mesmos Dockerfiles geram as imagens `prod` (DTEC 013).
- **Limites de desempenho ou custo:** a entrada deve responder em menos de 1 segundo no ambiente local. O Argon2 usa 64 MiB por cálculo, com no máximo 4 cálculos simultâneos (pico de 256 MiB). Nenhum serviço novo entra na stack.
- **Escala prevista:** dezenas de estudantes no acadêmico.

## Verificação da constituição

| Princípio | Como o plano atende | Evidência prevista |
|---|---|---|
| I Fontes exclusivas | Não se aplica: a spec não gera conteúdo. O aviso de privacidade (RF-013) prepara o envio de trechos ao provedor na spec 004 | Teste de componente do aviso no cadastro |
| II Proteção e isolamento | Filtro de dono no repositório e teste que percorre as rotas (DTEC 019); senha em Argon2id; sessão como hash; cookies `HttpOnly`; CSRF assinado; limites de tentativas; logs com mascaramento; exclusão completa (DTEC 021) | Testes `security/` e `adversarial/`; teste de logs; teste de catálogo após a exclusão |
| III Verificação humana | Exclusão da conta exige diálogo explícito e a senha atual; decisões técnicas novas registradas como DTEC e aprovadas com o plano | Teste de componente do diálogo; aprovação do plano |
| IV Servidor autoritativo | Sessão, limites, preferências e versões do FSRS decididos e guardados no servidor; instantes em UTC; o frontend só exibe o que a API confirma | Testes de integração do perfil e das versões do FSRS |
| V Qualidade verificável | Contrato OpenAPI com erros; teste de contrato; cenários da spec como testes funcionais; WCAG 2.2 AA com axe; integração contínua (DTEC 017) | `contracts/openapi.yaml`, `traceability.md` (etapa 7), relatórios da integração contínua |
| VI Entrega incremental | US1 e US2 (P1) demonstráveis antes de US3 e US4; a estrutura base entra junto da US1 | `quickstart.md`, verificação da história P1 |
| VII Rastreabilidade | DTEC 015 a 023 com alternativas; registro da sessão; IDs da spec citados em testes e tarefas | `docs/prompts/`, `traceability.md` |

Não há exceção aos princípios. As exceções técnicas estão em [Complexidade e exceções](#complexidade-e-exceções).

## Arquitetura e fluxo

### Contêineres (MVP)

```text
navegador ──http://localhost:5173──> web (Vite dev server)
                                     └── /api/* ──proxy──> api (FastAPI/Uvicorn :8000) ──> db (PostgreSQL)
                                                                └─ enfileira ──────────────┘   ▲
                                     worker (Procrastinate, mesmo código da api) ─────────────┘
migrate (Alembic, executa uma vez) ──> db, antes de api e worker
```

- **Mesma origem:** o Vite encaminha `/api` para a API, de modo que os cookies são do mesmo site e não há CORS. No final acadêmico, o Caddy cumpre esse papel (arquitetura, seção 5.2).
- **`migrate`:** é um serviço de execução única (`alembic upgrade head`). A `api` e o `worker` só sobem depois dele terminar com sucesso.
- **Verificações de saúde:** `/health` e `/health/ready` ficam fora de `/api`, não são encaminhadas pelo proxy e são usadas pelo `healthcheck` do Compose.

### Fluxo de uma requisição autenticada que altera estado

```text
requisição
 -> middleware de correlação (gera X-Request-ID, liga ao log)
 -> middleware de cabeçalhos de segurança e Cache-Control
 -> verificação de Origin/Sec-Fetch-Site e CSRF (POST/PATCH/PUT/DELETE)
 -> router (Controller): valida o DTO de entrada
 -> dependência UsuarioAtual: lê o cookie, busca a sessão pelo SHA-256, valida
    expiração e revogação, renova ultimo_uso_em (no máximo 1x/min)
 -> mapeador: DTO -> comando de domínio
 -> serviço (caso de uso): abre a unidade de trabalho (transação)
    -> regras de domínio (funções puras)
    -> repositórios (sempre com usuario_id)
    -> enfileiramento na mesma transação, quando houver
 -> mapeador: entidade -> DTO de saída
 -> resposta (ou ErroAplicacao -> handler central -> corpo Erro)
```

### Fluxos da spec

| Fluxo | Passos principais |
|---|---|
| **Cadastro (US1)** | CSRF pré-sessão → limite de cadastros por endereço de rede → validação (nome, e-mail, senha fora da lista comum, fuso com recurso `America/Sao_Paulo`) → hash Argon2id em *thread* → transação: `usuarios` (papel `estudante`, padrões de D-001) e `parametros_fsrs` versão 1 → nova sessão → cookies de sessão e CSRF ligados a ela → `201`. E-mail repetido gera `409 email_em_uso`, também na corrida entre dois cadastros (índice único). |
| **Entrada (US1)** | CSRF pré-sessão → *advisory lock* da chave da conta → limites por conta e por endereço (`429` mesmo com a senha certa) → busca do usuário; se não existe, verificação contra o hash fictício → senha errada registra a falha e responde `401 credenciais_invalidas` → senha certa apaga as falhas da conta, refaz o hash se os parâmetros mudaram e cria uma sessão nova → `200`. |
| **Saída (US1)** | Revoga a sessão (`revogada_em`) e apaga os cookies → `204`. Sem sessão válida, também `204`. |
| **Isolamento (US2)** | Nenhuma rota da 001 recebe identificador de recurso: todas operam sobre o usuário da sessão. Sem sessão válida, `401` sem dados. O mecanismo para recursos com identificador (busca por `public_id` e dono, `404` idêntico) fica pronto no núcleo para a spec 002. |
| **Perfil (US3)** | `GET` lê o usuário e a versão vigente do FSRS. `PATCH` valida tudo antes de alterar (tudo ou nada); trava a linha do usuário; se a retenção mudou, grava a versão n+1 copiando os demais parâmetros. |
| **Troca de senha (US4)** | Limite da conta → verificação da senha atual (falha conta como `falha_senha_atual`) → validação da nova → novo hash → revogação das outras sessões → `204`. |
| **Exclusão da conta (US4)** | Limite da conta → verificação da senha atual → transação: `SELECT ... FOR UPDATE` no usuário; registro de exclusão por domínio, em ordem; `DELETE` do usuário (sessões em cascata); enfileiramento de `apagar_objetos_usuario(public_id)` → apaga os cookies → `204`. |

### Tarefas assíncronas criadas nesta spec

| Tarefa | Gatilho | Comportamento |
|---|---|---|
| `apagar_objetos_usuario` | Exclusão da conta (mesma transação) | Chama `armazenamento.apagar_prefixo("usuarios/{public_id}/")`; idempotente; até 5 novas tentativas com espera crescente |
| `limpar_registros_expirados` | Periódica, diária às 3h UTC | Apaga `tentativas_acesso` com mais de 24 horas e sessões expiradas ou revogadas há mais de 30 dias |

Na 001, a interface de armazenamento tem só o adaptador em memória (testes) e o de disco local, com as operações necessárias à exclusão (`apagar_prefixo`). O restante da interface (gravar, ler) chega com a spec 002 ([DTEC 010](../../research.md#decisão-dtec-010-armazenamento-de-arquivos)).

## Estrutura do repositório

```text
/
├── compose.yaml                 # db, migrate, api, worker, web (MVP)
├── .env.example                 # variáveis documentadas, sem valores secretos
├── .editorconfig, .gitattributes  # UTF-8, LF, indentação
├── .pre-commit-config.yaml      # opcional: Ruff, Prettier, ESLint (DTEC 017)
├── .github/workflows/ci.yml     # integração contínua (DTEC 017)
├── backend/
│   ├── Dockerfile               # multi-stage: base -> dev -> prod
│   ├── .dockerignore
│   ├── .python-version          # 3.13
│   ├── pyproject.toml           # dependências, Ruff, mypy, pytest (marcadores)
│   ├── uv.lock
│   ├── alembic.ini
│   ├── migracoes/
│   │   ├── env.py
│   │   └── versions/            # 0001_procrastinate, 0002_identidade
│   ├── openapi.json             # OpenAPI gerado e versionado (fonte dos tipos do frontend)
│   ├── src/app/
│   │   ├── principal.py         # criar_aplicacao(): middlewares, handlers, routers
│   │   ├── worker.py            # ponto de entrada do worker do Procrastinate
│   │   ├── exportar_openapi.py  # grava backend/openapi.json
│   │   ├── nucleo/
│   │   │   ├── configuracao.py  # pydantic-settings
│   │   │   ├── banco.py         # engine, sessão assíncrona, unidade de trabalho
│   │   │   ├── erros.py         # hierarquia ErroAplicacao + handlers centrais
│   │   │   ├── dtos.py          # ModeloDTO (camelCase), ErroDTO, ErroCampoDTO
│   │   │   ├── logs.py          # structlog JSON, mascaramento, correlação
│   │   │   ├── middlewares.py   # X-Request-ID, cabeçalhos de segurança, Cache-Control
│   │   │   ├── rede.py          # endereço de rede com proxies confiáveis
│   │   │   ├── seguranca/       # senhas.py (Argon2), sessoes.py, csrf.py
│   │   │   ├── armazenamento/   # interface + adaptadores memoria.py e disco.py
│   │   │   ├── fila.py          # App do Procrastinate (PsycopgConnector)
│   │   │   └── exclusao.py      # registro de exclusão de dados por domínio
│   │   ├── identidade/          # domínio desta spec (camadas abaixo)
│   │   │   ├── rotas.py, dtos.py, mapeadores.py, servicos.py, dominio.py
│   │   │   ├── repositorios.py, modelos.py, excecoes.py, dependencias.py
│   │   │   ├── tarefas.py       # apagar_objetos_usuario, limpar_registros_expirados
│   │   │   ├── preferencias.py  # padrões e limites de D-001 (configuração versionada)
│   │   │   └── dados/senhas_comuns.txt
│   │   ├── revisao/             # só ParametrosFsrs nesta spec (modelos, repositório, serviço)
│   │   └── saude/rotas.py       # /health e /health/ready
│   └── tests/
│       ├── conftest.py          # banco de teste, savepoints, cliente HTTP, fábricas
│       ├── fabricas.py          # contas fictícias (sem dados pessoais reais)
│       ├── unit/  integration/  functional/  security/  adversarial/
│       └── arquitetura/         # dependências proibidas entre camadas
└── frontend/
    ├── Dockerfile               # multi-stage: deps -> dev -> build -> prod (estáticos)
    ├── .dockerignore, .nvmrc, package.json, package-lock.json
    ├── vite.config.ts           # proxy /api -> api:8000, plugin do TanStack Router
    ├── tsconfig.json, eslint.config.js, .prettierrc, vitest.config.ts
    ├── index.html
    └── src/
        ├── main.tsx
        ├── api/
        │   ├── esquema.gerado.d.ts    # openapi-typescript a partir de backend/openapi.json
        │   ├── limites.gerado.ts      # mínimos e máximos extraídos do OpenAPI
        │   ├── cliente.ts             # openapi-fetch + middleware CSRF e de erros
        │   └── erros.ts               # ErroApi tipado a partir do esquema Erro
        ├── rotas/                     # roteamento por arquivos (TanStack Router)
        │   ├── __root.tsx
        │   ├── _publico/entrar.tsx, _publico/cadastro.tsx
        │   └── _autenticado/index.tsx (trilha, vazia até a spec 005), _autenticado/perfil.tsx
        ├── funcionalidades/identidade/  # formulários, esquemas Zod, hooks de consulta
        ├── componentes/ui/            # wrappers do React Aria com os tokens (DTEC 016)
        ├── estilos/                   # tokens de design (Tailwind, @theme), claro e escuro
        └── testes/                    # MSW (handlers), utilitários de renderização
```

**Decisão de estrutura:**

- Backend e frontend são projetos independentes (arquitetura, seção 5.1). A fronteira é o OpenAPI: o backend gera e versiona `backend/openapi.json`, e o frontend gera dele os tipos (`npm run gerar:api`). A integração contínua falha se algum dos arquivos gerados estiver desatualizado.
- **Contrato de projeto × contrato gerado:** `docs/specs/NNN/contracts/openapi.yaml` é o contrato de projeto de cada spec. Um teste de contrato verifica que o OpenAPI gerado contém todos os caminhos, métodos, respostas e esquemas dele.
- **Domínios:** o backend é organizado por domínio, com as camadas de cada um em arquivos fixos. Um domínio só aparece quando uma spec o usa. A 001 cria `identidade`, `saude` e a parte de `revisao` que guarda os parâmetros do FSRS.
- **Testes:** os testes do backend ficam em pastas por tipo, que coincidem com os marcadores obrigatórios da regra 17. Os do frontend ficam ao lado do componente (`*.test.tsx`).

### Camadas do backend

Mapeamento MVC (constituição): **Model** = `modelos.py`, `dominio.py`, `servicos.py`, `repositorios.py`; **Controller** = `rotas.py`; **View** = `frontend/`. As regras da [DTEC 018](../../research.md#decisão-dtec-018-camadas-do-backend-dto-mapper-repositório-e-exceções):

| Arquivo | Responsabilidade | Pode importar | Não pode importar |
|---|---|---|---|
| `rotas.py` | Router fino: recebe DTO, chama um serviço, devolve DTO, define status e cookies | `dtos`, `mapeadores`, `servicos`, `dependencias`, `nucleo` | `modelos`, `repositorios`, SQLAlchemy |
| `dtos.py` | Modelos Pydantic de entrada e saída, camelCase no JSON, `extra="forbid"` na entrada, limites vindos de `preferencias.py` | `nucleo.dtos`, `preferencias` | `modelos`, FastAPI |
| `mapeadores.py` | Funções puras: DTO → comando de domínio e entidade → DTO | `dtos`, `dominio`, `modelos` | FastAPI, sessão do banco |
| `servicos.py` | Casos de uso; controlam a transação (unidade de trabalho) e o enfileiramento | `dominio`, `repositorios`, `excecoes`, `nucleo` | FastAPI, `dtos` |
| `dominio.py` | Regras puras: normalização de nome e e-mail, política de senha, validação de fuso, regra de nova versão do FSRS | biblioteca padrão, `preferencias`, `excecoes` | SQLAlchemy, FastAPI |
| `repositorios.py` | Consultas SQLAlchemy; todo método de recurso de estudante exige `usuario_id`; converte `IntegrityError` em `Conflito` | `modelos`, `excecoes`, `nucleo.banco` | FastAPI, `dtos` |
| `modelos.py` | Entidades SQLAlchemy (mapeamento declarativo tipado) | SQLAlchemy | todo o resto |
| `excecoes.py` | Exceções do domínio, subclasses de `nucleo.erros` | `nucleo.erros` | — |

**Controle de exceções** (`nucleo/erros.py`):

```text
ErroAplicacao(codigo, mensagem, status, campos=None)
├── RequisicaoMalformada   400  requisicao_malformada
├── NaoAutenticado         401  nao_autenticado | credenciais_invalidas
├── AcessoNegado           403  csrf_invalido | origem_nao_permitida
├── RecursoNaoEncontrado   404  recurso_nao_encontrado
├── Conflito               409  email_em_uso
├── EntradaInvalida        422  dados_invalidos | senha_atual_incorreta
└── LimiteExcedido         429  muitas_tentativas (+ Retry-After)
```

- **Handlers centrais** convertem `ErroAplicacao`, `RequestValidationError` (vira `422 dados_invalidos`, com mensagens em português e nomes de campo em camelCase), JSON inválido (vira `400`) e qualquer outra exceção (vira `500 erro_interno`, com a pilha só no log) no corpo `Erro` do [contrato](contracts/openapi.yaml), sempre com `idRequisicao`.
- **Respostas `401`** também apagam os cookies.
- **Nenhum `except` vazio:** toda exceção capturada é convertida numa `ErroAplicacao` ou registrada e relançada. Um teste de arquitetura (`tests/arquitetura/`) verifica as importações proibidas da tabela acima.

## Contratos

- O contrato completo está em [`contracts/openapi.yaml`](contracts/openapi.yaml):

  | Método e caminho | Uso | História |
  |---|---|---|
  | `GET /api/v1/auth/csrf` | Emite o token anti-CSRF | US1, US2 |
  | `POST /api/v1/auth/cadastro` | Cria a conta e inicia a sessão | US1 |
  | `POST /api/v1/auth/entrada` | Inicia a sessão | US1 |
  | `POST /api/v1/auth/saida` | Encerra a sessão | US1 |
  | `GET /api/v1/perfil` | Consulta o perfil | US3 |
  | `PATCH /api/v1/perfil` | Altera o perfil | US3 |
  | `POST /api/v1/perfil/senha` | Troca a senha | US4 |
  | `POST /api/v1/perfil/exclusao` | Exclui a conta | US4 |
  | `GET /health`, `GET /health/ready` | Verificações de saúde | — |

- **Erros:** corpo único `{codigo, mensagem, campos?, idRequisicao}` e códigos estáveis (`Erro.codigo`). As próximas specs acrescentam códigos, mas não mudam nem removem os existentes.
- **Versionamento:** prefixo `/api/v1`. Mudança incompatível exige `/api/v2` e uma nova DTEC.
- **Swagger UI:** em `/api/docs` e o OpenAPI em `/api/openapi.json`, somente quando `APP_AMBIENTE=desenvolvimento`.
- **Exclusão com POST:** a exclusão usa `POST /perfil/exclusao` porque `DELETE` com corpo (a senha) tem suporte irregular em proxies e clientes.

## Dados

- **Entidades e regras:** `usuarios`, `sessoes`, `parametros_fsrs` e `tentativas_acesso` (esta é nova), detalhadas em [data-model.md](data-model.md). O [esquema inicial](../../arquitetura/esquema-inicial.dbml) foi atualizado com a tabela nova e com o limite de 100 caracteres do nome.
- **Migrações:** Alembic, revisadas à mão, com PK `bigint generated always as identity` (convenção do `AGENTS.md`).
  - `0001` aplica o esquema da versão fixada do Procrastinate. As atualizações da biblioteca entram como novas revisões, com os arquivos de migração dela.
  - `0002` cria os enums `papel_usuario` e `origem_parametros_fsrs`, as quatro tabelas, os `CHECK` de D-001 e os índices.
- **Origem e validação:** só o cadastro cria usuários. Os limites ficam num único ponto (`preferencias.py`), repetidos como `CHECK` no banco e expostos ao frontend pelo OpenAPI (`limites.gerado.ts`).
- **Retenção e descarte:** a exclusão da conta é física e completa (DTEC 021). Tentativas expiram em 24 horas. Sessões inválidas são apagadas 30 dias depois.
- **Dados de teste:** contas fictícias geradas pelas fábricas, com domínio `exemplo.com` (regra 10).

## Estratégia de testes

Os marcadores `unit`, `integration`, `functional`, `security` e `adversarial` são obrigatórios. Um marcador desconhecido é erro (`--strict-markers`). Cada teste cita no nome ou na *docstring* o requisito que cobre (RF, RQ, CS ou cenário), e o `traceability.md` da etapa 7 consolida a ligação.

**Banco nos testes:** um banco `plataforma_teste` no mesmo contêiner do Postgres, migrado uma vez por execução. Cada teste roda numa transação externa com *savepoints* (`join_transaction_mode="create_savepoint"`), desfeita ao final. Os testes de concorrência usam conexões reais e limpam o que criam.

- **Unitários (`unit`):**
  - Normalização de nome e e-mail.
  - Política de senha: limites 7, 8, 128 e 129, só espaços e senha da lista comum em outra caixa.
  - Validação de fuso, com IANA válido, inválido e recurso no cadastro.
  - Limites de D-001 nas fronteiras.
  - Regra de nova versão do FSRS: o mesmo valor não cria versão.
  - Assinatura e verificação do token CSRF.
  - Cálculo de validade da sessão (inatividade × absoluta, com relógio controlado).
  - Mapeadores.
  - Hypothesis para normalização e validação de texto.
- **Integração (`integration`):**
  - Repositórios contra o Postgres.
  - Índice único de e-mail sem diferenciar caixa.
  - Cascata de sessões.
  - Versionamento de `parametros_fsrs` com travamento.
  - Enfileiramento atômico de `apagar_objetos_usuario`: o *rollback* não deixa tarefa.
  - Tarefa de exclusão de objetos com o adaptador de disco numa pasta temporária.
  - `limpar_registros_expirados`.
  - Migrações sobem e descem.
- **Contrato:** o OpenAPI gerado contém o `contracts/openapi.yaml`, e toda resposta de erro observada nos testes valida contra o esquema `Erro`.
- **Funcionais (`functional`):** um teste por cenário de aceitação da US1 a US4, de ponta a ponta pela API, com cookies e CSRF reais. Inclui:
  - Cadastro → saída → entrada.
  - Preservação dos valores digitados (verificada no frontend).
  - Troca de senha com duas sessões.
  - Exclusão seguida de novo cadastro com o mesmo e-mail.
- **Segurança (`security`):**
  - **Isolamento:**
    - Duas contas em todas as rotas.
    - Teste que percorre as rotas e exige cobertura de todo parâmetro de caminho (DTEC 019).
    - `401` sem dados em todas as rotas protegidas.
  - **Enumeração:**
    - Mesmo corpo e mesmo status para e-mail inexistente e senha errada.
    - Diferença de tempo de resposta dentro de uma tolerância estatística.
    - Bloqueio igual para e-mail com e sem conta.
  - **Força bruta:** 5 falhas por conta, 20 falhas por endereço de rede e 10 cadastros por hora (RQ-003). O bloqueio vale com a senha correta.
  - **Sessão:**
    - Fixação: o identificador muda na entrada.
    - Logout e uso posterior.
    - Expiração por inatividade e absoluta.
    - Sessão revogada em outra aba.
  - **CSRF:**
    - Sem cabeçalho, com token de outra sessão e com `Origin` estranha.
    - `Sec-Fetch-Site: cross-site` recusado.
  - **Cookies:** atributos `HttpOnly`, `Secure`, `SameSite` e o prefixo `__Host-`.
  - **Papel:** nenhum corpo consegue alterar o `papel` (RF-003), nem com `extra` no JSON.
  - **Senhas:** não aparecem no banco nem em logs (RQ-001, RQ-002), verificado com captura de logs.
  - **Exclusão:** depois da exclusão, nenhuma linha em tabela com `usuario_id` (pelo catálogo) nem objeto sob o prefixo (CS-004).
- **Adversariais (`adversarial`):**
  - **Entradas extremas:** payloads gigantes (corpo limitado a 64 KiB em `/api/v1/auth` e `/api/v1/perfil`), Unicode malicioso (caracteres de controle, RTL, combinação), e-mail com espaços e caixa mista e fuso com *path traversal* (`../../etc`).
  - **Concorrência:**
    - Dois cadastros simultâneos com o mesmo e-mail: só um cria a conta.
    - Exclusão pedida duas vezes em paralelo: um único efeito.
    - Rajada paralela de entradas: o limite não é ultrapassado.
    - Troca de retenção concorrente: versões sem lacuna nem duplicata.
  - **Reenvio:** cadastro reenviado depois de sucesso responde `409`.
- **Frontend (Vitest, Testing Library, MSW e `vitest-axe`):**
  - Formulários de cadastro, entrada e perfil: erros por campo vindos do `422`, foco no primeiro erro, valores preservados e mensagem neutra de entrada.
  - Aviso de privacidade (RF-013).
  - Explicação da retenção (US3-1).
  - Diálogo de exclusão com foco preso e senha obrigatória.
  - Redirecionamento de rota protegida.
  - Repetição única após `403 csrf_invalido`.
  - axe sem violações nas três telas (RQ-004).
- **Jornada:** a verificação manual da história P1 está no [quickstart](quickstart.md). O Playwright entra no final acadêmico (DTEC 014).
- **Casos de falha:** banco indisponível (`/health/ready` responde `503`, a API responde `500 erro_interno` sem detalhes), lista de senhas ausente (a aplicação não sobe) e segredo da aplicação curto ou ausente (a aplicação não sobe).

## Observabilidade e operação

- **Logs JSON (structlog):**
  - Campos: `idRequisicao`, método, rota (modelo, sem valores), status, duração, `usuario_public_id` quando autenticado, e eventos de domínio (`conta_criada`, `entrada_recusada`, `bloqueio_aplicado`, `sessao_revogada`, `conta_excluida`).
  - Um processador remove senha, cookies, `X-CSRF-Token` e corpos de `/auth` e `/perfil`; o teste do RQ-002 verifica isso.
  - O e-mail nunca é registrado; quando preciso, registra-se a chave HMAC.
- **Correlação:** o cabeçalho `X-Request-ID` de entrada é aceito só se for um UUID válido; caso contrário, um novo é gerado. Ele volta na resposta e no `idRequisicao`.
- **Saúde:** `/health` informa o processo; `/health/ready` testa `SELECT 1` e o acesso às tabelas do Procrastinate. O Compose usa os dois.
- **Cabeçalhos:** `X-Content-Type-Options: nosniff`, `Referrer-Policy: same-origin`, `X-Frame-Options: DENY`, e `Cache-Control: no-store` em `/api/v1/auth` e `/api/v1/perfil`. CSP e HSTS ficam no Caddy do final acadêmico (arquitetura, seção 8).
- **Falhas e retomada:** a tarefa de exclusão de objetos é idempotente e tem novas tentativas. Uma tarefa que esgota as tentativas fica visível no estado do Procrastinate e é tratada no runbook do final acadêmico.

## Integração contínua e qualidade ([DTEC 017](../../research.md#decisão-dtec-017-integração-contínua-e-verificação-local))

| Etapa | Backend | Frontend |
|---|---|---|
| Formatação | `ruff format --check` | `prettier --check` |
| Lint | `ruff check`, com regras de segurança (`S`), *bugbear*, *imports* e *pyupgrade* | `eslint` com `typescript-eslint` (*strict, type-checked*), `react-hooks` e `jsx-a11y` |
| Tipos | `mypy --strict` | `tsc --noEmit` |
| Testes | `pytest` com cobertura (relatório, sem mínimo no MVP; DTEC 014) | `vitest run` com cobertura |
| Contrato | `exportar_openapi` sem diferença com o versionado | `gerar:api` sem diferença com o versionado |
| Construção | imagem `prod` | `vite build` e imagem `prod` |

O fluxo constrói as imagens `dev` e executa tudo pelo Compose (DTEC 001: a suíte roda no contêiner), a cada push na `develop` e em todo pull request para a `main`.

## Variáveis de ambiente (`.env.example`)

| Variável | Uso | Padrão no exemplo |
|---|---|---|
| `APP_AMBIENTE` | `desenvolvimento`, `teste` ou `producao` | `desenvolvimento` |
| `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` | Banco local | sem senha (preencher) |
| `SEGREDO_APLICACAO` | HMAC do CSRF e da chave das tentativas; mínimo 32 bytes | sem valor (gerar) |
| `ORIGENS_PERMITIDAS` | Origens aceitas no `Origin` | `http://localhost:5173` |
| `PROXIES_CONFIAVEIS` | Endereços cujo `X-Forwarded-For` é aceito | rede do Compose |
| `COOKIE_SESSAO_NOME`, `COOKIE_CSRF_NOME` | Nomes dos cookies | `__Host-sessao`, `__Host-csrf` |
| `SESSAO_DIAS_INATIVIDADE`, `SESSAO_DIAS_MAXIMO` | RF-006, D-006 | `14`, `30` |
| `LIMITE_FALHAS_CONTA`, `LIMITE_FALHAS_IP`, `JANELA_TENTATIVAS_MIN`, `BLOQUEIO_MIN`, `LIMITE_CADASTROS_IP_HORA` | RQ-003 | `5`, `20`, `15`, `15`, `10` |
| `ARGON2_CONCORRENCIA` | Cálculos simultâneos de hash | `4` |
| `ARMAZENAMENTO_ADAPTADOR`, `ARMAZENAMENTO_DIRETORIO` | DTEC 010 | `local`, `/dados/arquivos` |
| `LOG_NIVEL` | Nível dos logs | `INFO` |

A aplicação valida todas as variáveis ao iniciar (pydantic-settings) e **não sobe** com valor ausente ou inválido.

## Riscos técnicos

| Risco | Consequência | Mitigação | Como verificar |
|---|---|---|---|
| Prazo de 15/10/2026 para o MVP inteiro | 002 a 007 sem tempo | Estrutura base mínima e completa primeiro; US1/US2 antes de US3/US4; tarefas por história | Quickstart da P1 funcionando antes da US3 |
| Enumeração de contas por tempo de resposta | Viola CS-003 | Hash fictício para e-mail inexistente; bloqueio pela chave do e-mail | Teste estatístico de tempo; teste de corpo idêntico |
| Força bruta distribuída | Senhas fracas comprometidas | Limites por conta e por IP, lista de senhas comuns, Argon2id | Testes `security/` de limites |
| Pico de memória do Argon2 na VPS | Falta de memória sob rajada | Semáforo de 4 cálculos (256 MiB no máximo) | Teste de carga simples no ensaio de deploy |
| Dependência sem *wheel* para Python 3.13 | Construção da imagem falha | Risco baixo: 3.13 é a versão adotada justamente pela maturidade do ecossistema (decisão de 13/10/2026) | Construção da imagem na integração contínua |
| Cookie `__Host-` em `http://localhost` em algum navegador | Sessão não persiste em desenvolvimento | Nome configurável por ambiente | Verificação do quickstart nos navegadores da equipe |
| `X-Forwarded-For` forjado | Limite por IP contornado | Só aceito de proxies confiáveis | Teste adversarial com cabeçalho forjado |
| Domínio novo esquecido no registro de exclusão | Dados remanescentes (viola CS-004) | Teste pelo catálogo do PostgreSQL | Teste de exclusão com todas as tabelas com `usuario_id` |
| Rota nova sem teste de isolamento (specs seguintes) | Vazamento entre estudantes | Teste que percorre as rotas (DTEC 019) | Falha automática na integração contínua |
| Node 26 vira LTS no fim de outubro de 2026 | Versão desatualizada após o MVP | Versão fixada; revisar depois da apresentação | Revisão de dependências no final acadêmico |

## Complexidade e exceções

| Exceção | Por que é necessária | Alternativa mais simples rejeitada porque |
|---|---|---|
| Na exclusão da conta, os objetos do armazenamento são apagados **depois** das linhas, por tarefa (contrária à regra "objetos antes das linhas" do esquema) | A exclusão precisa ser atômica e ter um único efeito (DTEC 021) | Apagar os objetos antes: uma falha no meio deixa linhas apontando para arquivos inexistentes |
| Nova tabela `tentativas_acesso`, fora do esquema inicial | Limites persistentes e consistentes sob concorrência (RQ-003, DTEC 020) | Contadores em memória: zeram a cada reinício e não funcionam com mais de um processo |
| Migração da 001 cria só as colunas que a 001 usa em `usuarios` | Cada spec é dona das colunas que usa (as de gamificação são da 006) | Criar a tabela inteira agora: a 001 passaria a carregar regras da 006 sem testes |

## Saídas do planejamento

- [`research.md`](research.md): DTEC 019 a 023. As decisões transversais deste planejamento (emenda da DTEC 002 e DTEC 015 a 018) estão em [`../../research.md`](../../research.md).
- [`data-model.md`](data-model.md): entidades, estados e validações.
- [`contracts/openapi.yaml`](contracts/openapi.yaml): contrato da API.
- [`quickstart.md`](quickstart.md): validação local.
- **Propagação:** [`esquema-inicial.dbml`](../../arquitetura/esquema-inicial.dbml), [arquitetura](../../arquitetura/README.md), [padrões de implementação](../../skills/padroes-implementacao.md) e [pendências](../../produto/pendencias.md) foram atualizados com as decisões acima.
- `tasks.md`: criado somente depois da aprovação deste plano (portão "Plano aprovado").
