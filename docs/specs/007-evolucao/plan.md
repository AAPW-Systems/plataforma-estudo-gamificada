# Plano de implementação

**Funcionalidade:** 007-evolucao (evolução mínima)  
**Spec:** [spec.md](spec.md), aprovada em 12/10/2026  
**Data:** 13/10/2026 ([registro](../../prompts/2026-10-13-007-evolucao-plano.md))  
**Responsáveis:**

- Artur Lins: decisões técnicas e aprovações desta fase de documentação.
- Implementação: qualquer pessoa da equipe pode assumir, e registra o nome abaixo antes da primeira tarefa.
  - **Responsável pela implementação:** *a definir no início da implementação*.

**Status:** em revisão (portão "Plano aprovado"), com as DTEC 064 a 067

Este plano **reaproveita sem redefinir** o que as specs anteriores já definiram (resumo em [`contexto-tecnico.md`](../../skills/contexto-tecnico.md)):

- da [001](../001-conta-acesso/plan.md) e das DTEC 015 a 018: a estrutura base, as camadas, o formato de erro, a sessão, `nucleo/banco.py` e o layout autenticado com a navegação;
- da [002](../002-materias-fontes/plan.md): as matérias e a ordem por nome da lista;
- da [005](../005-licao-trilha/plan.md): `cartoes.estabilidade`, `revisao/regras.py` (`VERSAO_REGRAS`, `LIMIAR_DOMINADO_DIAS`), `revisao/consultas.py` e a rota `/trilha` da interface;
- da [006](../006-xp-meta-sequencia/plan.md): `gamificacao/consultas.py` (`resumo`, `dias_no_intervalo`), o `ResumoGamificacao` e a liquidação em memória nas leituras (DTEC 061).

Aqui está só o que a 007 acrescenta.

## Resumo técnico

