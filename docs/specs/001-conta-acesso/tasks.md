# Tarefas da funcionalidade

**Funcionalidade:** 001-conta-acesso (conta, sessão, isolamento e preferências)  
**Entrada:** [spec](spec.md), [plano](plan.md) (aprovado em 12/10/2026), [pesquisa](research.md), [modelo de dados](data-model.md), [contrato](contracts/openapi.yaml) e [quickstart](quickstart.md)  
**Formato:** `[ID] [P?] [US?] ação com caminho exato e resultado verificável`  
**Status:** aprovadas em 13/10/2026 por Artur Lins (equipe), junto com a [rastreabilidade](traceability.md), com o Python 3.13 no lugar do 3.14

- `[P]` indica que a tarefa pode ser executada em paralelo, porque não altera os mesmos arquivos nem depende de outra tarefa pendente.
- `[US1]` relaciona a tarefa a uma história de usuário.
- Marque `[x]` somente quando o resultado e a sua verificação estiverem concluídos (regra 6).
- **Caminhos:** `backend/src/app/` aparece abreviado como `app/`, e `backend/tests/` como `tests/`.
- **Testes antes do código:** em cada história, as tarefas de teste vêm antes das de implementação. Os testes começam falhando e passam ao fim da história.
- **Commits:** todo trabalho acontece na `develop` (regra 14), com um commit atômico por tarefa ou por par teste e implementação, citando o ID (ex.: `feat(identidade): implementa o cadastro [T036]`).

## Fase 1 Preparação (estrutura base do repositório)

- [x] T001 Criar `.editorconfig` e `.gitattributes` (UTF-8, LF) na raiz e ampliar o `.gitignore` (`.venv/`, `__pycache__/`, `node_modules/`, `dist/`, `coverage/`, `.pytest_cache/`, `.mypy_cache/`, `dados/`).
- [x] T002 [P] Criar o projeto do backend com o uv em `backend/pyproject.toml`, `backend/.python-version` (3.13) e `backend/uv.lock`, com as dependências do plano em versões fixas. A configuração inclui:
  - Ruff: formatação e regras `E`, `F`, `I`, `B`, `S`, `UP`, `ASYNC`.
  - `mypy --strict`.
  - pytest com `--strict-markers` e os marcadores `unit`, `integration`, `functional`, `security` e `adversarial`, e `asyncio_mode=auto`.

  **Verificação:** `uv sync --locked` instala tudo em Python 3.13.
- [x] T003 [P] Criar o projeto do frontend:
  - **Pacote:** `frontend/package.json` (`engines.node` 24, scripts `dev`, `build`, `test`, `lint`, `typecheck`, `format`, `gerar:api`), `package-lock.json` e `.nvmrc`.
  - **Configuração:** `tsconfig.json` em modo *strict*, `eslint.config.js` (`typescript-eslint` com as regras *strict type-checked*, `react-hooks`, `jsx-a11y`), `.prettierrc`, `vite.config.ts` (proxy de `/api` para `api:8000` e plugin do TanStack Router) e `vitest.config.ts` (jsdom, setup do MSW).
  - **Ponto de entrada:** `index.html` e `src/main.tsx`.

  **Verificação:** `npm ci && npm run build` passa.
- [x] T004 [P] Criar `backend/Dockerfile` multi-stage (`base` com uv, `dev` com recarga, `prod` sem ferramentas de desenvolvimento e com usuário não root) e `backend/.dockerignore`.
- [x] T005 [P] Criar `frontend/Dockerfile` multi-stage (`deps`, `dev` com o servidor do Vite, `build`, `prod` com os estáticos) e `frontend/.dockerignore`.
- [ ] T006 Criar o `compose.yaml` com os serviços `db` (`pgvector/pgvector`, volume e *healthcheck*), `migrate` (execução única), `api` e `worker` (que dependem do `migrate` concluído) e `web`, além do `.env.example` com todas as variáveis da tabela do plano, sem valores secretos (regra 9).
- [ ] T007 [P] Criar `.github/workflows/ci.yml` com as etapas da tabela "Integração contínua e qualidade" do plano, a cada push na `develop` e em todo pull request para a `main` (DTEC 017).
- [ ] T008 [P] Criar `.pre-commit-config.yaml` com Ruff (lint e formatação), Prettier e ESLint, documentado como opcional.

