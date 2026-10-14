# Guia: contexto técnico consolidado

Resumo das decisões e convenções já aprovadas, para que um agente comece uma spec nova sem ler todos os planos e `research.md` anteriores. **Este guia não decide nada.** Ele aponta para a fonte, e em caso de divergência a fonte prevalece: a DTEC, o plano aprovado ou o esquema.

**Atualizado em:** 13/10/2026, até o plano da spec 007 ([registro](../prompts/2026-10-13-007-evolucao-plano.md)).

## Como usar

1. Leia este guia, a [constituição](../constitution.md) e a spec que vai planejar.
2. Abra a fonte (DTEC, plano ou `data-model.md` de outra spec) só quando precisar de um detalhe que o resumo não traz, ou antes de **alterar** algo já decidido.
3. Não redefina o que está aqui. Uma mudança vira emenda da DTEC de origem ou DTEC nova, com propagação registrada.
4. **Manutenção:** ao aprovar o plano de uma spec, atualize este guia no mesmo commit da aprovação (DTEC novas, códigos de erro, migração, obrigações).

## Estado das specs e migrações

| Spec | Estado | Migração | Domínios criados |
|---|---|---|---|
| [001](../specs/001-conta-acesso/plan.md) conta e acesso | Implementando | `0001_procrastinate`, `0002_identidade` | `identidade`, `saude`, parte de `revisao` (`parametros_fsrs`) |
| [002](../specs/002-materias-fontes/plan.md) matérias e fontes | Tarefas aprovadas | `0003_acervo` | `materias`, `fontes` |
| [003](../specs/003-cartoes-manuais/plan.md) cartões manuais | Tarefas aprovadas | `0004_cartoes` | `cartoes` |
| [004](../specs/004-geracao-cartoes/plan.md) geração de cartões | Tarefas aprovadas | `0005_geracao_cartoes` | `ia`, `cartoes/geracao` |
| [005](../specs/005-licao-trilha/plan.md) lição e trilha | Tarefas aprovadas | `0006_licoes_revisoes` | `revisao` (lição, apresentação, revisão, trilha); `nucleo/dia_estudo.py` e `nucleo/eventos_revisao.py` |
| [006](../specs/006-xp-meta-sequencia/plan.md) XP, meta e sequência | Tarefas aprovadas | `0007_gamificacao` | `gamificacao`; `nucleo/disponibilidade.py`; provedor em `revisao/disponibilidade.py` |
| [007](../specs/007-evolucao/plan.md) evolução mínima | Tarefas aprovadas | nenhuma (leitura sobre índices existentes, DTEC 066) | `evolucao` (sem persistência); `transacao_leitura_consistente` em `nucleo/banco.py` |

A próxima migração continua sendo a `0008` (a 007 não criou nenhuma). A documentação das specs do MVP (001 a 007) ficou completa em 13/10/2026, e a implementação está liberada. Decisão de 14/10/2026 de Artur Lins: a divisão da implementação entre duas pessoas (`docs/specs/divisao-implementacao-mvp.md`) foi descontinuada, e as specs são implementadas em sequência (001 → 002 → 003 → 004 → 005 → 006 → 007), uma de cada vez, por Artur Lins com o agente. A implementação da 001 começou na `develop` em 13/10/2026, em paralelo ao plano da 007, por revisão da decisão anterior feita por Artur Lins ([registro](../prompts/2026-10-13-001-conta-acesso-implementacao.md)).

## Convenções da API

- **Rotas:** `/api/v1`, JSON em camelCase, instantes em ISO 8601 UTC. Só `public_id` (UUID) sai da API; o `id` interno nunca.
- **Sessão e CSRF (DTEC 023):**
  - cookie `__Host-sessao`, `HttpOnly`, `Secure`, `SameSite=Lax`, com 256 bits e só o SHA-256 no banco;
  - expiração após 14 dias sem uso ou 30 dias após a entrada;
  - POST, PATCH, PUT e DELETE exigem `X-CSRF-Token` (*double submit* assinado, cookie `__Host-csrf`), `Origin` permitida e `Sec-Fetch-Site: same-origin`.
- **Isolamento (DTEC 019):**
  - todo repositório recebe `usuario_id` e filtra na consulta;
  - recurso de outro estudante responde `404 recurso_nao_encontrado`, idêntico ao de inexistente;
  - toda rota com identificador no caminho entra na tabela de `tests/security/test_isolamento_rotas.py`.
- **Erros:** corpo `Erro {codigo, mensagem, campos?, idRequisicao}`.
  - **Hierarquia:** `ErroAplicacao` com `RequisicaoMalformada` 400, `NaoAutenticado` 401, `AcessoNegado` 403, `RecursoNaoEncontrado` 404, `Conflito` 409, `ConteudoMuitoGrande` 413, `EntradaInvalida` 422 e `LimiteExcedido` 429 (com `Retry-After`).
  - **Códigos:** o enum `codigo` é cumulativo, e uma spec acrescenta códigos sem renomear nem remover (lista abaixo).
