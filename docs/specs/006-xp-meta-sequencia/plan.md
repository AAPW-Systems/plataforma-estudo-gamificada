# Plano de implementação

**Funcionalidade:** 006-xp-meta-sequencia (XP, meta diária e sequência)  
**Spec:** [spec.md](spec.md), aprovada em 12/10/2026  
**Data:** 13/10/2026 ([registro](../../prompts/2026-10-13-006-xp-meta-sequencia-plano.md))  
**Responsáveis:**

- Artur Lins: decisões técnicas e aprovações desta fase de documentação.
- Implementação: qualquer pessoa da equipe pode assumir, e registra o nome abaixo antes da primeira tarefa.
  - **Responsável pela implementação:** *a definir no início da implementação*.

**Status:** em revisão, aguardando o portão "Plano aprovado", com a DTEC 057 (transversal) e as DTEC 058 a 063

Este plano **reaproveita sem redefinir** o que as specs anteriores já definiram (resumo em [`contexto-tecnico.md`](../../skills/contexto-tecnico.md)):

- da [001](../001-conta-acesso/plan.md) e das DTEC 015 a 018: a estrutura base, as camadas, a hierarquia e o formato de erro, a sessão, o CSRF, as preferências (`meta_diaria`, `limite_novos_dia`, `fuso`), o `PATCH /perfil`, o registro `apagar_dados_usuario` e o teste de catálogo;
- da [003](../003-cartoes-manuais/plan.md): suspender, reativar e excluir cartões, o participante dos cartões (DTEC 027 e 038) e a obrigação do `set null` nas FKs de histórico;
- da [005](../005-licao-trilha/plan.md): o evento `RevisaoRegistrada` na mesma transação, `primeira_do_dia`, `tornou_dominado`, `versao_regras`, `dominado_em`, a elegibilidade (DTEC 051), a avaliação idempotente (DTEC 052), as respostas `Trilha`, `Licao`, `Fechamento` e `ResultadoAvaliacao`, e o `nucleo/dia_estudo.py` (DTEC 048).

Aqui está só o que a 006 acrescenta.

## Resumo técnico