## Fase 2 Base compartilhada (bloqueia todas as histórias)

### Núcleo do backend

- [x] T009 [P] Criar os testes da configuração em `tests/unit/nucleo/test_configuracao.py`: a aplicação não sobe sem `SEGREDO_APLICACAO`, com segredo de menos de 32 bytes ou com limite inválido. Implementar `app/nucleo/configuracao.py` (pydantic-settings).
- [x] T010 [P] Criar os testes de erros em `tests/unit/nucleo/test_erros.py`. Eles verificam que:
  - cada subclasse de `ErroAplicacao` vira o corpo `Erro` com o status certo;
  - `RequestValidationError` vira `422 dados_invalidos`, com campos em camelCase e mensagens em português;
  - JSON inválido vira `400 requisicao_malformada`;
  - uma exceção inesperada vira `500 erro_interno`, sem detalhes no corpo e com a pilha no log;
  - `LimiteExcedido` envia `Retry-After`.

  Implementar `app/nucleo/erros.py` e `app/nucleo/dtos.py` (`ModeloDTO` em camelCase, `ErroDTO`, `ErroCampoDTO`).
- [x] T011 [P] Criar os testes de logs e *middlewares* em `tests/unit/nucleo/test_logs.py`. Eles verificam que:
  - senha, cookies, `X-CSRF-Token` e os corpos de `/auth` e `/perfil` são mascarados (RQ-002);
  - um `X-Request-ID` que não é UUID é substituído;
  - a resposta tem `X-Content-Type-Options`, `Referrer-Policy`, `X-Frame-Options` e, nas rotas de conta, `Cache-Control: no-store`;
  - um corpo acima de 64 KiB é recusado.

  Implementar `app/nucleo/logs.py` (structlog JSON) e `app/nucleo/middlewares.py`.
- [x] T012 [P] Criar os testes do endereço de rede em `tests/unit/nucleo/test_rede.py`: o `X-Forwarded-For` só é aceito de proxies confiáveis. Implementar `app/nucleo/rede.py`.
- [x] T013 Implementar `app/nucleo/banco.py`: engine assíncrono `postgresql+psycopg`, sessão e unidade de trabalho que expõe a conexão psycopg da transação.
- [x] T014 Implementar `app/nucleo/fila.py`: `App` do Procrastinate com `PsycopgConnector` e uma função que enfileira na conexão da transação atual. Criar `app/worker.py`.
- [x] T015 Configurar o Alembic em `backend/alembic.ini` e `backend/migracoes/env.py`, e criar a revisão `backend/migracoes/versions/0001_procrastinate.py` com o esquema da versão fixada do Procrastinate.
- [x] T016 Criar `tests/conftest.py` e `tests/fabricas.py` com:
  - banco `plataforma_teste` criado e migrado uma vez por execução;
  - transação com *savepoints* por teste;
  - cliente `httpx.AsyncClient` que trata cookies e CSRF;
  - relógio controlável;
  - adaptador de armazenamento em memória;
  - fábricas de contas fictícias (`@exemplo.com`, regra 10).
