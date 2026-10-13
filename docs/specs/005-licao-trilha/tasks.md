# Tarefas da funcionalidade

**Funcionalidade:** 005-licao-trilha (lição com repetição espaçada e trilha de progressão)  
**Entrada:** [spec](spec.md), [plano](plan.md) (aprovado em 13/10/2026), [pesquisa](research.md), [modelo de dados](data-model.md), [contrato](contracts/openapi.yaml) e [quickstart](quickstart.md)  
**Formato:** `[ID] [P?] [US?] ação com caminho exato e resultado verificável`  
**Status:** aprovadas em 13/10/2026 por Artur Lins (equipe), junto com a [rastreabilidade](traceability.md)

- `[P]` indica que a tarefa pode ser executada em paralelo, porque não altera os mesmos arquivos nem depende de outra tarefa pendente.
- `[US1]` relaciona a tarefa a uma história de usuário.
- Marque `[x]` somente quando o resultado e a sua verificação estiverem concluídos (regra 6).
- **Caminhos:** `backend/src/app/` aparece abreviado como `app/`, e `backend/tests/` como `tests/`.
- **Pré-requisitos:**
  - da [spec 001](../001-conta-acesso/tasks.md), as tarefas até a US3 (T001 a T052): estrutura base, sessão, CSRF, contrato (T037), teste que percorre as rotas (T041), preferências (`tamanho_licao`, `limite_novos_dia`, `fuso`) e versões de `parametros_fsrs`;
  - da [spec 003](../003-cartoes-manuais/tasks.md), as tarefas até a US3 (T001 a T033): tabela `cartoes`, criação, edição (escritas disjuntas), suspender, reativar e excluir;
  - da [spec 004](../004-geracao-cartoes/tasks.md), a base (T001 a T011), porque a migração `0006` vem depois da `0005`. Para a US2 com cartão gerado, também as T023 a T028 (aceitação) e as T040 a T042 (`GET /cartoes/{id}/evidencias`).
- **Testes antes do código:** em cada história, as tarefas de teste vêm antes das de implementação. Os testes começam falhando e passam ao fim da história.
- **Relógio:** todo teste que depende de instante usa o relógio injetável da T007 (virada das 4h, passo curto, fuso). Nenhum teste dorme esperando o passo curto.
- **Commits:** todo trabalho acontece na `develop` (regra 14), com um commit atômico por tarefa ou por par teste e implementação, citando o ID da tarefa (ex.: `feat(revisao): implementa a montagem da lição [T021]`). Os escopos `revisao` e `trilha` identificam esta spec.

## Fase 1 Preparação

