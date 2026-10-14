# Retomada da implementação da spec 001 a partir da T027

**Data:** 2026-10-13
**Autor:** pessoa responsável por esta sessão (a confirmar)
**Agente e modelo:** Claude Code / claude-sonnet-5-5
**Etapa SDD:** implementar
**Funcionalidade:** 001-conta-acesso

## Contexto fornecido

Documentos e estado descritos no prompt literal abaixo. Esta sessão rodou num contêiner de nuvem (Linux), e não na máquina Windows descrita no prompt: o clone inicial estava atrás do remoto e foi atualizado por `git pull --ff-only origin develop` (sem commits locais a preservar).

## Prompts

### Prompt 1

```text
Continue a implementação da spec 001 (docs/specs/001-conta-acesso) na branch develop, a partir da T027. A sessão anterior foi pausada com segurança a pedido do usuário.

Leia antes, nesta ordem: .agents/AGENTS.md; docs/skills/contexto-tecnico.md e docs/skills/padroes-implementacao.md; docs/specs/001-conta-acesso/tasks.md, plan.md, data-model.md, research.md (DTEC 019 a 023) e contracts/openapi.yaml; docs/specs/divisao-implementacao-mvp.md (escopo: Onda 0, T001 a T045 da 001, até S1); os registros docs/prompts/2026-10-13-001-conta-acesso-implementacao.md, docs/prompts/2026-10-13-001-conta-acesso-implementacao-2.md e docs/prompts/2026-10-13-001-conta-acesso-implementacao-3.md. Para o frontend, leia também docs/skills/padroes-interface.md e docs/base-specs/design.md (seções 5 a 9.1). Crie um novo registro de prompts para sua sessão (regra 7) com este prompt literal e adicione-o ao índice docs/prompts/README.md.

Estado: T001 a T005 e T009 a T026 estão concluídas e com [x] no tasks.md. T006 a T008 e T027 seguem sem [x] por falta de verificação; T028 a T045 não foram iniciadas. S1 não foi alcançado. Os commits até cdb9e13 (T026) foram publicados na develop. Há commits de documentação posteriores apenas locais: confira git status e git log e preserve-os. O último git pull --rebase origin develop passou; antes do push, 216 testes do backend e 18 do frontend passaram nos contêineres. O backend usa uv, Python 3.13, FastAPI, SQLAlchemy 2 assíncrono, psycopg 3, Alembic e Procrastinate; o frontend usa React, Vite, TanStack Router/Query, TypeScript 5.9, React Aria, MSW e openapi-fetch nas versões fixadas.

Faça, em ordem, T027 (verificar docker compose up -d --build --wait, /health/ready com 200 e o CI remoto na develop), depois US1 e US2 (T028 a T045), com testes antes do código dentro de cada história. A T027 está apenas parcialmente verificada: docker compose up -d --wait passou, com db/api/web saudáveis, migrate exit 0 e worker ativo; a tentativa com --build foi interrompida durante o chown da imagem web. O CI remoto continua desconhecido: uma consulta pelo conector GitHub retornou 404, o que não comprova seu resultado. Não marque T027 ou T007 sem evidência do CI. T006 pode ser marcada após verificação própria do Compose; T008 depende da verificação do pre-commit. Pare na T045 (ponto S1) e avise Arthur Moura para começar a base da 002 somente após verificar S1.

Regras: um commit atômico por tarefa citando o ID (Conventional Commits, descrição em português); [x] no tasks.md só com teste ou demonstração executados (regra 6); nunca na main; nunca reescrever histórico publicado; sem segredos nem dados pessoais reais (contas @exemplo.com); use só a stack aprovada. Preserve o .env local ignorado e não imprima seus valores. Em outro ambiente, copie .env.example para .env e preencha POSTGRES_PASSWORD e SEGREDO_APLICACAO (mínimo 32 bytes). Rode a suíte no contêiner com docker compose up -d --wait db e docker compose run --rm --no-deps api uv run --frozen pytest. Antes de cada push: git pull --rebase origin develop e suíte completa. Não faça push com testes falhando.

Ambiente desta máquina: repositório em F:\Cesmac\Sistemas inteligentes\sistema\plataforma-estudo-gamificada; Git em C:\Program Files\Git\cmd\git.exe; Docker em C:\Program Files\Docker\Docker\resources\bin\docker.exe. Para build ou pull de imagens, acrescente o diretório bin do Docker ao PATH do processo para localizar docker-credential-desktop. Docker Desktop está iniciado. Respeite as autorizações do sandbox.

Atenção especial à segurança: T031, T032, T034 e T035 exigem advisory lock antes da contagem na mesma transação, testes de rajada com fabrica_real em vez de savepoints e teste de tempo da CS-003 estável. T041 deve percorrer as rotas e detectar ausência de casos de isolamento (DTEC 019). Leia os módulos existentes de sessão, CSRF, Argon2 e proteção antes de integrar.

Registre no tasks.md e no novo registro as divergências do plano: T037 terá cobertura incremental do contrato porque algumas rotas só chegam depois de S1; T041 não pode declarar cobertas as rotas de perfil, senha e exclusão previstas para T049/T056. A resposta 413 ainda falta no contrato (pendência T065). O OpenAPI gerado ainda contém só saúde; regenere os tipos após criar as rotas de identidade em T036/T037. A consulta de perfil do frontend usa temporariamente retorno unknown e deve passar ao cliente tipado na T037; o tratamento global de 401 chega na T044. app/nucleo/fila.py mantém MODULOS_TAREFAS vazio até T056. Não reinicie T021 a T026: o ponto de retomada é T027.
```