- [x] T017 Criar o teste de enfileiramento atômico em `tests/integration/nucleo/test_fila_transacao.py`: um *rollback* não deixa tarefa na fila, e um commit deixa (emenda da DTEC 002).
- [x] T018 [P] Criar a interface de armazenamento em `app/nucleo/armazenamento/` (`interface.py`, `memoria.py`, `disco.py`), com `apagar_prefixo`, e a suíte de contrato `tests/integration/nucleo/test_armazenamento_contrato.py`, rodada contra os dois adaptadores. A suíte inclui a recusa de chave que escapa da raiz, contra *path traversal* (DTEC 010 e 021).
- [x] T019 [P] Implementar o registro de exclusão por domínio em `app/nucleo/exclusao.py`, com teste unitário de ordem em `tests/unit/nucleo/test_exclusao.py`.
- [x] T020 [P] Criar os testes de segurança do núcleo em `tests/unit/nucleo/test_seguranca.py`:
  - **Sessão:** token de 256 bits; hash SHA-256; validade por inatividade de 14 dias e absoluta de 30 dias, com relógio controlado; renovação no máximo uma vez por minuto.
  - **CSRF:** a assinatura liga o token à sessão ou à pré-sessão; um token de outra sessão é recusado.
  - **Argon2:** perfil da RFC 9106, semáforo, `check_needs_rehash` e hash fictício.

  Implementar `app/nucleo/seguranca/sessoes.py`, `csrf.py` e `senhas.py`, além da verificação de CSRF, `Origin` e `Sec-Fetch-Site` nas requisições que alteram estado (DTEC 023).
- [x] T021 Criar as entidades e a migração da identidade:
  - **Entidades:** `app/identidade/modelos.py` (Usuario, Sessao, TentativaAcesso) e `app/revisao/modelos.py` (ParametrosFsrs).
  - **Migração** `backend/migracoes/versions/0002_identidade.py`: enums, as quatro tabelas, os `CHECK` de D-001, os índices (inclusive `lower(email)`), PK `generated always as identity` e `public_id` com `gen_random_uuid()`.

  **Verificação:** `tests/integration/test_migracoes.py` sobe e desce as migrações.
- [x] T022 Implementar `app/principal.py` (`criar_aplicacao`, *middlewares*, *handlers* e Swagger só em desenvolvimento), `app/saude/rotas.py` (`/health` e `/health/ready`) e `app/exportar_openapi.py`. Teste em `tests/integration/test_saude.py`: com o banco indisponível, `/health/ready` responde `503`.
- [ ] T023 [P] Criar o teste de arquitetura em `tests/arquitetura/test_camadas.py`, com as importações proibidas da tabela "Camadas do backend" do plano (DTEC 018).

### Base do frontend

- [ ] T024 [P] Criar os tokens de design claro e escuro em `frontend/src/estilos/` (seção 5 do [design](../../base-specs/design.md)) e os componentes de `frontend/src/componentes/ui/` sobre o React Aria (DTEC 016): `Botao`, `CampoTexto`, `CampoSenha`, `CampoNumero`, `CampoFuso`, `Dialogo`, `Aviso` e `MensagemErroFormulario`. Cada um tem um teste com Testing Library e `vitest-axe`.
- [ ] T025 Criar o cliente da API em `frontend/src/api/`:
  - `cliente.ts`: `openapi-fetch` com *middleware* que envia `X-CSRF-Token` e repete uma vez após `403 csrf_invalido`;
  - `erros.ts`: `ErroApi` tipado;
  - script `gerar:api`, que produz `esquema.gerado.d.ts` e `limites.gerado.ts` a partir de `backend/openapi.json`.

  Teste em `frontend/src/api/cliente.test.ts`, com MSW.
- [ ] T026 Criar o roteamento em `frontend/src/rotas/`: `__root.tsx` e os layouts `_publico` e `_autenticado`. O `beforeLoad` deste último consulta `GET /api/v1/perfil` pelo TanStack Query e redireciona para `/entrar` com `401`. Criar também `frontend/src/testes/`, com os *handlers* do MSW e a renderização com roteador. Teste: uma rota protegida sem sessão redireciona.
- [ ] T027 **Verificar a base:** `docker compose up --build` sobe todos os serviços saudáveis, `/health/ready` responde `200` e a integração contínua passa na `develop`. Registrar o resultado no registro de prompts da sessão de implementação.

## Fase 3 História de usuário 1 Criar conta e entrar (P1)

**Objetivo:** o estudante cria a conta, entra, sai e é protegido contra enumeração e força bruta.  
**Teste independente:** cadastrar uma conta fictícia, sair, entrar de novo e chegar à área do estudante; entrar com a senha errada e receber a mensagem neutra (passos 1 a 10 da US1 no [quickstart](quickstart.md)).

