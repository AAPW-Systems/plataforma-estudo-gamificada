# Implementação da spec 002 (matérias, envio e processamento de fontes)

**Data:** 2026-10-14
**Autor:** Artur Lins (condução); implementação pelo agente
**Agente e modelo:** Claude Code (o identificador do modelo não é registrado em artefatos do repositório)
**Etapa SDD:** implementar
**Funcionalidade:** 002-materias-fontes

## Contexto fornecido

- Spec 001 implementada e na `develop` (T063, teste guiado com três pessoas, segue humana e aberta).
- Esta sessão rodou num contêiner de nuvem Linux. O clone inicial era raso (profundidade 50) e estava atrás do remoto; foi aprofundado (`git fetch --unshallow`) e avançado por fast-forward (`git merge --ff-only origin/develop`), sem commits locais a preservar.
- Ambiente de execução: ver "Verificação".

## Prompts

### Prompt 1

```text
Implemente a spec 002 (docs/specs/002-materias-fontes: matérias, envio e processamento de fontes) na branch `develop`, da T001 até a T051, seguindo o AGENTS.md e o SDD à risca. Antes de agir, leia o AGENTS.md (CLAUDE.md aponta para ele) e, nesta ordem: docs/skills/contexto-tecnico.md, docs/skills/padroes-implementacao.md, docs/skills/padroes-interface.md, docs/skills/registrar-prompt.md e todos os artefatos de docs/specs/002-materias-fontes (spec, plan, research, data-model, contracts/openapi.yaml, quickstart, tasks, traceability). Leia também o registro da sessão anterior, docs/prompts/2026-10-13-001-conta-acesso-implementacao-4.md, onde estão as decisões, os achados e as armadilhas da 001.

## Mudança de processo (decisão de Artur Lins, 14/10/2026)

O plano de divisão entre Artur Lins e Arthur Moura (docs/specs/divisao-implementacao-mvp.md) foi descontinuado. As specs do MVP passam a ser implementadas em sequência (001 → 002 → 003 → 004 → 005 → 006 → 007), uma de cada vez, por Artur Lins com o agente, sem ondas, sem antecipações e sem pontos de sincronização com outra pessoa. O ponto S1 e a espera por Arthur Moura não valem mais. Esta sessão cuida só da 002; não comece a 003.

1. Primeiro commit, só de documentação (`docs(specs): ...`): registre a descontinuação sem reescrever o histórico. Troque a linha "Situação" do topo de docs/specs/divisao-implementacao-mvp.md para "descontinuada em 14/10/2026 por decisão de Artur Lins; implementação sequencial", mantendo o restante do texto como histórico. Ajuste a referência em docs/specs/README.md (linha 56), o "Estado atual" do .agents/AGENTS.md e o trecho equivalente de docs/skills/contexto-tecnico.md. Não edite os registros antigos de docs/prompts/ (regra 12). Não altere tarefas nem planos aprovados: os marcadores `[P]` e as frases sobre "pessoas diferentes" da 002 passam a significar só independência de arquivos, e a execução é sequencial.

## Estado de partida

- A spec 001 está implementada e na `develop` (US1 a US4, T001 a T062, T064 e T065). Resta a T063 (teste guiado com três pessoas, CS-001), humana e fora do escopo desta sessão. O pré-requisito da 002 (T001 a T045 da 001) está cumprido.
- Confira primeiro o CI da cabeça da `develop` (`git pull origin develop`; execuções do workflow `ci` do repositório aapw-systems/plataforma-estudo-gamificada). Se estiver vermelho, resolva antes de começar. Baseline: backend com 750 testes, frontend com 75, `ruff` e `mypy` limpos.
- A próxima migração é a `0003_acervo` (T008).

## Como trabalhar

- Siga a ordem do tasks.md: Fase 1 (T001, T002), Fase 2 (T003 a T013), US1 (T014 a T031), US2 (T032 a T039), US3 (T040 a T046), fase final (T047 a T051). Em cada história, os testes vêm antes do código e começam falhando (mostre o vermelho antes do verde). Um commit atômico por tarefa ou por par teste e implementação, em Conventional Commits em português, citando o ID (`feat(fontes): ... [T025]`). Nunca na `main`, nunca reescreva histórico publicado. Antes de cada push: `git pull --rebase origin develop`, suíte completa verde, e depois confira o CI.
- Só marque `[x]` no tasks.md com evidência executada (regra 6), e registre cada evidência no registro da sessão. Crie logo no início o registro docs/prompts/AAAA-MM-DD-002-materias-fontes-implementacao.md (prompt literal, saída aceita, verificação, pendências) e acrescente-o ao docs/prompts/README.md.
- Use somente a stack aprovada; a única dependência nova prevista é `pymupdf` e `python-multipart` (T001). Qualquer outra coisa exige DTEC nova antes. Sem segredos no repositório, sem dados pessoais reais (contas @exemplo.com, arquivos gerados por `tests/fabricas_arquivos.py`).
- Não decida produto. Dúvida de produto vira questão `Q-xxx` na spec, com opções e consequências; pare e pergunte a Artur Lins.
- Preserve o `.env` local (ignorado pelo git) e nunca imprima seus valores. Se faltar, copie `.env.example` e preencha `POSTGRES_PASSWORD` e `SEGREDO_APLICACAO` (mínimo de 32 bytes).

## Lições da 001 que se aplicam aqui

- **Ambiente de nuvem sem Compose completo:** se o `docker compose build` falhar por rede (ghcr.io e o npm dentro de contêineres podem estar bloqueados), rode o backend no host (uv, Python 3.13, com `UV_PROJECT_ENVIRONMENT` fora do repositório) contra um PostgreSQL local e o frontend com Node 24 no host, e diga isso claramente no registro. O CI do GitHub é a verificação em contêiner. O PostgreSQL local pode cair no meio da rodada (erro em massa de conexão recusada): reinicie o cluster antes de investigar o código.
- **T013 (verificar a base):** exige `docker compose up -d --build --wait` com o volume `arquivos`, `/health/ready` em 200 e CI verde. Só Artur Lins roda isso no Windows (Docker Desktop). Peça que ele rode e cole a saída; marque T013 só depois disso. Não espere para avançar a US1 se o resto da base estiver pronto, mas deixe o pedido explícito no relatório.
- **Comandos do frontend:** o serviço `web` tem IP fixo, então `docker compose run web ...` falha com `Address already in use` quando ele está de pé. Com o ambiente de pé use `docker compose exec web npm run ...`; o CI usa `run --rm --no-deps`. Os comandos verificados estão no quickstart da 001 e em padroes-implementacao.md, "Comandos e endereços".
- **Worker:** o Procrastinate só executa as tarefas dos módulos listados em `MODULOS_TAREFAS` (app/nucleo/fila.py) e carregadas por `carregar_tarefas()` em app/worker.py. Registre as tarefas de `app/fontes/tarefas.py` ali e mantenha um teste em subprocesso novo (a 001 já tem `integration/nucleo/test_worker.py`). Sem isso o worker sobe saudável e não processa nada.
- **Exclusão da conta:** `materias` e `fontes` devem entrar no registro de exclusão (`app/nucleo/exclusao.py`, DTEC 021) com `apagar_dados_usuario` na ordem certa, e a remoção dos objetos fica sob o prefixo `usuarios/{public_id}/`. O teste de catálogo (`security/identidade/test_exclusao_completa.py`) falha se qualquer tabela com `usuario_id` mantiver linhas da conta excluída: ele é a rede de segurança, e a exclusão de conta com fontes e arquivos precisa ganhar teste de ponta a ponta.
- **Isolamento e contrato:** `CASOS_DE_ISOLAMENTO` (security/test_isolamento_rotas.py) começa a ter casos reais agora: rota nova com identificador sem caso, ou protegida sem 401, é acusada pelo próprio teste. Use `buscar_do_dono` (app/nucleo/dono.py) para responder 404 idêntico ao inexistente. Amplie o teste de contrato para o openapi.yaml da 002 (T028), regenere `backend/openapi.json` (`python -m app.exportar_openapi`) e os tipos (`npm run gerar:api`), sem diferença no git. O 413 ficou como lacuna do contrato da 001; a 002 o introduz (T006), então confira que o contrato dela o declara.
- **Testes de concorrência e de rajada:** use `fabrica_real` e clientes pré-criados (não savepoints, não requisições escalonadas) e prove por mutação que o teste falha sem a trava ou a defesa que ele verifica. Teste que depende de relógio, ordem ou virada de segundo deve ser determinístico (foi o caso do `Set-Cookie` dos 401, que oscilava). Rode a suíte completa pelo menos duas vezes antes do push.
- **Segurança do envio (adversarial):** siga a tabela de validação da DTEC 028 e as defesas do plano: tipo e tamanho por conteúdo e não pelo nome, extensão e MIME forjados, UTF-8 com BOM, PDF malformado, protegido por senha, grande ou bomba de descompressão, nome de arquivo com travessia de caminho, extração PyMuPDF em subprocesso com limites, divisão em trechos determinística, reenvio e envio simultâneo do mesmo arquivo, cota por matéria e por estudante, e conteúdo com instruções embutidas (injeção de prompt) tratado só como texto. Nenhuma resposta de erro devolve caminho interno, pilha ou conteúdo do arquivo.
- **Frontend:** componentes sobre o React Aria (DTEC 016), cada tela com teste e `vitest-axe`; erros junto do campo e com foco no primeiro inválido; validar no envio, não no blur; 320 px sem rolagem horizontal. Use `asyncUtilTimeout` já configurado e evite `autoFocus`.

## Fase final e encerramento

- T047 a T051: suítes completas, qualidade estática, contrato, contagens e cobertura (a configuração de cobertura já mede greenlet), CI verde na cabeça; revisão de segurança e acessibilidade com axe no navegador real nos dois temas, 320 px, teclado, logs sem dados sensíveis; medições do plano; quickstart, padroes-implementacao.md e "Mapa do repositório" atualizados; traceability.md com os nomes reais dos testes.
- Verificação manual que só uma pessoa faz (leitor de tela, teste com usuários, Compose no Windows) fica explícita e aberta; não marque como feita.
- Ao encerrar (AGENTS.md, "Como encerrar uma sessão"): links relativos conferidos, registro completo, índices atualizados (docs/specs/README.md, README da 002, tasks, "Estado atual"), status da 002 em `Implementando` (ou `Convergida` somente se todas as tarefas, inclusive as humanas, tiverem evidência). Relate o que foi feito, como foi verificado e o que ficou pendente, sem declarar como verificado algo que não foi executado.
```