A evolução é uma **leitura consolidada**, sem dados novos, no domínio `evolucao` ([arquitetura, seção 5.1](../../arquitetura/README.md#51-organização-mvc-por-domínio)). Uma única rota, `GET /api/v1/evolucao`, abre uma transação `REPEATABLE READ, READ ONLY` e compõe quatro leituras, todas pelas consultas dos domínios donos:

- o `ResumoGamificacao` da 006, que dá o XP total, a sequência atual e o recorde idênticos aos da trilha (RF-002);
- as datas das últimas 26 semanas por `dias_no_intervalo`, com as situações da 006 mapeadas para estudado, não estudado, neutro e em andamento (RF-001);
- os dominados atuais por matéria, pela regra vigente de `revisao/regras.py` (RF-003);
- a existência de revisão, que define o estado vazio (RF-005).

Os detalhes estão nas [DTEC 064](research.md#decisão-dtec-064-leitura-consolidada-da-evolução), [065](research.md#decisão-dtec-065-período-e-situações-do-calendário) e [066](research.md#decisão-dtec-066-cartões-dominados-atuais).

**Interface.** A tela `/evolucao` mostra:

- os números em destaque, com rótulo em texto (D-003);
- um calendário em grade com semanas em linhas, navegável por teclado, em que cada dia anuncia a data e a situação e cada situação tem forma própria além da cor;
- a lista de dominados por matéria;
- sem revisões, um estado vazio com o acesso à trilha ([DTEC 067](research.md#decisão-dtec-067-calendário-acessível-e-responsivo)).

**Sem migração.** A spec não cria tabelas, colunas nem índices. As consultas usam índices existentes, e o desempenho é verificado com um ano de histórico (CS-002).

**Riscos principais:**

- o prazo de 15/10/2026: é a spec que se reduz primeiro, a XP e sequência, se o prazo apertar (suposição da spec);
- a acessibilidade do calendário (RQ-001);
- o p95 de 1 s com um ano de histórico (CS-002).

A história é única (US1, P1) e demonstrável sobre a 005 e a 006 (Princípio VI).

## Contexto técnico

- **Linguagem e versão:** as da 001: Python 3.13 com uv; TypeScript *strict* em Node 24 LTS com npm.
- **Dependências novas:** nenhuma. `Intl.DateTimeFormat` é do navegador, e os utilitários de foco e teclado do `react-aria` já vêm com o React Aria Components (DTEC 016).
- **Persistência:** nenhuma alteração. Não há migração `0008` ([modelo de dados](data-model.md)).
- **Testes:** pytest com pytest-asyncio, httpx e Postgres real; relógio injetável da 005; fábricas da 006 (histórico pelo serviço) e uma fábrica em massa para desempenho. No frontend, Vitest, Testing Library, MSW e `vitest-axe`.
- **Plataforma de execução:** os serviços do Compose das specs anteriores. Nenhum serviço, volume, variável ou tarefa nova.
- **Limites de desempenho:**
  - `GET /evolucao` em até 300 ms no percentil 95 no servidor, com um ano de histórico (365 dias liquidados, 30 dias ainda não liquidados, 3 mil cartões em 10 matérias e cerca de 30 mil revisões);
  - a tela completa (requisição, resposta e desenho do calendário) em até 1 s no percentil 95 no ambiente local (CS-002), medida com `performance.mark` (`evolucao-inicio` na entrada da rota e `evolucao-pronta` no primeiro desenho com dados) e `performance.measure('evolucao-carregada')` entre as duas.
- **Escala prevista:** dezenas de estudantes. Por estudante: até 182 datas no período, até 50 matérias e alguns milhares de cartões.

## Verificação da constituição

| Princípio | Como o plano atende | Evidência prevista |
|---|---|---|
| I Fontes exclusivas | Não se aplica: nenhum conteúdo gerado, nenhuma chamada à IA | Teste funcional com o provedor simulado registrando zero chamadas |
| II Proteção e isolamento | Todas as consultas recebem o `usuario_id` da sessão (DTEC 019); a rota não tem identificador; só `public_id` de matérias sai na resposta; logs sem nomes de matérias | Testes `security/` (dados de outra conta não alteram a resposta); teste de logs |
| III Verificação humana | DTEC 064 a 067 alinhadas na sessão e submetidas ao portão; interpretação verificável do contraste de 3:1 explicitada para aprovação | Este plano; registro da sessão |
| IV Servidor autoritativo | Todos os valores calculados no servidor; XP e sequência pela mesma consulta da trilha; nenhum cálculo na interface além da formatação | Teste de igualdade entre `GET /evolucao` e `GET /trilha`; teste de frontend que exibe só valores da resposta |
| V Qualidade verificável | CS-001 com valores escritos à mão; CS-002 por teste de desempenho e medida no quickstart; axe e teste de contraste dos tokens; contrato validado | `traceability.md`; `quickstart.md` |
| VI Entrega incremental | História única, demonstrável sobre as revisões da 005 e a gamificação da 006 | `quickstart.md` |
| VII Rastreabilidade | DTEC com alternativas; testes citam RF, RQ e CS | `docs/prompts/`, `traceability.md` |

Não há exceção aos princípios. As exceções técnicas estão em [Complexidade e exceções](#complexidade-e-exceções).

## Arquitetura e fluxo

### Dependências entre domínios

```text
evolucao ──(resumo, dias_no_intervalo)─────────────────> gamificacao/consultas.py (006)
evolucao ──(dominados_por_materia, existe_revisao)──────> revisao/consultas.py
                                                            └─(contar_dominados_por_materia)─> cartoes/consultas.py
evolucao ──(listar_nomes)───────────────────────────────> materias/consultas.py
evolucao ──(transacao_leitura_consistente)──────────────> nucleo/banco.py (001)
```

- `evolucao` é folha: nenhum domínio a importa, e ela não tem modelos, repositórios, migração nem registros de exclusão.
- `evolucao` importa só os `consultas.py` dos outros domínios, nunca modelos ORM nem repositórios. Ela não lê `dias_estudo` diretamente e não recalcula a sequência (obrigação da 006).
- `evolucao → revisao/consultas.py` é a primeira exceção à regra "nenhum domínio importa `revisao`" (DTEC 057). Não há ciclo, porque `revisao` não importa `evolucao`. O limiar de dominado continua só em `revisao/regras.py` (DTEC 066).
- O teste de arquitetura das specs anteriores ganha essas direções e a exceção, restrita a `revisao.consultas`.

### Fluxos da spec

| Fluxo | Passos principais |
|---|---|
| **Abrir a evolução (US1-1, US1-2, RF-001 a RF-004)** | Rota → sessão validada na transação da requisição (001) → serviço abre `transacao_leitura_consistente()` → `gamificacao.consultas.resumo(sessao, usuario_id, agora)` → `periodo(resumo.dia_estudo)` → `dias_no_intervalo(sessao, usuario_id, inicio, fim, agora)` → `situacao_exibida` em cada data e `totalEstudados` → `revisao.consultas.dominados_por_materia` + `materias.consultas.listar_nomes` → junção por matéria, com 0 nas ausentes, ordem por nome e total → `existe_revisao` → mapeador → `200` com `Cache-Control: no-store`. |
| **Estado vazio (US1-3, RF-005)** | Mesmo fluxo; `possuiRevisoes = false` → a interface mostra só o estado vazio ("Sua evolução começa na primeira lição") com o link para a trilha, sem números nem calendário. |
| **Cartão dominado excluído (US1-4)** | O cartão sai de `cartoes` e deixa de contar nos dominados; o `xpTotal` do resumo não muda (eventos preservados, 006). |
| **Dias não liquidados** | `dias_no_intervalo` classifica em memória, sem gravar (DTEC 061); a transação `READ ONLY` impede qualquer escrita. |
| **Outra aba revisando ao mesmo tempo** | O *snapshot* `REPEATABLE READ` mostra a revisão em todos os valores ou em nenhum. A próxima abertura da tela (TanStack Query, `staleTime: 0`) mostra o estado novo. |

### Tarefas assíncronas criadas ou alteradas nesta spec

Nenhuma.

## Exigências do PO

Conferido em 13/10/2026 em [`exigencias_po.md`](../../produto/exigencias_po.md) e na [pauta](../../produto/pauta-po.md):

- **EX-05 (dificuldade, PO-01):** saiu do MVP (D-009 da 005). Se o PO aprovar a proposta de exibir a dificuldade do FSRS em faixas, ela entra na [013](../013-evolucao-completa/spec.md). Nada neste plano a impede: a resposta pode ganhar um campo aditivo.
- **EX-01 a EX-04:** tratam da pesquisa externa, da geração, da explicação do erro e do tira-dúvidas, e nenhuma toca a evolução.

## Estrutura do repositório

Somente o que a 007 acrescenta às estruturas da [001](../001-conta-acesso/plan.md#estrutura-do-repositório) a [006](../006-xp-meta-sequencia/plan.md#estrutura-do-repositório):

```text
backend/
├── src/app/
│   ├── nucleo/banco.py          # + transacao_leitura_consistente() (REPEATABLE READ, READ ONLY; DTEC 064)
│   ├── evolucao/
│   │   ├── dominio.py           # puras: periodo, situacao_exibida, total_estudados, juntar_dominados
│   │   ├── servicos.py          # consultar_evolucao (compõe as consultas na transação de leitura)
│   │   ├── dtos.py, mapeadores.py, excecoes.py
│   │   └── rotas.py             # GET /api/v1/evolucao
│   ├── revisao/consultas.py     # + dominados_por_materia, existe_revisao (DTEC 066)
│   ├── cartoes/consultas.py     # + contar_dominados_por_materia(usuario_id, limiar)
│   ├── materias/consultas.py    # + listar_nomes(usuario_id)
│   └── gamificacao/consultas.py # dias_no_intervalo conforme o esclarecimento da DTEC 065 (tarefa da 006)
└── tests/
    ├── fabricas_evolucao.py     # histórico de um ano em massa, só para desempenho
    ├── unit/evolucao/           # periodo, situacao_exibida, total, junção dos dominados
    ├── integration/evolucao/    # consultas novas, transação read-only, sem escrita, snapshot
    ├── functional/evolucao/     # US1-1 a US1-4, CS-001 com valores à mão, casos de borda
    ├── functional/desempenho/   # + GET /evolucao com um ano (CS-002, servidor)
    ├── security/, adversarial/  # + isolamento da evolução; dados extremos
    └── arquitetura/             # + direções de evolucao e a exceção revisao.consultas
frontend/src/
├── rotas/_autenticado/evolucao.tsx       # rota /evolucao; performance.mark
├── funcionalidades/evolucao/             # TelaEvolucao, IndicadoresEvolucao, CalendarioEstudo,
│                                         # LegendaCalendario, ListaDominados, EstadoVazioEvolucao
├── componentes/                          # + item "Evolução" na navegação autenticada (design.md, seção 4)
└── estilos/                              # + tokens dia-estudado, dia-nao-estudado, dia-neutro, dia-andamento
```

**Decisão de estrutura:**

- **Domínio `evolucao`:** previsto pela arquitetura (seção 5.1) para a consolidação dos indicadores. Sem persistência, ele tem só as camadas que usa (DTEC 018). `modelos.py`, `repositorios.py` e `registros.py` são omitidos, porque não há o que guardar nem apagar.
- **Consultas nos domínios donos:** a regra de dominado fica em `revisao`, a contagem em `cartoes` e os dias em `gamificacao`, conforme as obrigações da 005 e da 006.
- **`CalendarioEstudo` em `funcionalidades/evolucao/`:** o componente é específico desta tela. Ele usa os utilitários de foco e teclado do `react-aria` diretamente, e só sobe para `componentes/ui/` se outra tela precisar dele.

## Exibição e acessibilidade (RF-004, RF-005, RQ-001, RQ-002)

- **Indicadores (D-003):** XP total, sequência atual (com "hoje falta" enquanto `hojeCumprido` for falso, como na trilha), sequência recorde e cartões dominados no total. São números em destaque com algarismos tabulares e rótulo em texto. Não há gráfico.
- **Calendário (DTEC 067):**
  - grade com 7 colunas (domingo a sábado) e 26 linhas, a semana corrente no topo;
  - `role="grid"`, com cabeçalhos de coluna e de linha (este visualmente oculto);
  - cada dia anuncia "domingo, 12 de outubro de 2026: estudado";
  - uma parada de Tab, com foco inicial em hoje, setas, Home, End, Ctrl+Home e Ctrl+End;
  - células vazias antes da conta e depois de hoje, com `aria-hidden` e fora do foco;
  - legenda visível, com as mesmas formas;
  - o total em texto acima da grade.
- **Situações:** estudado é preenchido com ✓, não estudado tem contorno com ×, neutro é hachurado com "–" e em andamento tem contorno tracejado com ponto. A cor reforça, mas nunca é a única pista.
- **Contraste de 3:1 (interpretação verificável do RQ-001, DTEC 067):** quatro situações não podem ter 3:1 entre todos os pares só pela luminância. Por isso as situações se distinguem pela forma, e o teste dos tokens exige, nos temas claro e escuro:
  - (a) indicador de cada situação com pelo menos 3:1 contra o fundo;
  - (b) preenchimento de estudado com pelo menos 3:1 contra as células sem preenchimento;
  - (c) glifo com pelo menos 3:1 contra o preenchimento da célula.
- **Dominados por matéria:** lista com o nome da matéria e o número, com o rótulo "cartões dominados", distinto de "domínio da matéria" da 012. Nomes longos quebram linha. Uma frase curta explica o critério ("estabilidade de 21 dias ou mais", a partir de `limiarDias`).
- **Estado vazio (RF-005):** título e texto ("Sua evolução começa na primeira lição"), com um botão para a trilha. Nenhum número, nenhuma grade e nenhum zero exibido.
- **Carregando e erro:** esqueleto sem números enquanto carrega, para não mostrar valores fictícios; erro com "Tentar de novo".
- **320 px (RQ-002):** células de cerca de 32 px (a grade ocupa menos de 288 px), indicadores empilhados e lista em coluna. A página não tem rolagem horizontal, e um teste verifica que a largura do conteúdo não passa da janela.
- **Servidor autoritativo:** a interface só formata. As datas chegam em texto e são formatadas sem conversão de fuso, e os números vêm da resposta.

## Contratos

O contrato está em [`contracts/openapi.yaml`](contracts/openapi.yaml), validado com `openapi-spec-validator`.

| Método e caminho | Resposta | História |
|---|---|---|
| `GET /api/v1/evolucao` | `200 Evolucao` (`possuiRevisoes`, `gamificacao`, `calendario`, `dominados`); `401 nao_autenticado` | US1 |

- **Esquemas novos:** `Evolucao`, `CalendarioEstudo`, `DiaCalendario`, `SituacaoDiaCalendario`, `DominadosAtuais` e `DominadosMateria`.
- **Esquemas reaproveitados:** `ResumoGamificacao`, `ProgressoMeta` e `Sequencia`, cópias exatas da 006. Um teste compara os dois contratos.
- **Códigos de erro:** nenhum novo. O enum `Erro.codigo` é cumulativo e continua com os da 001 a 006.
- **Isolamento:** a rota não tem identificador no caminho e por isso não entra na tabela de `tests/security/test_isolamento_rotas.py`. Um teste verifica que as revisões, matérias e cartões de outra conta não alteram a resposta.
- **Cache:** `Cache-Control: no-store`.
- **Contrato gerado:** o teste geral verifica que o OpenAPI gerado contém o contrato da 007, e o frontend gera os tipos com `npm run gerar:api`.

## Dados

- **Entidades e regras:** detalhadas em [data-model.md](data-model.md). O [esquema inicial](../../arquitetura/esquema-inicial.dbml) **não muda**.
- **Sem migração `0008`:**
  - os dias usam a PK `(usuario_id, dia)` de `dias_estudo`;
  - os dominados usam o prefixo `(usuario_id, situacao)` de `cartoes_devidos`;
  - a existência de revisão usa `(usuario_id, dia_estudo)` de `revisoes`;
  - as matérias usam `materias_nome_unico_por_usuario`.

  Um índice parcial por estabilidade ficaria preso a um limiar versionado (DTEC 066). Se o teste de desempenho reprovar, a contingência (índice ou consulta ajustada) vira tarefa nova, com migração.
- **Retenção:** nada é gravado. A exclusão da conta não ganha participante.
- **Dados de teste:** contas `@exemplo.com` e cartões fictícios (regra 10). O histórico do CS-001 é gerado pelos serviços com relógio controlado, e o do CS-002 pela fábrica em massa.

## Estratégia de testes

Marcadores obrigatórios da 001 (`unit`, `integration`, `functional`, `security`, `adversarial`). Cada teste cita no nome ou na *docstring* o requisito, o cenário ou o CS que cobre.

- **Unitários (`unit`):**
  - **Período (RF-001, D-002):** `periodo(hoje)` para hoje em cada dia da semana, na virada de mês e de ano, e em ano bissexto. O período tem sempre 26 semanas, de domingo a sábado, e contém hoje.
  - **Mapeamento (RF-001, casos de borda):** cada linha da tabela da DTEC 065; `pendente` em data passada lança erro de invariante; hoje nunca é `nao_estudado`; `data_pulada` vira `neutro`.
  - **Total e dominados:** `total_estudados` conta só `estudado`; `juntar_dominados` inclui matérias com 0, ordena por nome sem diferenciar maiúsculas e acentos, e o total é a soma.
- **Integração (`integration`):**
  - **`contar_dominados_por_materia` e `dominados_por_materia` (RF-003):** ativo e suspenso contam; `aguardando_revisao`, `recusado`, estabilidade nula e estabilidade logo abaixo do limiar não contam; exatamente no limiar conta; limiar de teste diferente (versão 2) muda a contagem sem alterar `dominado_em`; filtro de dono.
  - **`existe_revisao` (RF-005):** falso sem revisões; verdadeiro com revisão de cartão excluído; filtro de dono.
  - **`listar_nomes`:** só as matérias do dono, ordenadas por nome.
  - **`dias_no_intervalo` (esclarecimento da DTEC 065):** começa no primeiro dia do estudante; termina em hoje; datas não liquidadas calculadas; nada gravado.
  - **Transação de leitura (DTEC 064):** uma tentativa de escrita dentro de `transacao_leitura_consistente` falha; o nível é `repeatable read`; uma revisão confirmada por outra conexão durante a leitura não aparece em parte da resposta.
  - **Sem efeito colateral (DTEC 061):** com 10 dias não liquidados, `dias_estudo` e as colunas de `usuarios` ficam iguais depois de `GET /evolucao`.
- **Contrato da API:** o OpenAPI gerado contém o `contracts/openapi.yaml` da 007; `ResumoGamificacao`, `ProgressoMeta` e `Sequencia` são iguais aos da 006.
- **Funcionais (`functional`):** pela API, com cookies e relógio controlado.
  - **US1-1:** calendário com as quatro situações, período de 26 semanas e total de dias estudados.
  - **US1-2 (RF-002):** XP total, sequência atual e recorde iguais aos de `GET /trilha` no mesmo instante, inclusive com dias não liquidados que quebram a sequência.
  - **US1-3 (RF-005):** conta nova com `possuiRevisoes = false`, com cartões criados e sem revisão.
  - **US1-4:** excluir um cartão dominado diminui os dominados e mantém o XP.
  - **CS-001 (teste independente):** histórico de 30 dias com estudados, não estudados, neutros e um dia não liquidado, 2 matérias e cartões dominados (um que perdeu estabilidade, um suspenso, um excluído). Todos os valores da resposta são comparados com a tabela escrita à mão no teste.
  - **Casos de borda:** conta criada há 10 dias (só 10 datas, nenhuma anterior); hoje sem revisão (`em_andamento`) e hoje cumprido (`estudado`); cartão dominado que perdeu estabilidade depois de um Errei (sai dos dominados, mantém o bônus); suspenso dominado conta; matéria excluída some da lista e o XP permanece; mudança de fuso com data pulada (`neutro`) e com data repetida (uma só entrada).
  - **Desempenho (CS-002, servidor):** `GET /evolucao` repetido 50 vezes sobre a fábrica de um ano, em Postgres real, com p95 abaixo de 300 ms.
- **Segurança (`security`):**
  - **Isolamento (RQ-003):** com duas contas com históricos diferentes, a resposta de cada uma não muda com os dados da outra, e nenhum `materiaId` alheio aparece.
  - **Autenticação:** sem sessão, `401 nao_autenticado`.
  - **Exposição:** a resposta não tem `id` interno, e os logs da rota não têm nome de matéria.
- **Adversariais (`adversarial`):**
  - **Volume:** 50 matérias com nomes de 60 caracteres (incluindo emoji e RTL) e 182 dias estudados. A resposta continua válida no esquema.
  - **Concorrência:** `GET /evolucao` em paralelo com avaliações e suspensões, sem *deadlock* (a leitura não trava linhas) e com respostas coerentes.
  - **Parâmetros inesperados:** `?inicio=…`, `?usuario=…` e cabeçalhos estranhos não alteram o período nem o estudante.
- **Frontend (Vitest, Testing Library, MSW e `vitest-axe`):**
  - **Indicadores:** valores e rótulos da resposta; "hoje falta"; nada antes da resposta (esqueleto).
  - **Calendário (RQ-001):**
    - cada célula anuncia a data e a situação;
    - uma parada de Tab, com foco inicial em hoje;
    - setas, Home, End, Ctrl+Home e Ctrl+End;
    - células vazias fora do foco e com `aria-hidden`;
    - as formas aparecem também sem cor (classe sem cor nos testes);
    - a legenda está presente.
  - **Contraste (RQ-001):** teste unitário dos tokens com as razões (a), (b) e (c) nos temas claro e escuro.
  - **Estado vazio (RF-005):** sem números nem grade, com o botão para a trilha.
  - **320 px (RQ-002):** com a janela em 320 px, nenhum elemento mais largo que a janela.
  - **Acessibilidade:** axe sem violações na tela, no estado vazio e no erro.
- **Casos de falha:** banco indisponível (`500 erro_interno`, com a tela mostrando o erro e "Tentar de novo"); sessão expirada (`401`, redirecionamento ao login da 001).

## Observabilidade e operação

- **Evento de log (structlog, JSON):** `evolucao_consultada`, com o `public_id` do usuário, a duração em ms, o número de datas, de matérias e de dominados e se `possuiRevisoes`. Não leva nome de matéria nem texto de cartão.
- **Saúde:** sem mudança em `/health`.
- **Runbook** (no quickstart): conferir o total de dias estudados e os dominados por SQL de leitura.

## Variáveis de ambiente

Nenhuma nova. O período é decisão de produto (D-002), e o limiar é regra versionada em código (DTEC 055).

## Riscos técnicos

| Risco | Consequência | Mitigação | Como verificar |
|---|---|---|---|
| Prazo de 15/10/2026 | A tela não fica pronta | É o primeiro corte previsto pela spec: XP e sequência já aparecem na trilha (006). A ordem de tarefas entrega primeiro o backend completo e os indicadores, depois o calendário | Quickstart |
| Calendário inacessível | RQ-001 reprovado | Padrão *grid* do WAI-ARIA, testes de teclado e de anúncio, axe, formas além da cor | Testes do frontend; roteiro com leitor de tela no quickstart |
| Contraste de 3:1 impossível entre todos os pares | RQ-001 inverificável | Interpretação verificável (a), (b) e (c) com a forma como distinção principal, submetida no portão | Teste dos tokens |
| p95 acima do orçamento | CS-002 reprovado | Uma ida e volta; consultas agregadas com índices existentes; liquidação em memória limitada ao período | Teste de desempenho; medida no quickstart |
| `dias_no_intervalo` sem o recorte no primeiro dia | Dias anteriores à conta como não estudados | Esclarecimento registrado na T036 da 006 e teste de integração na 007 | Teste de integração |
| Valores diferentes da trilha | RF-002 reprovado | A mesma função `resumo`; teste de igualdade | Teste funcional |
| Escrita acidental numa leitura | Viola a DTEC 061 | Transação `READ ONLY` | Teste de integração |

## Complexidade e exceções

| Exceção | Por que é necessária | Alternativa mais simples rejeitada porque |
|---|---|---|
| `evolucao` importa `revisao/consultas.py` | O limiar de dominado e a sua consulta ficam no domínio que os define (DTEC 066) | Importar a constante e chamar `cartoes` espalharia a regra por dois domínios |
| Segunda transação de leitura por requisição | *Snapshot* único e `READ ONLY` para as quatro leituras; a transação da requisição escreve `ultimo_uso_em` (001) | Ler na transação da requisição não permite `READ ONLY` e, em `READ COMMITTED`, mistura instantes |
| Componente de grade próprio, sem o `Calendar` do React Aria | O `Calendar` é um seletor de data e anunciaria seleção (DTEC 067) | Uma tabela estática com 182 paradas de Tab é inviável pelo teclado |

## Saídas do planejamento

- [`research.md`](research.md): DTEC 064 a 067. Nenhuma decisão transversal: [`../../research.md`](../../research.md) não muda.
- [`data-model.md`](data-model.md): entidades calculadas, origem de cada valor e regras.
- [`contracts/openapi.yaml`](contracts/openapi.yaml): contrato da API.
- [`quickstart.md`](quickstart.md): validação local e demonstração.
- **Propagação, aplicada na aprovação deste plano:**
  - na T036 da 006, o esclarecimento de `dias_no_intervalo` (DTEC 065), sem mudança de comportamento;
  - em `contexto-tecnico.md`, as DTEC 064 a 067, a exceção de dependência, "nenhum código novo" e "nenhuma migração", e as obrigações cumpridas.

  O [esquema inicial](../../arquitetura/esquema-inicial.dbml) não muda.
- `tasks.md` criado somente depois da revisão deste plano.

### Obrigações registradas para as próximas specs

- **013 (evolução completa):** acrescentar parâmetros de período e filtros a `GET /evolucao` como campos aditivos, sem mudar os da 007. `xp_por_dia` da 006 está disponível. O tempo dedicado vem de `revisoes.duracao_ms` pela consulta de `revisao`.
- **012 (domínio por matéria):** o "domínio da matéria" (dominados sobre ativos) usa só os ativos e outro rótulo. A contagem pode reaproveitar `contar_dominados_por_materia` com um filtro de situação, sem mudar a regra do limiar, que fica em `revisao`.
- **Congelamento da sequência (incremento de F-10):** uma situação nova de dia exige um valor novo em `SituacaoDiaCalendario`, com uma forma e um token próprios.