- **Leituras:** `Cache-Control: no-store`. Corpo limitado a 64 KiB, salvo o envio de fonte. Entrada com `extra="forbid"`.
- **Paginação (DTEC 034):** cursor opaco *keyset*, resposta `{itens, proximoCursor, total}`, `limite` padrão 50 (de 1 a 100) e `422 cursor_invalido`.
- **Acompanhamento (DTEC 026):** *polling* de 2 s só enquanto houver item `pendente` ou `processando`, com anúncio por `aria-live`.
- **Contrato:** cada spec tem `contracts/openapi.yaml`, validado com `openapi-spec-validator`. Uma spec que só acrescenta campos às respostas de outra redefine os caminhos afetados como superconjunto do contrato anterior, com teste que compara os dois (DTEC 063). Um teste verifica que o OpenAPI gerado (`backend/openapi.json`, versionado) contém o de cada spec, e o frontend gera os tipos com `npm run gerar:api`.

**Códigos de `Erro` já usados:**

- **001:** `requisicao_malformada`, `dados_invalidos`, `email_em_uso`, `credenciais_invalidas`, `senha_atual_incorreta`, `nao_autenticado`, `csrf_invalido`, `origem_nao_permitida`, `recurso_nao_encontrado`, `muitas_tentativas`, `erro_interno`.
- **002:** `materia_nome_em_uso`, `cota_materias_excedida`, `cota_fontes_excedida`, `cota_armazenamento_excedida`, `fonte_duplicada`, `arquivo_muito_grande`, `formato_nao_aceito`, `tipo_divergente`, `arquivo_vazio`, `arquivo_corrompido`, `pdf_protegido`, `pdf_paginas_excedidas`, `codificacao_invalida`, `confirmacao_invalida`, `impacto_alterado`, `reprocessamento_indisponivel`.
- **003:** `cursor_invalido`.
- **004:** `ciencia_aviso_pendente`, `aviso_desatualizado`, `fonte_nao_concluida`, `idempotencia_divergente`, `sem_conteudo_novo`, `limite_geracoes_excedido`, `orcamento_ia_esgotado`, `cartao_ja_decidido`.
- **005:** `sem_cartoes_disponiveis`, `licao_encerrada`, `revelacao_pendente`, `apresentacao_ja_avaliada`, `cartao_indisponivel`, `limite_novos_atingido` (todos `409`).
- **006:** nenhum código novo (a 006 não cria rotas; acrescenta campos às respostas da 005).
- **007:** nenhum código novo (uma rota de leitura, `GET /evolucao`, que responde só `200` ou `401`).

## Banco de dados

- **Esquema de referência:** [esquema-inicial.dbml](../arquitetura/esquema-inicial.dbml). Cada spec cria só as tabelas, colunas e valores de enum que usa, e atualiza o `.dbml` quando o plano muda algo.
- **Migrações:** Alembic revisado à mão.
  - PK `bigint generated always as identity`; `public_id uuid` com `gen_random_uuid()` só nas tabelas expostas em rotas.
  - Toda migração sobe e desce nos testes.
  - `ALTER TYPE ... ADD VALUE` vai num `autocommit_block`, antes de qualquer uso do valor novo.
- **Instantes e dias:** `timestamptz` em UTC. O **dia de estudo** vira às 4h no fuso do estudante (`usuarios.fuso`, RN-15), calculado só por `nucleo/dia_estudo.py` (`dia_estudo`, `inicio_dia`, `proxima_virada`; DTEC 048), usado pela 004, pela 005 e pela 006. O SQL recebe os limites já calculados.
- **Dono:** FKs compostas `(materia_id, usuario_id)` e, para fonte, `(fonte_id, materia_id, usuario_id)` garantem o mesmo dono e a mesma matéria no banco. Desde a 005, `cartoes` e `licoes` têm índice único `(id, usuario_id)` como alvo de FKs compostas.
- **Exclusão:** física (RN-14). Quando uma spec cria FK de **histórico** para `cartoes`, `revisoes` ou `eventos_xp`, usa `on delete set null` para preservar o histórico (obrigação da 003); com FK composta, `ON DELETE SET NULL (coluna)`. Exceção registrada na 005: `licoes_cartoes` e `apresentacoes` (plano da sessão, não histórico) usam `cascade`. Na 006, `eventos_xp.cartao_id` usa `ON DELETE SET NULL (cartao_id)`, e `revisoes` ganhou o índice único `(id, usuario_id)` como alvo de FK composta.
- **Extensões:** `unaccent` (003). `vector` só no final acadêmico.

## Backend

- **Stack:**
  - FastAPI, SQLAlchemy 2 assíncrono e Alembic;
  - Pydantic e pydantic-settings;
  - psycopg 3 como único driver, com o enfileiramento na mesma transação (emenda da DTEC 002);
  - Python 3.13 com uv.