XP, meta e sequência ficam no domínio `gamificacao` ([arquitetura, seção 5.1](../../arquitetura/README.md#51-organização-mvc-por-domínio)). A 006 não cria rotas: ela reage a fatos e acrescenta campos às respostas da 005.

**XP.** Um ouvinte de `RevisaoRegistrada`, na transação da revisão, grava um evento `revisao` (10) quando a revisão tem `primeira_do_dia` e um evento `cartao_dominado` (25) quando tem `tornou_dominado`. Os valores vêm de uma regra versionada em código, e o total fica em cache em `usuarios.xp_total` ([DTEC 058](research.md#decisão-dtec-058-regra-de-valores-versionada) e [059](research.md#decisão-dtec-059-concessão-de-xp-idempotente-e-cache-do-total)).

**Meta.** A linha do dia em `dias_estudo` soma os cartões distintos e recalcula a meta efetiva com os restantes informados por um provedor que `revisao` registra no núcleo. Quando os revisados atingem a meta efetiva, o dia passa a `estudado`, de forma definitiva ([DTEC 057](../../research.md#decisão-dtec-057-disponibilidade-de-cartões-e-ganchos-de-alteração-no-núcleo) e [060](research.md#decisão-dtec-060-meta-efetiva-e-dia-estudado-sob-concorrência)).

**Sequência.** Os dias passados são liquidados na próxima escrita da gamificação, sem tarefa periódica. Os ganchos do núcleo liquidam antes de qualquer ação que altere a disponibilidade (suspender, reativar, excluir, mudar meta, limite de novos ou fuso), o que torna a reconstrução exata. Dias sem revisões e sem cartão disponível na virada são neutros ([DTEC 061](research.md#decisão-dtec-061-liquidação-dos-dias-passados-dia-neutro-e-sequência)). Datas puladas pela mudança de fuso também são neutras ([DTEC 062](research.md#decisão-dtec-062-mudança-de-fuso-e-horário-de-verão)).

**Exibição.** `ResumoGamificacao` entra na trilha, no fechamento e no resultado de cada avaliação, com `xpGanho` e `metaCumpridaAgora` para o anúncio discreto ([DTEC 063](research.md#decisão-dtec-063-exibição-contrato-aditivo-e-anúncio-acessível)).

**Riscos principais:**

- o prazo de 15/10/2026;
- a liquidação ter de ser exata em todos os caminhos que alteram a disponibilidade, o que exige ganchos chamados por domínios de outras specs;
- o orçamento de 150 ms da avaliação (CS-004 da 005).

A ordem US1 (XP, P1) → US2 (meta, P1) → US3 (sequência, P2) entrega primeiro o XP demonstrável sobre as revisões da 005 (Princípio VI).

## Contexto técnico

- **Linguagem e versão:** as da 001: Python 3.13 com uv; TypeScript *strict* em Node 24 LTS com npm.
- **Dependências novas:** nenhuma. `zoneinfo` e `dataclasses` são da biblioteca padrão. O Hypothesis já está na DTEC 014.
- **Persistência** (migração `0007_gamificacao`, [modelo de dados](data-model.md)):
  - os enums `tipo_evento_xp` e `situacao_dia`;
  - as tabelas `eventos_xp` e `dias_estudo`;
  - as colunas de gamificação de `usuarios`;
  - o índice único `revisoes_id_usuario`.
- **Testes:** pytest com pytest-asyncio, httpx, Hypothesis (com oráculo) e Postgres real; relógio injetável da 005; no frontend, Vitest, Testing Library, MSW e `vitest-axe`.
- **Plataforma de execução:** os serviços do Compose das specs anteriores. Nenhum serviço, volume, variável ou tarefa periódica novos.
- **Limites de desempenho:**
  - a avaliação continua em até 150 ms no percentil 95 no servidor (CS-004 da 005), já com a gamificação. O orçamento da 006 é de 25 ms: trava da linha do estudante, liquidação (na maioria das vezes sem nada a fazer), até dois `INSERT`, uma contagem de restantes e o *upsert* da linha do dia;
  - `GET /trilha` continua em até 200 ms no percentil 95 com 3 mil cartões ativos, também com 60 dias sem liquidar;
  - a liquidação de uma ausência de 365 dias leva até 100 ms, numa única inserção.
- **Escala prevista:** dezenas de estudantes; até centenas de linhas de `dias_estudo` e dezenas de milhares de eventos de XP por estudante ao longo do semestre.

## Verificação da constituição

| Princípio | Como o plano atende | Evidência prevista |
|---|---|---|
| I Fontes exclusivas | Não se aplica: nenhum conteúdo gerado, nenhuma chamada à IA | Teste funcional com o provedor simulado registrando zero chamadas nas rotas afetadas |
| II Proteção e isolamento | Todas as tabelas novas com `usuario_id` e FKs compostas com o dono; nenhuma rota nova; o resumo só lê o estudante da sessão; logs sem texto de cartão | Testes `security/`; teste de catálogo da exclusão da conta; teste de logs |
| III Verificação humana | Valores de D-001 registrados pela equipe; leitura de "disponível na virada" e de "data pulada" decididas na sessão; DTEC 057 a 063 para aprovação | Este plano; registro da sessão |
| IV Servidor autoritativo | XP, meta e sequência calculados só no servidor, na transação da revisão; idempotência herdada da 005 e repetida pelo banco (`(revisao_id, tipo)`); interface sem atualização otimista | Testes de reenvio, concorrência e propriedade (CS-001); teste de frontend sem valor antes da resposta |
| V Qualidade verificável | CS-001 e CS-003 por testes de propriedade; CS-002 por oráculo dia a dia com relógio controlado; axe nos componentes | `traceability.md`; quickstart |
| VI Entrega incremental | US1 (XP) demonstrável sozinha sobre as revisões da 005 | `quickstart.md` |
| VII Rastreabilidade | Evento de XP ligado à revisão e à versão dos valores; dias liquidados materializados; DTEC com alternativas | `docs/prompts/`, `traceability.md` |

Não há exceção aos princípios. As exceções técnicas estão em [Complexidade e exceções](#complexidade-e-exceções).

## Arquitetura e fluxo

### Dependências entre domínios

```text
revisao ──(compõe ResumoGamificacao, xpGanho, depoisDaMeta: gamificacao/consultas.py)──> gamificacao
   ├─ publica RevisaoRegistrada ──> nucleo/eventos_revisao.py <── gamificacao registra o ouvinte (DTEC 055)
   └─ registra o provedor ──────> nucleo/disponibilidade.py <── gamificacao consome o provedor e
                                                                registra os ouvintes dos ganchos (DTEC 057)
cartoes (suspender, reativar, excluir, participante) ──chama antes/depois──> nucleo/disponibilidade.py
identidade (PATCH /perfil: meta, limite de novos, fuso) ──chama antes/depois──> nucleo/disponibilidade.py
gamificacao ──(dia de estudo)──> nucleo/dia_estudo.py (DTEC 048)
gamificacao ──(meta_diaria, fuso, criado_em; trava e cache da linha)──> identidade (consultas e repositório de usuarios)
```

- `gamificacao` não importa `revisao`, `cartoes` nem `materias`. A disponibilidade vem só pelo provedor, que usa a regra da DTEC 051.
- `cartoes` e `identidade` não importam `gamificacao`: chamam só o núcleo.
- As colunas de gamificação de `usuarios` são escritas só por `gamificacao/repositorios.py`. O modelo ORM de `usuarios` continua em `identidade`, que expõe uma função de trava e leitura da linha para a gamificação.
- Um teste de arquitetura verifica essas direções, que os repositórios de `eventos_xp` não têm `update` nem `delete` (exceto `apagar_dados_usuario`) e que nenhum módulo fora de `gamificacao` escreve `xp_total`, `sequencia_*`, `ultimo_dia_estudado` ou `dias_liquidados_ate`.

### Fluxos da spec

| Fluxo | Passos principais |
|---|---|
| **Avaliar (US1 a US3, RF-001 a RF-009)** | Fluxo da 005 até gravar a revisão e as colunas do FSRS → `RevisaoRegistrada` → ouvinte: trava a linha do estudante (`FOR NO KEY UPDATE`) → liquida `[dias_liquidados_ate + 1, dia − 1]` (DTEC 061) → eventos de XP (`primeira_do_dia`: 10; `tornou_dominado`: 25) → `xp_total += soma` → linha do dia (`pendente` ou existente): revisados + 1 com `primeira_do_dia`, meta diária, restantes pelo provedor, meta efetiva → se `pendente` e `revisados >= max(1, meta_efetiva)`: `estudado`, `meta_cumprida_em`, `sequencia_atual += 1`, recorde e `ultimo_dia_estudado` → resposta da 005 com `xpGanho`, `metaCumpridaAgora` e `gamificacao`. |
| **Reenvio e outra aba (CB-24, CS-001)** | A 005 devolve a revisão existente sem publicar o evento → `xpGanho` e `metaCumpridaAgora` lidos dos eventos e da linha do dia, iguais aos originais → nenhum XP novo. Outra aba na mesma apresentação recebe `409 apresentacao_ja_avaliada` (005), sem efeito na gamificação. |
| **Retirar ou devolver cartão (003, DTEC 057)** | Trava do cartão (ou da fonte ou matéria) → `antes_de_alterar`: trava a linha do estudante e liquida os dias passados com o estado intacto → suspensão, reativação ou exclusão → `depois_de_alterar`: reavalia a linha de hoje (se existir), e a meta efetiva menor pode marcar o dia como estudado. |
| **Mudar preferências (001, `PATCH /perfil`)** | A 001 trava a linha → `antes_de_alterar` (liquida com a meta, o limite e o fuso anteriores) → grava → `depois_de_alterar` com `fuso_anterior` se o fuso mudou: datas puladas como `neutro` com `data_pulada`, nova liquidação no fuso novo, reavaliação de hoje (DTEC 062). |
| **Trilha (RF-010)** | Fluxo da 005 → `gamificacao.consultas.resumo`: XP total; linha de hoje; restantes de agora pelo provedor; liquidação em memória dos dias passados ainda não liquidados (sem gravar) → sequência exibida e `hojeCumprido` → `depoisDaMeta` de cada nó pela `meta_cumprida_em` do dia. |
| **Fechamento (RF-010)** | Fluxo da 005 → `xpGanho` = soma dos eventos das revisões da lição → `gamificacao` atualizado. |
| **Dia corrente sem revisões** | Nenhuma linha. A trilha exibe 0 revisados sobre a meta efetiva de agora; a sequência mostra "hoje falta". |
| **Exclusão de cartão (003, US3-3 da 003)** | `eventos_xp.cartao_id` nulo; `xp_total` inalterado; ganchos como em "Retirar". |
| **Excluir a conta (DTEC 021)** | `apagar_dados_usuario` de `gamificacao` apaga `eventos_xp` e `dias_estudo` antes do domínio `revisao`. |

### Tarefas assíncronas criadas ou alteradas nesta spec

Nenhuma. A liquidação acontece na próxima escrita da gamificação, e as leituras fazem o mesmo cálculo sem gravar (DTEC 061). Uma tarefa periódica foi rejeitada: no MVP local a máquina fica desligada e a tarefa não substituiria a reconstrução.

## Exigências do PO

Conferido em 13/10/2026 em [`exigencias_po.md`](../../produto/exigencias_po.md) e na [pauta](../../produto/pauta-po.md): nenhuma exigência (EX-01 a EX-05) toca XP, meta ou sequência. A EX-05 (PO-01), fora do MVP, não altera XP nem meta, como a spec registra.

## Estrutura do repositório

Somente o que a 006 acrescenta às estruturas da [001](../001-conta-acesso/plan.md#estrutura-do-repositório) a [005](../005-licao-trilha/plan.md#estrutura-do-repositório):

```text
backend/
├── migracoes/versions/0007_gamificacao.py  # enums, eventos_xp, dias_estudo, colunas de usuarios, revisoes_id_usuario
├── src/app/
│   ├── nucleo/
│   │   └── disponibilidade.py    # DTEC 057: provedor (registrado por revisao) e ganchos antes/depois
│   ├── gamificacao/
│   │   ├── regras.py             # RegraXp, PUBLICADAS, VIGENTE (DTEC 058)
│   │   ├── dominio.py            # puras: xp_da_revisao, meta_efetiva, cumpriu, liquidar, aplicar_sequencia, datas_puladas
│   │   ├── servicos.py           # conceder_xp, liquidar, avaliar_dia, resumo
│   │   ├── ouvintes.py           # ao_registrar_revisao; antes_de_alterar e depois_de_alterar
│   │   ├── consultas.py          # resumo, xp_da_revisao, xp_da_licao, meta_cumprida_em, dias_no_intervalo, xp_por_dia
│   │   ├── dtos.py, mapeadores.py, repositorios.py, modelos.py, excecoes.py
│   │   └── registros.py          # registra ouvintes; apagar_dados_usuario (eventos_xp, dias_estudo)
│   ├── revisao/
│   │   ├── disponibilidade.py    # provedor: restantes_hoje e primeiro_instante_disponivel (regra da DTEC 051)
│   │   ├── dtos.py, mapeadores.py, servicos.py   # + campos aditivos (DTEC 063)
│   │   └── registros.py          # + registro do provedor
│   ├── cartoes/servicos.py       # + ganchos em suspender, reativar e excluir
│   ├── cartoes/registros.py      # + ganchos no participante (ao_excluir_fonte, ao_excluir_materia)
│   └── identidade/servicos.py    # + ganchos no PATCH /perfil (meta, limite de novos, fuso)
└── tests/
    ├── fabricas_gamificacao.py   # histórico de dias por meio do serviço, com relógio avançando
    ├── unit/gamificacao/         # regras publicadas, xp, meta, liquidar e sequência com oráculo (Hypothesis)
    ├── integration/gamificacao/  # travas, concorrência, ganchos, migração, CHECKs, FKs, SET NULL, imutabilidade
    ├── functional/gamificacao/   # cenários da US1 a US3 pela API, com relógio, fuso e horário de verão
    ├── functional/desempenho/    # + avaliação com gamificação; trilha com dias sem liquidar
    ├── security/, adversarial/   # + campos novos; reenvio, abas e retirada concorrente
    └── arquitetura/              # + direções da gamificacao; eventos sem update; colunas de usuarios
frontend/src/
├── funcionalidades/gamificacao/  # PainelProgresso (XP, meta, sequência), AnuncioGamificacao (aria-live)
├── funcionalidades/trilha/       # + PainelProgresso no topo; marca discreta "depois da meta" nos nós
└── funcionalidades/licao/        # + ganho no fechamento; anúncio por avaliação
```

**Decisão de estrutura:**

- **Domínio `gamificacao`:** segue a arquitetura (seção 5.1), que já lhe atribui XP, meta, dia de estudo e sequência.
- **Provedor em `revisao/disponibilidade.py`:** a regra de elegibilidade fica no domínio que a aplica (DTEC 051); o núcleo só define o contrato (DTEC 057).
- **Ganchos nos serviços da 001 e da 003:** as chamadas são tarefas da 006, que altera esses serviços sem mudar o comportamento deles.

## Exibição e acessibilidade (RF-010, RQ-001, RQ-003)

- **Painel de progresso (trilha):** XP total, "12 de 20 cartões hoje" (revisados sobre a meta efetiva) com barra de progresso (`role="progressbar"` com `aria-valuenow` e `aria-valuemax`), e a sequência com o recorde. Enquanto hoje não foi cumprido, aparece "hoje falta" ao lado do número, que é a sequência até o último dia estudado (US3-5). Com meta efetiva menor que a diária, aparece o motivo, por exemplo "meta de hoje: 8, todos os cartões disponíveis".
- **Fechamento:** XP ganho na lição, progresso da meta e sequência, com destaque quando a meta foi cumprida nesta lição.
- **Anúncio:** uma única região `aria-live="polite"` por página, que recebe só o texto da última resposta: "Mais 10 de XP", "Mais 35 de XP. Cartão dominado." e "Meta de hoje cumprida. Sequência de 4 dias." Reapresentações (`xpGanho = 0`) não anunciam. O anúncio nunca move o foco, que segue no cartão seguinte (atalhos da 005).
- **Movimento e som:** nenhum som. O contador e a barra animam só sem `prefers-reduced-motion`; com a preferência, o valor muda direto. A animação dura no máximo 400 ms e não atrasa a exibição do cartão seguinte (CS-004 da 005).
- **Servidor autoritativo:** os valores vêm só das respostas. A interface atualiza o cache da trilha com o `gamificacao` da resposta da avaliação e nunca soma localmente. Um teste com MSW atrasando a resposta verifica que nada muda antes dela.
- **Contraste e leitura:** números com algarismos tabulares; estados (cumprida, falta) com texto e ícone, nunca só com cor; WCAG 2.2 AA e uso a partir de 320 px.

## Contratos

O contrato está em [`contracts/openapi.yaml`](contracts/openapi.yaml), validado com `openapi-spec-validator`. A 006 não cria rotas. Ela redefine como superconjunto os caminhos da 005 cujas respostas mudam:

| Método e caminho | Campos acrescentados | História |
|---|---|---|
| `GET /api/v1/trilha` | `Trilha.gamificacao`; `NoTrilha.depoisDaMeta` | US1 a US3 |
| `POST /api/v1/licoes` | `Licao.depoisDaMeta`; `Fechamento.xpGanho` e `Fechamento.gamificacao` (lição concluída na retomada) | US2 |
| `GET /api/v1/licoes/{licaoId}` | Os mesmos de `Licao` e `Fechamento` | US1, US2 |
| `POST /api/v1/apresentacoes/{apresentacaoId}/avaliacao` | `ResultadoAvaliacao.xpGanho`, `metaCumpridaAgora` e `gamificacao` | US1, US2 |

- **Esquemas novos:** `ResumoGamificacao`, `ProgressoMeta` e `Sequencia`.
- **Códigos de erro:** nenhum novo; o enum `Erro.codigo` é cumulativo e continua com os da 001 a 005.
- **Isolamento:** nenhuma rota nova com identificador. As rotas da 005 já estão na tabela de `tests/security/test_isolamento_rotas.py`; um teste novo verifica que o resumo de uma conta não muda com as revisões de outra.
- **Superconjunto:** um teste compara o contrato da 006 com o da 005 (nenhum campo, código de resposta ou valor de enum removido), além do teste geral de que o OpenAPI gerado contém o contrato de cada spec.
- **Cache:** leituras com `Cache-Control: no-store`.

## Dados

- **Entidades e regras:** detalhadas em [data-model.md](data-model.md). O [esquema inicial](../../arquitetura/esquema-inicial.dbml) foi atualizado: enum `situacao_dia`; `eventos_xp` com `versao_regra smallint`, índice `(revisao_id, tipo)` e FKs compostas; `dias_estudo` com situação, meta diária, `data_pulada` e `liquidado_em`; `usuarios.dias_liquidados_ate`; `revisoes_id_usuario`.
- **Migração `0007_gamificacao`:** revisada à mão; sobe e desce nos testes; a descida é recusada se houver eventos de XP.
- **Retenção:** exclusão física (RN-14). O XP permanece depois da exclusão do cartão, com `cartao_id` nulo, e só sai com a conta (RF-003).
- **Dados de teste:** contas `@exemplo.com`, cartões fictícios e históricos gerados pelo próprio serviço com relógio controlado (regra 10).

## Estratégia de testes

Marcadores obrigatórios da 001 (`unit`, `integration`, `functional`, `security`, `adversarial`). Cada teste cita no nome ou na *docstring* o requisito, o cenário ou o CS que cobre.

- **Unitários (`unit`):**
  - **Regras publicadas (RQ-004, DTEC 058):** valores fixos de cada versão de `RegraXp` e o par `(VERSAO_REGRAS, LIMIAR_DOMINADO_DIAS)` da 005.
  - **XP (RF-001, RF-002, CS-003):** `primeira_do_dia` e `tornou_dominado` nas quatro combinações; nota não altera o valor; com Hypothesis, qualquer sequência de notas para o mesmo cartão no dia rende 10 (mais 25 se dominou).
  - **Meta (RF-004 a RF-006):** `meta_efetiva` com restantes zero, menores e maiores que a meta; sem revisão nunca estudado; meta reduzida abaixo dos revisados.
  - **Liquidação e sequência (RF-007, RF-008, CS-002):** com Hypothesis, sequências aleatórias de dias (com ou sem revisões, disponibilidade e ações de retirada) comparadas a um oráculo que simula dia a dia; o teste independente da US3 ("estudado, estudado, neutro, estudado, não estudado, estudado" → atual 1, recorde 3); `pendente` liquidado vira `nao_estudado`; datas liquidadas não mudam.
  - **Datas puladas (DTEC 062):** `datas_puladas` com saltos de 0, 1 e 2 datas.
- **Integração (`integration`):**
  - **Mesma transação (RQ-002):** uma falha forçada no ouvinte desfaz a revisão, os eventos e a linha do dia; o reenvio com a mesma chave registra uma vez.
  - **Concorrência (CS-001, CB-24):** duas abas avaliando cartões diferentes ao mesmo tempo; mesma chave em paralelo; avaliação em paralelo com suspensão, exclusão e `PATCH /perfil`: sem *deadlock*, `xp_total = sum(eventos)` e uma marcação de estudado.
  - **Propriedade do cache (CS-001):** sequência aleatória de avaliações, reenvios e exclusões de cartões; ao fim, `xp_total = sum(eventos_xp.quantidade)` e um evento `revisao` por cartão e dia.
  - **Ganchos (DTEC 057):** cada chamador (suspender, reativar, excluir, participante na exclusão de fonte e de matéria, `PATCH /perfil`) chama `antes` e `depois` na própria transação; brecha fechada (suspender hoje o cartão devido ontem não salva a sequência); reativar não quebra a sequência; retirada que completa a meta marca o dia.
  - **Provedor:** `restantes_hoje` exclui os já revisados hoje e respeita o limite restante; `primeiro_instante_disponivel` usa o estado anterior às revisões de hoje; a aplicação não inicia sem provedor.
  - **Migração `0007`:** sobe e desce; descida recusada com eventos.
  - **`CHECK`, FKs e índices:** `estudado` com `meta_cumprida_em`; `neutro` sem revisados; `data_pulada` só com `neutro`; recorde maior ou igual à atual; FK composta recusa revisão de outro estudante; `SET NULL (cartao_id)` preserva `usuario_id`; índice `(revisao_id, tipo)` recusa duplicata.
  - **Imutabilidade:** nenhuma rota altera um evento de XP; teste de arquitetura sobre o repositório.
  - **Exclusão da conta:** o teste de catálogo da 001 continua verde com as tabelas novas preenchidas.
- **Contrato da API:** o OpenAPI gerado contém o `contracts/openapi.yaml` da 006 e o da 005; o da 006 é superconjunto do da 005.
- **Funcionais (`functional`):** um teste por cenário de aceitação, de ponta a ponta pela API, com cookies, CSRF e relógio controlado:
  - **US1:** cenários 1 a 5 e o teste independente (5 cartões, um Errei reapresentado: 50 de XP; reenvio sem mudança); o bônus de 25 uma única vez; o XP preservado após excluir o cartão.
  - **US2:** cenários 1 a 4 e o teste independente (meta 20, 8 disponíveis: meta efetiva 8 e dia estudado); lição extra depois da meta com `depoisDaMeta`.
  - **US3:** cenários 1 a 5 e o teste independente; revisão às 3h50 no dia anterior (CB-25).
  - **Casos de borda:** cartões aceitos e criados no meio do dia aumentam a meta efetiva; excluídos e suspensos deixam de contar como restantes; meta já cumprida e novos disponíveis depois; meta alterada no meio do dia (para baixo marca o dia; dia estudado não deixa de sê-lo); mudança de fuso vivida em parte, com data pulada e com data repetida; horário de verão em `America/Sao_Paulo` (ano com horário de verão) e `America/Santiago`; mudança dos valores de XP (versão 2 de teste) não altera o XP concedido.
  - **Reverificação obrigatória (plano da 003):** US3-3 da 003, a exclusão de cartão preserva as revisões e o XP.
  - **Desempenho:** o teste de avaliação da 005 continua abaixo de 150 ms no p95 com a gamificação; `GET /trilha` abaixo de 200 ms no p95 com 3 mil cartões e 60 dias sem liquidar; liquidação de 365 dias abaixo de 100 ms.
- **Segurança (`security`):**
  - **Isolamento:** revisões, retiradas e mudanças de fuso de uma conta não alteram XP, dias nem sequência de outra; resumo sempre do estudante da sessão.
  - **Servidor autoritativo:** nenhum campo da requisição influencia XP, meta ou sequência (`extra="forbid"` da 005 recusa `xp` ou `meta` no corpo).
  - **Logs:** eventos da gamificação sem texto de cartão, verificado com captura.
- **Adversariais (`adversarial`):**
  - **Abuso de XP:** errar o mesmo cartão 50 vezes no dia (CS-003); reenviar 100 vezes a mesma chave; avaliar a mesma apresentação de 10 abas.
  - **Abuso de sequência:** suspender, excluir ou reduzir o limite de novos para salvar o dia anterior; trocar o fuso no fim de um dia não estudado; reativar cartões em série; meta reduzida para 1 depois de uma revisão (permitido pela spec: marca o dia, sem desfazer nada).
  - **Limites:** ausência de 365 dias; recorde com sequência longa (1.000 dias por fábrica).
- **Frontend (Vitest, Testing Library, MSW e `vitest-axe`):**
  - **Painel:** XP, "12 de 20", sequência com "hoje falta", meta efetiva menor que a diária com o motivo, estados sem depender de cor.
  - **Anúncio:** texto certo para revisão, dominado e meta; nada em reapresentação; foco permanece no cartão seguinte; nenhuma mudança antes da resposta (MSW atrasado).
  - **Movimento:** com `prefers-reduced-motion`, sem animação.
  - **Acessibilidade:** axe sem violações; `progressbar` com valores; operação só por teclado inalterada.
- **Casos de falha:** banco indisponível durante a avaliação (nada registrado, nem XP; o reenvio registra uma vez); provedor lançando erro (a revisão é desfeita com `500 erro_interno`).

## Observabilidade e operação

- **Eventos de log (structlog, JSON):**
  - `xp_concedido`, com tipo, quantidade, `versao_regra` e o `public_id` do usuário;
  - `dia_estudado`, com revisados, meta diária, meta efetiva e a sequência resultante;
  - `dias_liquidados`, com o intervalo, as quantidades por situação e se houve quebra;
  - `datas_puladas_fuso`, com as datas e os fusos;
  - `sequencia_recorde`, quando o recorde sobe.

  Nenhum leva texto de cartão.
- **Saúde:** sem mudança em `/health`.
- **Runbook** (no quickstart): conferir por SQL que `xp_total` é a soma dos eventos e listar os dias de um estudante com a situação.

## Variáveis de ambiente

Nenhuma nova. Os valores de XP são regra versionada em código (DTEC 058), e a meta e o fuso são preferências do estudante (001).

## Riscos técnicos

| Risco | Consequência | Mitigação | Como verificar |
|---|---|---|---|
| Prazo de 15/10/2026 | US3 sem tempo | US1 e US2 primeiro; US3 isolada em `liquidar` (pura) e nos ganchos | Quickstart da US1 e da US2 funcionando antes da US3 |
| Um caminho que altera a disponibilidade sem chamar os ganchos | Classificação inexata de dias passados | Lista fechada de chamadores na DTEC 057; teste de integração por chamador; teste de arquitetura que procura escritas de `situacao` de cartões e de preferências fora dos serviços que chamam os ganchos | Testes de integração dos ganchos |
| Orçamento de 150 ms da avaliação | CS-004 da 005 reprovado | Uma trava, inserções pequenas, contagem com o índice `cartoes_devidos`; liquidação vazia na maioria das revisões | Teste de desempenho da 005 reexecutado |
| *Deadlock* entre avaliação, ganchos e `PATCH /perfil` | Erro intermitente | Linha do estudante sempre travada por último; nenhum caminho trava cartão depois dela | Testes de concorrência |
| Ausência longa | Liquidação lenta numa revisão | Uma única inserção; limite medido de 100 ms para 365 dias | Teste de desempenho |
| Divergência entre `xp_total` e os eventos | Total errado exibido | Mesma transação; `INSERT` sem `ON CONFLICT`; teste de propriedade | CS-001 |
| Mudança de fuso com data repetida | Dia contado duas vezes | Linha única por data; data liquidada imutável | Testes funcionais de fuso |

## Complexidade e exceções

| Exceção | Por que é necessária | Alternativa mais simples rejeitada porque |
|---|---|---|
| Ganchos `antes` e `depois` chamados pela 001 e pela 003 (DTEC 057) | Liquidação exata, sem brecha para salvar a sequência retirando cartões | Reconstruir só pelo estado atual erra a favor e contra o estudante (DTEC 061, alternativa 3) |
| Datas liquidadas materializadas em `dias_estudo` | Classificação imutável, conferência do CS-002 e base do calendário da 007 | Só um marcador de "liquidado até" não guardaria quais datas foram neutras |
| `revisao` importa `gamificacao/consultas.py` | Campos aditivos nas respostas da 005, numa ida e volta (CS-004 da 005) | Rota própria custaria outra requisição e contraria a obrigação do plano da 005 |
| Colunas de gamificação em `usuarios`, escritas só por `gamificacao` | Cache lido em toda trilha e trava única por estudante | Tabela separada de estado exigiria outra trava e outra leitura, sem ganho |

## Saídas do planejamento

- [`research.md`](research.md): DTEC 058 a 063. A decisão transversal deste planejamento está em [`../../research.md`](../../research.md): DTEC 057.
- [`data-model.md`](data-model.md): entidades, transições, restrições e validações.
- [`contracts/openapi.yaml`](contracts/openapi.yaml): contrato da API, superconjunto dos caminhos afetados da 005.
- [`quickstart.md`](quickstart.md): validação local e demonstração.
- **Propagação:**
  - o [`esquema-inicial.dbml`](../../arquitetura/esquema-inicial.dbml) foi atualizado;
  - a 001, a 003 e a 005 (ainda não implementadas) não mudam de comportamento. As chamadas aos ganchos nos serviços delas, o provedor em `revisao` e os campos aditivos nas respostas da 005 são tarefas da 006. Quem implementar primeiro uma spec que precise de `nucleo/disponibilidade.py` cria o módulo com os registros vazios (DTEC 057).

### Obrigações registradas para as próximas specs

- **007 (evolução):** ler os dias e o XP por `gamificacao/consultas.py` (`dias_no_intervalo`, que inclui as datas ainda não liquidadas calculadas sem gravar, e `xp_por_dia`), nunca recalcular a sequência nem consultar `dias_estudo` direto.
- **012 (filtro por matéria):** se a disponibilidade passar a ser filtrada por matéria, acrescentar o parâmetro ao provedor (DTEC 057) sem mudar a meta, que continua global.
- **Qualquer spec que altere a situação de cartões, a meta, o limite de novos ou o fuso:** chamar os ganchos da DTEC 057 na própria transação.
- **Congelamento da sequência (incremento posterior de F-10):** nova situação de dia e regra em `liquidar`, sem mudar as linhas já liquidadas.

O `tasks.md` só é criado depois da aprovação deste plano (portão "Plano aprovado").
