# Plano de implementação

**Funcionalidade:** 005-licao-trilha (lição com repetição espaçada e trilha de progressão)  
**Spec:** [spec.md](spec.md), aprovada em 12/10/2026  
**Data:** 13/10/2026 ([registro](../../prompts/2026-10-13-005-licao-trilha-plano.md))  
**Responsáveis:**

- Artur Lins: decisões técnicas e aprovações desta fase de documentação.
- Implementação: qualquer pessoa da equipe pode assumir, e registra o nome abaixo antes da primeira tarefa.
  - **Responsável pela implementação:** *a definir no início da implementação*.

**Status:** em revisão; aguarda o portão "Plano aprovado", com a DTEC 048 (transversal) e as DTEC 049 a 056

Este plano **reaproveita sem redefinir** o que as specs anteriores já definiram (resumo em [`contexto-tecnico.md`](../../skills/contexto-tecnico.md)):

- da [001](../001-conta-acesso/plan.md) e das DTEC 015 a 018: a estrutura base, as camadas, a hierarquia de erros, o formato de erro, o `/api/v1`, a sessão, o CSRF, as preferências (`tamanho_licao`, `limite_novos_dia`, `fuso`), as versões de `parametros_fsrs`, o registro `apagar_dados_usuario` e o teste de isolamento;
- da [002](../002-materias-fontes/plan.md): o *advisory lock* por estudante (DTEC 032);
- da [003](../003-cartoes-manuais/plan.md): a tabela `cartoes`, o estado inicial de `fsrs.Card()` e as escritas disjuntas (DTEC 037), as situações e `entrada_estudo_em`, a paginação por cursor (DTEC 034);
- da [004](../004-geracao-cartoes/plan.md): a idempotência com chave do cliente (`409 idempotencia_divergente`) e `GET /cartoes/{id}/evidencias`.

Aqui está só o que a 005 acrescenta.

## Resumo técnico