### Prompt 2

```text
$ docker compose up -d --build --wait
[+] Building 260.3s (32/32) FINISHED
[… log de construção omitido neste registro; as etapas relevantes:]
 => [web dev 2/2] RUN chown -R node:node /app                                                                                                                                                                    240.5s
[+] up 7/7
 ✔ Image plataforma-api:dev              Built                                                                                                                                                                    260.5s
 ✔ Image plataforma-web:dev              Built                                                                                                                                                                    260.5s
 ✔ Container plataforma-estudo-migrate-1 Exited                                                                                                                                                                    18.2s
 ✔ Container plataforma-estudo-worker-1  Healthy                                                                                                                                                                   16.7s
 ✔ Container plataforma-estudo-api-1     Healthy                                                                                                                                                                   16.7s
 ✔ Container plataforma-estudo-web-1     Healthy                                                                                                                                                                   21.4s
 ✔ Container plataforma-estudo-db-1      Healthy

t28 revisada

prossiga
```

Interpretado como: a verificação do Compose completo foi feita pelo usuário (fecha T006 e T027), a lista de senhas da T028 foi revisada pela equipe, e a sessão deve seguir para a US3 da 001 (T046 em diante), que é a próxima da divisão da implementação.

## Saída aceita

T028 a T045 concluídas e publicadas na `develop` (US1 e US2, ponto S1 em termos de código). Parada na T045, como pedido. T006 e T027 foram marcadas depois da execução do Compose pelo usuário (Prompt 2); T007 e T008 foram verificadas e marcadas.

