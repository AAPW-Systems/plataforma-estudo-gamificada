# Retomada da implementação da spec 001 a partir da T024

**Data:** 2026-10-13
**Autor:**
**Agente e modelo:** Codex / GPT-6
**Etapa SDD:** implementar
**Funcionalidade:** 001-conta-acesso

## Contexto fornecido

Pausa da implementação da spec 001 na branch develop.

## Prompt de retomada

```text
Continue a implementação da spec 001 (docs/specs/001-conta-acesso) na branch `develop`, a partir da conclusão da T024. A sessão anterior foi pausada com segurança a pedido do usuário.

Leia antes, nesta ordem: .agents/AGENTS.md; docs/skills/contexto-tecnico.md e docs/skills/padroes-implementacao.md; docs/specs/001-conta-acesso/tasks.md, plan.md, data-model.md, research.md (DTEC 019 a 023) e contracts/openapi.yaml; docs/specs/divisao-implementacao-mvp.md (escopo: Onda 0, T001 a T045 da 001, até o ponto S1); os registros docs/prompts/2026-10-13-001-conta-acesso-implementacao.md e docs/prompts/2026-10-13-001-conta-acesso-implementacao-2.md (andamento, decisões e pendências). Para o frontend, leia também docs/skills/padroes-interface.md e docs/base-specs/design.md (seções 5 a 9.1). Crie um novo registro de prompts para sua sessão (regra 7) com este prompt literal e adicione-o ao índice docs/prompts/README.md. Não reescreva os registros encerrados.

Estado: T001 a T005 e T009 a T023 estão concluídas e com [x] no tasks.md. T006, T007 e T008 seguem sem [x] por falta de verificação (Compose completo, CI remoto, pre-commit). T024 está implementada, mas SEM [x]: falta a validação final com o usuário padrão da imagem web corrigida. T025 a T045 não foram iniciadas. Não houve push nem rebase nesta sessão, e S1 NÃO foi alcançado. Confira git status e git log antes de agir; preserve os commits locais e quaisquer alterações posteriores.

Commits concluídos: d614b73 (T021), b1e6779 (T022), 266da48 (T023). A T024 foi preservada em um commit próprio de incremento, com pendência explícita de validação. Backend em backend/ (uv, Python 3.13, FastAPI, SQLAlchemy 2 assíncrono, psycopg 3, Alembic, Procrastinate); frontend em frontend/ (React, Vite, TanStack, TypeScript 5.9, ESLint 9). Use somente a stack e as versões aprovadas.

O que foi acrescentado:
- T021: app/identidade/modelos.py (Usuario, Sessao, TentativaAcesso), app/revisao/modelos.py (ParametrosFsrs), registro em app/modelos.py e migracoes/versions/0002_identidade.py. Atenção: os IDs Alembic são `0001` e `0002`, não os nomes dos arquivos. Há testes de subida/descida (inclusive retorno à 0001), PK identity ALWAYS, CHECKs de D-001, 21 pesos, lower(email) único e comparação ORM/esquema em tests/integration/test_migracoes.py. Só `padrao` foi criado no enum de origem FSRS, pois `otimizado` é posterior ao MVP.
- T022: app/principal.py com criar_aplicacao, ciclo de vida da fábrica de sessões, relógio injetável e middlewares na ordem correlação → cabeçalhos → limite de corpo → proteção CSRF → erros inesperados; app/saude/{rotas,dtos,servicos}.py; app/exportar_openapi.py e backend/openapi.json. Swagger em /api/docs e OpenAPI HTTP em /api/openapi.json somente em desenvolvimento. Fixtures aplicacao e cliente adicionadas ao conftest: httpx com base_url https://teste, cookies Secure e cabeçalho CSRF automático nas escritas quando há cookie. Para testes negativos de CSRF, use cliente sem esse hook ou desative-o explicitamente.
- T023: tests/arquitetura/test_camadas.py usa AST, verifica imports absolutos/relativos e tem testes do próprio detector. Modelos podem importar tipos da biblioteca padrão e app.nucleo.banco.Base, exceção estrutural documentada à tabela de camadas.
- T024: frontend/src/componentes/ui/ contém Botao, CampoTexto, CampoSenha, CampoNumero, CampoFuso, Dialogo, Aviso e MensagemErroFormulario, mais ui.test.tsx (11 testes). frontend/src/estilos/tokens.css e global.css têm tokens claro/escuro e estilos. Paleta é preset intercambiável enquanto UI-02/UI-03 estão pendentes. frontend/Dockerfile ganhou `RUN chown -R node:node /app` no estágio dev para corrigir EACCES na criação de node_modules/.vitest-cache pelo usuário node.

Verificações executadas: última suíte completa do backend no contêiner: 216 testes passando; Ruff e mypy passaram (55 arquivos). Frontend: typecheck e lint passaram; 11 testes passaram (axe dos oito componentes, diálogo aberto, campos e foco); `npm run build` passou. Essas verificações do frontend usaram temporariamente `--user root` porque o Dockerfile anterior deixava node_modules sem permissão. A imagem web corrigida foi reconstruída com sucesso, mas a validação final com o usuário padrão NÃO executou: a autorização foi recusada durante a pausa. Não marque T024 concluída antes de executar essa verificação. O teste de retorno de foco usa waitFor porque o React Aria restaura o foco de modo assíncrono. Há avisos de Vite sobre futuro configLoader e de jsdom sem canvas; axe em jsdom não comprova contraste visual, que continua pendente na T061.

Faça, em ordem:
1. Conclua a T024: `docker compose run --rm --no-deps web sh -c 'npm run format:check && npm run lint && npm test && npm run build'`, com usuário padrão. Corrija somente o necessário, execute de novo os checks afetados, registre a evidência e só então marque [x]. Não descarte o incremento existente nem repita T021 a T023 sem necessidade.
2. T025 (cliente openapi-fetch, CSRF com repetição única, ErroApi e script gerar:api), T026 (roteamento público/autenticado e testes MSW) e T027 (Compose completo e CI remoto).
3. US1 e US2: T028 a T045, testes antes do código dentro de cada história. Pare na T045 (ponto S1) e avise para Arthur Moura começar a base da 002 somente quando S1 estiver efetivamente verificado.

Regras: um commit atômico por tarefa citando o ID (Conventional Commits, descrição em português). A T024 já tem um commit de incremento; sua conclusão pode ter commit próprio citando T024, sem reescrever histórico publicado. [x] no tasks.md só com teste executado (regra 6); nunca na main; nunca reescrever histórico publicado; sem segredos nem dados pessoais reais (contas @exemplo.com). Antes de cada push: git pull --rebase e suíte completa. Não faça push com testes falhando.

Ambiente desta máquina: raiz do repositório em `F:\Cesmac\Sistemas inteligentes\sistema\plataforma-estudo-gamificada`; Git e Docker estão instalados, mas não estavam no PATH. Caminhos: `C:\Program Files\Git\cmd\git.exe` e `C:\Program Files\Docker\Docker\resources\bin\docker.exe`. Para pull/build, acrescente o diretório bin do Docker ao PATH do processo, pois o auxiliar docker-credential-desktop precisa dele. Docker Desktop foi iniciado nesta sessão; db ficou saudável. `.env` local já existe, é ignorado e contém valores aleatórios gerados sem exibição: preserve-o, não copie .env.example por cima e não imprima segredos. Em outro ambiente, copie .env.example para .env e preencha POSTGRES_PASSWORD e SEGREDO_APLICACAO (mín. 32 bytes). Rode `docker compose up -d --wait db` e `docker compose run --rm --no-deps api uv run --frozen pytest`. O sandbox desta sessão exigiu autorização para acesso ao Docker; respeite os controles do seu ambiente.

Atenção especial à segurança: T031, T032, T034 e T035 (advisory lock ANTES da contagem na mesma transação; testes de rajada com fabrica_real, não savepoints; teste de tempo CS-003 estável); T041 deve percorrer as rotas e detectar falta de casos de isolamento (DTEC 019). O núcleo da sessão/CSRF/Argon2 já existe; leia-o antes de integrar.

Divergências/pendências a registrar no tasks.md e no novo registro: T041 cita alteração de perfil, senha e exclusão, que só serão implementadas em T049/T056 (após S1); não declare essas rotas cobertas nem antecipe US3/US4 silenciosamente. T037 exige o contrato completo, mas parte das rotas também está após S1: registre explicitamente cobertura incremental e pendências. backend/openapi.json contém só saúde por enquanto; as rotas de identidade chegam na T036. A resposta 413 do limite de corpo ainda não consta do contrato, pendência herdada para T065. app/nucleo/fila.py mantém MODULOS_TAREFAS vazio até T056. Não há CI remoto verificado nem Compose completo verificado. O próximo agente deve continuar da T024, não da T021.
```

## Saída aceita

Prompt de continuidade preparado para outro agente. Prompt preparado após a primeira pausa. A retomada posterior está documentada no registro de implementação 3.

## Alterações humanas

Pendente de revisão.

## Verificação

Texto do prompt preservado literalmente do arquivo original.

## Pendências

Confirmar o estado do repositório e as verificações pendentes antes de continuar.