- [ ] T028 [P] [US1] Criar a lista de senhas em `app/identidade/dados/senhas_comuns.txt`: lista NCSC de 100 mil senhas do SecLists, com cabeçalho de origem e licença MIT, mais a lista curta em português (DTEC 022). A lista em português passa pela revisão da equipe no pull request.
- [ ] T029 [P] [US1] Criar os testes unitários do domínio em `tests/unit/identidade/test_dominio.py`, com Hypothesis na normalização:
  - normalização de nome e e-mail (NFC, extremidades, caixa);
  - nome vazio, só com espaços, com 100 e 101 caracteres, e com caracteres de controle;
  - senha com 7, 8, 128 e 129 caracteres, só com espaços e da lista comum em outra caixa;
  - fuso IANA válido e inválido, e recurso `America/Sao_Paulo` no cadastro.
- [ ] T030 [P] [US1] Criar os testes funcionais dos cenários 1 a 8 da US1 em `tests/functional/identidade/test_us1_conta_entrada.py`.
- [ ] T031 [P] [US1] Criar os testes de segurança da autenticação em `tests/security/identidade/test_autenticacao.py`:
  - **Enumeração:** corpo e status idênticos para e-mail inexistente e senha errada; tempo de resposta dentro da tolerância (CS-003).
  - **Limites:** 5 falhas por conta (com a senha correta na sexta), 20 por endereço de rede e 10 cadastros por hora (RQ-003); bloqueio igual para e-mail com e sem conta.
  - **Sessão:** novo identificador a cada entrada, contra fixação; atributos e prefixo dos cookies; sessão inacessível ao JavaScript (RQ-001).
  - **CSRF e papel:** CSRF no cadastro e na entrada; `papel` e campos extras recusados (RF-003).
  - **Dados sensíveis:** senha nunca gravada nem registrada em log (RQ-001, RQ-002).
- [ ] T032 [P] [US1] Criar os testes adversariais em `tests/adversarial/identidade/test_autenticacao_adversarial.py`:
  - dois cadastros simultâneos com o mesmo e-mail (só um cria a conta);
  - rajada paralela de entradas (o limite não é ultrapassado);
  - corpo acima de 64 KiB;
  - Unicode malicioso (RTL, combinação, controle) e e-mail com espaços e caixa mista;
  - `X-Forwarded-For` forjado;
  - cadastro reenviado depois do sucesso (`409`).
- [ ] T033 [US1] Implementar `app/identidade/preferencias.py` (padrões e limites de D-001), `app/identidade/dominio.py` e `app/identidade/excecoes.py`, até que a T029 passe.
- [ ] T034 [US1] Implementar os repositórios:
  - `app/identidade/repositorios.py`: usuários, sessões e tentativas com `pg_advisory_xact_lock` e chave HMAC; `IntegrityError` do e-mail vira `Conflito`.
  - `app/revisao/repositorios.py`: criação da versão de `parametros_fsrs`.

  Testes de integração em `tests/integration/identidade/test_repositorios.py`.
- [ ] T035 [US1] Implementar os serviços:
  - `app/identidade/servicos.py`: `cadastrar`, `entrar` e `sair`, com limites, hash fictício e novo hash quando os parâmetros mudam.
  - `app/revisao/servicos.py`: `criar_parametros_iniciais`, com os pesos de `fsrs.Scheduler()` e a versão da biblioteca.
- [ ] T036 [US1] Implementar `app/identidade/dtos.py`, `mapeadores.py`, `dependencias.py` (`UsuarioAtual`) e `rotas.py`, com `GET /auth/csrf`, `POST /auth/cadastro`, `POST /auth/entrada`, `POST /auth/saida` e `GET /perfil`, até que as T030 a T032 passem.
- [ ] T037 [US1] Criar o teste de contrato em `tests/integration/test_contrato_openapi.py`: o OpenAPI gerado contém os caminhos, métodos, respostas e esquemas de `contracts/openapi.yaml`, e todo corpo de erro observado valida contra `Erro`. Gerar e versionar `backend/openapi.json` e rodar `npm run gerar:api`.
- [ ] T038 [P] [US1] Criar os testes de componente em `frontend/src/funcionalidades/identidade/FormularioCadastro.test.tsx` e `FormularioEntrada.test.tsx`:
  - aviso de privacidade sem caixa de aceite (RF-013);
  - erros do `422` junto do campo, foco no primeiro erro e valores preservados (cenário 2);
  - mensagem neutra no `401`;
  - indicação de tentar mais tarde no `429`;
  - "e-mail já em uso" no `409`;
  - axe sem violações.