- [ ] T001 **Registrar a pessoa responsável:** quem assumir a implementação da 005 escreve o próprio nome no campo "Responsável pela implementação" do [plano](plan.md) e no registro de prompts da sessão de implementação. **Verificação:** o nome está nos dois lugares antes de qualquer outra tarefa, e Artur Lins aprova a mudança.
- [ ] T002 [P] Criar os testes do dia de estudo em `tests/unit/nucleo/test_dia_estudo.py` ([DTEC 048](../../research.md#decisão-dtec-048-dia-de-estudo-calculado-num-único-ponto)):
  - virada às 4h: 3h59 pertence ao dia anterior, 4h00 ao dia atual;
  - `inicio_dia` e `proxima_virada` em UTC para `America/Sao_Paulo`;
  - horário de verão: hora repetida (`fold=0`) e hora inexistente (primeiro instante válido) em fusos que mudam à meia-noite;
  - com Hypothesis, para qualquer instante e fuso da lista IANA: `inicio_dia(dia_estudo(t)) <= t < proxima_virada(t)`.

  Se a 004 já tiver sido implementada e criado o módulo, a tarefa só confere que estes testes existem e passam.
- [ ] T003 Implementar `app/nucleo/dia_estudo.py` (`dia_estudo`, `inicio_dia`, `proxima_virada`), só com `zoneinfo`, até que a T002 passe.

## Fase 2 Base compartilhada (bloqueia todas as histórias)

- [ ] T004 Criar as entidades e a migração da lição:
  - **Entidades** em `app/revisao/modelos.py`: `Licao`, `CartaoPrevisto`, `Apresentacao` e `Revisao`, com o enum `NotaRevisao`; em `app/cartoes/modelos.py`, a coluna `dominado_em`.
  - **Migração** `backend/migracoes/versions/0006_licoes_revisoes.py`, conforme o [modelo de dados](data-model.md):
    - o enum `nota_revisao` e as tabelas `licoes`, `licoes_cartoes`, `apresentacoes` e `revisoes`, com PK `generated always as identity`;
    - os índices únicos `(id, usuario_id)` em `cartoes` (`cartoes_id_usuario`) e em `licoes`, antes das FKs compostas;
    - as FKs compostas com o dono: `cascade` em `licoes_cartoes` e `apresentacoes`; `ON DELETE SET NULL (cartao_id)` em `revisoes`;
    - os `CHECK` (conclusão e encerramento exclusivos, `numero` só com conclusão, `avaliada_em` só com `revelada_em`, `revisado_em` e `retirado_em` exclusivos);
    - os índices parciais `licoes_numero`, `licoes_uma_aberta`, `apresentacoes_uma_pendente`, `revisoes_novos_dia` e `revisoes_primeira_do_dia`;
    - a coluna `cartoes.dominado_em`;
    - a descida, que remove o que a subida criou e recusa descer se houver revisões.

  **Verificação:** `tests/integration/test_migracoes.py` sobe e desce, e a descida é recusada com revisões. `tests/integration/revisao/test_restricoes.py` mostra que:
  - cada `CHECK` recusa a linha inválida;
  - as FKs compostas recusam lição, apresentação ou revisão com cartão de outro estudante;
  - apagar o cartão apaga previstos e apresentações e anula só o `cartao_id` da revisão, mantendo `usuario_id`;
  - os índices parciais recusam a segunda lição aberta, a segunda apresentação pendente da lição, a segunda revisão da mesma apresentação e a segunda `primeira_do_dia` do mesmo cartão no dia.
- [ ] T005 [P] Criar as consultas e a escrita do agendamento no domínio `cartoes` ([DTEC 051](research.md#decisão-dtec-051-elegibilidade-e-limite-de-novos-por-dia) e DTEC 037):
  - **`app/cartoes/consultas.py`:** `devidos_elegiveis(sessao, usuario_id, agora, proxima_virada, limite)`, `novos_elegiveis(sessao, usuario_id, limite)`, `contar_elegiveis`, `proximo_vencimento_nao_elegivel`, `existe_cartao_ativo` e `travar_para_revisao(sessao, usuario_id, cartao_id)` (`FOR NO KEY UPDATE`, devolve o estado do FSRS, a situação, a explicação e a origem);
  - **`app/cartoes/agendamento.py`:** `gravar_agendamento(sessao, cartao_id, estado, dominado_em|None)`, que atualiza **só** as colunas do FSRS e, quando preenchido, `dominado_em`.

  **Testes** em `tests/integration/cartoes/test_consultas_licao.py` e `tests/integration/cartoes/test_agendamento.py`: só `ativo` entra (suspenso, aguardando revisão e recusado fora); a ordem dos devidos e dos novos; o filtro de dono (DTEC 019); a escrita não toca frente, verso, explicação nem situação; `dominado_em` nunca volta a nulo.
- [ ] T006 [P] Criar `existe_materia(sessao, usuario_id)` em `app/materias/consultas.py`, com teste de dono em `tests/integration/materias/test_consultas.py`.
- [ ] T007 [P] Criar `tests/fabricas_revisao.py`:
  - cartões manuais fictícios com estados do FSRS fabricados (novo, devido em revisão, em passo curto vencido e não vencido, em revisão com intervalo longo, perto do limiar de dominado);
  - o relógio injetável (`fixture` `relogio`) usado pelo serviço da lição;
  - a linha de comando `python -m tests.fabricas_revisao --email` do quickstart (12 novos e 3 devidos em `Biologia`), que só roda com `APP_AMBIENTE=desenvolvimento` e só para contas `@exemplo.com` (regra 10).

  **Verificação:** a semeadura cria os 15 cartões e recusa uma conta fora de `exemplo.com`.
- [ ] T008 [P] Ampliar `tests/arquitetura/test_camadas.py`:
  - `app/cartoes`, `app/materias` e `app/identidade` não importam `app/revisao`;
  - `app/revisao` não importa os modelos ORM de `cartoes` nem de `materias` (só `consultas.py` e `agendamento.py`);
  - `fsrs` só é importado em `app/revisao/agendador.py` e na criação de cartões da 003;
  - o repositório de revisões não tem `update` nem `delete`, salvo em `apagar_dados_usuario`.
- [ ] T009 [P] Criar os testes de contrato da biblioteca em `tests/contrato/fsrs/` ([DTEC 053](research.md#decisão-dtec-053-agendamento-reprodutível-com-a-biblioteca-fsrs)):
  - **Ponto de *fuzz*:** `fsrs.scheduler.random` existe e é chamável na versão fixada; uma revisão de cartão em *Review* com intervalo de 2,5 dias ou mais sorteia exatamente uma vez; uma revisão em aprendizado não sorteia.
  - **CS-001:** uma sequência de referência de 20 revisões (inclui *Review* com intervalos longos e as quatro notas) executada pelo adaptador e pela biblioteca num subprocesso limpo, com `random.seed(semente)` e os mesmos parâmetros: vencimentos, estabilidades, dificuldades, estados e passos idênticos.
  - **Isolamento do gerador:** duas revisões concorrentes (`asyncio.gather` e duas *threads*) com sementes diferentes dão os mesmos resultados que em série.
  - **Mapeamento:** Errei a Fácil = `Rating.Again` a `Rating.Easy`; a conversão da linha do cartão em `fsrs.Card` e de volta preserva todos os campos.
- [ ] T010 Implementar `app/revisao/agendador.py` (`Scheduler` por versão de `parametros_fsrs` com *cache*, conversão do cartão, semente com `secrets.randbits(63)`, gerador por `ContextVar` no lugar de `fsrs.scheduler.random`, `revisar(estado, nota, agora, duracao_ms, parametros, semente)`) e `app/revisao/regras.py` (`VERSAO_REGRAS = 1`, `LIMIAR_DOMINADO_DIAS = 21`), até que a T009 passe.
- [ ] T011 [P] Criar `app/nucleo/eventos_revisao.py` (registro de ouvintes, *dataclass* `RevisaoRegistrada`, `publicar(sessao, evento)`), com testes em `tests/unit/nucleo/test_eventos_revisao.py`: os ouvintes rodam em ordem de registro; a exceção de um ouvinte é propagada; sem ouvintes, nada acontece.
- [ ] T012 [P] Criar `AtalhoTeclado` em `frontend/src/componentes/ui/` (rótulo visível da tecla e `aria-keyshortcuts`), com teste e `vitest-axe`.
- [ ] T013 **Verificar a base:** `docker compose up --build` aplica a `0006`, `\d revisoes` mostra as colunas e os índices do modelo, e a integração contínua passa na `develop`. Registrar a evidência no registro de prompts da sessão de implementação.

## Fase 3 História de usuário 1 Fazer a lição do dia (P1)

**Objetivo:** começar a lição, revelar, avaliar com quatro notas, ver o passo curto voltar e concluir a lição.  
**Teste independente:** com 12 novos e 3 devidos, lição de 10 e limite de 20, a lição tem os 3 devidos (mais atrasado primeiro) e 7 novos; cada cartão ganha vencimento; o cartão marcado Errei volta como "revendo"; a lição termina e o nó acende.

- [ ] T014 [P] [US1] Criar os testes unitários da montagem em `tests/unit/revisao/test_montagem.py` (DTEC 051):
  - elegibilidade (CS-003): revisão vencendo 1 µs antes e na própria virada; passo curto vencido e não vencido; novo; com Hypothesis, nenhum elegível com vencimento depois da próxima virada;
  - ordem dos devidos (mais atrasado primeiro, desempate por `id`) e dos novos (`entrada_estudo_em`, `id`);
  - vagas de novos `min(tamanho − devidos, limite − novos_hoje)`; limite zero (só devidos); menos disponíveis que o tamanho; nenhum disponível.
- [ ] T015 [P] [US1] Criar os testes unitários da lição em `tests/unit/revisao/test_licao.py` (DTEC 052, 054 e 055):
  - próximo: passo curto vencido antes do previsto; dois passos curtos (o mais antigo primeiro); previsto retirado pulado; só passos não vencidos conclui; Errei repetido não impede a conclusão (D-004);
  - posição: cartões distintos revisados sobre previstos não retirados; a reapresentação não muda a posição;
  - duração limitada a `[0, (agora − exibida_em) + 2 s]`;
  - dominado: limiar exato; `tornou_dominado` só na primeira vez; queda posterior não apaga `dominado_em`;
  - `primeira_do_dia` verdadeira só na primeira revisão do cartão no dia de estudo, inclusive numa lição que atravessa as 4h (CB-25);
  - fechamento: revisões, distintos, dominados, passos curtos pendentes e `voltamEm`.
- [ ] T016 [P] [US1] Criar os testes de integração em `tests/integration/revisao/test_concorrencia.py`, `test_evento.py` e `test_cascata.py`:
  - 10 `POST /licoes` simultâneos criam uma lição só, e todos recebem a mesma;
  - duas avaliações de novos em paralelo com 1 vaga no limite: uma registra e a outra recebe `409 limite_novos_atingido`;
  - duas avaliações da mesma apresentação com chaves diferentes: uma revisão só (CS-002);
  - a mesma chave em paralelo: uma revisão, e as duas respostas iguais;
  - edição de conteúdo da 003 em paralelo com a avaliação: as duas mudanças ficam (DTEC 037);
  - um ouvinte de teste recebe `RevisaoRegistrada` com os campos certos, e a falha dele desfaz a revisão;
  - excluir o cartão, a fonte ou a matéria durante a lição remove previstos e apresentações e mantém as revisões (CB-27);
  - nenhuma ordem de chamadas concorrentes (abertura, avaliação, suspensão) produz *deadlock* em 200 repetições.
- [ ] T017 [P] [US1] Criar os testes funcionais em `tests/functional/revisao/test_us1_licao.py`, de ponta a ponta pela API, com cookies, CSRF e o relógio:
  - cenários 1 a 6 da US1, com o teste independente;
  - casos de borda: avaliação sem revelação (`409 revelacao_pendente`); reenvio com a mesma chave (`200` com o resultado original, também depois da conclusão); mesma chave com outra nota (`409 idempotencia_divergente`); duas abas (`409 apresentacao_ja_avaliada` e `GET /licoes/{id}` com a apresentação seguinte); aba fechada com passo curto e retomada no mesmo dia (CB-28); lição de dia anterior encerrada sem nó e novos sem consumo do limite (D-005, D-007); lição atravessando as 4h com revisões em dias diferentes (CB-25); cartão suspenso durante a lição (`409 cartao_indisponivel` e retirada na retomada); cartão aceito durante a lição fora dela; retenção alterada durante a lição (a revisão seguinte usa a versão nova, CB-29); limite zero; tamanho alterado durante a lição; Errei repetido;
  - RF-007: cada revisão grava estado antes e depois, versão dos parâmetros, semente e versão das regras;
  - RQ-004: reproduzir cada revisão gravada com o agendador dá o mesmo estado depois.
- [ ] T018 [US1] Criar as reverificações obrigatórias com lições reais em `tests/functional/revisao/test_reverificacoes.py` (planos da 003 e da 004):
  - **US1-1 da 003:** o cartão manual recém-criado entra na lição como novo;
  - **US3-1 e CS-003 da 003:** o cartão suspenso não entra em nenhuma lição;
  - **US3-2 da 003:** o cartão reativado volta com o vencimento anterior;
  - **US1-4 da 004:** os gerados aceitos entram como novos, na ordem de aceitação; aguardando revisão e recusados nunca entram.
- [ ] T019 [P] [US1] Criar os testes de segurança em `tests/security/revisao/test_licao_seguranca.py`:
  - acrescentar à tabela de `tests/security/test_isolamento_rotas.py` as rotas `GET /licoes/{licaoId}`, `POST /apresentacoes/{id}/revelacao` e `POST /apresentacoes/{id}/avaliacao`, com `404` idêntico para recurso alheio;
  - o verso não aparece em nenhuma resposta da 005 além da revelação, e a explicação só em Errei;
  - logs sem frente, verso nem explicação, verificado com captura;
  - `401` sem sessão e `403` sem CSRF nas rotas novas.
- [ ] T020 [P] [US1] Criar os testes adversariais em `tests/adversarial/revisao/test_licao_adversarial.py`:
  - nota fora do enum; `duracaoMs` negativa, acima de 86.400.000 ou não inteira; chave inválida; campos extras; corpo acima de 64 KiB;
  - avaliar uma apresentação já avaliada; avaliar numa lição encerrada (`409 licao_encerrada`); revelar e avaliar depois da exclusão do cartão (`404`); reenviar a mesma chave para outra apresentação;
  - avaliação em paralelo com a suspensão do cartão; com a mudança do limite de novos para zero; `POST /licoes` em paralelo com a avaliação do último cartão.
- [ ] T021 [US1] Implementar `app/revisao/dominio.py` (elegibilidade, montagem, próximo, término, posição, duração, dominado e fechamento), até que as T014 e T015 passem.
- [ ] T022 [US1] Implementar "começar ou continuar" e a leitura da lição em `app/revisao/servicos.py`, `repositorios.py`, `dtos.py`, `mapeadores.py`, `excecoes.py` e `rotas.py` (`POST /licoes` e `GET /licoes/{licaoId}`), com o *advisory lock* `licao`, o encerramento do dia anterior, a retirada na retomada e a numeração na conclusão (DTEC 050 e 056).
- [ ] T023 [US1] Implementar a revelação e a avaliação (`POST /apresentacoes/{id}/revelacao` e `/avaliacao`), na ordem da [DTEC 052](research.md#decisão-dtec-052-revelação-avaliação-idempotente-e-duração), com a gravação pelo `cartoes/agendamento.py`, a publicação de `RevisaoRegistrada` e a escolha do próximo na mesma transação, até que as T016, T017, T019 e T020 passem.
- [ ] T024 [US1] Ampliar `app/revisao/registros.py` com `apagar_dados_usuario` das tabelas novas (antes de `parametros_fsrs` e dos cartões) e criar `app/revisao/reproduzir.py` (runbook do RQ-004). **Verificação:** o teste de catálogo da exclusão da conta (001) passa com as quatro tabelas preenchidas, e a T018 passa.
- [ ] T025 [US1] Ampliar `tests/integration/test_contrato_openapi.py` para verificar também `docs/specs/005-licao-trilha/contracts/openapi.yaml`, incluindo os 6 códigos novos do enum de `Erro`. Regenerar e versionar `backend/openapi.json` e rodar `npm run gerar:api`.
- [ ] T026 [P] [US1] Criar os testes de componente em `frontend/src/funcionalidades/licao/`, todos com axe sem violações:
  - `CartaoLicao.test.tsx`: frente sem verso; "revendo"; posição; foco na frente a cada cartão novo;
  - `BotoesAvaliacao.test.tsx`: desabilitados antes da revelação; atalhos Espaço, Enter e 1 a 4 só com o foco fora de campos de texto; chave gerada uma vez por avaliação (duplo clique reenvia a mesma);
  - `Licao.test.tsx`: a rota chama `POST /licoes` ao carregar; `409 apresentacao_ja_avaliada` sincroniza com `GET /licoes/{id}`; `409 cartao_indisponivel` e `limite_novos_atingido` chamam `POST /licoes`; `aria-live` com o resultado; movimento reduzido; medida `transicao-cartao` gravada;
  - `FechamentoLicao.test.tsx`: revisões, dominados e passos curtos pendentes com o horário no fuso.
- [ ] T027 [US1] Implementar a rota `frontend/src/rotas/_autenticado/licao.tsx` e os componentes `CartaoLicao`, `BotoesAvaliacao` e `FechamentoLicao`, com os atalhos e a medição `performance.mark`, até que a T026 passe.
- [ ] T028 [US1] Executar os passos 1 a 8 da US1 no quickstart e os testes `functional`, `security`, `adversarial` e `contrato` da US1. Registrar a evidência.

## Fase 4 História de usuário 2 Entender o erro (P1)

**Objetivo:** ao marcar Errei, ver a explicação e o acesso à evidência antes de seguir, sem chamada à IA.  
**Teste independente:** Errei num cartão gerado mostra a explicação e "Ver evidência"; num manual sem explicação, a lição segue sem a área.

- [ ] T029 [P] [US2] Criar os testes funcionais em `tests/functional/revisao/test_us2_explicacao.py`:
  - cenário 1: cartão gerado (fábrica da 004) com Errei devolve `explicacao` e `evidenciaDisponivel = true`, e `GET /cartoes/{id}/evidencias` devolve a evidência;
  - cenário 2: cartão manual sem explicação devolve `explicacao` nula, sem erro;
  - cenário 3: o provedor simulado registra zero chamadas durante a lição (RN-16);
  - com Bom, Difícil e Fácil, a resposta não traz explicação.
- [ ] T030 [US2] Implementar `explicacao` e `evidenciaDisponivel` na resposta da avaliação, só com a nota Errei, a partir de `travar_para_revisao` (origem e existência de evidência), até que a T029 passe.
- [ ] T031 [P] [US2] Criar `ExplicacaoErro.test.tsx` em `frontend/src/funcionalidades/licao/`: explicação antes do próximo cartão; "Ver evidência" recolhido por padrão que abre o `PainelEvidencia` (004) sem esconder a explicação; Enter segue; manual sem explicação segue direto; axe sem violações.
- [ ] T032 [US2] Implementar `ExplicacaoErro` na lição, reutilizando o `PainelEvidencia`, até que a T031 passe.
- [ ] T033 [US2] Executar os passos 1 a 4 da US2 no quickstart, com o provedor simulado, e registrar a evidência (incluindo a ausência de `chamada_ia` no log).

## Fase 5 História de usuário 3 Ver a trilha e saber o próximo passo (P1)

**Objetivo:** ver os nós alcançados, o nó atual e o próximo passo, ou o próximo vencimento sem disponíveis.  
**Teste independente:** com 3 lições concluídas, 3 nós alcançados, o nó atual e o próximo passo; sem disponíveis, nenhuma lição e o próximo vencimento.  
**Bloqueio:** a T038 depende da decisão da Q-001 pela equipe (prazo 14/10/2026). As T034 a T037 não dependem dela.

- [ ] T034 [P] [US3] Criar os testes da trilha em `tests/unit/revisao/test_trilha.py` e `tests/functional/revisao/test_us3_trilha.py` (DTEC 056):
  - estado do nó atual: `sem_materias` (cenário 1), `sem_cartoes`, `comecar`, `continuar` (cenário 2) e `sem_disponiveis` com `proximoVencimento` (cenário 3, CB-13);
  - lição aberta de dia anterior aparece como `comecar`, e `GET /trilha` não escreve nada;
  - `proximoVencimento`: próximo cartão revisado não elegível; próxima virada quando há novos barrados pelo limite; nulo sem cartões ativos;
  - nós sem buracos depois de uma lição encerrada (D-005); paginação por cursor com 35 lições.
- [ ] T035 [P] [US3] Criar os testes de segurança e adversariais da trilha em `tests/security/revisao/test_trilha_seguranca.py`: nós de outro estudante nunca aparecem; cursor adulterado (`422 cursor_invalido`); `limite` fora de 1 a 100 (`422 dados_invalidos`).
- [ ] T036 [US3] Implementar `GET /trilha` em `app/revisao/servicos.py`, `repositorios.py`, `consultas.py` (lições concluídas por dia, para a 006 e a 007), `mapeadores.py` e `rotas.py`, até que as T034 e T035 passem.
- [ ] T037 [P] [US3] Criar os testes de componente em `frontend/src/funcionalidades/trilha/`: convite inicial sem nós fictícios; nós alcançados, atual e futuros com estados por forma e texto (não só por cor); "Começar lição" e "Continuar lição"; sem disponíveis com o horário no fuso e o aviso de dia neutro; teclado; 320 px; axe sem violações.
- [ ] T038 [US3] Implementar a trilha em `frontend/src/rotas/_autenticado/index.tsx` e `frontend/src/funcionalidades/trilha/`, na composição decidida pela equipe na Q-001 (registrar a decisão na spec antes de começar), até que a T037 passe.
- [ ] T039 [US3] Executar a verificação da US3 no quickstart e registrar a evidência.

## Fase 6 História de usuário 4 Continuar estudando depois da meta (P3)

**Objetivo:** lições extras enquanto houver disponíveis.  
**Teste independente:** concluir a lição com disponíveis restantes e iniciar uma extra; esgotar os disponíveis e conferir que "Continuar" não aparece.

- [ ] T040 [P] [US4] Criar os testes funcionais em `tests/functional/revisao/test_us4_extras.py`: cenário 1 (`continuarDisponivel`, nova lição com `extra = true` e novo nó); cenário 2 (sem disponíveis, `continuarDisponivel` falso e `proximoVencimento`, CB-30); cartões que ainda não venceram nunca entram nas extras (RF-012).
- [ ] T041 [US4] Implementar `extra` na montagem e `continuarDisponivel` e `proximoVencimento` no fechamento, até que a T040 passe.
- [ ] T042 [P] [US4] Ampliar `FechamentoLicao.test.tsx`: "Continuar" só com disponíveis; sem eles, o próximo vencimento; "Voltar à trilha".
- [ ] T043 [US4] Implementar "Continuar" e "Voltar à trilha" no fechamento, até que a T042 passe.
- [ ] T044 [US4] Executar a verificação da US4 no quickstart e registrar a evidência.

## Fase final Qualidade transversal

- [ ] T045 Executar nos contêineres as suítes completas do backend e do frontend, a qualidade estática e a verificação do contrato, e confirmar a integração contínua aprovada na `develop`. Registrar as contagens de testes e a cobertura.
- [ ] T046 Revisar e registrar as evidências:
  - logs da lição sem texto dos cartões;
  - verificação manual de teclado, leitor de tela, 320 px e movimento reduzido na lição e na trilha (RQ-003).
- [ ] T047 Criar `tests/functional/desempenho/test_transicao.py` e medir, no ambiente local:
  - **CS-004 (servidor):** lição de 10 cartões repetida 30 vezes; p95 de avaliar e de revelar abaixo de 150 ms;
  - **CS-004 (navegador):** roteiro do quickstart com a medida `transicao-cartao`, p95 até 300 ms, e uma lição inteira só com o teclado;
  - `POST /licoes` e `GET /trilha` com 3 mil cartões ativos: p95 até 200 ms.
- [ ] T048 Atualizar a documentação:
  - o [quickstart](quickstart.md), com os comandos realmente verificados;
  - `docs/skills/padroes-implementacao.md`, com `nucleo/dia_estudo.py`, `revisao/agendador.py` (única porta da `fsrs`), o relógio injetável e o evento `RevisaoRegistrada`;
  - o "Mapa do repositório" do `.agents/AGENTS.md`, com o domínio `revisao` completo.
- [ ] T049 Atualizar o [traceability.md](traceability.md) com os nomes reais dos testes e corrigir requisitos sem teste ou tarefa.

## Dependências

- **Specs anteriores:** as T001 a T052 da 001, as T001 a T033 da 003 e as T001 a T011 da 004 bloqueiam toda esta lista. A US2 completa (T029) depende também das T023 a T028 e T040 a T042 da 004; sem elas, a T029 roda com o cartão gerado inserido pela fábrica e a evidência fica para a reverificação.
- **Preparação e base:**
  - a T001 vem antes de tudo;
  - a T002 bloqueia a T003, e a T003 bloqueia a Fase 2;
  - a T004 bloqueia as T005, T007, T009 e todos os testes de integração;
  - a T010 depende da T009; a T012 bloqueia a T026;
  - a Fase 2 (T004 a T013) bloqueia todas as histórias.
- **US1:** T014 a T017, T019 e T020 sem dependência entre si → T021 → T022 → T023 → T024 → T018 → T025 → T027 (usa os tipos gerados) → T028. A T026 pode ser escrita em paralelo ao backend.
- **US2:** depende da T023. T029 → T030; T031 → T032; → T033.
- **US3:** depende da T022 (numeração na conclusão). Pode ser feita em paralelo à US2, por pessoas diferentes. A T038 depende da decisão da Q-001.
- **US4:** depende da US1 (T022 e T023) e da US3 (`proximoVencimento`, T036).
- **Specs seguintes:** a 006 registra o ouvinte de `RevisaoRegistrada`, usa `primeira_do_dia` e `tornou_dominado` e acrescenta XP e sequência ao fechamento ([obrigações no plano](plan.md#obrigações-registradas-para-as-próximas-specs)).
- **Fase final:** depende de todas as histórias.

## Pontos de paralelismo

- **Base:** T005, T006, T007, T008, T009, T011 e T012 alteram arquivos distintos.
- **Histórias:** em cada uma, as tarefas de teste marcadas com `[P]` podem ser escritas em paralelo. O frontend (T026 e T027; T031 e T032; T037 e T038; T042 e T043) avança em paralelo ao backend depois da T025.
- **Entre histórias:** depois da US1, a US2 e a US3 podem seguir com pessoas diferentes.

## Estratégia de incremento

1. **Base completa:** a T013 prova a migração, o agendador reproduzível (CS-001) e o dia de estudo.
2. **P1 demonstrável:** entregar a US1 e a US2 juntas, com cartões manuais e um gerado da fábrica, sem IA. A lição completa com a explicação ao errar é o centro da apresentação de 15/10/2026.
3. **Trilha:** acrescentar a US3 assim que a Q-001 for decidida, sem quebrar a P1. A suíte completa passa a cada commit.
4. **Extras e verificação final:** a US4, as medições do CS-004 e a fase final. Nenhum merge na `main` acontece sem todos os testes passando (regra 17).