- **Camadas por domínio (DTEC 018):** `rotas`, `dtos`, `mapeadores`, `servicos`, `dominio`, `repositorios`, `modelos` e `excecoes`, mais `registros.py` (participante e exclusão de conta) e `tarefas.py`. Regras puras em `dominio.py`, sem FastAPI nem SQLAlchemy. Um teste de arquitetura vigia as dependências proibidas.
- **Núcleo (`app/nucleo/`):**
  - `configuracao.py`, com a validação ao iniciar;
  - `erros.py` e `logs.py` (structlog JSON, sem conteúdo do estudante);
  - `fila.py` (Procrastinate e `reenfileirar_tarefas_travadas`);
  - `exclusao.py` (`apagar_dados_usuario` por domínio, DTEC 021);
  - `participantes_acervo.py` (DTEC 027);
  - `isolamento.py` (`executar_isolado`, DTEC 024);
  - `armazenamento/` (DTEC 010 e 025);
  - `disponibilidade.py` (DTEC 057): provedor de disponibilidade registrado por `revisao` e ganchos `antes_de_alterar` e `depois_de_alterar`, cujos ouvintes são da `gamificacao`;
  - `banco.py` (001) com `transacao_leitura_consistente()`: transação própria `REPEATABLE READ, READ ONLY` para leituras consolidadas, separada da transação da requisição, que renova a sessão (DTEC 064).
- **Sentido das dependências:**
  - `cartoes` → `fontes` → `materias`;
  - `cartoes/geracao` → `ia`;
  - `revisao` → `cartoes` (`consultas.py` e `agendamento.py`), `materias` (`consultas.py`) e `identidade`;
  - `materias`, `fontes` e `identidade` não importam `cartoes`, e nenhum domínio importa `revisao` (a 006 se liga pelo evento do núcleo);
  - `ia` não importa domínio de negócio;
  - `revisao` → `gamificacao` (`consultas.py`, só para compor as respostas); `gamificacao` não importa `revisao`, `cartoes` nem `materias` e recebe a disponibilidade pelo provedor do núcleo (DTEC 057);
  - `cartoes` (suspender, reativar, excluir e participante) e `identidade` (`PATCH /perfil` com meta, limite de novos ou fuso) chamam os ganchos da DTEC 057 na própria transação, antes e depois da escrita;
  - `evolucao` → `gamificacao/consultas.py` (`resumo`, `dias_no_intervalo`), `revisao/consultas.py` (`dominados_por_materia`, `existe_revisao`) e `materias/consultas.py` (`listar_nomes`). É folha (ninguém a importa) e a única exceção a "nenhum domínio importa `revisao`", restrita a `consultas.py` (DTEC 064 e 066).

  Os efeitos cruzados (contagens e exclusão) passam pelos registros do núcleo.
- **Tarefas assíncronas (DTEC 030 e 043):**
  - enfileiradas na transação que cria o registro;
  - `queueing_lock` e `lock` por registro;
  - `RetryStrategy(max_attempts=2)`, ou seja, até 2 novas tentativas, só para erros transitórios;
  - estado e código de falha no próprio registro;
  - terminam **sem efeito** se o registro sumiu ou já está num estado final;
  - nenhuma trava aberta durante chamadas externas;
  - a periódica `reenfileirar_tarefas_travadas` cobre todas.
- **Concorrência:**
  - **Cotas e limites por estudante:** `pg_advisory_xact_lock` por estudante, num espaço próprio por operação (DTEC 020, 032 e 044).
  - **Exclusão:** trava a fonte ou a matéria com `FOR UPDATE` e recalcula o impacto confirmado (`409 impacto_alterado`, DTEC 031).
  - **Quem cria a partir de uma fonte** trava a fonte com `FOR SHARE` (DTEC 035 e 043).
  - **Idempotência pelo estado:** quando a própria situação já indica o efeito (ex.: suspender ou aceitar de novo responde `200` sem escrita).
  - **Idempotência com chave do cliente:** índice único `(usuario_id, chave)`; mesma chave com conteúdo diferente responde `409` (RN-10).
- **Exclusão de fonte e matéria (DTEC 027):** cada domínio registra um participante com `contar_por_materia`, `impacto_fonte`, `ao_excluir_fonte(modo)` e `ao_excluir_materia`, todos na transação de quem chama. Os participantes de cartões vêm antes do de `fontes`.
  - **`ContagensAcervo`:** `fontes`, `cartoes_ativos`, `cartoes_suspensos`, `cartoes_aguardando_revisao`, `cartoes_gerados_aceitos` e `cartoes_referencia`.
- **Exclusão da conta (DTEC 021):**
  - transação única nas linhas, e depois a tarefa `apagar_objetos_usuario` (prefixo `usuarios/{public_id}/`);
  - um teste de catálogo exige que toda tabela com `usuario_id` fique vazia.
- **Cartões (DTEC 036 a 038 e 045):**
  - **Texto:** `normalizar_texto_cartao` e `validar_limites` (*code points*, limites por ambiente em `GET /cartoes/limites`) e `origem_apos_edicao`.
  - **FSRS:** estado inicial de `fsrs.Card()`.
  - **Escritas disjuntas por coluna:** a edição escreve só conteúdo, e a revisão só o FSRS.
  - **Situações:** `ativo`, `suspenso`, `aguardando_revisao` e `recusado`. Só `ativo` entra em lições.
  - **Ordem dos novos:** `entrada_estudo_em`.
  - **Selo de verificado:** derivado da origem e da fonte da geração.