## Saída aceita

Sessão **interrompida de propósito** por pedido de Artur Lins, depois da US2 (T001 a T012 e T014 a T039 prontas). Faltam a T013 (humana), a US3 (T040 a T046) e a fase final (T047 a T051).

| Artefato | Ação |
|---|---|
| `docs/specs/divisao-implementacao-mvp.md`, `docs/specs/README.md`, `.agents/AGENTS.md`, `docs/skills/contexto-tecnico.md` | alterados: descontinuação da divisão (14/10/2026) |
| `backend/src/app/{nucleo,materias,fontes}/`, `backend/migracoes/versions/0003_acervo.py`, `backend/openapi.json` | criados e alterados: acervo, isolamento, armazenamento, fila, matérias, fontes, exclusão de fonte |
| `frontend/src/{api,componentes/ui,funcionalidades/{materias,fontes},rotas/_autenticado/materias}/` | telas de matérias, envio, acervo, painel e diálogo de exclusão |
| `backend/tests/`, `frontend/src/**/*.test.tsx` | testes unitários, de integração, funcionais, de segurança, adversariais e de componente |
| `docs/specs/002-materias-fontes/tasks.md` | T001 a T012 e T014 a T039 marcadas com evidência; T013 com a situação |

## Alterações humanas

Pendente de revisão.

