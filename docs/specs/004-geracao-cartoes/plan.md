# Plano de implementação

**Funcionalidade:** 004-geracao-cartoes (geração de cartões pela IA e revisão dos gerados)  
**Spec:** [spec.md](spec.md), aprovada em 12/10/2026  
**Data:** 13/10/2026 ([registro](../../prompts/2026-10-13-004-geracao-cartoes-plano.md))  
**Responsáveis:**

- Artur Lins: decisões técnicas e aprovações desta fase de documentação.
- Implementação e revisão do conjunto de avaliação (RQ-007, D-012): qualquer pessoa da equipe pode assumir. Quem assumir registra o nome abaixo antes da primeira execução do conjunto de avaliação (tarefa de abertura).
  - **Responsável pela implementação e revisor do conjunto de avaliação:** Artur Lins (registrado em 29/10/2026, T001).

**Status:** aprovado em 13/10/2026 por Artur Lins (equipe), com as DTEC 039 a 047

Este plano **reaproveita sem redefinir** o que as specs anteriores já definiram:

- da [001](../001-conta-acesso/plan.md) e das DTEC 015 a 018: a estrutura base, as camadas do backend, a hierarquia de erros (com `LimiteExcedido` 429 e `Retry-After`), o formato de erro, o camelCase, o `/api/v1`, a sessão, o CSRF, o registro `apagar_dados_usuario` e o teste de isolamento;
- da [002](../002-materias-fontes/plan.md): os domínios `materias` e `fontes`, os trechos (DTEC 029), as tarefas idempotentes e os jobs travados (DTEC 030), a exclusão sob concorrência (DTEC 031), o *advisory lock* por estudante (DTEC 032), o *polling* (DTEC 026) e os participantes da exclusão (DTEC 027);
- da [003](../003-cartoes-manuais/plan.md): a tabela `cartoes`, as regras de texto e de origem (`normalizar_texto_cartao`, `validar_limites`, `houve_mudanca`, `origem_apos_edicao`), o estado inicial do FSRS e a fronteira com a 004 (DTEC 036 a 038).

Aqui está só o que a 004 acrescenta.

## Resumo técnico