- **Lição e revisão (DTEC 049 a 056):**
  - **Começar ou continuar:** `POST /licoes` sob *advisory lock* do estudante (espaço `licao`); uma lição aberta por estudante (índice parcial); a de dia anterior é encerrada só ali (D-005), e as leituras não escrevem.
  - **Elegíveis:** `ativo` em `revisao` com `vencimento < proxima_virada`; em aprendizado ou reaprendizado já revisado só com `vencimento <= agora`; novos por `entrada_estudo_em`, dentro do limite contado pelas primeiras revisões do dia e reconferido na primeira revisão.
  - **Apresentação:** o verso só sai pela revelação; a avaliação exige revelação, é idempotente pela chave do cliente e pela apresentação, e a ordem das travas é *advisory lock* → lição → apresentação → cartão.
  - **FSRS:** só `revisao/agendador.py` revisa com a `fsrs`; semente por revisão (`revisoes.semente_fuzz`) com gerador por contexto no lugar de `fsrs.scheduler.random`, coberto por teste de contrato; a escrita das colunas do FSRS e de `dominado_em` fica só em `cartoes/agendamento.py`.
  - **Revisões:** imutáveis, com estado antes e depois, versão dos parâmetros, semente, `versao_regras`, `primeira_do_dia` e `tornou_dominado`; publicam `RevisaoRegistrada` em `nucleo/eventos_revisao.py`, na mesma transação.
  - **Dominado:** `LIMIAR_DOMINADO_DIAS = 21` em `revisao/regras.py` (versionado); `dominado_em` preenchido uma vez.
  - **Trilha:** `numero` atribuído na conclusão; `GET /trilha` com cursor, estado do nó atual e próximo vencimento.
- **Gamificação (DTEC 057 a 063):**
  - **Valores de XP:** `gamificacao/regras.py` com histórico imutável (`PUBLICADAS = {1: RegraXp(1, 10, 25)}`); `eventos_xp.versao_regra smallint`; o limiar de dominado continua só em `revisao/regras.py`; um teste de referência fixa as versões publicadas.
  - **XP:** ouvinte de `RevisaoRegistrada` grava `revisao` (com `primeira_do_dia`) e `cartao_dominado` (com `tornou_dominado`) por `INSERT` simples, com índice único `(revisao_id, tipo)`, e incrementa `usuarios.xp_total` na mesma transação.
  - **Trava:** toda escrita da gamificação começa com `FOR NO KEY UPDATE` na linha do estudante em `usuarios`, sempre depois das travas de quem chama (nenhum caminho trava cartão depois dela).
  - **Meta:** linha do dia em `dias_estudo` (`pendente` → `estudado`, definitivo) com meta efetiva `min(meta_diaria, revisados + restantes)`; restantes pelo provedor.
  - **Sequência:** liquidação preguiçosa e exata dos dias passados (`liquidar`, função pura) na próxima escrita da gamificação, com `usuarios.dias_liquidados_ate`; leituras calculam sem gravar; datas liquidadas materializadas (`estudado`, `nao_estudado`, `neutro`) e imutáveis; sem tarefa periódica.
  - **Fuso:** data pulada (que nunca foi o dia corrente) vira `neutro` com `data_pulada`; data repetida reaproveita a linha.
  - **Exibição:** `ResumoGamificacao` aditivo em `Trilha`, `Fechamento` e `ResultadoAvaliacao`, mais `xpGanho`, `metaCumpridaAgora` e `depoisDaMeta`.
- **Evolução (DTEC 064 a 067):**
  - **Rota:** `GET /evolucao` devolve `possuiRevisoes`, `gamificacao` (o mesmo `ResumoGamificacao` e a mesma função `resumo` da trilha), `calendario` e `dominados`, numa transação `REPEATABLE READ, READ ONLY`.
  - **Calendário:** 26 semanas de domingo a sábado, a última é a corrente; datas de `max(inicio, primeiro dia do estudante)` até hoje por `dias_no_intervalo`; situações exibidas `estudado`, `nao_estudado`, `neutro` (inclui `data_pulada`) e `em_andamento` (só hoje, enquanto a meta não foi cumprida).
  - **Dominados atuais:** `ativo` ou `suspenso` com `estabilidade >= LIMIAR_DOMINADO_DIAS` vigente, aplicados só em `revisao/consultas.py`; distintos de `dominado_em` (marco do bônus); todas as matérias, inclusive com 0, por nome.
  - **Estado vazio:** `existe_revisao` (revisões de cartões excluídos contam), não `xp_total = 0`.

## Frontend

- **Stack:**
  - React com TypeScript *strict* e Vite;
  - Tailwind;
  - TanStack Router e Query, com `openapi-fetch` e `openapi-typescript` (DTEC 015);
  - React Aria Components encapsulado em `src/componentes/ui/` (DTEC 016);
  - Zod e React Hook Form.