A lição e a trilha ficam no domínio `revisao` ([arquitetura, seção 5.1](../../arquitetura/README.md#51-organização-mvc-por-domínio)), que já guarda `parametros_fsrs` desde a 001. O dia de estudo é calculado num único módulo do núcleo ([DTEC 048](../../research.md#decisão-dtec-048-dia-de-estudo-calculado-num-único-ponto)).

**Começar ou continuar.** `POST /licoes`, sob *advisory lock* do estudante, devolve a lição aberta do dia, encerra a de um dia anterior sem acender o nó (D-005) ou monta uma nova. A montagem escolhe os devidos elegíveis e os novos dentro do limite restante, e grava os previstos em `licoes_cartoes` ([DTEC 049 a 051](research.md#decisão-dtec-049-modelo-da-lição-cartões-previstos-e-apresentações)).

**Cada cartão** é uma apresentação: a frente sai sem o verso; a revelação grava o instante e devolve o verso; a avaliação exige a revelação e é idempotente pela chave do cliente e pela apresentação ([DTEC 052](research.md#decisão-dtec-052-revelação-avaliação-idempotente-e-duração)).

**O agendamento** vem só da biblioteca `fsrs`, com os parâmetros vigentes e uma semente por revisão gravada no evento, o que torna cada revisão reproduzível ([DTEC 053](research.md#decisão-dtec-053-agendamento-reprodutível-com-a-biblioteca-fsrs)). A resposta da avaliação já traz o próximo cartão (passo curto vencido primeiro) ou o fechamento ([DTEC 054](research.md#decisão-dtec-054-próximo-cartão-término-e-desempenho-da-transição)).

**A revisão** grava `primeira_do_dia` e `tornou_dominado` e chama um gancho do núcleo, que a 006 usará para o XP ([DTEC 055](research.md#decisão-dtec-055-dominado-e-fatos-entregues-à-gamificação)). A trilha numera os nós na conclusão e expõe o estado do nó atual e o próximo vencimento ([DTEC 056](research.md#decisão-dtec-056-trilha-numeração-dos-nós-e-lições-extras)).

**Riscos principais:** o prazo de 15/10/2026; a substituição do gerador do *fuzz* depender de um símbolo interno da biblioteca (coberta por teste de contrato); a virada das 4h com fuso e horário de verão; e a meta de 300 ms por transição.

A ordem US1 com US2 (P1, o fluxo da lição com a explicação) → US3 (trilha) → US4 (extras) entrega primeiro a lição demonstrável com cartões manuais, sem IA (Princípio VI).

## Contexto técnico

- **Linguagem e versão:** as da 001: Python 3.13 com uv; TypeScript *strict* em Node 24 LTS com npm.
- **Dependências novas:** nenhuma. A `fsrs` já está nas dependências da 001 (DTEC 012), com a versão fixada no `uv.lock`. `zoneinfo`, `secrets` e `contextvars` são da biblioteca padrão.
- **Persistência** (migração `0006_licoes_revisoes`, [modelo de dados](data-model.md)):
  - as tabelas `licoes`, `licoes_cartoes`, `apresentacoes` e `revisoes`;
  - o enum `nota_revisao`;
  - a coluna `cartoes.dominado_em` e o índice único `cartoes_id_usuario`.
- **Testes:** pytest com pytest-asyncio, httpx, Hypothesis e Postgres real; relógio injetável no serviço; no frontend, Vitest, Testing Library, MSW e `vitest-axe`.
- **Plataforma de execução:** os serviços do Compose das specs anteriores. Nenhum serviço, volume ou variável novos.
- **Limites de desempenho:**
  - cada transição de cartão em até 300 ms no percentil 95, no ambiente local (CS-004); orçamento de 150 ms no servidor para avaliar e para revelar;
  - `POST /licoes` e `GET /trilha` em até 200 ms no percentil 95 com 3 mil cartões ativos.
- **Escala prevista:** dezenas de estudantes, de centenas a poucos milhares de cartões por estudante, algumas lições por dia.

## Verificação da constituição

| Princípio | Como o plano atende | Evidência prevista |
|---|---|---|
| I Fontes exclusivas | A explicação exibida ao errar é a gravada com o cartão; a evidência vem da rota da 004; nenhuma chamada à IA na lição (RF-009, RN-16) | Teste funcional da US2 com o provedor simulado registrando zero chamadas |
| II Proteção e isolamento | FKs compostas com o dono em todas as tabelas novas; 3 rotas novas com identificador na tabela de isolamento (DTEC 019); verso só pela revelação; logs sem frente, verso nem explicação | Testes `security/`; teste de logs; teste de catálogo da exclusão da conta |
| III Verificação humana | Q-001 e Q-002 ficam com a equipe e o PO; DTEC 048 a 056 registradas para aprovação | Este plano; registro da sessão |
| IV Servidor autoritativo | Montagem, elegibilidade, limite, revelação, agendamento, término e trilha decididos no servidor; idempotência pela chave e pela apresentação; revisão imutável com estado antes e depois | Testes de concorrência e de reenvio (CS-002); teste de imutabilidade |
| V Qualidade verificável | CS-001 comparado com a biblioteca isolada; CS-003 por testes de elegibilidade com relógio controlado; CS-004 medido; axe nos componentes | `traceability.md`; roteiro de medição no quickstart |
| VI Entrega incremental | US1 e US2 demonstráveis com cartões manuais, sem IA | `quickstart.md` |
| VII Rastreabilidade | DTEC com alternativas; registro da sessão; revisões com versão dos parâmetros, semente e versão das regras | `docs/prompts/`, `traceability.md` |

Não há exceção aos princípios. As exceções técnicas estão em [Complexidade e exceções](#complexidade-e-exceções).

## Arquitetura e fluxo

### Dependências entre domínios

```text
revisao ──(elegíveis, trava e escrita das colunas do FSRS: cartoes/consultas.py e cartoes/agendamento.py)──> cartoes
   │──(existência de matérias: materias/consultas.py)──> materias
   │──(fuso, tamanho da lição, limite de novos)──> identidade
   │──(dia de estudo)──> nucleo/dia_estudo.py (DTEC 048)
   └─ publica RevisaoRegistrada ──> nucleo/eventos_revisao.py <── 006 registra o ouvinte
```

- `cartoes`, `materias` e `identidade` não importam `revisao`.
- `revisao` não acessa os modelos ORM de `cartoes` nem de `materias`: usa as consultas expostas por eles. A escrita do estado do FSRS fica numa única função de `cartoes/agendamento.py`, que atualiza só as colunas do FSRS e `dominado_em` (DTEC 037).
- Só `revisao/agendador.py` importa `fsrs` para revisar; a 003 continua usando `fsrs.Card()` na criação.
- Um teste de arquitetura verifica essas direções, e que o repositório de revisões não tem `update` nem `delete` (exceto `apagar_dados_usuario`).

### Fluxos da spec

| Fluxo | Passos principais |
|---|---|
| **Trilha (US3, RF-010, RF-013)** | `GET /trilha` → nós concluídos por cursor → estado do nó atual (`sem_materias`, `sem_cartoes`, `comecar`, `continuar`, `sem_disponiveis`) → disponíveis e `proximoVencimento` (DTEC 056). Sem escrita. |
| **Começar ou continuar (US1, RF-001, RF-002, RF-011)** | `POST /licoes` → *advisory lock* `licao` → lição aberta do dia: garante a apresentação atual (retira cartão fora de `ativo` ou novo além do limite) → `200`; aberta de dia anterior: `encerrada_em` → montagem; sem aberta: montagem (devidos, depois novos dentro do limite) → `licoes_cartoes` → primeira apresentação → `201`; nada a montar: `409 sem_cartoes_disponiveis`. |
| **Revelar (RF-003)** | `POST /apresentacoes/{id}/revelacao` → apresentação do dono (`404`) → lição aberta (`409 licao_encerrada`) → cartão `ativo` (`409 cartao_indisponivel`) → grava `revelada_em` uma vez → `200 {verso}`. |
| **Avaliar (US1, US2, RF-004 a RF-009)** | `POST /apresentacoes/{id}/avaliacao` → chave (`200` reenvio ou `409 idempotencia_divergente`) → apresentação (`404`) → *advisory lock* se novo → lição `FOR UPDATE` e nova busca da chave → já avaliada (`409 apresentacao_ja_avaliada`) → revelação (`409 revelacao_pendente`) → cartão `FOR NO KEY UPDATE` (`409 cartao_indisponivel`) → limite (`409 limite_novos_atingido`) → `agendador.revisar` com semente → `revisoes` → colunas do FSRS e `dominado_em` → `revisado_em` e `avaliada_em` → evento `RevisaoRegistrada` → próximo ou conclusão → `201` com a explicação só em Errei. |
| **Próximo e término (RF-006, D-004)** | Passo curto vencido da lição ("revendo") → próximo previsto pela posição → conclusão com `numero` e fechamento (revisões, distintos, dominados, passos curtos pendentes, "Continuar", próximo vencimento). |
| **Outra aba (CB-24)** | `409 apresentacao_ja_avaliada` → `GET /licoes/{id}` → apresentação pendente atual ou fechamento. |
| **Extra (US4, RF-012)** | "Continuar" no fechamento → `POST /licoes` → nova lição com `extra = true`. Sem disponíveis, "Continuar" não aparece e o fechamento mostra o próximo vencimento (CB-30). |
| **Explicação e evidência (US2, EX-03)** | Resposta da avaliação com `explicacao` e `evidenciaDisponivel` → painel com a explicação e "Ver evidência" recolhido (`PainelEvidencia` da 004, `GET /cartoes/{id}/evidencias`) → Enter segue para o próximo. |
| **Exclusão de cartão, fonte ou matéria (003, CB-27)** | Cascata em `licoes_cartoes` e `apresentacoes`; `revisoes.cartao_id` nulo. A lição em andamento segue sem o cartão; se era o pendente, `GET /licoes/{id}` devolve `atual` nulo e a interface chama `POST /licoes`. |
| **Excluir a conta (DTEC 021)** | `apagar_dados_usuario` do domínio `revisao` apaga `apresentacoes`, `licoes_cartoes`, `revisoes` e `licoes` antes de `parametros_fsrs` e dos cartões. |

### Tarefas assíncronas criadas ou alteradas nesta spec

Nenhuma. Toda a lição é síncrona, e o encerramento da lição de dia anterior acontece no próximo `POST /licoes` (DTEC 050), sem tarefa periódica.

## O que a 005 entrega à 006

A 005 **não** calcula XP, meta nem sequência. Ela entrega:

- **Evento de revisão:** `RevisaoRegistrada`, publicado por `nucleo/eventos_revisao.py` na mesma transação da revisão, com o usuário, o cartão, a revisão, a nota, o instante, o dia de estudo, `primeira_do_dia`, `tornou_dominado` e `versao_regras`. Na 005 não há ouvinte.
- **Primeira revisão do dia:** `revisoes.primeira_do_dia`, garantida por índice único parcial, que é a base do XP por cartão distinto (RN-18) e da meta (RN-21).
- **Dominado:** `cartoes.dominado_em`, preenchido uma única vez, e `revisoes.tornou_dominado`, base do bônus único.
- **Fechamento extensível:** o esquema `Fechamento` recebe campos aditivos de XP e sequência na 006, e `extra` permanece como "lição depois de outra concluída no dia"; a classificação "depois da meta" é da 006.
- **Lições concluídas por dia:** `revisao/consultas.py`, para a 006 e a 007.

## Q-001 (composição da trilha, UI-05): opções para a equipe

O plano **não decide** a Q-001; a decisão é da equipe até 14/10/2026. A API (DTEC 056) atende às três opções sem mudança.

| Opção | Descrição | Consequências |
|---|---|---|
| 1. Caminho vertical contínuo | Um nó por lição concluída, nó atual destacado e três nós futuros esmaecidos; marco visual a cada 10 lições; no celular, a mesma coluna | Mais simples; não depende da 006 nem da 007; muitas lições extras alongam o caminho |
| 2. Estações por dia de estudo | Os nós de um mesmo dia agrupados numa "estação", com as extras dentro dela | Mais compacta com muitas extras; liga a trilha ao dia de estudo, como a sequência da 006; pede o agrupamento por `diaEstudo` na interface |
| 3. Marcos por cartões dominados | Caminho vertical, com marcos ao atingir 10, 25 e 50 cartões dominados acumulados | Liga a trilha ao domínio; pede um campo aditivo com o total de dominados na trilha; depende de o limiar de 21 dias ser atingido, o que leva semanas |

Sugestão do agente, a confirmar pela equipe: opção 1 no MVP, por ser a mais simples e independente. Os estados de nó nunca dependem só de cor (forma e rótulo textual), conforme a seção 9.2 do design.

## EX-05 (Q-002)

Até a resposta do PO, a 005 **não** tem nenhum requisito de dificuldade. A dificuldade calculada pelo FSRS já fica gravada em `cartoes.dificuldade` e em cada revisão; se o PO aprovar a proposta de três faixas (PO-01), exibi-la é uma leitura, sem mudança de esquema nem de agendamento (RN-26).

## Estrutura do repositório

Somente o que a 005 acrescenta às estruturas da [001](../001-conta-acesso/plan.md#estrutura-do-repositório) a [004](../004-geracao-cartoes/plan.md#estrutura-do-repositório):

```text
backend/
├── migracoes/versions/0006_licoes_revisoes.py  # enum nota_revisao, 4 tabelas, CHECKs, índices parciais, FKs compostas, dominado_em
├── src/app/
│   ├── nucleo/
│   │   ├── dia_estudo.py         # DTEC 048: dia_estudo, inicio_dia, proxima_virada (puras)
│   │   └── eventos_revisao.py    # ouvintes de RevisaoRegistrada (vazio na 005)
│   ├── cartoes/
│   │   ├── consultas.py          # + elegíveis (devidos, passo curto, novos), contagens, trava para revisão
│   │   └── agendamento.py        # única escrita das colunas do FSRS e de dominado_em (DTEC 037)
│   ├── materias/consultas.py     # + existe_materia(usuario_id)
│   └── revisao/                  # (001: parametros_fsrs) + lição, apresentação, revisão e trilha
│       ├── rotas.py              # /trilha, /licoes, /licoes/{id}, /apresentacoes/{id}/revelacao|avaliacao
│       ├── dtos.py, mapeadores.py, servicos.py, repositorios.py, modelos.py, excecoes.py
│       ├── dominio.py            # elegibilidade, montagem, próximo e término, posição, fechamento, duração
│       ├── agendador.py          # porta única da fsrs: Scheduler por versão, Card, semente (DTEC 053)
│       ├── regras.py             # VERSAO_REGRAS, LIMIAR_DOMINADO_DIAS (DTEC 055)
│       ├── consultas.py          # lições concluídas por dia (006 e 007)
│       ├── reproduzir.py         # runbook: refaz uma revisão gravada e compara (RQ-004)
│       └── registros.py          # (001) + apagar_dados_usuario das tabelas novas
└── tests/
    ├── fabricas_revisao.py       # estados do FSRS fabricados; relógio controlado; semeadura do quickstart
    ├── unit/nucleo/              # dia de estudo (Hypothesis, fusos, horário de verão)
    ├── unit/revisao/             # elegibilidade, montagem, próximo, término, duração, dominado
    ├── contrato/fsrs/            # ponto de fuzz da versão fixada; CS-001 contra a biblioteca isolada
    ├── integration/revisao/      # travas, concorrência, migração, CHECKs, FKs, cascata, imutabilidade
    ├── functional/revisao/       # cenários da US1 a US4 pela API; reverificações da 003 e da 004
    ├── functional/desempenho/    # p95 de avaliar e revelar (CS-004, parte do servidor)
    ├── security/, adversarial/   # + rotas novas; verso antes da revelação, reenvios, payloads
    └── arquitetura/              # + direções de revisao; fsrs só no agendador; revisões sem update
frontend/src/
├── rotas/_autenticado/index.tsx  # trilha (início)
├── rotas/_autenticado/licao.tsx  # lição: chama POST /licoes ao carregar
├── funcionalidades/trilha/       # Trilha, NoTrilha, EstadoNoAtual, ProximoVencimento, convite inicial
├── funcionalidades/licao/        # CartaoLicao, BotoesAvaliacao, ExplicacaoErro, FechamentoLicao,
│                                 # atalhos de teclado, medição de transição (performance.mark)
└── componentes/ui/               # + AtalhoTeclado (rótulo e aria-keyshortcuts)
```

**Decisão de estrutura:**

- **Domínio `revisao`:** segue a arquitetura (seção 5.1), que já lhe atribui lições, autoavaliação, FSRS e idempotência.
- **`cartoes/agendamento.py`:** a escrita das colunas do FSRS fica no domínio dono da tabela, numa função só, o que mantém a DTEC 037 verificável num ponto.
- **Rota única da lição (`/licao`, sem identificador):** há no máximo uma lição aberta, e carregar a página é "voltar" (DTEC 050).
- **Trilha como componente próprio:** sem biblioteca de componentes que imponha aparência ([arquitetura, seção 6](../../arquitetura/README.md#6-frontend)).

## Teclado e acessibilidade (RF-015, RQ-003)

- **Atalhos:** Espaço ou Enter revela; 1, 2, 3 e 4 dão Errei, Difícil, Bom e Fácil; depois de Errei com explicação, Enter segue para o próximo (a explicação aparece **antes** de seguir, US2-1).
- **Escopo:** atalhos ativos só com o foco fora de campos de texto, declarados em `aria-keyshortcuts` e exibidos nos botões.
- **Foco:** vai para a frente de cada cartão novo e para o título do fechamento.
- **Anúncio:** resultado discreto por `aria-live="polite"` ("Revisado. Próximo cartão." / "Revendo este cartão.").
- **Movimento:** transições respeitam `prefers-reduced-motion`, e nenhuma espera animação para mostrar o próximo cartão.
- **Trilha:** estados de nó por forma, ícone e texto, nunca só por cor; navegável por teclado; a partir de 320 px sem rolagem horizontal.

## Contratos

O contrato completo está em [`contracts/openapi.yaml`](contracts/openapi.yaml), validado com `openapi-spec-validator`:

| Método e caminho | Uso | História |
|---|---|---|
| `GET /api/v1/trilha` | Nós, nó atual, disponíveis e próximo vencimento | US3, US4 |
| `POST /api/v1/licoes` | Começar ou continuar a lição | US1, US4 |
| `GET /api/v1/licoes/{licaoId}` | Estado da lição (outra aba, fechamento) | US1 |
| `POST /api/v1/apresentacoes/{apresentacaoId}/revelacao` | Revela o verso | US1 |
| `POST /api/v1/apresentacoes/{apresentacaoId}/avaliacao` | Autoavaliação, próximo ou fechamento, explicação ao errar | US1, US2 |

- **Códigos de erro novos** (o enum `Erro.codigo` é cumulativo), todos `409`: `sem_cartoes_disponiveis`, `licao_encerrada`, `revelacao_pendente`, `apresentacao_ja_avaliada`, `cartao_indisponivel` e `limite_novos_atingido`. Reaproveitados: `idempotencia_divergente` (004), `recurso_nao_encontrado`, `dados_invalidos` e `cursor_invalido`.
- **Isolamento:** as 3 rotas com `{licaoId}` ou `{apresentacaoId}` entram na tabela de `tests/security/test_isolamento_rotas.py` (DTEC 019).
- **Verso:** só a revelação devolve o verso; um teste percorre todas as respostas das rotas da 005 e verifica que nenhuma outra o contém.
- **Cache:** leituras com `Cache-Control: no-store`.

## Dados

- **Entidades e regras:** detalhadas em [data-model.md](data-model.md). O [esquema inicial](../../arquitetura/esquema-inicial.dbml) foi atualizado com `numero` na conclusão, `encerrada_em`, a lição aberta única, `licoes_cartoes`, `apresentacoes`, os campos novos de `revisoes`, as FKs compostas e o índice `cartoes_id_usuario`.
- **Migração `0006_licoes_revisoes`:** revisada à mão; sobe e desce nos testes; a descida é recusada se houver revisões.
- **Retenção:** exclusão física (RN-14). Revisões permanecem depois da exclusão do cartão, com `cartao_id` nulo; o plano da lição sai em cascata.
- **Dados de teste:** cartões manuais fictícios em contas `@exemplo.com`, estados do FSRS fabricados e relógio controlado (regra 10).

## Estratégia de testes

Marcadores obrigatórios da 001 (`unit`, `integration`, `functional`, `security`, `adversarial`). Cada teste cita no nome ou na *docstring* o requisito, o cenário ou o CS que cobre.

- **Unitários (`unit`):**
  - **Dia de estudo (DTEC 048):** virada às 4h; fusos com horário de verão (hora repetida e inexistente); com Hypothesis, `inicio_dia(dia_estudo(t)) <= t < proxima_virada(t)` para qualquer instante e fuso.
  - **Elegibilidade (CS-003):** cartão em revisão vencendo 1 µs antes e na própria virada; passo curto vencido e não vencido; novo; suspenso, aguardando revisão e recusado fora; com Hypothesis, nenhum elegível com vencimento depois da próxima virada.
  - **Montagem:** ordem dos devidos (mais atrasado primeiro, desempate por `id`); novos por `entrada_estudo_em`; limite restante; limite zero (só devidos); menos disponíveis que o tamanho.
  - **Próximo e término:** passo curto vencido antes do previsto; dois passos curtos (o mais antigo primeiro); só passos não vencidos conclui; Errei repetido não impede a conclusão; posição não muda na reapresentação.
  - **Duração:** limites `[0, (agora − exibida_em) + 2 s]`.
  - **Dominado:** limiar exato; queda posterior não apaga `dominado_em`; `tornou_dominado` só na primeira vez.
  - **Mapeamento de notas:** Errei a Fácil = `Rating.Again` a `Rating.Easy`.
- **Contrato da biblioteca (`unit`, pasta `contrato/fsrs`):**
  - `fsrs.scheduler.random` existe e é chamável na versão fixada; uma revisão com *fuzz* sorteia exatamente uma vez;
  - **CS-001:** uma sequência de referência (20 revisões, incluindo *Review* com intervalos longos) executada pelo adaptador e pela biblioteca num subprocesso limpo, com `random.seed(semente)` e os mesmos parâmetros: vencimentos, estabilidades e dificuldades idênticos;
  - **RQ-004:** reproduzir uma revisão gravada a partir do estado antes, da versão dos parâmetros e da semente dá o mesmo estado depois.
- **Integração (`integration`):**
  - **Concorrência da abertura:** 10 `POST /licoes` simultâneos criam uma lição só.
  - **Limite sob concorrência:** duas avaliações de novos em paralelo com 1 vaga: uma registra e a outra recebe `409 limite_novos_atingido`.
  - **Duas avaliações da mesma apresentação** com chaves diferentes: uma revisão só (CS-002).
  - **Mesma chave em paralelo:** uma revisão, e as duas respostas iguais.
  - **Escritas disjuntas (DTEC 037):** edição de conteúdo da 003 em paralelo com a avaliação: as duas mudanças ficam.
  - **Migração `0006`:** sobe e desce; descida recusada com revisões.
  - **`CHECK`, FKs e índices parciais:** `numero` só com conclusão; conclusão e encerramento exclusivos; avaliação só com revelação; FKs compostas recusam cartão de outro estudante; `SET NULL (cartao_id)` preserva `usuario_id`.
  - **Cascata:** excluir cartão, fonte ou matéria durante a lição remove previstos e apresentações e mantém as revisões.
  - **Imutabilidade:** nenhuma rota altera uma revisão; teste de arquitetura sobre o repositório.
  - **Evento:** um ouvinte de teste recebe `RevisaoRegistrada` com os campos certos, na mesma transação (falha do ouvinte desfaz a revisão).
  - **Exclusão da conta:** o teste de catálogo da 001 continua verde com as tabelas novas preenchidas.
- **Contrato da API:** o OpenAPI gerado contém o `contracts/openapi.yaml`, e toda resposta de erro observada valida contra `Erro`.
- **Funcionais (`functional`):** um teste por cenário de aceitação, de ponta a ponta pela API, com cookies, CSRF e relógio controlado:
  - **US1:** cenários 1 a 6, incluindo o teste independente (12 novos, 3 devidos, lição de 10, limite de 20) e o passo curto que volta e o que fica para a próxima lição.
  - **US2:** cenários 1 a 3 com um cartão gerado (via fábrica da 004) e um manual sem explicação; o provedor simulado registra zero chamadas.
  - **US3:** cenários 1 a 3, com `sem_materias`, nós alcançados, `continuar` e `sem_disponiveis` com o próximo vencimento.
  - **US4:** cenários 1 e 2, com `extra = true` e "Continuar" ausente sem disponíveis.
  - **Casos de borda:** avaliação sem revelação; reenvio e duas abas; aba fechada com passo curto e retomada no mesmo dia; lição de dia anterior encerrada sem nó e novos sem consumo do limite; lição atravessando as 4h com revisões em dias diferentes; cartão excluído, suspenso e com fonte excluída durante a lição; cartão aceito durante a lição fora dela; retenção alterada durante a lição (próxima revisão usa a versão nova); limite zero; tamanho alterado durante a lição; Errei repetido.
  - **Reverificações obrigatórias (planos da 003 e da 004):** US1-1 da 003 (cartão novo entra na lição), US3-1 e CS-003 da 003 (suspenso fora da lição), US3-2 da 003 (reativado volta com o vencimento anterior) e US1-4 da 004 (aceito entra como novo, na ordem de aceitação), agora com lições reais.
  - **Desempenho (CS-004, servidor):** lição de 10 cartões repetida 30 vezes sobre Postgres real; p95 de avaliar e de revelar abaixo de 150 ms.
- **Segurança (`security`):**
  - **Isolamento:** duas contas nas 3 rotas com identificador e o teste que percorre as rotas (DTEC 019); lição e apresentação alheias respondem `404` idêntico ao de inexistente.
  - **Verso:** nenhuma resposta além da revelação contém o verso; a explicação só sai em Errei.
  - **Logs:** sem frente, verso nem explicação, verificado com captura.
  - **Proteções herdadas:** `401` sem sessão e `403` sem CSRF nas rotas novas.
- **Adversariais (`adversarial`):**
  - **Entradas:** nota fora do enum; `duracaoMs` negativa, enorme ou não inteira; chave inválida; campos extras; corpo acima de 64 KiB; cursor adulterado.
  - **Fluxo:** avaliar uma apresentação antiga já avaliada; avaliar a apresentação de uma lição encerrada; revelar e avaliar depois da exclusão do cartão; reenviar a mesma chave para outra apresentação.
  - **Concorrência:** avaliação em paralelo com a suspensão do cartão; avaliação em paralelo com a mudança do limite de novos para zero; `POST /licoes` em paralelo com a avaliação do último cartão.
- **Frontend (Vitest, Testing Library, MSW e `vitest-axe`):**
  - **Lição:** frente sem verso; botões de avaliação desabilitados antes da revelação; atalhos Espaço, Enter e 1 a 4; "revendo"; posição; explicação e "Ver evidência" recolhido depois de Errei; Enter para seguir; manual sem explicação segue direto; chave gerada uma vez por avaliação (o duplo clique reenvia a mesma); `409 apresentacao_ja_avaliada` sincroniza com `GET /licoes/{id}`.
  - **Fechamento:** revisões, dominados, passos curtos pendentes com o horário, "Continuar" ou próximo vencimento.
  - **Trilha:** convite inicial, nós, "Começar" e "Continuar", sem disponíveis com o horário no fuso; estados sem depender de cor.
  - **Acessibilidade:** axe sem violações; operação só por teclado (CS-004); `aria-live`; movimento reduzido.
- **Jornada:** a verificação manual da P1 e a medição do CS-004 no navegador estão no [quickstart](quickstart.md). O Playwright entra no final acadêmico (DTEC 014).
- **Casos de falha:** banco indisponível durante a avaliação (nada registrado; o reenvio com a mesma chave registra uma vez); atualização da biblioteca que mude o ponto de *fuzz* (o teste de contrato falha antes do merge).

## Observabilidade e operação

- **Eventos de log (structlog, JSON):**
  - `licao_iniciada`, com previstos, devidos, novos e `extra`;
  - `licao_retomada`; `licao_encerrada_virada`; `licao_concluida`, com revisões, distintos, dominados e passos curtos pendentes;
  - `revisao_registrada`, com nota, estados antes e depois, intervalo em dias, `primeira_do_dia`, `tornou_dominado` e `duracao_ajustada`;
  - `revisao_reenviada`; `avaliacao_recusada`, com o código;
  - `cartao_retirado_licao`, com o motivo (`indisponivel` ou `limite_novos`).

  Todos levam os `public_id` da lição, da apresentação e do usuário, nunca texto do cartão.
- **Saúde:** sem mudança em `/health`.
- **Runbook** (no quickstart): conferir por SQL as revisões de um dia e reproduzir uma revisão a partir do registro.

## Variáveis de ambiente

Nenhuma nova. O limiar de dominado é regra versionada em código (DTEC 055), e o tamanho da lição e o limite de novos são preferências do estudante (001).

## Riscos técnicos

| Risco | Consequência | Mitigação | Como verificar |
|---|---|---|---|
| Prazo de 15/10/2026 | US3 e US4 sem tempo | US1 com US2 primeiro; trilha simples (opção 1 da Q-001, se a equipe aprovar) | Quickstart da P1 funcionando antes da US3 |
| Símbolo interno `fsrs.scheduler.random` mudar | Fuzz fora do controle da semente; CS-001 quebrado | Versão fixada; teste de contrato bloqueia a atualização | `contrato/fsrs` na integração contínua |
| Virada das 4h com fuso e horário de verão | Lição ou limite no dia errado (CS-003) | Módulo único (DTEC 048); testes de propriedade; relógio injetável | Testes unitários e funcionais da virada |
| p95 acima de 300 ms | CS-004 reprovado | Uma ida e volta por transição; índices; orçamento de 150 ms no servidor | Teste de desempenho; roteiro do quickstart |
| *Deadlock* entre avaliação, abertura e edição | Erro intermitente | Ordem única das travas (DTEC 052); edição em colunas disjuntas | Testes de concorrência |
| Lição deixada aberta por dias | Usuário retoma lição antiga | Encerramento no `POST /licoes`, que a página chama ao carregar | Teste funcional do D-005 |
| Decisão da Q-001 tardia | Interface da trilha refeita | API neutra às três opções | Revisão da equipe em 14/10 |

## Complexidade e exceções

| Exceção | Por que é necessária | Alternativa mais simples rejeitada porque |
|---|---|---|
| Tabela `apresentacoes` | Revelação verificada no servidor (CB-22), duas abas na mesma apresentação, retomada | Revelação só no cliente não cumpre o RF-003 no servidor (Princípio IV) |
| `on delete cascade` de `licoes_cartoes` e `apresentacoes` para `cartoes`, contra a obrigação do `set null` da 003 | O plano da lição não é histórico; o cartão excluído sai do critério de término sozinho (CB-27) | `set null` deixaria linhas sem cartão que todo o domínio teria de filtrar; o histórico continua protegido pelo `set null` de `revisoes` |
| Substituição de `fsrs.scheduler.random` por gerador por contexto | Reprodutibilidade exata com o *fuzz* ligado (CS-001, RQ-004) | Semente no gerador global não é segura com *threads*; desligar o *fuzz* contraria o RF-005 |
| *Advisory lock* do estudante na abertura e na primeira revisão de novos | Uma lição aberta e o limite de novos sob concorrência | Só o índice único devolveria erro de violação em vez de `200` com a lição existente, e não protege a contagem do limite |
| Escrita do FSRS em `cartoes/agendamento.py`, chamada por `revisao` | Um único ponto para a DTEC 037 | `revisao` escrevendo em `cartoes` pelo ORM espalharia a regra das colunas disjuntas |

## Saídas do planejamento

- [`research.md`](research.md): DTEC 049 a 056. A decisão transversal deste planejamento está em [`../../research.md`](../../research.md): DTEC 048.
- [`data-model.md`](data-model.md): entidades, estados, restrições e validações.
- [`contracts/openapi.yaml`](contracts/openapi.yaml): contrato da API.
- [`quickstart.md`](quickstart.md): validação local, demonstração e medição do CS-004.
- **Propagação:**
  - o [`esquema-inicial.dbml`](../../arquitetura/esquema-inicial.dbml) foi atualizado;
  - a 004 (ainda não implementada) passa a usar `nucleo/dia_estudo.py` no limite de gerações e no orçamento (DTEC 048), sem mudança de comportamento; quem implementar primeiro cria o módulo.

### Obrigações registradas para as próximas specs

- **006:**
  - registrar o ouvinte de `RevisaoRegistrada` em `nucleo/eventos_revisao.py`, na mesma transação da revisão;
  - conceder XP só com `primeira_do_dia` e o bônus só com `tornou_dominado` (RN-18), com regra versionada própria;
  - criar `eventos_xp.cartao_id` com `on delete set null` (obrigação da 003) e reverificar a US3-3 da 003;
  - acrescentar XP e sequência ao `Fechamento` e à trilha como campos aditivos;
  - usar `nucleo/dia_estudo.py` (DTEC 048) na meta e na sequência.
- **007:** ler `dominado_em`, a estabilidade atual e as revisões por dia pelas consultas de `revisao` e `cartoes`.
- **012 (filtro por matéria):** acrescentar o filtro à elegibilidade (DTEC 051) e rever a unicidade da lição aberta (DTEC 050).
- **015 (tira-dúvidas):** ação secundária na apresentação, sem alterar o fluxo da avaliação.

O `tasks.md` só é criado depois da aprovação deste plano (portão "Plano aprovado").