## Verificação

**Ambiente da sessão.** Contêiner de nuvem Linux (não o Windows com Docker Desktop da equipe). Backend no host (uv, Python 3.13, `UV_PROJECT_ENVIRONMENT` fora do repositório) contra o PostgreSQL 16 do sistema; frontend com Node 22 local e Node 24 (o do CI) em teste. O CI do GitHub é a verificação em contêiner.

- **Suíte do backend no host (fim da US2):** ruff e mypy limpos e 1475 testes passando, 1 pulado (superusuário). **Frontend:** 161 testes, lint, tipos e formatação, nos Node 22 e 24.
- **CI da `develop`:** execução 19 (`d61dee3`) verde nos dois jobs. As execuções 17 e 18 falharam e foram corrigidas (ver os achados). A execução 20 (`3abeda8`, cabeça da sessão) estava na fila ao encerrar: **conferir o resultado**.

### Achados do CI e do navegador (todos corrigidos)

- **Execução 17:** um teste de estouro de memória com teto de 1 MB e PDF real passou no CI (o `RLIMIT_AS` soma o tamanho virtual do filho, que já carrega o PyMuPDF; a folga do alocador varia). Troca por executor simulado; o estouro real segue em `test_isolamento.py`.
- **Execução 18:** os testes de envio do frontend falhavam no Node 24 (o `fetch` não envia `File` do jsdom e o MSW se atrapalha ao ler corpos multipart). Passaram a usar `FormData`, `File` e `Blob` nativos (sem dependência nova) e o handler não lê o corpo.
- **Navegador, US2:** a 320 px o diálogo de exclusão era mais alto que a tela e a sobreposição não rolava (Cancelar e Excluir inalcançáveis, WCAG 1.4.10). Corrigido no CSS (vale também para o diálogo de excluir a conta da 001).
- **Log:** `processamento_falhou` não trazia a `tentativa` pedida no plano. Corrigido, com teste.