- **Texto do estudante:** sempre como texto puro (`pre-wrap`). `dangerouslySetInnerHTML` é proibido por lint (DTEC 036).
- **Componentes já previstos:** `DialogoConfirmacao` (destrutivo), `ZonaArquivo`, `GrupoOpcoes`, `SeloEstado`, `CampoTextoLongo`, `SeloOrigem`, `PainelEvidencia`, `CitacaoDestacada` e `AtalhoTeclado`.
- **Trilha do MVP:** caminho vertical contínuo (D-008 da 005); a do final acadêmico está em discussão (QA-34).
- **Lição:** rota única `/licao`, que chama `POST /licoes` ao carregar; atalhos Espaço ou Enter (revelar), 1 a 4 (notas) e Enter depois da explicação; medida `transicao-cartao` com `performance.mark` (CS-004 da 005).
- **Gamificação (006):** `PainelProgresso` e `AnuncioGamificacao` em `funcionalidades/gamificacao/`; uma região `aria-live="polite"` por página; valores só da resposta do servidor (sem atualização otimista); sem som; animação só sem `prefers-reduced-motion`.
- **Evolução (007, DTEC 067):** rota `/evolucao` e componentes em `funcionalidades/evolucao/`; `CalendarioEstudo` com o padrão *grid* do WAI-ARIA (semanas em linhas, a corrente no topo, *roving tabindex*, cada dia anuncia data e situação); forma além da cor em cada situação; tokens `dia-*` com teste de contraste de 3:1 (indicador contra o fundo, preenchimento contra células vazias, glifo contra o preenchimento); medida `evolucao-carregada` com `performance.measure`.
- **Acessibilidade:** WCAG 2.2 AA, `vitest-axe` em todo componente, uso a partir de 320 px.

## Testes

- **Backend:** pytest (DTEC 001) com pytest-asyncio, httpx, Hypothesis e Postgres real.
  - **Marcadores obrigatórios:** `unit`, `integration`, `functional`, `security` e `adversarial`, cada teste citando o requisito.
  - **`avaliacao_ia`:** marcador fora da suíte que bloqueia o merge.
- **Frontend:** Vitest, Testing Library e MSW. O Playwright só no final acadêmico (DTEC 014).
- **IA nos testes:** `FunctionModel` e `TestModel` do PydanticAI, com `ALLOW_MODEL_REQUESTS = False`.
- **Integração contínua:** GitHub Actions na `develop` e nos PRs para a `main` (DTEC 017).
- **Fábricas:** só textos fictícios e contas `@exemplo.com` (regra 10).

## IA (DTEC 007, 011 e 039 a 047)

- **Provedor:** PydanticAI, com Gemini na camada gratuita e Groq alternativo, configurados por `IA_PROVEDOR`.
- **Porta única:** `ia/cliente.py`, com orçamento diário de *tokens* por estudante, timeout, `UsageLimits` e uma linha de `consumo_ia` por chamada, sem conteúdo.
- **Ciência do aviso:** versionada por provedor (`ciencias_aviso_ia`) e exigida antes de qualquer envio (`409 ciencia_aviso_pendente`).
- **Geração (004):**
  - janela de trechos não cobertos;
  - portões determinísticos (vínculo, citação literal, cobertura lexical);
  - juíza que só reprova;
  - filtro lexical de repetição;
  - publicação atômica;
  - conjunto de avaliação revisado por pessoa.

## Decisões técnicas (DTEC)

