# Tarefas da funcionalidade

**Funcionalidade:** 006-xp-meta-sequencia (XP, meta diária e sequência)  
**Entrada:** [spec](spec.md), [plano](plan.md) (aprovado em 13/10/2026), [pesquisa](research.md), [modelo de dados](data-model.md), [contrato](contracts/openapi.yaml) e [quickstart](quickstart.md)  
**Formato:** `[ID] [P?] [US?] ação com caminho exato e resultado verificável`  
**Status:** aprovadas em 13/10/2026 por Artur Lins (equipe), junto com a [rastreabilidade](traceability.md)

- `[P]` indica que a tarefa pode ser executada em paralelo, porque não altera os mesmos arquivos nem depende de outra tarefa pendente.
- `[US1]` relaciona a tarefa a uma história de usuário.
- Marque `[x]` somente quando o resultado e a sua verificação estiverem concluídos (regra 6).
- **Caminhos:** `backend/src/app/` aparece abreviado como `app/`, e `backend/tests/` como `tests/`.
- **Pré-requisitos:**
  - da [spec 001](../001-conta-acesso/tasks.md), as tarefas até a US3 (T001 a T052): estrutura base, contrato (T037), `PATCH /perfil` com trava da linha (T049) e o teste de catálogo da exclusão da conta;
  - da [spec 003](../003-cartoes-manuais/tasks.md), as tarefas até a US3 (T001 a T033): participante dos cartões (T009 e T010) e suspender, reativar e excluir (T030);
  - da [spec 005](../005-licao-trilha/tasks.md), todas as tarefas (T001 a T049): evento `RevisaoRegistrada` (T011), avaliação (T023), trilha (T036), extras (T041), relógio injetável e fábrica (T007).
- **Testes antes do código:** em cada história, as tarefas de teste vêm antes das de implementação. Os testes começam falhando e passam ao fim da história.
- **Relógio:** todo teste que depende de instante usa o relógio injetável da T007 da 005. Nenhum teste dorme esperando a virada.
- **Alterações em specs anteriores:** as tarefas que mexem em serviços da 001, da 003 e da 005 não mudam o comportamento delas. As suítes dessas specs continuam verdes a cada commit.
- **Commits:** todo trabalho acontece na `develop` (regra 14), com um commit atômico por tarefa ou por par teste e implementação, citando o ID da tarefa (ex.: `feat(gamificacao): concede XP pela revisão [T017]`). O escopo `gamificacao` identifica esta spec.

## Fase 1 Preparação