### Evidência da T031 (quickstart, passos 1 a 12, Chromium real)

API, worker e PostgreSQL locais; arquivos fictícios gerados por `python -m tests.fabricas_arquivos`; envio pelo seletor de arquivos como o estudante. 14 de 14 verificações: estado vazio com "Criar primeira matéria"; página da matéria com "Enviar a primeira fonte"; lista com 0 fontes, 0 cartões ativos e 0 aguardando; nome repetido recusado junto do campo com o valor preservado; formatos e limite de 2 MB visíveis; `Citologia` Pendente → Processando → Concluído sozinha (cerca de 4,5 s); painel com arquivo, tipo, tamanho, data, 90 páginas e 130 trechos; duplicata recusada com «Citologia»; os 6 inválidos recusados com 6 mensagens distintas e nada no acervo; digitalizado em Falhou, sem "Tentar novamente"; `um-paragrafo.txt` com 1 trecho; falha técnica real (o worker rodando como usuário sem acesso ao objeto, equivalente ao `chmod 000`, que como superusuário não bloqueia): 3 execuções (esperas de 5 s e 25 s, 28 s no total), Falhou com "Tentar novamente", e depois de devolver o acesso volta e conclui com os mesmos 2 trechos, sem duplicar; CS-003: PDF de 2 MB Concluído em cerca de 10,7 s (meta de 60 s). Logs com `public_id`, sem nome nem conteúdo; as chaves no volume são `usuarios/{uuid}/fontes/{uuid}`.

Observações: nas execuções rápidas o estado Pendente pode durar menos que um *polling* e não ser visto (a transição completa foi vista em uma das rodadas); o passo 11 foi adaptado como acima, e não rodado com `docker compose`.

### Evidência da T039 (US2, Chromium real)

12 de 12 verificações: diálogo com título, "Ação definitiva", as duas opções sem nenhuma marcada e confirmar desabilitado; foco dentro do diálogo, preso em 8 Tab, e Escape devolve o foco ao botão; cancelar não muda fonte, arquivos nem trechos; confirmar com "Manter os cartões" apaga a fonte, o arquivo do volume e os 130 trechos; a fonte que falhou também é excluída; o painel da fonte excluída fecha; a 320 px não há rolagem horizontal e Cancelar é alcançável; `fonte_excluida` logado com modo e contagens, sem título nem nome. axe sem violações no diálogo aberto. As contagens de cartões são zero (003 e 004 ainda não existem); com cartões, o teste é refeito pelas specs seguintes (DTEC 027), e os testes da 002 usam um participante falso.

## Decisões e divergências a confirmar com Artur Lins