A geração fica no subpacote `cartoes/geracao/` do domínio `cartoes` ([arquitetura, seção 5.1](../../arquitetura/README.md#51-organização-mvc-por-domínio)). As chamadas ao provedor ficam no novo domínio `ia`, o único que conhece o PydanticAI e as chaves. Ele também guarda o aviso, a ciência e o consumo ([DTEC 039](../../research.md#decisão-dtec-039-aviso-e-ciência-do-uso-de-provedor-de-ia-externo) e [DTEC 040](../../research.md#decisão-dtec-040-consumo-orçamento-e-limites-operacionais-da-ia)).

**Pedido.** `POST /fontes/{id}/geracoes` passa, numa transação, por:

1. idempotência;
2. ciência do aviso;
3. fonte concluída;
4. uma geração por fonte;
5. limite diário e orçamento, sob *advisory lock*;
6. trechos ainda não cobertos.

Depois cria a geração `pendente` e enfileira `gerar_cartoes` ([DTEC 044](research.md#decisão-dtec-044-pedido-de-geração-sob-reenvio-e-concorrência)).

**Geração.** O worker:

1. escolhe uma janela de trechos não cobertos, de até 30 mil caracteres ([DTEC 041](research.md#decisão-dtec-041-janela-de-trechos-cobertura-e-não-repetição));
2. chama o agente gerador fora de qualquer transação;
3. aplica os portões determinísticos (estrutura, vínculo, citação literal e cobertura lexical) e uma juíza que só reprova ([DTEC 042](research.md#decisão-dtec-042-validação-estrutural-e-de-sustentação));
4. publica tudo de uma vez, com a fonte travada `FOR SHARE`, depois do filtro de repetição. Uma falha técnica termina em `falhou`, com código e sem nenhum cartão parcial ([DTEC 043](research.md#decisão-dtec-043-execução-estados-e-falhas-da-geração)).

**Revisão.** A revisão é por geração. Aceitar, editar e aceitar, recusar (com motivo opcional) e aceitar todos são transições de situação idempotentes pelo próprio estado, e reutilizam as regras da 003 ([DTEC 045](research.md#decisão-dtec-045-revisão-dos-cartões-gerados)). Os descartados ficam guardados só para análise e saem em toda exclusão ([DTEC 046](research.md#decisão-dtec-046-participante-da-exclusão-descartes-e-retenção)). A defesa contra instruções embutidas e o conjunto de avaliação estão na [DTEC 047](research.md#decisão-dtec-047-instruções-embutidas-contradições-e-avaliação).

**Riscos principais:**

- o prazo de 15/10/2026;
- um cartão publicado sem sustentação (Princípio I);
- os limites da camada gratuita do provedor;
- a contagem divergente na exclusão de fontes;
- a cobertura lenta de fontes grandes. A demonstração usa PDFs pequenos, e a limitação é explicada ao PO.

A ordem US1 com US4 (P1) → US3 → US2 entrega primeiro a geração com as falhas tratadas, que é o critério de pronto da US1.

## Contexto técnico

- **Linguagem e versão:** as da 001: Python 3.13 com uv; TypeScript *strict* em Node 24 LTS com npm.
- **Dependências novas do backend** (já aprovadas nas DTEC 007 e 011, que entram agora no `pyproject.toml`):
  - `pydantic-ai-slim` com os extras `google` e `groq`;
  - `pydantic-evals`, no grupo de desenvolvimento.

  As versões ficam fixadas no `uv.lock`. Nenhuma dependência fora da stack.
- **Dependências novas do frontend:** nenhuma. O aviso usa o `Dialog` do React Aria (DTEC 016), o acompanhamento usa o `refetchInterval` do TanStack Query (DTEC 026), e o "editar e aceitar" reaproveita o painel da 003.
- **Persistência** (migração `0005_geracao_cartoes`, [modelo de dados](data-model.md)):
  - as tabelas `geracoes`, `geracoes_trechos`, `evidencias_cartoes`, `cartoes_descartados`, `consumo_ia` e `ciencias_aviso_ia`;
  - os enums `estado_geracao`, `codigo_falha_geracao`, `motivo_recusa` e `motivo_descarte`;
  - os valores `aguardando_revisao` e `recusado` em `situacao_cartao`;
  - as colunas `geracao_id` e `motivo_recusa` e os `CHECK` novos em `cartoes`.
- **Provedor:**
  - Gemini na camada gratuita como principal, e Groq como alternativo por configuração (DTEC 007);
  - nos testes, o adaptador simulado do PydanticAI (`FunctionModel` e `TestModel`), com `ALLOW_MODEL_REQUESTS = False`;
  - o modelo padrão (`IA_MODELO_GERACAO`) é conferido na implementação contra a lista vigente da camada gratuita, e o escolhido fica registrado no relatório de avaliação.
- **Testes:**
  - pytest com pytest-asyncio, httpx, Hypothesis e Postgres real;
  - o conjunto de avaliação com pydantic-evals no marcador `avaliacao_ia`, fora da suíte que bloqueia o merge (DTEC 011);
  - no frontend, Vitest, Testing Library, MSW e `vitest-axe`.
- **Plataforma de execução:** os serviços do Compose das specs anteriores. O worker passa a ter as variáveis do provedor. Nenhum serviço nem volume novo.
- **Limites de desempenho:**
  - Uma geração de 10 cartões termina em até 2 minutos com o provedor disponível (CS-006), independentemente do tamanho da fonte, porque cada geração envia no máximo `GERACAO_JANELA_MAX_CARACTERES`.
  - O pedido e as ações da revisão respondem em até 200 ms no percentil 95, no ambiente local.
  - O filtro de repetição numa matéria de 3 mil cartões leva menos de 100 ms.
- **Escala prevista:** dezenas de estudantes, até 20 gerações por estudante por dia, e de centenas a poucos milhares de cartões por matéria.

## Verificação da constituição

| Princípio | Como o plano atende | Evidência prevista |
|---|---|---|
| I Fontes exclusivas | Janela só com trechos da fonte pedida (RF-005); citação literal e cobertura lexical determinísticas; juíza que só reprova; vínculo por rótulos locais; selo derivado e "Fonte apagada" | Testes unitários dos portões; testes adversariais com o provedor simulado; CS-001 a CS-004 no conjunto de avaliação |
| II Proteção e isolamento | Ciência versionada antes de qualquer envio (DTEC 039); FKs compostas para matéria e fonte; 8 rotas novas com identificador na tabela de isolamento (DTEC 019); nenhum conteúdo em logs nem em `consumo_ia`; descartados e recusados apagados com a fonte | Testes `security/` e `adversarial/`; teste de logs; teste de catálogo da exclusão da conta |
| III Verificação humana | O estudante decide cada cartão; o conjunto de avaliação é revisado por pessoa; DTEC 039 a 047 registradas para aprovação | Testes funcionais da US1; relatório de avaliação revisado |
| IV Servidor autoritativo | Limite, orçamento, ciência, cobertura, validação e ordem de entrada decididos no servidor; o estado da geração vem do banco | Testes de concorrência do pedido; testes funcionais |
| V Qualidade verificável | Portões determinísticos antes da juíza; conjunto com 15 casos ou mais; métricas versionadas por modelo e instruções; precisão com e sem a juíza | `avaliacao/` versionada; `traceability.md` |
| VI Entrega incremental | US1 e US4 (P1) demonstráveis com o provedor real ou simulado; US3 e US2 ampliam | `quickstart.md` |
| VII Rastreabilidade | Geração com provedor, modelo, versão das instruções e trechos (RF-017); DTEC com alternativas; registro da sessão | `docs/prompts/`, `traceability.md` |

Não há exceção aos princípios. As exceções técnicas estão em [Complexidade e exceções](#complexidade-e-exceções).

## Arquitetura e fluxo

### Dependências entre domínios

```text
cartoes/geracao ──(provedor, ciência, orçamento)──> ia
       │──(fonte do dono, trechos da janela: fontes/consultas.py)──> fontes ──> materias
       │──(regras de texto e origem)──> cartoes/dominio.py (003)
       └─ registra participante ──> nucleo/participantes_acervo
ia ── registra apagar_dados_usuario ──> nucleo/exclusao
```

- `ia` não importa nenhum domínio de negócio. Ele expõe `ia/cliente.py` (chamada com orçamento, timeout, teto da execução e registro do consumo) e `ia/aviso.py` (versão, texto e ciência).
- `fontes`, `materias` e `ia` não importam `cartoes`.
- `cartoes/geracao` lê os trechos só por `fontes/consultas.py` (leitura por dono e fonte), sem acessar o modelo ORM de `fontes`.
- Um teste de arquitetura verifica essas direções. Outro garante que `pydantic_ai` só é importado em `ia/` e em `cartoes/geracao/agentes.py` (definição dos agentes, que recebem o modelo do `ia/cliente.py`), e que as chaves e o provedor só são lidos em `ia/`.

### Fluxos da spec

| Fluxo | Passos principais |
|---|---|
| **Aviso (RF-002, US1-1)** | `GET /ia/aviso` → versão e texto do provedor configurado e se há ciência → a interface mostra o diálogo só sem ciência → `POST /ia/aviso/ciencia {versao}` (`409 aviso_desatualizado` se a versão mudou) → `204`. |
| **Uso (D-005)** | `GET /geracoes/uso` → `{limiteDia, usadasHoje, voltaEm, orcamentoDisponivel}` → a interface desabilita a ação com a explicação. |
| **Pedir cartões (US1-2, RF-001, RF-004, RF-019)** | DTO `{chaveIdempotencia}` → transação: fonte do dono `FOR SHARE` (`404`) → chave existente (`200` ou `409 idempotencia_divergente`) → ciência (`409 ciencia_aviso_pendente`) → fonte `concluido` (`409 fonte_nao_concluida`) → *advisory lock* `geracoes` → em andamento da fonte (`200`) → limite (`429 limite_geracoes_excedido`) → orçamento (`429 orcamento_ia_esgotado`) → trechos não cobertos (`409 sem_conteudo_novo`) → inserção `pendente` e enfileiramento → `202` com `Location`. |
| **Gerar (worker, US1, US4)** | Transação A (trava, `fonte_excluida` se a fonte sumiu, `processando`, janela, `geracoes_trechos`) → leitura dos trechos → gerador (`ia/cliente`) → portões 1 a 4 → juíza (portão 5) → transação B (trava da geração, `FOR SHARE` na fonte, *advisory lock* `publicacao_cartoes`, repetição, excedente, cartões em `aguardando_revisao` com estado de `fsrs.Card()`, evidências, descartados, `concluida`). Falhas: `falhou` com código, sem cartões. |
| **Acompanhar (RF-003)** | `GET /geracoes/{id}` e `GET /materias/{id}/geracoes` a cada 2 s enquanto houver geração `pendente` ou `processando` (DTEC 026) → anúncio por `aria-live`. |
| **Revisar (US1-3 a 9)** | `GET /geracoes/{id}/cartoes` (aguardando revisão, com evidência) → `POST /cartoes/{id}/aceitacao` (com ou sem edição) / `POST /cartoes/{id}/recusa` (motivo opcional, completável depois) / `POST /geracoes/{id}/aceitacao` (todos os restantes, na ordem) → `200` com o cartão ou o resumo. |
| **Resumo e "Gerar mais" (US2)** | `GET /geracoes/{id}` com `aguardandoRevisao = 0` → resumo (publicados, aceitos, recusados) → "Gerar mais" = novo `POST /fontes/{fonteId}/geracoes` com uma nova chave → janela seguinte, sem repetição (DTEC 041) ou `409 sem_conteudo_novo` (CB-26). |
| **Evidência (US3, RF-018)** | `GET /cartoes/{id}/evidencias` (gerado em `aguardando_revisao`, `ativo` ou `suspenso`) → fonte, trecho, página e citação, ou "Fonte apagada" com a descrição da origem, sem o trecho. |
| **Exclusão de fonte (002, DTEC 027 e 046)** | `impacto_fonte` conta os aguardando revisão e os aceitos das gerações da fonte → `ao_excluir_fonte(modo)`: gerações em andamento → `falhou/fonte_excluida`; apaga os aguardando, os recusados e os descartados; no modo `excluir`, apaga os aceitos; no modo `manter`, os aceitos ficam com "Fonte apagada" e sem selo. |
| **Exclusão de matéria (002)** | `contar_por_materia` acrescenta `cartoes_aguardando_revisao`. A 003 apaga todos os cartões, e as gerações saem em cascata com a matéria. |
| **Lista de matérias (002, RF-002; design 9.3)** | `cartoesAguardandoRevisao` passa a vir do participante da 004. |
| **Excluir a conta (DTEC 021)** | `apagar_dados_usuario` das gerações (depois dos cartões, antes de `fontes` e `materias`) e do domínio `ia` (consumo e ciências). |

### Tarefas assíncronas criadas ou alteradas nesta spec

| Tarefa | Gatilho | Comportamento |
|---|---|---|
| `gerar_cartoes(geracao_id)` | Pedido de geração (mesma transação) | DTEC 043: `queueing_lock` e `lock` por geração; `RetryStrategy(max_attempts=2, exponential_wait=5)` só para erros transitórios; sem efeito se a geração não existir ou não estiver em `pendente` ou `processando`; publicação atômica com `FOR SHARE` na fonte |
| `reenfileirar_tarefas_travadas` | Periódica (núcleo, DTEC 030) | Sem mudança; passa a cobrir `gerar_cartoes` |

## Estrutura do repositório

Somente o que a 004 acrescenta às estruturas da [001](../001-conta-acesso/plan.md#estrutura-do-repositório), da [002](../002-materias-fontes/plan.md#estrutura-do-repositório) e da [003](../003-cartoes-manuais/plan.md#estrutura-do-repositório):

```text
compose.yaml                      # worker e api recebem as variáveis IA_* (sem serviço novo)
.env.example                      # + variáveis da tabela abaixo (chaves vazias, regra 9)
backend/
├── pyproject.toml                # + pydantic-ai-slim[google,groq]; pydantic-evals (dev); marcador avaliacao_ia
├── migracoes/versions/0005_geracao_cartoes.py  # ADD VALUE em bloco autocommit; enums, tabelas, CHECKs, índices
├── src/app/
│   ├── ia/                       # domínio novo
│   │   ├── configuracao.py       # provedor, modelos, timeout, orçamento; avisos por provedor
│   │   ├── cliente.py            # executar(agente, ...): orçamento, timeout, UsageLimits, consumo, erros
│   │   ├── provedores.py         # fábrica do modelo PydanticAI por provedor (gemini, groq, teste)
│   │   ├── aviso.py              # versão e texto do aviso; ciência
│   │   ├── rotas.py, dtos.py, mapeadores.py, servicos.py, repositorios.py, modelos.py, excecoes.py
│   │   └── registros.py          # apagar_dados_usuario (consumo e ciências)
│   ├── fontes/consultas.py       # + leitura de fonte e trechos por dono, para a geração (sem ORM exposto)
│   └── cartoes/
│       ├── dominio.py            # (003) reutilizado; + verificado e fonte apagada derivados (DTEC 045)
│       ├── repositorios.py       # (003) + left join com geracoes para o selo derivado
│       └── geracao/
│           ├── rotas.py          # /fontes/{id}/geracoes, /geracoes/..., /cartoes/{id}/aceitacao|recusa|evidencias
│           ├── dtos.py, mapeadores.py, servicos.py, repositorios.py, modelos.py, excecoes.py
│           ├── dominio.py        # janela, assinatura e repetição, transições da revisão, catálogo de falhas
│           ├── validacao.py      # portões 1 a 4 (funções puras) e normalização da citação
│           ├── agentes.py        # agente gerador e juíza (saídas tipadas), montagem do prompt com nonce
│           ├── instrucoes/       # gerador_v1.md, juiza_v1.md (versionadas)
│           ├── dados/palavras_vazias.txt  # palavras vazias do português (versionadas)
│           ├── tarefas.py        # gerar_cartoes
│           ├── analise.py        # taxa de aceitação e motivos (CS-005), usada pela avaliação
│           └── registros.py      # participante geracoes_cartoes e apagar_dados_usuario
└── tests/
    ├── conftest.py               # + ALLOW_MODEL_REQUESTS = False; provedor "teste"
    ├── fabricas_geracao.py       # fontes com trechos fictícios; FunctionModel por cenário
    ├── unit/geracao/             # janela, assinatura, portões (Hypothesis), transições, prompt, catálogo
    ├── unit/ia/                  # orçamento, dia de estudo, avisos configurados, classificação de erros
    ├── integration/geracao/      # tarefa, travas, migração, CHECKs, participante, repetição concorrente
    ├── functional/geracao/       # cenários da US1 a US4 pela API, com o worker executado no teste
    ├── functional/fontes/, functional/materias/, functional/cartoes/  # + reexecuções com dados reais
    ├── security/, adversarial/   # + rotas novas; injeção, citação inventada, payloads, concorrência
    ├── arquitetura/              # + direções de ia e cartoes/geracao; pydantic_ai só onde permitido
    └── avaliacao_ia/             # marcador avaliacao_ia (fora do merge): casos, dados fictícios, relatório
frontend/src/
├── rotas/_autenticado/materias/$materiaId.geracoes.$geracaoId.tsx  # revisão de uma geração
├── funcionalidades/geracao/      # botão "Pedir cartões", diálogo do aviso, estado da geração,
│                                 # revisão, cartão em revisão, motivo da recusa, resumo, uso
├── funcionalidades/cartoes/      # (003) painel reaproveitado no modo "editar e aceitar"
└── componentes/ui/               # + PainelEvidencia, CitacaoDestacada
docs/specs/004-geracao-cartoes/avaliacao/  # relatórios versionados do conjunto de avaliação
```

**Decisão de estrutura:**

- **Domínio `ia`:** segue a arquitetura (5.1 e 5.4) e é a única porta para o provedor (RQ-001). Trocar o provedor muda só `IA_PROVEDOR` e as chaves.
- **`cartoes/geracao/`:** é um subpacote de `cartoes`, porque a arquitetura põe a geração e a revisão no domínio `cartoes` (seção 5.1), e porque ele reutiliza o `dominio.py` da 003 sem cópia.
- **Instruções e palavras vazias como arquivos versionados:** uma mudança neles aparece no diff e muda a versão das instruções (RQ-006).
- **Tela de revisão:** é uma rota filha da matéria ([design, seção 9.6](../../base-specs/design.md)). A página da matéria mostra o aviso "N cartões aguardando revisão", com o atalho para as gerações pendentes, e o botão "Pedir cartões" em cada fonte `concluido` (seção 9.4).

## Contratos

O contrato completo está em [`contracts/openapi.yaml`](contracts/openapi.yaml), validado com `openapi-spec-validator`:

| Método e caminho | Uso | História |
|---|---|---|
| `GET /api/v1/ia/aviso` | Aviso do provedor configurado e ciência | US1 |
| `POST /api/v1/ia/aviso/ciencia` | Registra a ciência da versão lida | US1 |
| `GET /api/v1/geracoes/uso` | Limite diário, uso e orçamento | US1, US2 |
| `POST /api/v1/fontes/{fonteId}/geracoes` | Pede cartões de uma fonte (e "Gerar mais") | US1, US2 |
| `GET /api/v1/materias/{materiaId}/geracoes` | Gerações em andamento, com cartões aguardando revisão e a última de cada fonte | US1 |
| `GET /api/v1/geracoes/{geracaoId}` | Estado, falha e resumo | US1, US2, US4 |
| `GET /api/v1/geracoes/{geracaoId}/cartoes` | Cartões aguardando revisão, com evidência | US1 |
| `POST /api/v1/geracoes/{geracaoId}/aceitacao` | Aceitar todos | US1 |
| `POST /api/v1/cartoes/{cartaoId}/aceitacao` | Aceitar, ou editar e aceitar | US1 |
| `POST /api/v1/cartoes/{cartaoId}/recusa` | Recusar, com motivo opcional | US1 |
| `GET /api/v1/cartoes/{cartaoId}/evidencias` | Evidência e descrição da origem | US3 |

- **Códigos de erro novos** (o enum `Erro.codigo` é cumulativo):
  - `ciencia_aviso_pendente`, `aviso_desatualizado`, `fonte_nao_concluida`, `idempotencia_divergente`, `sem_conteudo_novo` e `cartao_ja_decidido` (409);
  - `limite_geracoes_excedido` e `orcamento_ia_esgotado` (429, com `Retry-After`).
- **Esquema `Cartao` da 003:** `verificado` passa a ser derivado também da fonte (DTEC 045), e a 004 acrescenta o campo `geracao`, `{geracaoId, fonteTitulo, fonteApagada}` ou nulo. É uma mudança aditiva.
- **Isolamento:** as 8 rotas com `{fonteId}`, `{materiaId}`, `{geracaoId}` ou `{cartaoId}` entram na tabela de `tests/security/test_isolamento_rotas.py` (DTEC 019). Uma geração, um cartão ou uma fonte de outro estudante respondem `404` idêntico ao de inexistente.
- **Cache:** todas as leituras com `Cache-Control: no-store`.
- **Sem conteúdo do provedor:** nenhuma resposta expõe o provedor além do nome no aviso, nem as instruções, os *tokens* ou os descartados.

## Dados

- **Entidades e regras:** detalhadas em [data-model.md](data-model.md). O [esquema inicial](../../arquitetura/esquema-inicial.dbml) foi atualizado com:
  - `codigo_falha` no lugar de `motivo_falha`;
  - a FK composta da geração para a fonte com `SET NULL (fonte_id)`;
  - o índice único parcial por fonte em andamento;
  - `geracoes_trechos`, `cartoes_descartados` e `ciencias_aviso_ia`;
  - `motivo_recusa`;
  - os deslocamentos da citação nas evidências;
  - os `CHECK` novos de `cartoes`.
- **Migração `0005_geracao_cartoes`:** revisada à mão.
  - Os valores `aguardando_revisao` e `recusado` entram com `ALTER TYPE ... ADD VALUE` num `autocommit_block` do Alembic, antes dos `CHECK` que os citam, porque o PostgreSQL não usa o valor novo antes do *commit*.
  - A descida remove tabelas, colunas e enums novos, mas não os valores de enum, que o PostgreSQL não remove. Ela recusa a descida se houver cartão `aguardando_revisao` ou `recusado`.
- **Retenção e descarte:** exclusão física (RN-14).
  - Recusados e descartados saem junto com a fonte, em qualquer modo, e com a matéria e a conta.
  - Gerações e consumo permanecem sem conteúdo depois da exclusão da fonte.
- **Dados de teste:**
  - fontes fictícias com trechos de biologia e de história escritos pela equipe (ex.: "A mitocôndria produz ATP por respiração celular."), com e sem página;
  - um trecho com instrução embutida e um par de trechos contraditórios;
  - um texto longo de 2 MB gerado por fábrica, para o CS-006 e a janela.

  Nenhum dado pessoal real (regra 10).

## Estratégia de testes

Marcadores obrigatórios da 001 (`unit`, `integration`, `functional`, `security`, `adversarial`), mais `avaliacao_ia` (fora do merge). Cada teste cita no nome ou na *docstring* o requisito, o cenário ou o CS que cobre.

- **Unitários (`unit`):**
  - **Janela:** ordem, teto de caracteres, trecho nunca cortado, pelo menos um trecho, fonte esgotada.
  - **Assinatura e repetição:** NFC, acentos, caixa, palavras vazias e radicais. Com Hypothesis: a assinatura é idempotente, e a similaridade de Jaccard é simétrica e vai de 0 a 1. Também: frente igual, limiar exato e paráfrase com palavras em comum.
  - **Portões:**
    - estrutura com os limites da 003 e a explicação obrigatória;
    - rótulo inexistente;
    - citação literal com espaços, caixa e aspas tipográficas diferentes;
    - citação inventada;
    - deslocamentos corretos (`trecho[inicio:fim]` normalizado igual à citação);
    - cobertura no limiar e abaixo dele, com números e uma resposta de uma palavra.
  - **Juíza:** índice ausente vira reprovação; a juíza nunca aprova o que um portão reprovou.
  - **Transições da revisão:** a tabela completa (situação × ação × corpo), incluindo os `409 cartao_ja_decidido`.
  - **Ordem:** os deslocamentos de microssegundos do "Aceitar todos".
  - **Dia de estudo:** virada das 4h, fuso e horário de verão, para o limite e o orçamento.
  - **Prompt:** *nonce* diferente a cada chamada, trechos só dentro dos delimitadores, frentes vizinhas incluídas.
  - **Catálogo de falhas:** classificação dos erros do provedor em transitório, `limite_provedor` e `resposta_invalida`.
  - **Avisos:** todo provedor configurado tem versão e texto.
  - **Configuração:** a aplicação não sobe com limiar fora de (0, 1], janela abaixo do tamanho máximo de um trecho, ou `GERACAO_CARTOES_MAX` acima de 10.
- **Integração (`integration`):**
  - **Tarefa:** com o `FunctionModel`, do pedido ao `concluida`. Também: reexecução depois de uma morte simulada entre A e B (sem duplicar cartões nem trechos), geração inexistente, geração já concluída e fonte apagada entre A e B (nada publicado).
  - **Travas:** a exclusão da fonte em paralelo à transação B se serializa. Ou os cartões nascem antes e entram no impacto, ou nada é publicado.
  - **Repetição concorrente:** duas gerações de fontes diferentes da mesma matéria propondo o mesmo cartão publicam um só.
  - **Pedido:**
    - 20 pedidos simultâneos com 19 gerações no dia: só 1 é aceito;
    - 2 pedidos simultâneos para a mesma fonte: uma geração só;
    - mesma chave em paralelo: uma geração só.
  - **Migração `0005`:** sobe e desce, e a descida é recusada com cartão gerado.
  - **`CHECK` e FKs:** situações × origem; `motivo_recusa`; explicação obrigatória; `codigo_falha` coerente; geração com fonte de outra matéria recusada pela FK composta; `SET NULL (fonte_id)` mantém `materia_id`.
  - **Participante:** `impacto_fonte` e `ao_excluir_fonte` nos dois modos, `contar_por_materia` e geração em andamento interrompida.
  - **Consumo:** uma linha por chamada, com sucesso ou falha, e sem conteúdo.
  - **Orçamento:** conferido antes da segunda chamada.
  - **Exclusão da conta:** o teste de catálogo da 001 continua verde com todas as tabelas novas preenchidas.
- **Contrato:** o OpenAPI gerado contém o `contracts/openapi.yaml`, e toda resposta de erro observada valida contra `Erro`.
- **Funcionais (`functional`):** um teste por cenário de aceitação, de ponta a ponta pela API, com cookies, CSRF e o worker executado no próprio teste com o provedor simulado:
  - **US1:** cenários 1 a 9. Os 4 aceitos ficam ativos, com origem e evidência corretas (teste independente). A entrada como cartão novo é verificada pelo estado gravado e reverificada com a lição real pela 005.
  - **US2:** cenários 1 a 3. Três "Gerar mais" seguidos sem nenhuma repetição, pelo filtro, e a fonte esgotada com `409 sem_conteudo_novo` sem chamar o provedor.
  - **US3:** cenários 1 a 3, com "Fonte apagada" depois da exclusão no modo `manter`.
  - **US4:** cenários 1 a 6, com cada cenário do `FunctionModel`: erro, 429, resposta malformada, cartão sem trecho, citação inventada, cartão fora do assunto, instrução obedecida, contradição e todos descartados.
  - **Casos de borda:** clique duplo, nova geração com uma em andamento, fonte excluída durante a geração, fonte não concluída, fonte com um parágrafo, limite atingido com `Retry-After`, falha que não conta no limite, nova geração com cartões aguardando, "Aceitar todos" duas vezes, edição com frente vazia e 15 cartões devolvidos.
  - **Reexecuções obrigatórias (DTEC 038 e 027):**
    - a US2-2 da 003 com geração real: editar um cartão aceito mantém a evidência acessível;
    - o caso de borda da 003 "aguardando revisão fora da lista", com dados reais;
    - os testes funcionais da US2 e da US3 da 002, com o participante da 004. As contagens exibidas devem ser iguais às apagadas (CS-004 da 002), e no modo `manter` os aceitos ficam com "Fonte apagada" e sem selo.
- **Segurança (`security`):**
  - **Isolamento:** duas contas nas 8 rotas com identificador e o teste que percorre as rotas (DTEC 019).
  - **Fonte alheia:** a geração recusa com `404`, e nenhum trecho alheio entra na janela.
  - **Ciência:** sem ela, nenhuma chamada ao provedor (o provedor simulado registra zero chamadas).
  - **Logs e consumo:** sem texto de trechos, cartões, instruções nem citações, verificado com captura.
  - **Respostas de erro:** sem detalhes do provedor (RQ-005).
  - **Proteções herdadas:** `401` sem sessão e `403` sem CSRF nas rotas novas.
  - **Isolamento das rotas da 003:** aguardando revisão e recusado continuam com `404` nelas.
- **Adversariais (`adversarial`):**
  - **Injeção (CB-15):** um trecho que manda mudar de assunto, revelar as instruções, inventar página ou fechar o delimitador. O provedor simulado "obedece", e nenhum cartão é publicado.
  - **Saídas extremas:** 15 cartões; campos com 50 mil caracteres; marcação e script nos campos (publicados como texto, RQ-001 da 003); rótulos inventados (`T999`); citação vazia.
  - **Entradas:** chave de idempotência inválida; motivo fora do enum; corpo de aceitação com campos extras (`extra="forbid"`); corpo acima de 64 KiB.
  - **Concorrência:**
    - aceitar e recusar o mesmo cartão em paralelo: um efeito só, e o outro recebe `409`;
    - "Aceitar todos" em paralelo com uma recusa: o cartão recusado não é aceito;
    - aceitar durante a exclusão da fonte no modo `excluir`: ou o aceito entra no impacto e é apagado, ou a aceitação recebe `404`.
- **Avaliação (`avaliacao_ia`, fora do merge):** DTEC 047, com no mínimo 15 casos e o relatório versionado. O CS-001 é calculado automaticamente, e os CS-002 a CS-004 e o CS-007 dependem do revisor (RQ-007). O CS-005 sai da consulta de análise.
- **Frontend (Vitest, Testing Library, MSW e `vitest-axe`):**
  - **Aviso:** diálogo só sem ciência, foco preso, "Entendi e gerar" registra e pede, e "Cancelar" não pede.
  - **Pedido:** "Pedir cartões" só em fonte `concluido`; desabilitado com a explicação e o horário do limite; chave gerada uma vez por intenção (o clique duplo reenvia a mesma).
  - **Acompanhamento:** estados com anúncio por `aria-live`; o *polling* para no estado final.
  - **Revisão:**
    - frente, verso, explicação e "Ver trecho";
    - aceitar, editar e aceitar (painel da 003), e recusar com os quatro motivos de um clique;
    - foco no próximo cartão depois de cada decisão;
    - "Aceitar todos" depois da lista;
    - resumo com "Gerar mais";
    - mensagens distintas para falha técnica, sem cartões sustentados e sem conteúdo novo.
  - **Evidência:** citação destacada, página só quando conhecida, e "Fonte apagada" sem o trecho.
  - **Acessibilidade:** axe sem violações e operação só por teclado (RQ-004).
- **Jornada:** a verificação manual da P1 e o CS-006 estão no [quickstart](quickstart.md). O Playwright entra no final acadêmico (DTEC 014).
- **Casos de falha:**
  - provedor fora do ar: `falhou/provedor_indisponivel` depois de 2 novas tentativas, nada publicado;
  - banco indisponível na transação B: nova tentativa da fila, sem duplicar;
  - chave do provedor ausente no ambiente: a aplicação sobe com `IA_PROVEDOR=teste`, ou falha ao iniciar com uma mensagem clara se o provedor real estiver configurado sem a chave.

## Observabilidade e operação

- **Eventos de log (structlog, JSON):**
  - `geracao_pedida`, com `reenvio` e `existente`;
  - `geracao_recusada`, com o código;
  - `geracao_iniciada`, com o número de trechos e de caracteres da janela;
  - `geracao_concluida`, com as quantidades por motivo de descarte, os pontos contraditórios e a duração;
  - `geracao_falhou`, com o código e a tentativa;
  - `chamada_ia`, com a operação, o provedor, o modelo, a versão, os *tokens*, a latência e o sucesso;
  - `cartao_aceito`, com `editado`;
  - `cartao_recusado`, com o motivo;
  - `cartoes_aceitos_em_lote`, com a quantidade;
  - `ciencia_registrada`, com a versão;
  - `geracoes_interrompidas` e `cartoes_gerados_apagados`, na exclusão da fonte.

  Todos levam o `public_id` da geração, do cartão e do usuário, nunca texto.
- **Saúde:** `/health/ready` não chama o provedor (o custo seria da camada gratuita). A disponibilidade do provedor aparece nas gerações `falhou/provedor_indisponivel` e no log.
- **Runbook** (no quickstart):
  - provedor fora do ar ou cota esgotada;
  - troca de Gemini para Groq por variável, com o novo aviso pedindo ciência de novo e o conjunto de avaliação reexecutado (RQ-006);
  - consulta de consumo do dia.

## Variáveis de ambiente (acréscimos ao `.env.example`)

| Variável | Uso | Padrão no exemplo |
|---|---|---|
| `IA_PROVEDOR` | DTEC 007 e 040 (`gemini`, `groq`, `teste`) | `teste` |
| `IA_MODELO_GERACAO`, `IA_MODELO_VERIFICADOR` | DTEC 040 | Conferidos na implementação contra a camada gratuita vigente |
| `GEMINI_API_KEY`, `GROQ_API_KEY` | Chaves do provedor (só no `.env`, regra 9) | vazias |
| `IA_TIMEOUT_SEGUNDOS` | DTEC 040 | `60` |
| `IA_ORCAMENTO_TOKENS_DIA` | RQ-002, DTEC 040 | `300000` |
| `GERACAO_LIMITE_DIA` | D-005, RF-019 | `20` |
| `GERACAO_CARTOES_MAX` | D-002 (teto 10) | `10` |
| `GERACAO_JANELA_MAX_CARACTERES` | DTEC 041 | `30000` |
| `GERACAO_LIMIAR_COBERTURA` | DTEC 042 | `0.6` |
| `GERACAO_LIMIAR_REPETICAO` | DTEC 041 | `0.7` |
| `GERACAO_VERIFICADOR_IA` | DTEC 042 | `true` |

A aplicação valida todas ao iniciar. Com `IA_PROVEDOR=teste` fora dos testes e do desenvolvimento, ela não sobe.

## Riscos técnicos

| Risco | Consequência | Mitigação | Como verificar |
|---|---|---|---|
| Prazo de 15/10/2026 | US2 e US3 sem tempo | US1 com US4 primeiro (P1); tarefas por história; provedor simulado desde o primeiro teste | Quickstart da P1 funcionando antes da US3 |
| Cartão publicado sem sustentação | Viola o Princípio I e o CS-004 | Portões determinísticos antes da juíza; publicação atômica; nada visível antes da validação | Testes adversariais; conjunto de avaliação |
| Camada gratuita do provedor esgotada ou instável | Demonstração sem geração | Novas tentativas, `limite_provedor` visível, Groq por variável, orçamento por estudante; demonstração com PDFs pequenos | Teste de 429 e de troca de provedor; quickstart |
| **Cobertura lenta de fontes grandes** | Uma fonte de 2 MB pede perto de 60 "Gerar mais", acima do limite de 20 por dia | Limitação registrada (DTEC 041); demonstração com PDFs pequenos; explicação ao PO; a geração da matéria inteira (010) é o caminho do final acadêmico | Quickstart; nota ao PO |
| Repetição por paráfrase sem palavras em comum | CS-007 reprovado pelo revisor | Passada única por trecho; frentes vizinhas no prompt; embeddings no final acadêmico | CS-007 no conjunto de avaliação |
| Limiares mal calibrados | Muitos descartes de cartões corretos, ou o contrário | Limiares por configuração; precisão com e sem a juíza no relatório | Relatório de avaliação |
| Contagem divergente na exclusão | Diálogo com números errados (CS-004 da 002) | Contagem pela geração; divisão de contagens com a 003 (DTEC 038); `FOR SHARE` na publicação | Reexecução dos testes funcionais da 002 |
| `ADD VALUE` usado na mesma transação | Migração falha | `autocommit_block` antes dos `CHECK` | Teste da migração `0005` |
| Chave do provedor exposta | Vazamento de segredo (regra 9) | Só no `.env`; `SecretStr`; mascaramento nos logs | Teste de logs; revisão do `.env.example` |
| Mudança de modelo sem reavaliar | Qualidade não verificada (RQ-006) | Versão gravada em cada geração; relatório por modelo e versão | Relatório de avaliação |

## Complexidade e exceções

| Exceção | Por que é necessária | Alternativa mais simples rejeitada porque |
|---|---|---|
| Domínio `ia` separado | Único ponto para provedor, chaves, orçamento e consumo (RQ-001, DTEC 040); reaproveitado pelo chat (014) | Chamar o provedor dentro de `cartoes` espalharia chaves e limites pelo código e seria refeito na 014 |
| Juíza além dos portões determinísticos | Lê sentido (negação, contradição) que regras lexicais não leem (DTEC 042) | Só portões deixariam passar afirmações com as mesmas palavras e sentido oposto; só a juíza não prova nada (Princípio V) |
| Tabela `geracoes_trechos` | Registro dos trechos usados (RF-017) e cobertura para a não repetição (DTEC 041) | Guardar a lista em JSON na geração impediria a consulta de cobertura por índice |
| `cartoes_descartados` com texto | Análise da qualidade com saídas reais (RF-007) | Só a contagem limitaria a melhoria das instruções ao conjunto de avaliação |
| FK composta com `SET NULL (fonte_id)` | Mesma matéria e dono garantidos pelo banco, sem perder a geração ao apagar a fonte | FK simples permitiria uma geração apontando para a fonte de outra matéria |
| *Advisory lock* na publicação | Repetição entre gerações concorrentes da mesma matéria | Sem trava, duas fontes poderiam publicar o mesmo cartão ao mesmo tempo |

## Saídas do planejamento

- [`research.md`](research.md): DTEC 041 a 047. As decisões transversais deste planejamento estão em [`../../research.md`](../../research.md): DTEC 039 e DTEC 040.
- [`data-model.md`](data-model.md): entidades, estados, restrições e validações.
- [`contracts/openapi.yaml`](contracts/openapi.yaml): contrato da API.
- [`quickstart.md`](quickstart.md): validação local, demonstração e runbook.
- **Propagação:** foram atualizados com as decisões acima:
  - o [`esquema-inicial.dbml`](../../arquitetura/esquema-inicial.dbml);
  - a [arquitetura](../../arquitetura/README.md) (tarefa `gerar_cartoes` e seção 5.4);
  - o README e o modelo de dados da [spec 003](../003-cartoes-manuais/README.md): `verificado` e "Fonte apagada" dos gerados passam a ser derivados da geração (DTEC 045), com registro no histórico. A mudança no mapeador da 003 é feita por uma tarefa da 004.

### Obrigações registradas para as próximas specs

- **005:**
  - montar a lição só com cartões `ativo`: aguardando revisão e recusados nunca entram (RF-010 da 004);
  - os novos aceitos entram na ordem de `entrada_estudo_em` (RN-20);
  - exibir a explicação ao marcar "Errei" com o acesso a `GET /cartoes/{id}/evidencias` (EX-03, RN-16), sem nova chamada à IA;
  - reverificar a US1-4 da 004 (aceito entra como novo) com lições reais.
- **006:** nenhuma obrigação nova.
- **010 (geração da matéria inteira):** reutilizar a janela, a cobertura, os portões e o filtro de repetição. A geração com `fonte_id` nulo e a publicação em lotes ficam para essa spec.
- **014 (chat):** usar o `ia/cliente.py` (orçamento e consumo) e a ciência da DTEC 039 antes do primeiro envio. Registrar o participante dos índices e das citações.

O `tasks.md` só é criado depois da aprovação deste plano (portão "Plano aprovado").