- [ ] T001 **Registrar a pessoa responsável:** quem assumir a implementação da 006 escreve o próprio nome no campo "Responsável pela implementação" do [plano](plan.md) e no registro de prompts da sessão de implementação. **Verificação:** o nome está nos dois lugares antes de qualquer outra tarefa, e Artur Lins aprova a mudança.
- [ ] T002 [P] Criar os testes do núcleo de disponibilidade em `tests/unit/nucleo/test_disponibilidade.py` ([DTEC 057](../../research.md#decisão-dtec-057-disponibilidade-de-cartões-e-ganchos-de-alteração-no-núcleo)):
  - um único provedor: registrar o segundo falha;
  - a verificação ao iniciar recusa a aplicação sem provedor;
  - os ouvintes de `antes_de_alterar` e `depois_de_alterar` rodam em ordem de registro, com a `AlteracaoDisponibilidade(usuario_id, agora, fuso_anterior)` recebida;
  - a exceção de um ouvinte é propagada; sem ouvintes, nada acontece.

  Se outra spec já tiver criado o módulo vazio, a tarefa confere que estes testes existem e passam.
- [ ] T003 Implementar `app/nucleo/disponibilidade.py` (protocolo `ProvedorDisponibilidade` com `restantes_hoje` e `primeiro_instante_disponivel`, *dataclass* `AlteracaoDisponibilidade`, registros, `antes_de_alterar`, `depois_de_alterar` e a verificação ao iniciar em `app/nucleo/configuracao.py`), até que a T002 passe.

## Fase 2 Base compartilhada (bloqueia todas as histórias)

- [ ] T004 Criar as entidades e a migração da gamificação:
  - **Entidades** em `app/gamificacao/modelos.py`: `EventoXp` e `DiaEstudo`, com os enums `TipoEventoXp` e `SituacaoDia`; em `app/identidade/modelos.py`, as cinco colunas de gamificação de `usuarios`.
  - **Migração** `backend/migracoes/versions/0007_gamificacao.py`, conforme o [modelo de dados](data-model.md):
    - os enums `tipo_evento_xp` e `situacao_dia`;
    - o índice único `revisoes_id_usuario`, antes da FK composta;
    - `eventos_xp` com PK `generated always as identity`, FKs compostas (`(revisao_id, usuario_id)` → `revisoes`; `(cartao_id, usuario_id)` → `cartoes` com `ON DELETE SET NULL (cartao_id)`), índice único `eventos_xp_revisao_tipo`, índices `(usuario_id, dia_estudo)` e `cartao_id`, e `CHECK (quantidade > 0)`;
    - `dias_estudo` com PK `(usuario_id, dia)` e os `CHECK` do modelo;
    - as colunas `xp_total`, `sequencia_atual`, `sequencia_recorde`, `ultimo_dia_estudado` e `dias_liquidados_ate` em `usuarios`, com padrões e `CHECK`;
    - a descida, que remove o que a subida criou e recusa descer se houver eventos de XP.

  **Verificação:** `tests/integration/test_migracoes.py` sobe e desce, e a descida é recusada com eventos. `tests/integration/gamificacao/test_restricoes.py` mostra que:
  - cada `CHECK` recusa a linha inválida (`estudado` sem `meta_cumprida_em`, `neutro` com revisados, `data_pulada` fora de `neutro`, recorde menor que a atual, `xp_total` negativo, quantidade zero);
  - as FKs compostas recusam evento com revisão ou cartão de outro estudante;
  - o índice `(revisao_id, tipo)` recusa o segundo evento do mesmo tipo para a revisão;
  - apagar o cartão anula só `eventos_xp.cartao_id`, mantendo `usuario_id`, a quantidade e a revisão.
- [ ] T005 [P] Criar `app/gamificacao/regras.py` (`RegraXp`, `PUBLICADAS = {1: RegraXp(1, 10, 25)}`, `VIGENTE`) e o teste de referência `tests/unit/gamificacao/test_regras_publicadas.py` ([DTEC 058](research.md#decisão-dtec-058-regra-de-valores-versionada)): os valores de cada versão publicada; o par `(VERSAO_REGRAS, LIMIAR_DOMINADO_DIAS) = (1, 21)` de `app/revisao/regras.py`; `VIGENTE` é a maior versão.
- [ ] T006 [P] Criar o provedor em `app/revisao/disponibilidade.py` e registrá-lo em `app/revisao/registros.py` (DTEC 057), usando as consultas de `app/cartoes/consultas.py` da 005:
  - `restantes_hoje`: devidos, passos curtos vencidos e novos dentro do limite restante (DTEC 051), sem os cartões com revisão `primeira_do_dia` no dia corrente;
  - `primeiro_instante_disponivel`: o menor entre `greatest(vencimento, entrada_estudo_em)` dos ativos já revisados e `entrada_estudo_em` dos novos (só com `limite_novos_dia > 0`), com `vencimento_antes` e `ultima_revisao_antes` da primeira revisão de hoje para os cartões revisados hoje; nulo sem cartão.

  **Testes** em `tests/integration/revisao/test_provedor_disponibilidade.py`: cartão revisado hoje em passo curto vencido não conta nos restantes; limite restante respeitado; suspensos, aguardando revisão e recusados fora; cartão criado depois de ontem não antecipa a disponibilidade; cartão revisado hoje usa o estado anterior; filtro de dono (DTEC 019).
- [ ] T007 [P] Criar a trava e o acesso às colunas de gamificação:
  - em `app/identidade/consultas.py`, `travar_para_gamificacao(sessao, usuario_id)` (`FOR NO KEY UPDATE`, devolve `meta_diaria`, `limite_novos_dia`, `fuso`, `criado_em` e as colunas de gamificação);
  - em `app/gamificacao/repositorios.py`, os repositórios de `eventos_xp` (só inserção e leitura), de `dias_estudo` e a atualização das colunas de gamificação de `usuarios`.

  **Testes** em `tests/integration/gamificacao/test_repositorios.py`: filtro de dono; a trava bloqueia uma segunda transação até o fim da primeira.
- [ ] T008 [P] Criar `tests/fabricas_gamificacao.py` (histórico de dias produzido pelo próprio serviço, com o relógio avançando: revisões, retiradas e mudanças de preferência em dias escolhidos) e acrescentar `--novos` e `--devidos` a `tests/fabricas_revisao.py` (padrões 12 e 3, o comportamento da 005). **Verificação:** a fábrica produz a sequência do teste independente da US3; a semeadura com `--novos 5 --devidos 0` cria 5 cartões e continua recusando contas fora de `exemplo.com`.
- [ ] T009 [P] Ampliar `tests/arquitetura/test_camadas.py`:
  - `app/gamificacao` não importa `app/revisao`, `app/cartoes` nem `app/materias`;
  - `app/cartoes`, `app/materias` e `app/identidade` não importam `app/gamificacao`;
  - só `app/gamificacao/repositorios.py` escreve `xp_total`, `sequencia_atual`, `sequencia_recorde`, `ultimo_dia_estudado` e `dias_liquidados_ate`;
  - o repositório de eventos de XP não tem `update` nem `delete`, salvo em `apagar_dados_usuario`;
  - as escritas de `cartoes.situacao` e de `meta_diaria`, `limite_novos_dia` e `fuso` só acontecem nos serviços que chamam os ganchos da DTEC 057.
- [ ] T010 [P] Ampliar `tests/integration/test_contrato_openapi.py`: o OpenAPI gerado contém também `docs/specs/006-xp-meta-sequencia/contracts/openapi.yaml`, e um teste novo verifica que esse contrato é superconjunto do da 005 nos caminhos e esquemas comuns (nenhum campo, resposta ou valor de enum removido).
- [ ] T011 Criar `app/gamificacao/registros.py`: `apagar_dados_usuario` (apaga `eventos_xp` e `dias_estudo`, registrado antes do domínio `revisao`) e o registro dos ouvintes no início da aplicação. **Verificação:** o teste de catálogo da exclusão da conta (001) fica verde com as tabelas novas preenchidas.
- [ ] T012 Criar `ResumoGamificacao`, `ProgressoMeta` e `Sequencia` em `app/gamificacao/dtos.py` e `mapeadores.py`, e `resumo(sessao, usuario_id, agora)` em `app/gamificacao/consultas.py`, que nesta fase lê o XP e a sequência do cache e a meta da linha de hoje mais os restantes do provedor. Acrescentar os campos aditivos da [DTEC 063](research.md#decisão-dtec-063-exibição-contrato-aditivo-e-anúncio-acessível) às respostas da 005 em `app/revisao/dtos.py`, `mapeadores.py` e `servicos.py` (`gamificacao` na trilha, no fechamento e na avaliação; `xpGanho` 0, `metaCumpridaAgora` falso e `depoisDaMeta` falso até as histórias). **Verificação:** a T010 passa e as suítes da 005 continuam verdes.
- [ ] T013 **Verificar a base:** `docker compose up --build` aplica a `0007`, `\d eventos_xp` e `\d dias_estudo` mostram as colunas e os índices do modelo, `npm run gerar:api` gera os tipos novos, e a integração contínua passa na `develop`. Registrar a evidência no registro de prompts da sessão de implementação.

## Fase 3 História de usuário 1 Ganhar XP ao revisar (P1)

**Objetivo:** cada primeira revisão do cartão no dia rende 10 de XP, o cartão dominado rende 25 uma vez, e o total sobrevive a reenvios e exclusões.  
**Teste independente:** revisar 5 cartões distintos, um deles marcado Errei e reapresentado na mesma lição, e confirmar 50 de XP (e não 60); reenviar uma revisão e confirmar que o XP não muda.

- [ ] T014 [P] [US1] Criar os testes unitários em `tests/unit/gamificacao/test_xp.py`: `xp_da_revisao` nas quatro combinações de `primeira_do_dia` e `tornou_dominado`; a nota não altera o valor; com Hypothesis, qualquer sequência de notas para o mesmo cartão no dia rende 10, mais 25 se dominou (CS-003).
- [ ] T015 [P] [US1] Criar os testes de integração em `tests/integration/gamificacao/test_concessao_xp.py` ([DTEC 059](research.md#decisão-dtec-059-concessão-de-xp-idempotente-e-cache-do-total)):
  - **mesma transação (RQ-002):** uma falha forçada no ouvinte desfaz a revisão, os eventos e o cache; o reenvio com a mesma chave registra uma vez;
  - **concorrência (CB-24):** duas abas avaliando cartões diferentes; a mesma chave em paralelo; 10 abas na mesma apresentação: um evento por fato;
  - **propriedade do cache (CS-001):** com Hypothesis, sequências de avaliações, reenvios e exclusões de cartões; ao fim, `xp_total = sum(eventos_xp.quantidade)` e um evento `revisao` por cartão e dia;
  - **campos copiados:** `dia_estudo`, `concedido_em` e `versao_regra` iguais aos da revisão e da regra vigente;
  - **FSRS soberano (RF-011, RN-26):** a mesma sequência de avaliações, com as mesmas sementes, grava estados do FSRS idênticos com o ouvinte da gamificação registrado e sem ele.
- [ ] T016 [P] [US1] Criar os testes funcionais em `tests/functional/gamificacao/test_us1_xp.py`:
  - cenários 1 a 5 e o teste independente (50 de XP; reenvio sem mudança; `xpGanho` vindo da resposta);
  - bônus de 25 uma única vez, mesmo com queda e nova subida da estabilidade;
  - mudança dos valores (uma `RegraXp` versão 2 de teste) não altera o XP já concedido (RQ-004);
  - **reverificação obrigatória da US3-3 da 003:** excluir um cartão revisado preserva as revisões e o XP;
  - **adversariais:** errar o mesmo cartão 50 vezes no dia (CS-003); reenviar 100 vezes a mesma chave; campos `xp` ou `meta` no corpo da avaliação recusados com `422 dados_invalidos`.
- [ ] T017 [US1] Implementar `xp_da_revisao` em `app/gamificacao/dominio.py`, `conceder_xp` em `app/gamificacao/servicos.py` e `ao_registrar_revisao` em `app/gamificacao/ouvintes.py` (trava da T007, eventos por `INSERT` simples, `xp_total += soma`, log `xp_concedido`), registrado na T011, até que as T014 e T015 passem.
- [ ] T018 [US1] Implementar `xp_da_revisao(revisao_id)` e `xp_da_licao(licao_id)` em `app/gamificacao/consultas.py` e preencher `ResultadoAvaliacao.xpGanho` (original no reenvio) e `Fechamento.xpGanho`, até que a T016 passe.
- [ ] T019 [P] [US1] Criar os testes de componente em `frontend/src/funcionalidades/gamificacao/`:
  - `AnuncioGamificacao.test.tsx`: "Mais 10 de XP" e "Mais 35 de XP. Cartão dominado."; nada quando `xpGanho` é 0; o foco continua no cartão seguinte; nenhuma mudança antes da resposta (MSW atrasado); sem animação com `prefers-reduced-motion`;
  - `PainelProgresso.test.tsx`: XP total com algarismos tabulares;
  - `FechamentoLicao.test.tsx` (005, ampliado): XP ganho na lição;
  - `vitest-axe` sem violações.
- [ ] T020 [US1] Implementar `AnuncioGamificacao` (uma região `aria-live="polite"` por página) e a parte de XP de `PainelProgresso`, ligá-los à lição e ao fechamento e atualizar o cache da trilha com o `gamificacao` da resposta, sem soma local, até que a T019 passe.
- [ ] T021 [US1] Executar a verificação da US1 no [quickstart](quickstart.md) e registrar a evidência.

## Fase 4 História de usuário 2 Cumprir a meta diária (P1)

**Objetivo:** progresso em cartões distintos sobre a meta efetiva, e o dia marcado como estudado de forma definitiva.  
**Teste independente:** com meta de 20 e só 8 cartões disponíveis no dia, revisar os 8 e confirmar meta efetiva de 8, meta cumprida e dia estudado.

- [ ] T022 [P] [US2] Criar os testes unitários em `tests/unit/gamificacao/test_meta.py`: `meta_efetiva` com restantes zero, menores e maiores que a meta; `cumpriu` falso sem revisão; meta reduzida abaixo dos revisados; transições permitidas da linha do dia (`pendente` → `estudado`, nunca de volta).
- [ ] T023 [P] [US2] Criar os testes de integração em `tests/integration/gamificacao/test_meta_dia.py` ([DTEC 060](research.md#decisão-dtec-060-meta-efetiva-e-dia-estudado-sob-concorrência)):
  - **ganchos `depois_de_alterar`:** suspender, excluir, excluir a fonte ou a matéria (participante dos cartões) e reduzir a meta ou o limite de novos completam a meta sem nova revisão e marcam o dia;
  - **cada chamador chama `antes` e `depois` na própria transação:** suspender, reativar e excluir (003), o participante em `ao_excluir_fonte` e `ao_excluir_materia` e o `PATCH /perfil` quando mudam a meta, o limite ou o fuso (001), com uma falha no ouvinte desfazendo a ação;
  - **concorrência:** avaliação em paralelo com suspensão, exclusão e `PATCH /perfil`: sem *deadlock* e uma única marcação.
- [ ] T024 [P] [US2] Criar os testes funcionais em `tests/functional/gamificacao/test_us2_meta.py`:
  - cenários 1 a 4 e o teste independente;
  - casos de borda: cartões aceitos ou criados no meio do dia aumentam a meta efetiva; excluídos e suspensos deixam de contar nos restantes, e os revisados continuam contando; meta cumprida e novos disponíveis depois; meta alterada no meio do dia (reduzida marca o dia; o dia estudado não deixa de sê-lo);
  - lição extra depois da meta com `depoisDaMeta` na lição e no nó;
  - `metaCumpridaAgora` só na revisão que cumpriu, e igual no reenvio dela.
- [ ] T025 [US2] Implementar `meta_efetiva` e `cumpriu` em `app/gamificacao/dominio.py` e `avaliar_dia` em `app/gamificacao/servicos.py` (linha do dia, revisados com `primeira_do_dia`, cópia da meta e do fuso, restantes pelo provedor, marcação com `meta_cumprida_em` e `ultimo_dia_estudado`, log `dia_estudado`), chamado pelo ouvinte da T017, até que as T022 e a parte de revisões da T024 passem.
- [ ] T026 [US2] Inserir as chamadas aos ganchos da DTEC 057 em `app/cartoes/servicos.py` (suspender, reativar, excluir), `app/cartoes/registros.py` (participante) e `app/identidade/servicos.py` (`PATCH /perfil`, com `fuso_anterior` quando o fuso muda), sempre depois das travas de quem chama, e implementar `depois_de_alterar` em `app/gamificacao/ouvintes.py` (reavalia a linha de hoje, se existir), até que as T023 e T024 passem. O ouvinte de `antes_de_alterar` fica vazio até a T035. As suítes da 001 e da 003 continuam verdes.
- [ ] T027 [US2] Implementar `meta_cumprida_em(dia)` em `app/gamificacao/consultas.py`, `depoisDaMeta` em `NoTrilha` e `Licao` e `metaCumpridaAgora` na resposta da avaliação, com a meta efetiva da trilha recalculada pelos restantes de agora, sem gravar, até que a T024 passe.
- [ ] T028 [P] [US2] Ampliar os testes de componente: `PainelProgresso` com "12 de 20 cartões hoje", `progressbar` com valores, meta efetiva menor que a diária com o motivo e meta cumprida com texto e ícone (sem depender só de cor); `AnuncioGamificacao` com "Meta de hoje cumprida."; marca "depois da meta" nos nós da trilha; `vitest-axe`.
- [ ] T029 [US2] Implementar a meta no `PainelProgresso` (topo da trilha e fechamento), o anúncio da meta e a marca nos nós, até que a T028 passe.
- [ ] T030 [US2] Executar a verificação da US2 no [quickstart](quickstart.md) e registrar a evidência.

## Fase 5 História de usuário 3 Manter a sequência sem punição injusta (P2)

**Objetivo:** sequência atual e recorde exatos, com dias neutros, sem tarefa periódica e sem brechas.  
**Teste independente:** simular, com relógio controlado, a sequência de dias "estudado, estudado, neutro, estudado, não estudado, estudado" e confirmar a sequência atual de 1 e o recorde de 3.

- [ ] T031 [P] [US3] Criar os testes unitários em `tests/unit/gamificacao/test_sequencia.py` ([DTEC 061](research.md#decisão-dtec-061-liquidação-dos-dias-passados-dia-neutro-e-sequência) e [062](research.md#decisão-dtec-062-mudança-de-fuso-e-horário-de-verão)):
  - `liquidar` e `aplicar_sequencia` contra um oráculo que simula dia a dia, com Hypothesis (dias com ou sem revisões, disponibilidade, retiradas e mudanças de meta) (CS-002);
  - o teste independente da US3 (atual 1, recorde 3);
  - `pendente` liquidado vira `nao_estudado`; datas sem linha antes do primeiro dia disponível viram `neutro`, e as demais `nao_estudado`; linhas já liquidadas não mudam; linha `estudado` no intervalo não é contada de novo;
  - `datas_puladas` com saltos de 0, 1 e 2 datas.
- [ ] T032 [P] [US3] Criar os testes de integração em `tests/integration/gamificacao/test_liquidacao.py`:
  - **brecha fechada:** suspender, excluir ou zerar o limite de novos hoje não salva a sequência quebrada ontem; trocar o fuso no fim de um dia não estudado não o torna neutro;
  - **sem quebra injusta:** reativar hoje um cartão suspenso durante a ausência não quebra a sequência;
  - **estado anterior:** a primeira revisão de hoje liquida com o estado anterior do cartão revisado;
  - **leitura sem escrita:** `GET /trilha` exibe a quebra ainda não liquidada sem gravar `dias_estudo` nem `usuarios`;
  - **limites:** ausência de 365 dias liquidada numa inserção; sequência longa (1.000 dias pela fábrica) com o recorde certo.
- [ ] T033 [P] [US3] Criar os testes funcionais em `tests/functional/gamificacao/test_us3_sequencia.py`:
  - cenários 1 a 5 e o teste independente, com relógio controlado;
  - revisão às 3h50 no fuso do estudante conta para o dia anterior (CB-25);
  - mudança de fuso vivida em parte (`America/Sao_Paulo` → `Asia/Tokyo`), com data pulada (`Pacific/Pago_Pago` → `Pacific/Kiritimati`, `data_pulada`) e com data repetida (caminho inverso), contada uma vez (D-003);
  - horário de verão em `America/Sao_Paulo` (ano com horário de verão) e `America/Santiago`;
  - **segurança:** as revisões, retiradas e mudanças de fuso de uma conta não alteram dias, XP nem sequência de outra.
- [ ] T034 [US3] Implementar `liquidar`, `aplicar_sequencia` e `datas_puladas` em `app/gamificacao/dominio.py`, como funções puras, até que a T031 passe.
- [ ] T035 [US3] Implementar `liquidar` em `app/gamificacao/servicos.py`: chamado pelo ouvinte da revisão antes dos eventos e por `antes_de_alterar`; em `depois_de_alterar` com `fuso_anterior`, as datas puladas como `neutro` e nova liquidação no fuso novo; a marcação do dia passa a fazer `sequencia_atual += 1`, o recorde e `dias_liquidados_ate`; logs `dias_liquidados`, `datas_puladas_fuso` e `sequencia_recorde`. Implementar até que as T032 e T033 passem.
- [ ] T036 [US3] Completar `resumo` em `app/gamificacao/consultas.py` com a liquidação em memória (sequência exibida, `hojeCumprido`) e criar `dias_no_intervalo` e `xp_por_dia` para a 007, com testes em `tests/integration/gamificacao/test_consultas.py` (datas não liquidadas calculadas sem gravar; filtro de dono). Esclarecimento de 13/10/2026 pelo plano da 007 ([DTEC 065](../007-evolucao/research.md#decisão-dtec-065-período-e-situações-do-calendário)), sem mudança de comportamento: `dias_no_intervalo(sessao, usuario_id, inicio, fim, agora)` devolve uma entrada por data de `max(inicio, primeiro dia do estudante)` até `min(fim, hoje)`, com a situação gravada ou calculada nas datas passadas, `estudado`, `pendente` ou ausente em hoje, e `data_pulada`; testes do recorte no primeiro dia e em hoje.
- [ ] T037 [P] [US3] Ampliar `PainelProgresso.test.tsx`: sequência com "hoje falta" enquanto hoje não foi cumprido (US3-5); recorde; sequência 0 depois de uma quebra; anúncio "Sequência de N dias." ao cumprir a meta; `vitest-axe`.
- [ ] T038 [US3] Implementar a sequência e o recorde no `PainelProgresso` e no fechamento, até que a T037 passe.
- [ ] T039 [US3] Executar a verificação da US3 no [quickstart](quickstart.md) (saída dos testes com o teste independente) e registrar a evidência.

## Fase final Qualidade transversal

- [ ] T040 Criar `tests/security/gamificacao/test_gamificacao_seguranca.py`: o resumo é sempre do estudante da sessão; logs da gamificação sem texto de cartão (captura); `401` sem sessão e `403` sem CSRF continuam nas rotas afetadas; o provedor simulado de IA registra zero chamadas nas rotas afetadas.
- [ ] T041 Ampliar `tests/functional/desempenho/` e medir no ambiente local: a avaliação da 005 com a gamificação abaixo de 150 ms no p95 (CS-004 da 005); `GET /trilha` com 3 mil cartões e 60 dias sem liquidar abaixo de 200 ms no p95; a liquidação de 365 dias abaixo de 100 ms.
- [ ] T042 Executar nos contêineres as suítes completas do backend e do frontend (inclusive as da 001, da 003 e da 005), a qualidade estática e a verificação do contrato, e confirmar a integração contínua aprovada na `develop`. Registrar as contagens de testes e a cobertura.
- [ ] T043 Revisar e registrar as evidências manuais: teclado, leitor de tela (anúncio de XP e da meta sem mover o foco), 320 px, contraste e movimento reduzido na trilha, na lição e no fechamento (RQ-003).
- [ ] T044 Atualizar a documentação:
  - o [quickstart](quickstart.md), com os comandos realmente verificados;
  - `docs/skills/padroes-implementacao.md`, com `nucleo/disponibilidade.py` (provedor e ganchos), a trava da linha do estudante e a regra de que toda alteração de disponibilidade chama os ganchos;
  - o "Mapa do repositório" do `.agents/AGENTS.md`, com o domínio `gamificacao`.
- [ ] T045 Atualizar o [traceability.md](traceability.md) com os nomes reais dos testes e corrigir requisitos sem teste ou tarefa.

## Dependências

- **Specs anteriores:** as T001 a T052 da 001, as T001 a T033 da 003 e as T001 a T049 da 005 bloqueiam toda esta lista.
- **Preparação e base:**
  - a T001 vem antes de tudo;
  - a T002 bloqueia a T003, e a T003 bloqueia a Fase 2;
  - a T004 bloqueia as T006, T007, T008 e todos os testes de integração;
  - as T006 e T007 bloqueiam a T012; a T011 e a T012 dependem da T004;
  - a Fase 2 (T004 a T013) bloqueia todas as histórias.
- **US1:** T014, T015 e T016 sem dependência entre si → T017 → T018 → T020 (usa os tipos gerados) → T021. A T019 pode ser escrita em paralelo ao backend.
- **US2:** depende da T017 (ouvinte). T022, T023 e T024 → T025 → T026 → T027 → T029 → T030; a T028 em paralelo ao backend.
- **US3:** depende da T025 (marcação) e da T026 (ganchos chamados). T031 → T034; T032 e T033 → T035 → T036 → T038 → T039; a T037 em paralelo ao backend.
- **Specs seguintes:** a 007 lê dias e XP por `gamificacao/consultas.py` (T036) ([obrigações no plano](plan.md#obrigações-registradas-para-as-próximas-specs)).
- **Fase final:** depende de todas as histórias.

## Pontos de paralelismo

- **Base:** T005, T006, T007, T008, T009 e T010 alteram arquivos distintos.
- **Histórias:** em cada uma, as tarefas de teste marcadas com `[P]` podem ser escritas em paralelo. O frontend (T019 e T020; T028 e T029; T037 e T038) avança em paralelo ao backend depois da T012.
- **Entre histórias:** a T034 (funções puras da sequência) pode ser feita por outra pessoa durante a US2, porque não depende de banco.

## Estratégia de incremento

1. **Base completa:** a T013 prova a migração, o provedor, os campos aditivos nas respostas da 005 e o contrato superconjunto.
2. **P1 demonstrável:** entregar a US1 (XP com anúncio) e a US2 (meta e dia estudado) sobre as lições da 005. É o que entra na apresentação de 15/10/2026.
3. **Sequência:** acrescentar a US3 (liquidação, ganchos `antes` e fuso), sem quebrar a P1. A suíte completa passa a cada commit.
4. **Verificação final:** desempenho, evidências manuais e documentação. Nenhum merge na `main` acontece sem todos os testes passando (regra 17).