- **Hifenização (DTEC 029):** o PyMuPDF não desfaz a hifenização com `TEXT_DEHYPHENATE`; há um teste de caracterização. Decidir se a DTEC 029 recebe uma emenda.
- A checagem de dono vem antes da leitura do arquivo (404 igual antes de gastar trabalho); `processamento.py` existe fora da estrutura do plano; o CHECK `concluido_coerente` ficou mais estrito (se e somente se, por coluna); identificador malformado no caminho responde 404 e não 422 (DTEC 019).
- O diálogo de exclusão mantém as duas opções mesmo sem cartões, como o quickstart pede.
- Limitação conhecida: se o banco ficar fora no último retry, a fonte pode ficar em `processando` até a tarefa de reenfileirar travadas atuar.

## Pendências

- **Pedido explícito a Artur Lins (T013):** no Windows, rodar `docker compose up -d --build --wait` com o volume `arquivos`, conferir `/health/ready` em 200 e colar a saída; só então marcar a T013.
- **Verificações humanas:** leitor de tela, teste com usuários, e conferir o CI (execução 20 e seguintes).
- **Retomar:** US3 (T040 a T046), fase final (T047 a T051), atualizar o "Mapa do repositório" e "Estado atual" do AGENTS.md, `padroes-implementacao.md`, `contexto-tecnico.md`, o README da 002, a rastreabilidade (`traceability.md` com os nomes reais dos testes) e o status da 002 (hoje `Tarefas aprovadas`; passar a `Implementando`). Prompt de retomada na seção seguinte.

## Prompt de retomada

```text
Continue a implementação da spec 002 (docs/specs/002-materias-fontes) na branch `develop`, a partir da T040
(US3: organizar matérias e fontes), seguindo o AGENTS.md e o SDD à risca. Antes de agir, leia o AGENTS.md,
o registro docs/prompts/2026-10-14-002-materias-fontes-implementacao.md (inclusive "Achados do CI",
"Decisões e divergências" e "Pendências"), o tasks.md da 002 e docs/skills/contexto-tecnico.md.

Estado de partida: T001 a T012 e T014 a T039 prontas e marcadas com evidência; T013 é humana (Artur Lins roda
o Compose no Windows). Backend: 1475 testes no host; frontend: 161 testes (rode também no Node 24, o do CI).
Primeiro confira o CI da `develop` (execução 20, commit 3abeda8 e seguintes) e corrija o que estiver vermelho.

Regras: testes antes do código (mostre vermelho, depois verde); um commit atômico por tarefa ou par
teste+implementação; suíte completa verde e `git pull --rebase origin develop` antes de cada push; só
`pymupdf` e `python-multipart` como dependências novas; dúvida de produto vira Q-xxx e pergunta a Artur;
marque [x] só com evidência. Não escreva identificador de modelo em artefatos do repositório. Não comece a 003.

Faça: US3 (T040 a T046): renomear matéria e fonte, excluir matéria com o nome digitado (reuse
ImpactoAlterado do núcleo, `travar_acervo` e a ordem dos participantes de DTEC 027/031), e o teste de exclusão
de conta com matérias, fontes e objetos; depois a fase final (T047 a T051): suítes, cobertura, CI, revisão de
logs/segurança/acessibilidade com axe no navegador real em 2 temas e a 320 px (inclusive o diálogo aberto),
medições (CS-003, tempo de envio, pico de memória), quickstart, padroes-implementacao.md, Mapa do repositório,
traceability.md e status da 002 em `Implementando`.

Ambiente local de verificação (se o contêiner for novo): backend no host com UV_PROJECT_ENVIRONMENT fora do
repositório contra um PostgreSQL local; para o navegador, Playwright global (/opt/node-tools) com o Chromium
em /opt/pw-browsers; ao simular falha de permissão como root, rode o worker como outro usuário (setpriv).
Cuidado: `pkill -f` com padrão que aparece na própria linha de comando mata o shell; use PIDs.

Ao encerrar: links relativos conferidos, registro completo, índices e "Estado atual" atualizados; relate o que
foi feito, como foi verificado e o que ficou pendente, sem declarar verificado o que não foi executado, e
repita o pedido a Artur sobre a T013 e as verificações humanas.
```
