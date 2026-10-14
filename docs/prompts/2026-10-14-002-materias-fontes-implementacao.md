# Implementação da spec 002 (matérias, envio e processamento de fontes)

**Data:** 2026-10-14
**Autor:** Artur Lins (condução); implementação pelo agente
**Agente e modelo:** Claude Code / claude-sonnet-5-5
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

Em andamento. Preenchida ao longo da sessão.

| Artefato | Ação |
|---|---|
| `docs/specs/divisao-implementacao-mvp.md`, `docs/specs/README.md`, `.agents/AGENTS.md`, `docs/skills/contexto-tecnico.md` | alterados: descontinuação da divisão (14/10/2026) |

## Alterações humanas

Pendente de revisão.

## Verificação

**Ambiente da sessão.** Contêiner de nuvem Linux (não o Windows com Docker Desktop da equipe). Backend no host, com uv e Python 3.13 (`UV_PROJECT_ENVIRONMENT` fora do repositório), contra o PostgreSQL 16 do sistema, e `.env` local gerado a partir do `.env.example` (ignorado pelo git; valores não registrados). O CI do GitHub é a verificação em contêiner.

- **CI da cabeça da `develop` antes de começar:** execução 15 (`1884fcf`), `success`.
- **Baseline do backend no host:** 750 testes passando em 40 s.

## Pendências

- A preencher ao longo da sessão.