- [ ] T039 [US1] Implementar as telas `frontend/src/rotas/_publico/cadastro.tsx` e `entrar.tsx`, com os formulários e os esquemas Zod de `frontend/src/funcionalidades/identidade/`, que usam os limites gerados. O cadastro envia o fuso de `Intl.DateTimeFormat().resolvedOptions().timeZone`. O layout tem dois painéis no desktop e coluna única no mobile ([design, 9.1](../../base-specs/design.md#91-autenticação)). Implementar também a ação "Sair" no layout autenticado e a trilha vazia em `frontend/src/rotas/_autenticado/index.tsx`.
- [ ] T040 [US1] Executar os passos 1 a 10 da US1 no quickstart e os testes `functional`, `security` e `adversarial` da US1, e registrar a evidência no registro de prompts da sessão.

## Fase 4 História de usuário 2 Acessar somente meus dados (P1)

**Objetivo:** nenhuma operação entrega, altera ou confirma recurso de outro estudante, e as requisições sem sessão ou sem proteção anti-CSRF são recusadas.  
**Teste independente:** com as contas fictícias A e B, a conta B usa nas operações expostas os identificadores e as credenciais da conta A, e nada vaza. `pytest -m security` passa, inclusive o teste que percorre as rotas.

- [ ] T041 [P] [US2] Criar `tests/security/test_isolamento_rotas.py` (DTEC 019). O teste:
  - lista `app.routes` e falha se alguma rota com parâmetro de caminho não estiver na tabela de casos;
  - confirma `401` sem dados em toda rota protegida sem sessão (cenário 2);
  - com duas contas, confirma que perfil, senha, exclusão e saída da conta B não afetam a conta A;
  - tem uma rota de teste com identificador, que só existe no teste, para provar que um recurso de outro dono responde `404` idêntico ao de inexistente (cenário 1).
- [ ] T042 [P] [US2] Criar `tests/security/test_csrf_origem.py`, parametrizado por todas as rotas que alteram estado (cenário 3): sem cabeçalho, com token de outra sessão, com `Origin` fora da lista e com `Sec-Fetch-Site: cross-site`, todas recusadas com `403`.
- [ ] T043 [US2] Implementar em `app/nucleo/` o auxiliar de busca por dono (`public_id` e `usuario_id`, `RecursoNaoEncontrado`), usado pelas specs 002 em diante, até que a T041 passe.
- [ ] T044 [US2] Implementar no `frontend/src/api/cliente.ts` o tratamento global de `401`: limpa o cache do TanStack Query e redireciona para `/entrar`. Teste em `frontend/src/api/cliente.test.ts`.
- [ ] T045 [US2] Executar os passos da US2 no quickstart e `pytest -m security`, e registrar a evidência.

## Fase 5 História de usuário 3 Ajustar perfil e preferências (P2)

**Objetivo:** o estudante ajusta nome, fuso e ritmo, só com valores válidos, e a retenção cria uma nova versão dos parâmetros do FSRS.  
**Teste independente:** alterar cada preferência para um valor válido e um inválido; alterar a retenção e conferir que a versão nova vale e que a anterior continua intacta.

- [ ] T046 [P] [US3] Criar os testes unitários dos limites de D-001 nas fronteiras e da regra de nova versão (o mesmo valor não cria versão) em `tests/unit/identidade/test_preferencias.py` e `tests/unit/revisao/test_parametros_fsrs.py`.
- [ ] T047 [P] [US3] Criar os testes funcionais dos cenários 1 a 4 da US3 em `tests/functional/identidade/test_us3_perfil.py`:
  - alteração tudo ou nada com vários campos inválidos;
  - versão n+1 criada e versão n intacta (RF-010, CB-29);
  - fuso alterado sem mexer em dados anteriores.
- [ ] T048 [P] [US3] Criar os testes adversariais em `tests/adversarial/identidade/test_perfil_adversarial.py`:
  - trocas de retenção concorrentes (versões sem lacuna nem duplicata);
  - fuso `../../etc/passwd`;
  - retenção com três casas;
  - corpo vazio;
  - campos extras (`papel`, `email`).
- [ ] T049 [US3] Implementar `PATCH /perfil`: regras em `app/identidade/dominio.py`, `alterar_perfil` em `app/identidade/servicos.py` (com `FOR UPDATE`), `nova_versao_retencao` em `app/revisao/servicos.py`, e os DTOs, mapeadores e rota. **Pronto quando:** as T046 a T048 passam.
- [ ] T050 [P] [US3] Criar o teste de componente em `frontend/src/funcionalidades/identidade/FormularioPerfil.test.tsx`: explicação em linguagem simples do efeito da retenção (cenário 1), erros por campo, valores preservados e axe sem violações.
- [ ] T051 [US3] Implementar a tela `frontend/src/rotas/_autenticado/perfil.tsx` ([design, 9.11](../../base-specs/design.md#911-perfil)), que invalida a consulta do perfil depois de salvar.
- [ ] T052 [US3] Executar o teste independente da US3 e registrar a evidência.

## Fase 6 História de usuário 4 Proteger e encerrar a conta (P3)

**Objetivo:** o estudante troca a senha, o que encerra as outras sessões, e exclui a conta, sem que nenhum dado permaneça.  
**Teste independente:** trocar a senha com duas sessões abertas e conferir que só a atual continua válida; excluir uma conta fictícia e conferir que nada permanece e que o e-mail pode ser cadastrado de novo.

- [ ] T053 [P] [US4] Criar os testes funcionais dos cenários 1 a 4 da US4 em `tests/functional/identidade/test_us4_senha_exclusao.py`. Eles cobrem:
  - duas sessões na troca de senha;
  - senha atual errada contando para o limite (cenário 2);
  - exclusão seguida de novo cadastro com o mesmo e-mail.
- [ ] T054 [P] [US4] Criar os testes de exclusão completa e das tarefas:
  - **Exclusão completa (CS-004)**, em `tests/security/identidade/test_exclusao_completa.py`: pelo catálogo do PostgreSQL, toda tabela com coluna `usuario_id` fica sem linhas da conta, e nenhum objeto sob `usuarios/{public_id}/` resta no adaptador de disco depois da tarefa.
  - **Tarefas**, em `tests/integration/identidade/test_tarefas.py`: `apagar_objetos_usuario` é idempotente, e `limpar_registros_expirados` apaga tentativas com mais de 24 horas e sessões inválidas há mais de 30 dias.
- [ ] T055 [P] [US4] Criar os testes adversariais em `tests/adversarial/identidade/test_exclusao_adversarial.py`:
  - exclusão pedida duas vezes em paralelo (um único efeito; o segundo pedido recebe `401`);
  - trocas de senha concorrentes;
  - exclusão com a conta bloqueada (`429`).
- [ ] T056 [US4] Implementar `trocar_senha` e `excluir_conta` em `app/identidade/servicos.py`:
  - a exclusão roda numa transação, com `FOR UPDATE`, o registro de exclusão e o enfileiramento de `apagar_objetos_usuario`;
  - as funções `apagar_dados_usuario` de `identidade` e `revisao` entram no registro.

  Implementar também `app/identidade/tarefas.py`, com `apagar_objetos_usuario` e a tarefa periódica `limpar_registros_expirados` às 3h UTC, e as rotas `POST /perfil/senha` e `POST /perfil/exclusao`, até que as T053 a T055 passem.
- [ ] T057 [P] [US4] Criar os testes de componente em `frontend/src/funcionalidades/identidade/FormularioSenha.test.tsx` e `DialogoExclusao.test.tsx`. O diálogo deve:
  - explicar que a exclusão é definitiva e o que é apagado (cenário 3);
  - prender o foco;
  - exigir a senha;
  - mostrar o erro de senha incorreta;
  - passar no axe sem violações.
- [ ] T058 [US4] Implementar no perfil a seção de segurança, com a troca de senha e o diálogo de exclusão. Depois da exclusão, a tela limpa o cache e redireciona para o cadastro.
- [ ] T059 [US4] Executar o teste independente da US4 e registrar a evidência.

## Fase final Qualidade transversal

- [ ] T060 Executar nos contêineres as suítes completas do backend e do frontend, a qualidade estática e a verificação do contrato, e confirmar a integração contínua aprovada na `develop`. Registrar as contagens de testes e a cobertura.
- [ ] T061 Revisar os itens de segurança e acessibilidade e registrar as evidências:
  - logs da `api` sem senha, e-mail, cookie ou corpo de autenticação (RQ-002);
  - ausência de segredos no repositório (regra 9);
  - cabeçalhos de segurança;
  - mensagens de erro em português;
  - teclado e leitor de tela nas três telas, uso em 320 px sem rolagem horizontal e contraste (RQ-004).
- [ ] T062 Medir o tempo de resposta da entrada no ambiente local (meta: menos de 1 segundo, conforme o plano) e o pico de memória da `api` numa rajada de 10 entradas, e registrar.
- [ ] T063 Conduzir o teste guiado com três pessoas, que criam a conta e chegam à trilha em até 2 minutos, sem ajuda (CS-001). Registrar os tempos sem dados pessoais.
- [ ] T064 Atualizar o [quickstart](quickstart.md) com os comandos realmente verificados, `docs/skills/padroes-implementacao.md` com os comandos e endereços, e o "Mapa do repositório" do `.agents/AGENTS.md` com `backend/` e `frontend/`.
- [ ] T065 Atualizar o [traceability.md](traceability.md) com os nomes reais dos testes e corrigir requisitos sem teste ou tarefa.

## Dependências

- **Preparação e base:** a Fase 1 bloqueia a Fase 2. A Fase 2 (T009 a T027) bloqueia todas as histórias. T013 bloqueia T014, T017 e T021; T015 bloqueia T021; T016 bloqueia todos os testes de integração em diante; T021 bloqueia T034.
- **US1:** T033 → T034 → T035 → T036 → T037. As tarefas de teste T029 a T032 e T038 não dependem umas das outras. T039 depende de T025, T026 e T037, porque usa os tipos gerados.
- **US2:** depende das rotas da US1 (T036). T041 e T042 rodam em paralelo.
- **US3 e US4:** dependem da US1 e podem ser feitas em paralelo, por pessoas diferentes, porque alteram funções distintas de `servicos.py` e `rotas.py`. Mesmo assim, os commits são separados e rebaseados localmente antes do push, nunca depois.
- **Fase final:** depende de todas as histórias.

## Pontos de paralelismo

- **Preparação:** T002, T003, T004, T005, T007 e T008 alteram arquivos distintos.
- **Base:** T009 a T012, T018 a T020, T023 e T024 são independentes entre si.
- **Histórias:** em cada uma, as tarefas de teste marcadas com `[P]` podem ser escritas em paralelo. O frontend de cada história (componentes e testes) avança em paralelo ao backend, desde que o contrato já esteja gerado (T037).

## Estratégia de incremento

1. **Base completa:** concluir a preparação e a base compartilhada. A T027 prova que o ambiente sobe com um comando e que a integração contínua passa.
2. **P1 demonstrável:** entregar a US1 e a US2, que é o mínimo para as specs 002 a 007 começarem.
3. **Histórias seguintes:** acrescentar a US3 e a US4 sem quebrar a P1. A suíte completa passa a cada commit.
4. **Verificação final:** executar a fase final e atualizar os artefatos afetados. Nenhum merge na `main` acontece sem todos os testes passando (regra 17).