| Artefato | Ação |
|---|---|
| `.github/workflows/ci.yml` | corrigido: as etapas do frontend que gravam arquivos rodam como root (T007) |
| `.pre-commit-config.yaml` | corrigido: sem `--config` no Ruff (T008) |
| `.gitignore` | `dados/` passou a `/dados/` (ignorava a lista de senhas versionada) |
| `compose.yaml` | volume `./docs:/docs:ro` nos serviços do backend (testes de contrato) |
| `backend/src/app/identidade/` | `dados/senhas_comuns.txt`, `preferencias.py`, `excecoes.py`, `dominio.py`, `repositorios.py`, `servicos.py`, `dtos.py`, `mapeadores.py`, `dependencias.py`, `rotas.py` (T028, T033 a T036) |
| `backend/src/app/revisao/` | `repositorios.py` e `servicos.py` (`criar_parametros_iniciais`, `retencao_vigente`) |
| `backend/src/app/nucleo/` | `dono.py` (T043), `codigos.py` (`CodigoErro`, movido de `erros.py`), `openapi.py` (nomes do contrato, sem o sufixo `DTO`); `sessoes.py` com `TypeGuard` |
| `backend/src/app/principal.py` | serviço de identidade ligado no ciclo de vida; aceita `servico_senhas` e `senhas_comuns` |
| `backend/openapi.json`, `frontend/src/api/*.gerado.*` | regenerados com as rotas da identidade (T037) |
| `backend/tests/` | `unit/identidade` (domínio e limites), `integration/identidade/test_repositorios.py`, `integration/test_contrato_openapi.py`, `functional/`, `security/` (autenticação, isolamento por rota, CSRF e origem), `adversarial/`; apoio em `apoio_http.py`, `apoio_rotas.py`, `contrato.py` e `conftest.py` |
| `frontend/src/` | `funcionalidades/identidade/` (esquemas, erros, `FormularioCadastro`, `FormularioEntrada`, `LayoutAutenticacao`), rotas `entrar`, `cadastro`, layout autenticado com "Sair" e trilha vazia, cliente com 401 global (T044), consulta de perfil tipada; `CampoTexto` e `CampoNumero` corrigidos |
| `docs/specs/001-conta-acesso/tasks.md` | T007, T008, T028 a T045 marcadas (menos T006 e T027), com notas das divergências |
| `.agents/AGENTS.md`, `docs/skills/contexto-tecnico.md`, `docs/specs/README.md`, `docs/specs/001-conta-acesso/README.md` | estado atualizado para `Implementando` |

Commits (todos na `develop`, com o CI conferido): `9b239d6` (T007), `897bdde` (T028), `43429c2` (T029 e T033), `8dfe92c`, `e748370` (T034), `bef57cf` (T035), `c197650` (T030, T031, T032, T036 e T037), `9790138` (volume do Compose), `8288389` (T038 e T039), `8402a40` (T041 a T043), `0e8a2e1` (T044) e o commit da T008.

## Alterações humanas

Pendente de revisão. A lista de senhas em português (parte 2 de `senhas_comuns.txt`) espera a revisão da equipe (T028).

## Verificação

**Ambiente da sessão.** Contêiner de nuvem Linux, não a máquina Windows do prompt. O clone estava atrás do remoto e foi atualizado com `git pull --ff-only`. O daemon do Docker foi iniciado na sessão. A política de rede bloqueia `pkg-containers.githubusercontent.com` (blobs do `ghcr.io`, de onde o `Dockerfile` do backend copia o `uv`) e o `npm` dentro de contêineres não confia na CA do proxy; por isso o *build* das imagens `api`/`worker`/`web` não foi possível. A suíte do backend rodou **no host** (uv, Python 3.13) contra o **PostgreSQL 16 do sistema** (o Compose usa o 17 com pgvector, que a 001 não exige), e o frontend no host com Node 24.21 (o requerido, obtido pelo pacote `node` do npm). Isso não substitui a execução em contêiner (regra 11), que o CI faz.

