# Pesquisa e decisões técnicas

**Funcionalidade:** 005-licao-trilha (lição com repetição espaçada e trilha de progressão)  
**Data:** 13/10/2026 ([registro](../../prompts/2026-10-13-005-licao-trilha-plano.md))  
**Status:** DTEC 049 a 056 aprovadas em 13/10/2026 por Artur Lins, com o plano

Este arquivo registra só as dúvidas técnicas **novas** da spec 005. As decisões já tomadas não são reabertas:

- de [`../../research.md`](../../research.md): FSRS com a biblioteca `fsrs` e FSRS soberano (DTEC 012), camadas (DTEC 018) e paginação por cursor (DTEC 034);
- da [spec 001](../001-conta-acesso/research.md): isolamento (DTEC 019) e exclusão da conta (DTEC 021);
- da [spec 002](../002-materias-fontes/research.md): *advisory lock* por estudante (DTEC 032);
- da [spec 003](../003-cartoes-manuais/research.md): estado inicial de `fsrs.Card()` e escritas disjuntas (DTEC 037);
- da [spec 004](../004-geracao-cartoes/research.md): idempotência com chave do cliente (DTEC 044) e evidência dos gerados (DTEC 045).

Vale também a DTEC transversal proposta neste planejamento: dia de estudo num único ponto ([DTEC 048](../../research.md#decisão-dtec-048-dia-de-estudo-calculado-num-único-ponto)). A numeração das DTEC é única no projeto.

| Decisão | Título |
|---|---|
| [DTEC 049](#decisão-dtec-049-modelo-da-lição-cartões-previstos-e-apresentações) | Modelo da lição: cartões previstos e apresentações |
| [DTEC 050](#decisão-dtec-050-abertura-retomada-e-encerramento-da-lição) | Abertura, retomada e encerramento da lição |
| [DTEC 051](#decisão-dtec-051-elegibilidade-e-limite-de-novos-por-dia) | Elegibilidade e limite de novos por dia |
| [DTEC 052](#decisão-dtec-052-revelação-avaliação-idempotente-e-duração) | Revelação, avaliação idempotente e duração |
| [DTEC 053](#decisão-dtec-053-agendamento-reprodutível-com-a-biblioteca-fsrs) | Agendamento reprodutível com a biblioteca `fsrs` |
| [DTEC 054](#decisão-dtec-054-próximo-cartão-término-e-desempenho-da-transição) | Próximo cartão, término e desempenho da transição |
| [DTEC 055](#decisão-dtec-055-dominado-e-fatos-entregues-à-gamificação) | Dominado e fatos entregues à gamificação |
| [DTEC 056](#decisão-dtec-056-trilha-numeração-dos-nós-e-lições-extras) | Trilha, numeração dos nós e lições extras |

## Decisão DTEC 049 Modelo da lição: cartões previstos e apresentações

**Questão:** a spec pede que a lição tenha cartões previstos (entidade "Lição"), seja retomada no ponto em que parou (RF-011), termine quando todos os previstos forem revisados ao menos uma vez (RF-006) e recuse a avaliação sem revelação "naquela apresentação" (RF-003, CB-22). O esquema inicial só tinha `licoes` e `revisoes`. Onde ficam os previstos e cada exibição?  
**Critérios:** regras decididas no servidor (Princípio IV); retomada sem estado no cliente; consultas simples para o término; histórico de revisões intocado pela exclusão de cartões (RN-14).  
**Alternativas consideradas:**

1. **Duas tabelas novas:** `licoes_cartoes` (previstos, com posição, marca de novo, primeira revisão e retirada) e `apresentacoes` (uma linha por exibição, inclusive cada "revendo", com `exibida_em`, `revelada_em` e `avaliada_em`).
2. **Array de identificadores em `licoes` e revelação só no cliente:** mais enxuto, mas o CB-22 deixaria de ser verificado no servidor.
3. **Derivar tudo de `revisoes`:** não distingue um previsto ainda não revisado de um cartão que nunca esteve na lição.

**Decisão:** alternativa 1.  
**Justificativa:** retomada, término e revelação viram consultas por índice, e cada revisão aponta a apresentação de onde veio.  
**Consequências:**

- **Dono:** as duas tabelas têm `usuario_id` e FKs compostas `(licao_id, usuario_id)` e `(cartao_id, usuario_id)` (DTEC 019). A migração cria os índices únicos `(id, usuario_id)` em `licoes` e `cartoes` como alvo.
- **Exclusão do cartão:** as duas FKs para `cartoes` usam `on delete cascade`, uma exceção justificada à obrigação do `set null` da 003. O plano da lição não é histórico; o histórico é `revisoes`, que mantém o `set null`. O cartão excluído sai também do critério de término (CB-27) sem filtro extra.
- **Uma apresentação pendente por lição:** índice único parcial `apresentacoes (licao_id) where avaliada_em is null`. Duas abas veem a mesma apresentação.
- **Revisão ligada à apresentação:** `revisoes.apresentacao_public_id` guarda o valor, sem FK, para sobreviver à exclusão do cartão, com índice único (uma revisão por apresentação, CB-24).

**Condição para revisão:** desfazer revisão (incremento posterior de F-05), que pode pedir o vínculo inverso.

## Decisão DTEC 050 Abertura, retomada e encerramento da lição

**Questão:** como impedir duas lições abertas (dois cliques, duas abas), retomar a lição em andamento (RF-011, CB-28) e conciliar o D-005 (lição deixada aberta de um dia anterior é encerrada) com o CB-25 (lição iniciada antes das 4h e continuada depois segue, com cada revisão no dia do seu instante)?  
**Critérios:** no máximo uma lição aberta por estudante; nenhuma perda de revisão; quem está estudando na virada não perde a lição; regra verificável por teste.  
**Alternativas consideradas:**

1. **"Começar ou continuar" com trava e encerramento só nos pontos de entrada.** `POST /licoes` roda sob `pg_advisory_xact_lock` do estudante. A lição aberta do dia atual é devolvida; a de um dia anterior é encerrada (`encerrada_em`) e uma nova é montada. Revelar e avaliar continuam valendo depois da virada.
2. **Encerrar toda lição aberta no instante da virada:** contraria o CB-25.
3. **Tolerância depois da virada (ex.: 2 h):** regra arbitrária, que seria decisão de produto.

**Decisão:** alternativa 1.  
**Justificativa:** separa "continuar" (ações dentro da lição) de "voltar" (entrar pela trilha ou recarregar a página da lição), que é a distinção entre o CB-25 e o D-005.  
**Consequências:**

- **Trava:** espaço próprio do *advisory lock* (`licao`), no padrão da DTEC 032, com o índice único parcial `licoes (usuario_id) where concluida_em is null and encerrada_em is null` como garantia final.
- **Respostas:** `201` com a lição nova; `200` com a aberta do dia atual (reenvio, duas abas); `409 sem_cartoes_disponiveis` se não houver o que montar (RF-013).
- **Encerramento (D-005):** a lição aberta com `dia_estudo` anterior ao atual recebe `encerrada_em`, sem `numero` e sem acender o nó. As revisões já registradas ficam. Os novos previstos e não revisados não consumiram o limite (D-007) e voltam a ser elegíveis na montagem seguinte.
- **Leitura sem efeito:** `GET /trilha` e `GET /licoes/{id}` não escrevem. A trilha mostra uma lição aberta de dia anterior como "Começar lição"; o encerramento é gravado no próximo `POST /licoes`.
- **Página da lição:** ao carregar, a rota da lição chama `POST /licoes`. Recarregar a página é "voltar"; revelar e avaliar são "continuar".
- **Retomada:** `POST /licoes` também garante a apresentação atual. Se a pendente aponta para um cartão que deixou de estar `ativo`, ou para um novo que estouraria o limite, o cartão é retirado (`licoes_cartoes.retirado_em`) e o próximo é escolhido (DTEC 054).

**Condição para revisão:** lições simultâneas por matéria (filtro da 012), que mudariam a unicidade para `(usuario_id, filtro)`.

## Decisão DTEC 051 Elegibilidade e limite de novos por dia

**Questão:** quais cartões podem entrar numa lição nova (RF-001, RF-012, CS-003) e como o limite de novos por dia (RF-002, D-007) vale mesmo com o limite reduzido durante a lição ou com a lição atravessando a virada? O RN-26 diz que um cartão é devido se vencer antes da próxima virada, e também que cartões que ainda não venceram não entram em lições; o D-004 diz que o cartão em passo curto entra "no instante calculado".  
**Critérios:** FSRS soberano; nenhum cartão com vencimento depois da próxima virada; o limite nunca ultrapassado; montagem rápida com índice.  
**Alternativas consideradas:**

1. **Elegibilidade pelo estado do FSRS e limite reconferido na primeira revisão.**
2. **"Devido no dia" para todos os estados e limite só na montagem:** um cartão de passo curto entraria numa lição nova antes de vencer (contraria o D-004), e a redução do limite durante a lição permitiria ultrapassá-lo.

**Decisão:** alternativa 1.  
**Justificativa:** é a leitura conjunta do RN-26 e do D-004, sem regra nova, e mantém o RF-002 como invariante, não como estimativa.  
**Consequências:**

- **Elegíveis**, sempre com `situacao = 'ativo'` e cartão existente (obrigações da 003 e da 004):
  - **devidos em revisão:** `estado_fsrs = 'revisao'` e `vencimento < proxima_virada(agora, fuso)`;
  - **devidos em passo curto:** `estado_fsrs` em `aprendizado` ou `reaprendizado`, `ultima_revisao` não nula e `vencimento <= agora`;
  - **novos:** `ultima_revisao` nula, na ordem de `entrada_estudo_em` e `id`.
- **Montagem:** devidos do vencimento mais antigo ao mais recente (desempate por `id`) até `tamanho_alvo`; depois `min(tamanho_alvo − devidos, limite_novos_dia − novos_revisados_hoje)` novos. `novos_revisados_hoje` conta as revisões do dia de estudo com `ultima_revisao_antes` nula (índice parcial `revisoes_novos_dia`).
- **Na primeira revisão de um novo:** sob o mesmo *advisory lock* do estudante, a contagem é refeita. Se o limite vigente já foi atingido, responde `409 limite_novos_atingido`, sem efeito; a retomada retira o cartão da lição, e ele continua elegível depois (D-007).
- **Dia do limite:** o da revisão (CB-25). Uma lição iniciada às 3h50 com novos previstos conta, depois das 4h, no limite do novo dia.
- **Cartão aceito durante uma lição aberta:** não entra nela (os previstos são fixados na montagem).
- **Índices:** `cartoes_devidos (usuario_id, situacao, vencimento)` e `cartoes_novos (usuario_id, situacao, entrada_estudo_em)`, já criados pela 003, servem às duas consultas.

**Condição para revisão:** filtro por matéria (012), que acrescenta um predicado sem mudar a regra.

## Decisão DTEC 052 Revelação, avaliação idempotente e duração

**Questão:** como garantir que o verso só chegue ao navegador depois da revelação (RF-003), que a avaliação sem revelação seja recusada (CB-22), que o reenvio e as duas abas tenham um único efeito (RF-008, CB-24, CS-002) e que a duração vá da exibição da frente até a nota (D-006)?  
**Critérios:** verificação no servidor; um único efeito sob concorrência; códigos de erro estáveis; duração fiel ao que o estudante viu.  
**Alternativas consideradas:**

1. **Apresentação como recurso, revelação e avaliação como ações sobre ela, duração medida no cliente e limitada pelo servidor.**
2. **Revelação e avaliação numa só chamada:** o verso teria de estar no navegador antes da revelação.
3. **Duração calculada só no servidor (`recebida − exibida_em`):** inclui a rede e a renderização, e diverge da exibição real quando a resposta anterior já trouxe a frente seguinte (DTEC 054).

**Decisão:** alternativa 1.  
**Justificativa:** o servidor sabe o que foi revelado e avaliado; o cliente sabe quando a frente apareceu; os limites do servidor impedem valores impossíveis.  
**Consequências:**

- **Revelação:** `POST /apresentacoes/{id}/revelacao` grava `revelada_em` (só a primeira vez) e devolve o verso. Repetir devolve o mesmo verso com `200`. Lição concluída ou encerrada responde `409 licao_encerrada`, e cartão que deixou de estar `ativo`, `409 cartao_indisponivel`. A resposta da apresentação nunca contém o verso nem a explicação.
- **Avaliação:** `POST /apresentacoes/{id}/avaliacao` com `{chaveIdempotencia, nota, duracaoMs}`, numa transação, nesta ordem:
  1. chave existente: mesma apresentação e mesma nota devolvem o resultado original com `200`, mesmo que a lição já tenha sido concluída por essa avaliação; outra apresentação ou outra nota, `409 idempotencia_divergente`. A `duracaoMs` não entra na comparação;
  2. apresentação do dono (`404`); se o cartão é novo, *advisory lock* do estudante (DTEC 051);
  3. lição `FOR UPDATE` e nova busca da chave (dois envios simultâneos da mesma chave se resolvem como reenvio); se a lição não estiver aberta, `409 licao_encerrada`;
  4. apresentação `FOR UPDATE`: já avaliada com outra chave, `409 apresentacao_ja_avaliada` (a outra aba recarrega); sem revelação, `409 revelacao_pendente`;
  5. cartão `FOR NO KEY UPDATE`: fora de `ativo`, `409 cartao_indisponivel`;
  6. limite de novos (DTEC 051);
  7. agendamento (DTEC 053), inserção da revisão, atualização **só** das colunas do FSRS e de `dominado_em` (DTEC 037 e 055), marca da primeira revisão na lição, `avaliada_em` e escolha do próximo (DTEC 054).
- **Garantias finais:** índices únicos `(usuario_id, chave_idempotencia)` e `apresentacao_public_id` em `revisoes`.
- **Duração:** o cliente mede com `performance.now()`, da exibição da frente até a nota. O servidor limita o valor ao intervalo `[0, (agora − exibida_em) + 2 s]` e grava o valor limitado; o log registra quando houve ajuste. O valor nunca influencia XP nem agendamento.
- **Explicação ao errar (RF-009, EX-03):** vem na resposta da avaliação só quando a nota é Errei, com `evidenciaDisponivel` para o acesso a `GET /cartoes/{id}/evidencias` (004). Nenhuma chamada à IA (RN-16).
- **Ordem das travas:** *advisory lock* → lição → apresentação → cartão, a mesma em `POST /licoes`, o que evita *deadlock*. A edição de conteúdo da 003 escreve outras colunas (DTEC 037) e só espera a trava do cartão por microssegundos.

**Condição para revisão:** modo sem conexão, que pediria uma fila local de avaliações.

## Decisão DTEC 053 Agendamento reprodutível com a biblioteca `fsrs`

**Questão:** o CS-001 exige que os vencimentos coincidam com os da biblioteca executada isoladamente "com os mesmos parâmetros e a mesma semente", e o RQ-004, que cada revisão seja reproduzível. A leitura do código da biblioteca (`fsrs/scheduler.py`) mostrou que o *fuzz* usa `from random import random`, isto é, o gerador global do processo, e que só se aplica a cartões no estado *Review* com intervalo de pelo menos 2,5 dias. Como tornar cada revisão reproduzível sem desligar o *fuzz* (RF-005)?  
**Critérios:** cálculo só pela biblioteca (RN-26); resultado idêntico bit a bit na reprodução; seguro com corrotinas e *threads*; nenhuma dependência nova.  
**Alternativas consideradas:**

1. **Semente por revisão e gerador por contexto.** Uma semente de 63 bits (`secrets.randbits(63)`) é gravada em `revisoes.semente_fuzz`. Ao importar o adaptador, o nome `random` do módulo `fsrs.scheduler` passa a apontar para uma função que lê um `random.Random(semente)` guardado numa `ContextVar`.
2. **`random.seed(semente)` no gerador global, com trava de *thread* e estado salvo e restaurado:** não toca símbolo interno da biblioteca, mas outra *thread* que use `random` entre a semente e o sorteio quebra o determinismo.
3. **Sem semente:** guardar só o resultado e testar o CS-001 com o *fuzz* desligado. Não atende ao texto do CS-001.

**Decisão:** alternativa 1.  
**Justificativa:** o gerador é isolado por contexto e não depende do estado global; com o estado anterior, a versão dos parâmetros e a semente, a reprodução é exata.  
**Consequências:**

- **Porta única:** `revisao/agendador.py` é o único módulo que importa `fsrs` para revisar. Ele monta o `Scheduler` a partir da versão de `parametros_fsrs` (com *cache* por versão), converte a linha do cartão em `fsrs.Card` e de volta, e chama `review_card(card, nota, review_datetime=agora, review_duration=duracao)`. O estado inicial continua com a 003 (`fsrs.Card()`, DTEC 037).
- **Notas:** Errei, Difícil, Bom e Fácil correspondem a `Rating.Again`, `Hard`, `Good` e `Easy` (RF-004).
- **Testes de contrato sobre a versão fixada no `uv.lock`:**
  - o módulo `fsrs.scheduler` tem o atributo `random` chamável, e `review_card` sorteia exatamente uma vez quando há *fuzz* (falha ao atualizar a biblioteca se o ponto mudar);
  - o CS-001 compara, para uma sequência de referência com cartões em *Review*, o resultado do adaptador com o da biblioteca executada num subprocesso limpo, com `random.seed(semente)` global e sem o adaptador. Os dois produzem o mesmo primeiro sorteio, então os vencimentos devem coincidir.
- **Parâmetros vigentes:** cada revisão lê a maior versão de `parametros_fsrs` do estudante. Mudar a retenção durante a lição vale a partir da próxima revisão (CB-29).
- **Atualização da biblioteca:** exige reexecutar os testes de contrato e registrar a versão nova em `parametros_fsrs.versao_biblioteca` nas versões criadas depois dela.

**Condição para revisão:** uma versão da biblioteca que aceite um gerador ou uma semente por parâmetro, que torna o adaptador desnecessário.

## Decisão DTEC 054 Próximo cartão, término e desempenho da transição

**Questão:** como escolher o próximo cartão de modo que o passo curto volte "quando vencer" (RF-006), a lição termine pelo critério do D-004 e cada transição caiba em 300 ms no percentil 95 (CS-004)?  
**Critérios:** regra determinística e testável; um único pedido por transição; nenhum verso antecipado (RF-003).  
**Alternativas consideradas:**

1. **Escolha no servidor, na mesma transação da avaliação, com a próxima apresentação na resposta.**
2. **Reapresentar os passos curtos só depois de esgotar os previstos:** atrasa o reforço e conclui mais lições com cartões pendentes.
3. **Pré-carregar a frente seguinte antes da avaliação:** não funciona com passos curtos, porque o próximo cartão depende da nota.

**Decisão:** alternativa 1.  
**Justificativa:** uma ida e volta por transição, sem estado no cliente, e a ordem do passo curto fica testável.  
**Consequências:**

- **Escolha**, em ordem:
  1. um cartão da lição já revisado nela, `ativo`, em `aprendizado` ou `reaprendizado`, com `vencimento <= agora` (o de vencimento mais antigo primeiro, desempate pela posição), apresentado como "revendo";
  2. senão, o próximo previsto sem revisão e sem retirada, pela posição; se ele deixou de estar `ativo`, ou é novo e o limite foi atingido, é retirado e a escolha continua;
  3. senão, a lição é concluída (`concluida_em`, `numero`), mesmo com passos curtos ainda não vencidos (D-004).
- **Posição exibida:** cartões distintos com primeira revisão na lição sobre os previstos não retirados. A reapresentação não muda a posição.
- **Fechamento (RF-014):** revisões feitas, cartões distintos, cartões que se tornaram dominados (DTEC 055), cartões em passo curto pendente com o instante em que voltam, "Continuar" disponível (DTEC 056) e o próximo vencimento quando não houver disponíveis (RF-013).
- **Desempenho:**
  - a resposta da avaliação traz a próxima apresentação, só com a frente, ou o fechamento;
  - a revelação é um pedido curto à parte;
  - a interface não espera animação, e o movimento reduzido é respeitado;
  - orçamento de 150 ms no servidor no percentil 95, medido por teste sobre Postgres real com uma lição de 10 cartões; o restante dos 300 ms fica para a rede local e a renderização, medido no roteiro do `quickstart.md` com `performance.mark` (o Playwright só chega no final acadêmico, DTEC 014).

**Condição para revisão:** p95 acima da meta, que pediria a escolha do próximo fora da transação da avaliação.

## Decisão DTEC 055 Dominado e fatos entregues à gamificação

**Questão:** como aplicar o D-003 (dominado com estabilidade de pelo menos 21 dias, limiar numa configuração versionada) e o que a 005 deve gravar para que a 006 conceda XP pela primeira revisão de cada cartão no dia (RN-18) e o bônus único de dominado, sem implementar XP agora?  
**Critérios:** bônus único mesmo com queda posterior da estabilidade; mudança de limiar sem alterar o passado (QA-24); a 006 sem consulta concorrente para descobrir fatos da revisão.  
**Alternativas consideradas:**

1. **Regras versionadas em código e fatos gravados na revisão:** `revisao/regras.py` com `VERSAO_REGRAS` e `LIMIAR_DOMINADO_DIAS = 21`; a revisão grava `versao_regras`, `primeira_do_dia` e `tornou_dominado`, e chama um gancho do núcleo na mesma transação.
2. **A 006 deriva os fatos depois, por consulta:** mais frágil sob concorrência e duplica a regra.
3. **Limiar em variável de ambiente:** mudaria sem versão nem diff revisado.

**Decisão:** alternativa 1.  
**Justificativa:** o fato fica registrado no evento imutável, com a versão da regra que o produziu.  
**Consequências:**

- **`dominado_em`:** preenchido na primeira revisão em que `estabilidade_depois >= LIMIAR_DOMINADO_DIAS`, e nunca volta a nulo. O estado "dominado agora" (pela estabilidade atual) é leitura da 007.
- **`primeira_do_dia`:** verdadeira se não há revisão anterior do mesmo cartão no mesmo dia de estudo. É decidida com o cartão travado e garantida pelo índice único parcial `(usuario_id, cartao_id, dia_estudo) where primeira_do_dia`.
- **Gancho:** `nucleo/eventos_revisao.py` registra ouvintes de `ao_registrar_revisao(sessao, RevisaoRegistrada)`. O evento é um *dataclass* com os identificadores internos, nota, instante, dia de estudo, `primeira_do_dia`, `tornou_dominado` e `versao_regras`. Na 005 não há ouvinte; a 006 registra o seu, que roda na mesma transação.
- **Mudança de limiar:** incrementa `VERSAO_REGRAS`. Revisões antigas mantêm a versão gravada, e `dominado_em` já preenchido não muda.

**Condição para revisão:** limiar por estudante, que levaria as regras para `parametros_fsrs` ou para uma tabela versionada.

## Decisão DTEC 056 Trilha, numeração dos nós e lições extras

**Questão:** como expor a trilha (RF-010) sem fixar a composição visual ainda em aberto (Q-001), numerar os nós sem buracos quando lições são encerradas (D-005), marcar lições extras (RF-012) e informar o próximo vencimento sem cartões disponíveis (RF-013)?  
**Critérios:** leitura sem efeito; tamanho de resposta limitado com o tempo de uso; mesma API para todas as opções da Q-001.  
**Alternativas consideradas:**

1. **`numero` atribuído na conclusão e `GET /trilha` com os últimos nós por cursor, o estado do nó atual, os disponíveis e o próximo vencimento.**
2. **`numero` na criação:** as lições encerradas deixariam buracos visíveis na trilha.
3. **Devolver todos os nós:** a resposta cresceria sem limite.

**Decisão:** alternativa 1.  
**Justificativa:** a trilha mostra só lições concluídas como nós alcançados, e a interface decide a composição sem mudar a API.  
**Consequências:**

- **Numeração:** `numero = max(numero) + 1` do estudante na conclusão, com a lição travada; índice único parcial `(usuario_id, numero) where numero is not null`.
- **`GET /trilha`:** os 30 nós mais recentes (de `limite`, 1 a 100, DTEC 034), com cursor para os anteriores; cada nó traz número, dia de estudo, extra, conclusão, revisões e dominados. O estado do nó atual é um de:
  - `sem_materias`: estudante sem matérias (convite para criar a primeira matéria e enviar a primeira fonte, US3-1);
  - `sem_cartoes`: matérias sem nenhum cartão `ativo`;
  - `continuar`: lição aberta do dia atual;
  - `comecar`: há cartões disponíveis;
  - `sem_disponiveis`: nenhum disponível agora, com `proximoVencimento` (CB-13).
- **Disponíveis:** devidos elegíveis e novos elegíveis dentro do limite restante (DTEC 051).
- **`proximoVencimento`:** o menor entre o vencimento do próximo cartão `ativo` já revisado que ainda não é elegível e a próxima virada, quando há novos barrados pelo limite. Nulo sem nenhum cartão `ativo`.
- **Extra:** `extra = true` quando já existe lição concluída no mesmo dia de estudo. "Depois da meta" é classificação da 006, que conhece a meta.
- **Dependências de leitura:** `revisao` lê `materias` (existência) e `cartoes` (elegíveis) por consultas expostas por esses domínios, sem acessar os modelos ORM deles.

**Condição para revisão:** decisão da Q-001 que exija dados que a API não traz (ex.: marcos por dominados acumulados), atendida com campos aditivos.

## Fontes consultadas

- Código-fonte da biblioteca `fsrs` (`fsrs/scheduler.py` no repositório oficial `open-spaced-repetition/py-fsrs`) e documentação da API (`Scheduler`, `Card`, `ReviewLog`, `review_card`, `enable_fuzzing`), consultados em 13/10/2026 para as DTEC 053 e 055.
- Documentação da biblioteca padrão do Python (`random`, `secrets`, `contextvars`), consultada em 13/10/2026 para a DTEC 053.
- Documentação do PostgreSQL 17 (índices únicos parciais, `SELECT ... FOR UPDATE` e `FOR NO KEY UPDATE`, `pg_advisory_xact_lock`, `ON DELETE SET NULL` com lista de colunas), consultada em 13/10/2026 para as DTEC 049 a 052.