| DTEC | Decisão em uma linha | Fonte |
|---|---|---|
| 001 | pytest como ferramenta única de testes Python | [research](../research.md#decisão-dtec-001-ferramenta-de-testes-do-backend) |
| 002 | FastAPI, SQLAlchemy 2 assíncrono, Alembic e Pydantic com uv; emenda: psycopg 3 como único driver | [research](../research.md#decisão-dtec-002-framework-do-backend) |
| 003 | Autenticação própria: Argon2id e sessão opaca em cookie | [research](../research.md#decisão-dtec-003-autenticação) |
| 004 | React, TypeScript, Vite e Tailwind; Zod, React Hook Form, ESLint e Prettier | [research](../research.md#decisão-dtec-004-frontend) |
| 005 | PostgreSQL único na imagem `pgvector/pgvector` | [research](../research.md#decisão-dtec-005-banco-de-dados-único) |
| 006 | Procrastinate (fila no Postgres), contêiner `worker` | [research](../research.md#decisão-dtec-006-fila-e-processamento-assíncrono) |
| 007 | Gemini gratuito, Groq alternativo, PydanticAI desde o MVP | [research](../research.md#decisão-dtec-007-llm-e-framework-de-agentes) |
| 008 | bge-m3 e reranker no Workers AI (final acadêmico) | [research](../research.md#decisão-dtec-008-embeddings-e-reranking) |
| 009 | PyMuPDF para PDF; TXT e MD diretos; SRT, VTT e DOCX no final | [research](../research.md#decisão-dtec-009-extração-de-texto) |
| 010 | Interface de armazenamento: disco no MVP, R2 no final, memória nos testes | [research](../research.md#decisão-dtec-010-armazenamento-de-arquivos) |
| 011 | Logs JSON, `/health`, `consumo_ia`; pydantic-evals fora do merge; taxa de aceitação | [research](../research.md#decisão-dtec-011-observabilidade-e-avaliação-da-ia) |
| 012 | Biblioteca `fsrs` com versão fixada; FSRS soberano (RN-26) | [research](../research.md#decisão-dtec-012-algoritmo-de-repetição-espaçada) |
| 013 | VPS de 2 a 4 GB com Compose e backup no R2 (final) | [research](../research.md#decisão-dtec-013-hospedagem-e-operação) |
| 014 | Complementos de teste; Vitest, Testing Library e MSW; Playwright no final | [research](../research.md#decisão-dtec-014-complementos-de-teste) |
| 015 | TanStack Router e Query, `openapi-fetch` | [research](../research.md#decisão-dtec-015-roteamento-e-estado-do-servidor-no-frontend) |
| 016 | React Aria Components em `componentes/ui/` | [research](../research.md#decisão-dtec-016-primitivas-acessíveis-da-interface) |
| 017 | GitHub Actions: lint, tipos, migrações, suítes, OpenAPI e imagens | [research](../research.md#decisão-dtec-017-integração-contínua-e-verificação-local) |
| 018 | Camadas DTO, mapeador, serviço, domínio, repositório e exceções | [research](../research.md#decisão-dtec-018-camadas-do-backend-dto-mapper-repositório-e-exceções) |
| 019 | Isolamento: filtro de dono no repositório, FKs compostas e teste que percorre as rotas | [001](../specs/001-conta-acesso/research.md#decisão-dtec-019-garantia-do-isolamento-entre-estudantes) |
| 020 | Tentativas de acesso numa tabela, com *advisory lock* | [001](../specs/001-conta-acesso/research.md#decisão-dtec-020-registro-e-limite-das-tentativas-de-acesso) |
| 021 | Exclusão da conta: transação nas linhas, tarefa no armazenamento, teste de catálogo | [001](../specs/001-conta-acesso/research.md#decisão-dtec-021-exclusão-da-conta-e-chaves-de-armazenamento-por-usuário) |
| 022 | Lista local de senhas comuns | [001](../specs/001-conta-acesso/research.md#decisão-dtec-022-lista-local-de-senhas-comuns) |
| 023 | Parâmetros de sessão, CSRF assinado e Argon2id (RFC 9106) | [001](../specs/001-conta-acesso/research.md#decisão-dtec-023-detalhes-da-sessão-do-csrf-e-do-hash-de-senha) |
| 024 | Arquivos não confiáveis em subprocesso com tempo e memória limitados | [research](../research.md#decisão-dtec-024-execução-isolada-do-processamento-de-arquivos-não-confiáveis) |
| 025 | Objeto antes da linha, compensação e reconciliação periódica | [research](../research.md#decisão-dtec-025-consistência-entre-o-armazenamento-de-objetos-e-o-banco) |
| 026 | *Polling* condicional de 2 s | [research](../research.md#decisão-dtec-026-acompanhamento-de-processamentos-assíncronos-na-interface) |
| 027 | Participantes da exclusão de fontes e matérias (emenda: `cartoes_suspensos`) | [research](../research.md#decisão-dtec-027-participantes-da-exclusão-de-fontes-e-matérias) |
| 028 | Validação do arquivo no envio, em ordem e com códigos; texto só em UTF-8 | [002](../specs/002-materias-fontes/research.md#decisão-dtec-028-validação-do-arquivo-no-envio) |
| 029 | Trechos por estrutura: alvo 1.200, máximo 2.000, sobreposição 150; página por trecho | [002](../specs/002-materias-fontes/research.md#decisão-dtec-029-extração-normalização-e-divisão-em-trechos) |
| 030 | Estados, códigos de falha, novas tentativas e jobs travados | [002](../specs/002-materias-fontes/research.md#decisão-dtec-030-estados-falhas-e-novas-tentativas-do-processamento) |
| 031 | Impacto confirmado na exclusão; `FOR SHARE` ao publicar a partir de uma fonte | [002](../specs/002-materias-fontes/research.md#decisão-dtec-031-impacto-da-exclusão-sob-concorrência) |
| 032 | Cotas com *advisory lock* por estudante e índices únicos | [002](../specs/002-materias-fontes/research.md#decisão-dtec-032-cotas-e-duplicatas-sob-concorrência) |
| 033 | Busca com `unaccent`, sem índice | [research](../research.md#decisão-dtec-033-busca-sem-diferenciar-maiúsculas-e-acentos) |
| 034 | Paginação por cursor | [research](../research.md#decisão-dtec-034-paginação-das-listagens-por-cursor) |
| 035 | Referência do cartão manual com cópia da origem e FK composta `restrict` | [003](../specs/003-cartoes-manuais/research.md#decisão-dtec-035-referência-de-um-cartão-manual-a-uma-fonte) |
| 036 | Texto e limites dos cartões num único ponto | [003](../specs/003-cartoes-manuais/research.md#decisão-dtec-036-texto-limites-e-validação-dos-cartões) |
| 037 | Estado inicial de `fsrs.Card()`; escritas disjuntas entre edição e revisão | [003](../specs/003-cartoes-manuais/research.md#decisão-dtec-037-estado-de-agendamento-edição-e-situação-do-cartão) |
| 038 | Fronteira entre 003 e 004; participante dos cartões | [003](../specs/003-cartoes-manuais/research.md#decisão-dtec-038-fronteira-com-a-spec-004-e-participante-da-exclusão) |
| 039 | Aviso e ciência do provedor de IA, versionados | [research](../research.md#decisão-dtec-039-aviso-e-ciência-do-uso-de-provedor-de-ia-externo) |
| 040 | Consumo, orçamento de *tokens* e limites da IA | [research](../research.md#decisão-dtec-040-consumo-orçamento-e-limites-operacionais-da-ia) |
| 041 | Janela de trechos, cobertura e filtro de repetição | [004](../specs/004-geracao-cartoes/research.md#decisão-dtec-041-janela-de-trechos-cobertura-e-não-repetição) |
| 042 | Portões determinísticos e juíza que só reprova | [004](../specs/004-geracao-cartoes/research.md#decisão-dtec-042-validação-estrutural-e-de-sustentação) |
| 043 | Execução da geração em duas transações, com códigos de falha | [004](../specs/004-geracao-cartoes/research.md#decisão-dtec-043-execução-estados-e-falhas-da-geração) |
| 044 | Pedido de geração: chave, uma por fonte, limite diário com *advisory lock* | [004](../specs/004-geracao-cartoes/research.md#decisão-dtec-044-pedido-de-geração-sob-reenvio-e-concorrência) |
| 045 | Revisão dos gerados: transições, ordem e selo derivado | [004](../specs/004-geracao-cartoes/research.md#decisão-dtec-045-revisão-dos-cartões-gerados) |
| 046 | Participante da geração, descartados e retenção | [004](../specs/004-geracao-cartoes/research.md#decisão-dtec-046-participante-da-exclusão-descartes-e-retenção) |
| 047 | Instruções embutidas, contradições e conjunto de avaliação | [004](../specs/004-geracao-cartoes/research.md#decisão-dtec-047-instruções-embutidas-contradições-e-avaliação) |
| 048 | Dia de estudo calculado num único ponto (`nucleo/dia_estudo.py`) | [research](../research.md#decisão-dtec-048-dia-de-estudo-calculado-num-único-ponto) |
| 049 | Lição com cartões previstos e apresentações; `cascade` justificado | [005](../specs/005-licao-trilha/research.md#decisão-dtec-049-modelo-da-lição-cartões-previstos-e-apresentações) |
| 050 | "Começar ou continuar" com trava; encerramento do dia anterior só no `POST /licoes` | [005](../specs/005-licao-trilha/research.md#decisão-dtec-050-abertura-retomada-e-encerramento-da-lição) |
| 051 | Elegibilidade pelo estado do FSRS; limite de novos reconferido na primeira revisão | [005](../specs/005-licao-trilha/research.md#decisão-dtec-051-elegibilidade-e-limite-de-novos-por-dia) |
| 052 | Revelação no servidor, avaliação idempotente, duração medida no cliente | [005](../specs/005-licao-trilha/research.md#decisão-dtec-052-revelação-avaliação-idempotente-e-duração) |
| 053 | Semente por revisão e gerador por contexto na `fsrs` | [005](../specs/005-licao-trilha/research.md#decisão-dtec-053-agendamento-reprodutível-com-a-biblioteca-fsrs) |
| 054 | Próximo cartão (passo curto vencido primeiro), término e transição numa ida e volta | [005](../specs/005-licao-trilha/research.md#decisão-dtec-054-próximo-cartão-término-e-desempenho-da-transição) |
| 055 | Dominado com regras versionadas; fatos e evento entregues à 006 | [005](../specs/005-licao-trilha/research.md#decisão-dtec-055-dominado-e-fatos-entregues-à-gamificação) |
| 056 | Trilha: `numero` na conclusão, cursor, estado do nó atual e extras | [005](../specs/005-licao-trilha/research.md#decisão-dtec-056-trilha-numeração-dos-nós-e-lições-extras) |
| 057 | Disponibilidade de cartões (provedor) e ganchos de alteração no núcleo | [research](../research.md#decisão-dtec-057-disponibilidade-de-cartões-e-ganchos-de-alteração-no-núcleo) |
| 058 | Regra de valores de XP versionada, limiar só na 005 | [006](../specs/006-xp-meta-sequencia/research.md#decisão-dtec-058-regra-de-valores-versionada) |
| 059 | XP por `INSERT` com índice `(revisao_id, tipo)` e cache `xp_total` | [006](../specs/006-xp-meta-sequencia/research.md#decisão-dtec-059-concessão-de-xp-idempotente-e-cache-do-total) |
| 060 | Meta efetiva e dia estudado definitivo sob a trava do estudante | [006](../specs/006-xp-meta-sequencia/research.md#decisão-dtec-060-meta-efetiva-e-dia-estudado-sob-concorrência) |
| 061 | Liquidação preguiçosa e exata dos dias passados; dia neutro e sequência | [006](../specs/006-xp-meta-sequencia/research.md#decisão-dtec-061-liquidação-dos-dias-passados-dia-neutro-e-sequência) |
| 062 | Mudança de fuso (data pulada neutra, repetida uma vez) e horário de verão | [006](../specs/006-xp-meta-sequencia/research.md#decisão-dtec-062-mudança-de-fuso-e-horário-de-verão) |
| 063 | `ResumoGamificacao` aditivo nas respostas da 005 e anúncio acessível | [006](../specs/006-xp-meta-sequencia/research.md#decisão-dtec-063-exibição-contrato-aditivo-e-anúncio-acessível) |
| 064 | Evolução numa rota, com transação `REPEATABLE READ, READ ONLY` e consultas dos donos | [007](../specs/007-evolucao/research.md#decisão-dtec-064-leitura-consolidada-da-evolução) |
| 065 | Calendário de 26 semanas (domingo a sábado) e mapeamento das situações da 006 | [007](../specs/007-evolucao/research.md#decisão-dtec-065-período-e-situações-do-calendário) |
| 066 | Dominados atuais pelo limiar vigente em `revisao/consultas.py`; sem índice novo | [007](../specs/007-evolucao/research.md#decisão-dtec-066-cartões-dominados-atuais) |
| 067 | Calendário em *grid* acessível, forma além da cor e contraste verificável | [007](../specs/007-evolucao/research.md#decisão-dtec-067-calendário-acessível-e-responsivo) |

A próxima DTEC é a **068**.

## Obrigações pendentes entre specs

| Para | Obrigação | Origem |
|---|---|---|
| 004 (implementação) | Usar `nucleo/dia_estudo.py` no limite de gerações e no orçamento; quem implementar primeiro (004 ou 005) cria o módulo | [DTEC 048](../research.md#decisão-dtec-048-dia-de-estudo-calculado-num-único-ponto) |
| 006 (implementação) | `dias_no_intervalo` com o recorte no primeiro dia do estudante e em hoje (esclarecimento da T036 da 006) | [DTEC 065](../specs/007-evolucao/research.md#decisão-dtec-065-período-e-situações-do-calendário) |
| Toda spec que altere a situação de cartões, a meta, o limite de novos ou o fuso | Chamar os ganchos `antes_de_alterar` e `depois_de_alterar` da DTEC 057 na própria transação | [DTEC 057](../research.md#decisão-dtec-057-disponibilidade-de-cartões-e-ganchos-de-alteração-no-núcleo) |
| 001, 003 e 005 (implementação) | Não mudam de comportamento: as chamadas aos ganchos, o provedor em `revisao` e os campos aditivos são tarefas da 006; quem implementar primeiro uma spec que precise de `nucleo/disponibilidade.py` cria o módulo com os registros vazios | [Plano da 006](../specs/006-xp-meta-sequencia/plan.md#saídas-do-planejamento) |
| 010 | Reutilizar janela, cobertura, portões e filtro de repetição; geração com `fonte_id` nulo e publicação em lotes | Plano da 004 |
| 011 | Criar `chave_imagem`; imagem segue a DTEC 025 (objeto antes das linhas) | Plano da 003 |
| 013 | Acrescentar período e filtros a `GET /evolucao` como campos aditivos; `xp_por_dia` (006) disponível; tempo dedicado por `revisoes.duracao_ms` pela consulta de `revisao` | [Plano da 007](../specs/007-evolucao/plan.md#obrigações-registradas-para-as-próximas-specs) |
| 012 | "Domínio da matéria" (só ativos) com rótulo distinto de "cartões dominados"; pode reaproveitar `contar_dominados_por_materia` com filtro de situação, com o limiar só em `revisao` | [Plano da 007](../specs/007-evolucao/plan.md#obrigações-registradas-para-as-próximas-specs) |
| 012 | Acrescentar o filtro por matéria à elegibilidade (DTEC 051) e rever a unicidade da lição aberta (DTEC 050); se a disponibilidade for filtrada por matéria, acrescentar o parâmetro ao provedor da DTEC 057, com a meta continuando global | Planos da 005 e da 006 |
| 014 | Usar `ia/cliente.py` e a ciência da DTEC 039; registrar o participante dos índices e das citações | Planos da 002 e da 004 |
| 015 | Tira-dúvidas como ação secundária na apresentação, sem alterar a avaliação | Plano da 005 |

As obrigações da 003 e da 005 para a 006 (ouvinte de `RevisaoRegistrada`, XP só com `primeira_do_dia` e bônus só com `tornou_dominado`, `eventos_xp.cartao_id` com `set null` e a reverificação da US3-3 da 003, campos aditivos, `nucleo/dia_estudo.py` na meta e na sequência, "extra depois da meta") estão no plano da 006 e viram tarefas dela. As obrigações da 003 e da 004 para a 005 (lição só com `ativo`, ordem de `entrada_estudo_em`, `revisoes.cartao_id` com `set null`, `dominado_em`, escritas disjuntas, explicação ao errar com a evidência e as reverificações da US1-1, US3-1, US3-2 e CS-003 da 003 e da US1-4 da 004) estão no plano da 005 e viram tarefas dela.

As obrigações da 005 e da 006 para a 007 (ler dominados, estabilidade e revisões pelas consultas de `revisao` e `cartoes`; ler dias e XP só por `gamificacao/consultas.py`, sem recalcular a sequência nem ler `dias_estudo`) estão no plano da 007 e viram tarefas dela.