- **Backend:** 496 testes passando (216 no início da sessão), repetidos 3 vezes sem oscilação; `ruff check`, `ruff format --check` e `mypy --strict` limpos (89 arquivos); `exportar_openapi` sem diferença.
- **Frontend:** 47 testes (18 no início); lint, tipos, `prettier --check`, `vite build` e `gerar:api` sem diferença.
- **CI remoto na `develop`:** as execuções 1 a 4 estavam vermelhas (job `frontend`: `EACCES` em `/app/coverage`); depois da correção, a 5 (`9b239d6`) e a 7 (`8288389`) passaram nos dois jobs. A 6 (`c197650`) falhou porque os testes de contrato leem `docs/.../openapi.yaml`, que não estava montado no contêiner de teste; reproduzido e corrigido (`9790138`). A execução 8 (`0e8a2e1`) foi cancelada pela execução seguinte; a **9 (`e9acfca`, cabeça da `develop`, que contém todo o código das T028 a T045) passou nos dois jobs** ([run](https://github.com/AAPW-Systems/plataforma-estudo-gamificada/actions/runs/38489553575)).
- **Mutação:** sem o *advisory lock*, as rajadas por endereço, por cadastro e por conta (30 clientes preparados, POSTs simultâneos) falham; sem o hash fictício, o teste de tempo falha (diferença de 72% entre as medianas, tolerância de 25%); uma rota nova com identificador sem caso, ou protegida sem `401`, é acusada pelos testes de isolamento. Uma primeira versão das rajadas não detectava a falta da trava (os POSTs eram escalonados) e foi reescrita.
- **pre-commit:** `pre-commit run --all-files` passou (Ruff, Prettier, ESLint) e reprova um arquivo com importação sobrando.

### Evidência da T040

Ensaio real: API (uvicorn, Argon2id da RFC 9106, banco `plataforma_e2e` migrado) e Vite com proxy, Chromium pelo Playwright; contas fictícias `@exemplo.com`. 15 verificações, 0 falhas:

1. sem sessão, `/` redireciona para `/entrar`;
2. o cadastro mostra o aviso de privacidade, sem caixa de aceite;
3. a senha `12345678` é recusada junto do campo, com nome e e-mail preservados e foco na senha;
4. o cadastro válido entra na trilha vazia;
5. o perfil (via API; a tela é da T051) traz estudante, fuso do navegador (`UTC` neste ambiente), meta 20, lição 10, novos 20 e retenção 0,90;
6. o cookie de sessão é `HttpOnly`, `Secure` e `SameSite=Lax`, e `document.cookie` não o mostra (o do CSRF é legível);
7. depois de sair, voltar e recarregar leva à entrada, e o cookie antigo responde `401`;
8. senha errada e e-mail inexistente dão a mesma mensagem;
9. cinco erros e a senha certa em seguida: "Muitas tentativas. Tente de novo em alguns minutos."; liberado o bloqueio, a entrada completa leva cerca de 270 ms;
10. o e-mail repetido com outra caixa mostra "e-mail já em uso";
- RQ-004: `/entrar` e `/cadastro` a 320 px sem rolagem horizontal, ordem de tabulação e-mail → senha, sem erro de JavaScript.

Testes: `pytest -m functional` (28), `security` (29 da US1) e `adversarial` (38). Log da `api`: eventos `conta_criada`, `entrada_recusada`, `bloqueio_aplicado` e `sessao_revogada` presentes; zero ocorrências de e-mail, senha, nome, cookie ou `argon2id` (RQ-002).

### Evidência da T045

`pytest -m security`: 91 testes. No ensaio real: `GET /api/v1/perfil` sem sessão responde `401 nao_autenticado` só com `codigo`, `mensagem` e `idRequisicao`, `Cache-Control: no-store` e cookies apagados; `PATCH /api/v1/perfil` sem `X-CSRF-Token` com sessão aberta responde `403 csrf_invalido`; token adulterado também. O passo "sair numa aba e recarregar na outra" compartilha os cookies do mesmo contexto do navegador, então a invalidação no servidor está provada pelo passo 7 da T040 e pelos testes.

### Evidência da T052 (US3, depois do Prompt 2)

Teste independente no Chromium (API e Vite reais, banco `plataforma_e2e`), 10 verificações, 0 falhas: perfil com os padrões e a explicação da retenção; meta 0 e retenção 0,99 recusadas na interface, com erro junto do campo, foco na meta e nada gravado; meta 35, lição 12 e novos 7 salvos sem nova versão do FSRS; retenção 0,85 cria a versão 2 e a 1 segue `0.90` com os mesmos pesos; o mesmo valor mostra "Nada para salvar" e não cria versão; fuso `Asia/Tokyo` salvo sem mexer em versões; fuso `Marte/Phobos` recusado pelo servidor junto do campo, valor preservado; `/perfil` a 320 px sem rolagem horizontal. Testes: backend 665 (era 496), frontend 57 (era 47); `pytest` repetido duas vezes sem oscilação.

Achados da verificação no navegador, corrigidos antes do commit:

- **Clique perdido:** com validação no *blur*, o erro empurrava o botão e o clique do estudante não enviava nada (nem dava foco ao campo). Os três formulários passaram a validar no envio e a revalidar a cada alteração depois dele (commit `0676736`).
- **Cabeçalho a 320 px:** transbordava (338 px); passou a quebrar linha.
- **Foco no primeiro erro:** passou a seguir a ordem do formulário, não a da resposta do servidor.
- **Teste oscilante:** o limite de 1 s dos `findBy*` estourava com a máquina carregada; passou a 4 s.
- **Lista de rotas protegidas:** o teste de `401` sem sessão pedia o token anti-CSRF uma só vez, mas a `401` apaga os cookies; passou a pedir antes de cada requisição.

Decisões da US3: `PATCH /perfil` valida tudo antes de gravar e informa todos os campos inválidos; a retenção é um número JSON estrito (sem `"0.9"`) com até duas casas, e um `null` enviado conta como valor inválido; as trocas concorrentes de retenção são serializadas pelo `FOR UPDATE` do usuário (testadas com 20 trocas simultâneas: versões 1 a 21 sem lacuna nem repetição); o contrato e o teste de isolamento deixaram de listar `PATCH /perfil` como pendente.

### Evidência da T059 (US4, depois do Prompt 2)

Teste independente no Chromium, com API, **worker** do Procrastinate e armazenamento em disco reais (banco `plataforma_e2e`), duas sessões da mesma conta em dois contextos de navegador; 14 verificações, 0 falhas:

1. senha atual errada: erro junto do campo, foco nele, nenhuma sessão revogada;
2. nova senha comum (`12345678`): recusada junto do campo da nova senha;
3. troca válida: aviso "as outras sessões foram encerradas"; a outra sessão cai (recarregar leva à entrada) e a atual continua; a senha antiga não entra e a nova entra;
4. diálogo de exclusão: explica que é definitiva e o que é apagado (matérias, fontes, cartões, revisões, XP e sequência); o foco fica preso (10 Tabs); Escape fecha e devolve o foco ao botão "Excluir conta"; nada é excluído;
5. senha errada no diálogo: erro dentro dele, que segue aberto, sem excluir;
6. senha certa: redireciona ao cadastro; `usuarios`, `sessoes` e `parametros_fsrs` ficam em 0; a tarefa `identidade.apagar_objetos_usuario` termina `succeeded` e o worker apaga os 3 arquivos de `usuarios/{public_id}/`, sem tocar o prefixo de outro estudante;
7. o mesmo e-mail se cadastra de novo; `/perfil` e o diálogo a 320 px sem rolagem horizontal.

Testes: backend 748 (era 665), frontend 75 (era 57). Logs da `api` e do `worker`: eventos `senha_trocada`, `senha_atual_recusada`, `conta_excluida` e `objetos_do_usuario_apagados`, com zero ocorrências de e-mail, nome, senhas ou cookies.

**Achado da verificação:** o worker iniciou só com as tarefas internas do Procrastinate. O Procrastinate importa `import_paths` pela linha de comando dele, não por `run_worker_async`; o `worker.py` do projeto passou a chamar `carregar_tarefas()` (teste em processo novo, vermelho sem a correção). Sem isso, a remoção de objetos da exclusão nunca rodaria. Outros achados: `senhasenha123` não consta na lista de senhas comuns (só `senhasenha`), e o `autoFocus` do campo de senha do diálogo foi retirado pela regra `jsx-a11y/no-autofocus` (o React Aria já leva o foco para o diálogo).

Decisões da US4: a troca de senha e a exclusão rodam sob a mesma trava da conta e do endereço que a entrada, e a falha da senha atual conta como `falha_senha_atual` para o limite único da conta (RQ-003); a senha atual correta zera as falhas da conta; a exclusão trava o usuário (`FOR UPDATE`) e roda o registro de exclusão (`revisao` em 900, `identidade` em 950, que apaga sessões e o usuário), apaga as falhas da conta e enfileira `apagar_objetos_usuario` (com `queueing_lock`) na mesma transação; 6 pedidos paralelos de exclusão dão um `204` e cinco `401`; 4 trocas paralelas de senha dão um `204` e três `422`; a tabela de casos do isolamento passou a incluir senha e exclusão, e as listas de pendências do contrato e do isolamento ficaram vazias.

### Evidência da fase final (T060 a T065, depois do Prompt 2)

**T060.** CI na `develop`: a execução 13 (`9232f70`, cabeça com todo o código da spec) passou nos dois jobs ([run](https://github.com/AAPW-Systems/plataforma-estudo-gamificada/actions/runs/38493543653)). As contagens e a cobertura vêm da execução local (host, PostgreSQL 16), com os mesmos comandos do CI: backend **748 testes**, `ruff format`/`ruff check`/`mypy` limpos (103 arquivos), `exportar_openapi` sem diferença; frontend **75 testes** em 9 arquivos, `prettier`, `eslint` e `tsc` limpos, `gerar:api` sem diferença. Cobertura do backend **94%** (instruções e ramos) e do frontend **92,6% das instruções e 79,5% dos ramos**. A primeira medição do backend deu 91%: o *coverage* perdia as linhas depois de cada troca de *greenlet* do SQLAlchemy assíncrono (`servicos.py` aparecia com 74%, mas o limite de 10 cadastros por hora, por exemplo, é exercitado por teste). A configuração passou a medir `greenlet` e `thread` (commit `6378ceb`; `servicos.py` foi a 95%).

**T061 (parcial; a tarefa segue aberta).** Executado:

- *Logs:* ensaio real com API e worker (212 linhas da `api`, 13 do `worker`): eventos `requisicao`, `conta_criada`, `objetos_do_usuario_apagados` e `worker_iniciado`, só com `usuario_public_id` e `idRequisicao`; zero ocorrências de e-mail, senha, cookie, `argon2id`, nome do cookie, `SEGREDO_APLICACAO` ou `POSTGRES_PASSWORD`.
- *Segredos:* nenhum `.env` versionado (`.gitignore` o cobre); nenhum padrão de chave privada ou token nos arquivos versionados; os valores do `.env` local não aparecem em arquivo versionado nem em nenhum commit do histórico (`git log -S`); `.env.example` com as duas variáveis vazias.
- *Cabeçalhos:* a `api` responde `X-Content-Type-Options: nosniff`, `Referrer-Policy: same-origin`, `X-Frame-Options: DENY`, `Cache-Control: no-store` e `X-Request-Id`; a imagem estática da interface (`Caddyfile`) envia os três primeiros. CSP e HSTS ficam no Caddy de borda do final acadêmico (arquitetura, seções 5.2 e 8), fora desta spec.
- *Mensagens em português:* sete respostas reais (401, 403 de CSRF, 404, 400, 422 com campos, credenciais inválidas) conferidas: todas em português, no corpo `Erro`.
- *Acessibilidade:* axe-core no Chromium real, com as regras `wcag2a`, `wcag2aa`, `wcag21a`, `wcag21aa`, `wcag22aa` e `best-practice` (inclui contraste de cor), em 8 telas e estados (entrada, entrada com erros, cadastro, cadastro com erro do servidor, trilha vazia, perfil, perfil com erro, diálogo de exclusão) nos temas claro e escuro: **16 verificações, 0 violações**. Teclado e 320 px: ordem de tabulação (T040), foco preso, `Esc` e devolução do foco no diálogo (T059), sem rolagem horizontal a 320 px em entrada, cadastro, perfil e diálogo (T040, T052, T059).
- *Não executado:* passagem com leitor de tela (NVDA, VoiceOver ou TalkBack), que exige uma pessoa e um navegador com tecnologia assistiva. A estrutura (rótulos, descrição dos erros, papéis, foco) só foi conferida pelo axe e pelos testes de componente, o que não a substitui. Por isso a T061 não foi marcada.

**T062.** API real (uvicorn, Argon2id da RFC 9106 em pouca memória, semáforo de 4 cálculos), PostgreSQL 16 local, 4 núcleos, contas fictícias: entradas sequenciais com **mediana de 85 a 89 ms e p95 de cerca de 100 ms** (meta: menos de 1 s); rajada de **10 entradas simultâneas** de contas e endereços distintos em 0,73 a 0,84 s no total (mediana por entrada de 0,56 a 0,61 s), todas `200`; memória do processo da `api`: 107 MiB em repouso e **pico (VmHWM) de cerca de 363 MiB**, igual antes e depois da rajada (base mais os 4 cálculos de 64 MiB que o semáforo permite). Uma primeira leitura de memória mediu por engano o processo-invólucro do `uv` (3 MiB) e foi descartada. A medição é local, não da VPS.

**T063.** Não feita: depende de três pessoas.

**T064.** Quickstart atualizado com os comandos do CI (`up -d --wait db`, `--no-deps`, `--frozen`, `--user root` no frontend), os endereços e as verificações das histórias P2 e P3; `docs/skills/padroes-implementacao.md` ganhou a seção "Comandos e endereços"; o "Mapa do repositório" do `.agents/AGENTS.md` descreve `backend/`, `frontend/`, `compose.yaml` e o CI. Corrigido no quickstart: o banco não publica porta no computador.

**T065.** `traceability.md` reescrito com os nomes reais dos testes (111 nomes conferidos contra o código por script; os prefixos com `*` apontam para o arquivo) e com a seção "Lacunas registradas na implementação": CS-001 (T063), leitor de tela, `413` e `securitySchemes` ausentes do contrato de projeto (o ajuste do contrato aprovado depende da equipe), cobertura.

### Verificação de Artur Lins no Windows (Prompt 3, 14/10/2026)

Prompt 3 (literal, resumido do que foi colado): o usuário rodou `docker compose up -d --build --wait` e os comandos de teste do quickstart, e informou: "rodei os testes, apenas um falhou. os demais testes estão ok, incluindo as telas e narrador". A saída colada mostrava o `up` saudável, `pytest` com 747 passando e 1 falha, `ruff` e `mypy` limpos, e os três comandos do frontend (`lint`, `typecheck`, `test:cobertura`) sem executar, com `Address already in use`.

Achados e correções:

1. **Teste intermitente de cabeçalhos (CS-003).** `test_entrada_tem_corpo_e_status_identicos_para_conta_inexistente_e_senha_errada` falhou porque o `Set-Cookie` dos 401 (cookies apagados) levava `Expires` igual ao instante da resposta: o `delete_cookie` do Starlette grava "agora". Com a virada do segundo entre as quatro requisições (no log colado, `...24.987` e `...25.002`), os cabeçalhos diferiam. Passou antes no CI e no ambiente do agente por sorte, não por estar correto. Dois testes novos (`tests/unit/nucleo/test_cookies.py`) falharam antes da correção e passam depois; os cookies agora expiram em 01/01/1970 com `Max-Age=0`, em qualquer instante (commit `4ad9e24`). Backend: 750 testes passando, `ruff` e `mypy` limpos.
2. **Comandos do frontend com `run` (T064).** O serviço `web` tem IP fixo (`172.28.0.10`) e `docker compose run web ...` cria outro contêiner na mesma rede com o mesmo IP, o que falha com o `web` de pé. O CI não sobe o `web`, e o agente não executou o Compose. Quickstart e `padroes-implementacao.md` passaram a usar `exec` com o ambiente de pé (não executado pelo agente; depende da confirmação do usuário).
3. **T061.** O usuário relatou as telas e o Narrador do Windows como corretos (sem detalhe por item). A T061 foi marcada com essa evidência, registrada como relato.

## Decisões e divergências

1. **Ordem do limite de cadastros.** O plano põe o limite antes da validação; aqui valida-se antes (função pura, sem efeito) e só o pedido válido consome o limite de 10 por hora. Assim, erros de digitação não bloqueiam quem se cadastra, e o `409 email_em_uso` também conta (a enumeração por cadastro fica limitada). A contagem e o registro usam a mesma transação, sob *advisory lock*.
2. **Bloqueio.** A L-ésima falha dentro da janela inicia um bloqueio de `BLOQUEIO_MIN` (função pura `bloqueado_ate`), o que dá sentido às duas variáveis `JANELA_TENTATIVAS_MIN` e `BLOQUEIO_MIN`. A verificação da senha acontece sob a trava (conta e endereço, em ordem alfabética); consequência: entradas do mesmo endereço se serializam.
3. **Limites dos DTOs.** Os mínimos e máximos vão ao OpenAPI (`json_schema_extra`), mas quem os impõe é o domínio, sobre o texto normalizado, informando todos os campos inválidos de uma vez. Senha longa demais ou não codificável na **entrada** é tratada como credencial inválida (custo igual, sem hash do valor gigante).
4. **Nome e senha.** Recusa de caracteres de controle, de direção bidirecional (RTL), de uso privado e de substitutos isolados (que quebrariam a gravação e o hash); a parte local do e-mail tem até 64 octetos (a biblioteca não impõe).
5. **Contrato (T037).** `OPERACOES_PENDENTES` e `ESQUEMAS_PENDENTES` (T049 e T056) com guarda que obriga a retirá-las; o OpenAPI gerado não declara `securitySchemes`; a resposta `413` falta no contrato (T065); os campos opcionais saem como `X | null` e a comparação aceita esse superconjunto; `Erro.codigo` passou a enum (`CodigoErro`, agora em `nucleo/codigos.py`) e os esquemas perderam o sufixo `DTO` no OpenAPI.
6. **T041.** Não declara cobertas as rotas de perfil, senha e exclusão (T049 e T056). `CASOS_DE_ISOLAMENTO` está vazio porque nenhuma rota da 001 recebe identificador; o mecanismo é provado por uma rota que só existe no teste. A enumeração de rotas percorre o `_IncludedRouter` do FastAPI 0.143 por *duck typing* e é conferida contra o OpenAPI.
7. **Dependência entre domínios.** `identidade` chama `revisao/servicos.py` (parâmetros iniciais do FSRS), como no plano e nas tarefas aprovados; isso diverge da frase de `contexto-tecnico.md` "nenhum domínio importa `revisao`", que trata das specs seguintes. Não alterei o guia.
8. **Frontend.** `CampoTexto` e `CampoNumero` passaram a usar `slot="errorMessage"` (o erro e a ajuda no mesmo *slot* de descrição só associavam um deles ao campo) e `validationBehavior="aria"` (o `required` nativo marcava o campo vazio como inválido); o cliente resolve o `fetch` a cada chamada; o 401 `nao_autenticado` limpa o cache e leva à entrada, e o `credenciais_invalidas` não.
9. **Registros de log.** Eventos `conta_criada`, `entrada_recusada`, `bloqueio_aplicado` e `sessao_revogada`, só com o `public_id` do usuário.
10. `MODULOS_TAREFAS` de `app/nucleo/fila.py` segue vazio até a T056.

## Pendências

- ~~T006 e T027~~ (fechadas com o Compose do usuário, Prompt 2) e ~~revisão da lista em português (T028)~~.
- **Ponto S1:** código na `develop`, CI verde e Compose completo verificado; o aviso a Arthur Moura para começar a base da 002 fica com o usuário.
- **Spec 001, fase final:** T060 a T062, T064 e T065 concluídas com evidência (T061 com o relato de Artur Lins sobre as telas e o Narrador). **T063** (teste guiado com três pessoas, CS-001) é humana e segue aberta; a 001 permanece em `Implementando`.
- **Contrato:** `413` e `securitySchemes` não estão em `contracts/openapi.yaml`; decidir com a equipe se o contrato de projeto é emendado ou se os desvios ficam documentados (registrado na rastreabilidade).
- **Limpeza do ambiente da sessão (não versionada):** servidores de desenvolvimento e o banco `plataforma_e2e` do ensaio real.
