# Tarefas da funcionalidade

**Funcionalidade:** 007-evolucao (evolução mínima)  
**Entrada:** [spec](spec.md), [plano](plan.md) (aprovado em 13/10/2026), [pesquisa](research.md), [modelo de dados](data-model.md), [contrato](contracts/openapi.yaml) e [quickstart](quickstart.md)  
**Formato:** `[ID] [P?] [US?] ação com caminho exato e resultado verificável`  
**Status:** aprovadas em 13/10/2026 por Artur Lins (equipe), junto com a [rastreabilidade](traceability.md)

- `[P]` indica que a tarefa pode ser executada em paralelo, porque não altera os mesmos arquivos nem depende de outra tarefa pendente.
- `[US1]` relaciona a tarefa à história de usuário única da spec.
- Marque `[x]` somente quando o resultado e a sua verificação estiverem concluídos (regra 6).
- **Caminhos:** `backend/src/app/` aparece abreviado como `app/`, e `backend/tests/` como `tests/`.
- **Pré-requisitos:**
  - da [spec 006](../006-xp-meta-sequencia/tasks.md), todas as tarefas (T001 a T045), o que já inclui as da 005 e as partes da 001 e da 003 de que a 006 depende. As mais usadas aqui são `gamificacao/consultas.py` com `resumo` e `dias_no_intervalo` (T036), a fábrica `tests/fabricas_gamificacao.py` (T008) e o teste de arquitetura (T009);
  - da [spec 002](../002-materias-fontes/tasks.md), todas as tarefas (T001 a T051): matérias, a lista ordenada por nome e a exclusão de matéria, usada num caso de borda;
  - da [spec 001](../001-conta-acesso/tasks.md), o layout autenticado (T026) e o teste de contrato (T037).
- **Testes antes do código:** as tarefas de teste vêm antes das de implementação. Os testes começam falhando e passam ao fim da história.
- **Relógio:** todo teste que depende de instante usa o relógio injetável da T007 da 005.
- **Alterações em specs anteriores:** as consultas novas em `cartoes`, `revisao` e `materias` são só de leitura e não mudam o comportamento dessas specs. As suítes delas continuam verdes a cada commit.
- **Commits:** todo trabalho acontece na `develop` (regra 14), com um commit atômico por tarefa ou por par teste e implementação, citando o ID da tarefa (ex.: `feat(evolucao): calcula o período do calendário [T010]`). O escopo `evolucao` identifica esta spec.

## Fase 1 Preparação

- [ ] T001 **Registrar a pessoa responsável:** quem assumir a implementação da 007 escreve o próprio nome no campo "Responsável pela implementação" do [plano](plan.md) e no registro de prompts da sessão de implementação. **Verificação:** o nome está nos dois lugares antes de qualquer outra tarefa, e Artur Lins aprova a mudança.
- [ ] T002 [P] Criar `tests/integration/nucleo/test_transacao_leitura.py` ([DTEC 064](research.md#decisão-dtec-064-leitura-consolidada-da-evolução)):
  - dentro de `transacao_leitura_consistente()`, `show transaction_isolation` devolve `repeatable read` e `show transaction_read_only` devolve `on`;
  - um `INSERT` ou `UPDATE` falha com erro de transação somente leitura;
  - uma linha confirmada por outra conexão depois da primeira leitura não aparece nas leituras seguintes da mesma transação;
  - a transação da requisição (sessão da 001) continua `read committed` e grava `ultimo_uso_em`.
- [ ] T003 Implementar `transacao_leitura_consistente()` em `app/nucleo/banco.py`, com `isolation_level="REPEATABLE READ"` e `postgresql_readonly=True`, ou `SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY` como primeira instrução se o dialeto do psycopg 3 não aplicar a opção, até que a T002 passe.

## Fase 2 Base compartilhada (bloqueia a história)

- [ ] T004 [P] Criar os testes das consultas novas nos domínios donos, em `tests/integration/evolucao/test_consultas_donos.py` ([DTEC 066](research.md#decisão-dtec-066-cartões-dominados-atuais)):
  - **`contar_dominados_por_materia(sessao, usuario_id, limiar)`:**
    - `ativo` e `suspenso` com estabilidade acima do limiar contam, e exatamente no limiar também;
    - não contam `aguardando_revisao`, `recusado`, estabilidade nula e estabilidade 20,99;
    - a contagem é agrupada por `materia_id`.
  - **`dominados_por_materia(sessao, usuario_id)`:**
    - usa `LIMIAR_DOMINADO_DIAS` vigente;
    - com um limiar de teste diferente (versão 2, por *monkeypatch* de `app/revisao/regras.py`), a contagem muda e `dominado_em` não muda;
    - um cartão que tem `dominado_em` mas estabilidade 5 (caiu depois de um Errei) não conta.
  - **`existe_revisao(sessao, usuario_id)`:** falso sem revisões; verdadeiro com uma revisão de cartão já excluído (`cartao_id` nulo).
  - **`listar_nomes(sessao, usuario_id)`:** `id`, `public_id` e nome, ordenados como a lista de matérias da 002.
  - **Isolamento (DTEC 019):** toda consulta recebe `usuario_id` e ignora os dados de outra conta.
- [ ] T005 Implementar as consultas da T004, até que ela passe:
  - `contar_dominados_por_materia` em `app/cartoes/consultas.py`, com uma única consulta agregada;
  - `dominados_por_materia` e `existe_revisao` em `app/revisao/consultas.py`. O limiar é lido só de `app/revisao/regras.py`;
  - `listar_nomes` em `app/materias/consultas.py`.
- [ ] T006 [P] Criar `tests/integration/evolucao/test_dias_no_intervalo.py`, que confere o esclarecimento da [DTEC 065](research.md#decisão-dtec-065-período-e-situações-do-calendário) sobre a T036 da 006:
  - conta criada há 10 dias: o intervalo de 26 semanas devolve só 10 datas, a primeira é o dia de estudo de `criado_em`, e a última é hoje;
  - um `fim` posterior a hoje para em hoje;
  - hoje volta como `pendente`, `estudado` ou ausente;
  - datas passadas não liquidadas voltam calculadas, e `dias_estudo` e `usuarios` não mudam;
  - `data_pulada` volta nas datas puladas.

  Se a T036 da 006 já cobrir esses casos, a tarefa confere e referencia os testes existentes. Se faltar o recorte, ele é implementado em `app/gamificacao/consultas.py`, sem mudar as demais saídas.
- [ ] T007 [P] Ampliar `tests/arquitetura/test_camadas.py`:
  - `app/evolucao` importa só `gamificacao.consultas`, `revisao.consultas`, `materias.consultas` e `app.nucleo`; nenhum modelo ORM nem repositório de outro domínio;
  - nenhum domínio importa `app.evolucao`;
  - a regra "nenhum domínio importa `revisao`" ganha só a exceção `evolucao` → `revisao.consultas`;
  - `app/evolucao` não tem `modelos.py`, `repositorios.py` nem `registros.py`;
  - nenhum módulo fora de `revisao` lê `LIMIAR_DOMINADO_DIAS`.
- [ ] T008 [P] Criar a fábrica `tests/fabricas_evolucao.py`, que roda como módulo, só com `APP_AMBIENTE=desenvolvimento` e só com contas `@exemplo.com` (regra 10):
  - **`--cenario trinta-dias`:** usa `tests/fabricas_gamificacao.py` (006) e os serviços da 003 e da 005 com o relógio avançando. Cria a conta 30 dias no passado e 2 matérias (`Biologia` e `História`) e combina:
    - dias estudados, não estudados e neutros, mais um dia ainda não liquidado;
    - dominados nas duas matérias;
    - um cartão que perdeu estabilidade depois de um Errei, um suspenso dominado e um excluído dominado.

    Imprime a tabela de valores esperados, que fica também numa constante usada pelo teste da T011.
  - **`--cenario um-ano`:** inserção em massa respeitando os `CHECK` da 006, com 365 dias liquidados, 30 não liquidados, 3 mil cartões em 10 matérias, cerca de 30 mil revisões e os eventos de XP correspondentes, mais `xp_total` coerente.

  **Verificação:** os dois cenários rodam; o segundo leva menos de 60 s; contas fora de `exemplo.com` são recusadas.

## Fase 3 História de usuário 1 Ver minha evolução (P1)

**Objetivo:** a tela de evolução mostra o calendário das últimas 26 semanas, o XP total, a sequência atual e o recorde, e os cartões dominados no total e por matéria, todos calculados no servidor e em texto, com o estado vazio para quem ainda não revisou.  
**Teste independente:** com dados fictícios de 30 dias (estudados, não estudados e neutros), 2 matérias e cartões dominados, abrir a evolução e conferir cada valor com o calculado à mão (CS-001).

### Backend

- [ ] T009 [P] [US1] Criar `tests/unit/evolucao/test_dominio.py` (DTEC 065 e 066):
  - **`periodo(hoje)`:** para cada dia da semana, na virada de mês e de ano e em 29/02 de ano bissexto, `inicio` é domingo, `fim` é sábado, há 182 dias e `inicio <= hoje <= fim`;
  - **`situacao_exibida`:** cada linha da tabela da DTEC 065; `pendente` em data passada lança o erro de invariante; hoje nunca é `nao_estudado`; `data_pulada` vira `neutro`;
  - **`total_estudados`:** conta só `estudado`, inclusive hoje cumprido;
  - **`juntar_dominados`:** inclui as matérias com 0, mantém a ordem recebida de `listar_nomes`, e o total é a soma.
- [ ] T010 [US1] Implementar `periodo`, `situacao_exibida`, `total_estudados` e `juntar_dominados` em `app/evolucao/dominio.py`, como funções puras, sem FastAPI nem SQLAlchemy, até que a T009 passe.
- [ ] T011 [P] [US1] Criar `tests/functional/evolucao/test_us1_evolucao.py`, pela API, com cookies e relógio controlado:
  - **US1-1 (RF-001):** as quatro situações, `inicio` e `fim` da grade, datas contíguas até hoje e `totalEstudados`;
  - **US1-2 (RF-002, RF-003):** XP total, sequência atual e recorde **iguais** aos de `GET /trilha` no mesmo instante, inclusive com dias não liquidados que quebram a sequência; dominados por matéria e total;
  - **US1-3 (RF-005):** conta com matéria e cartões, mas sem revisão, tem `possuiRevisoes = false`;
  - **US1-4:** excluir um cartão dominado diminui os dominados em 1 e não muda `xpTotal`;
  - **CS-001 (teste independente):** cenário `trinta-dias` da T008, com todos os campos da resposta comparados à tabela escrita à mão;
  - **Casos de borda:**
    - conta criada há 10 dias, sem datas anteriores;
    - hoje sem revisão é `em_andamento`, e hoje cumprido é `estudado`;
    - um dominado que perdeu estabilidade sai da contagem e mantém o bônus em `eventos_xp`;
    - um suspenso dominado conta;
    - uma matéria excluída some da lista, e o XP permanece;
    - mudança de fuso com data pulada (`neutro`) e com data repetida (uma entrada);
  - **Sem efeito colateral (DTEC 061):** com 10 dias não liquidados, `dias_estudo` e `usuarios` ficam iguais depois da leitura;
  - **Cache:** `Cache-Control: no-store`.
- [ ] T012 [P] [US1] Criar `tests/security/evolucao/test_evolucao_seguranca.py` (RQ-003):
  - com duas contas e históricos diferentes, a resposta de cada uma não muda com revisões, matérias, cartões e exclusões da outra, e nenhum `materiaId` alheio aparece;
  - sem sessão, `401 nao_autenticado`;
  - a resposta não tem `id` interno (busca recursiva por chaves `id`);
  - o log `evolucao_consultada` não tem nome de matéria nem texto de cartão (captura);
  - o provedor simulado de IA registra zero chamadas.
- [ ] T013 [P] [US1] Criar `tests/adversarial/evolucao/test_evolucao_adversarial.py`:
  - 50 matérias com nomes de 60 caracteres (emoji, texto da direita para a esquerda e caracteres combinantes) e 182 dias estudados: a resposta valida contra o esquema `Evolucao`;
  - parâmetros `?inicio=…`, `?fim=…` e `?usuario=…` não alteram o período nem o estudante;
  - `GET /evolucao` em paralelo com avaliações (005) e suspensões (003): sem *deadlock* e com cada resposta coerente (`xpTotal` igual à soma dos eventos no *snapshot*).
- [ ] T014 [US1] Implementar a rota, até que as T011 a T013 passem:
  - `consultar_evolucao(usuario_id, agora)` em `app/evolucao/servicos.py`: abre `transacao_leitura_consistente()` e, nela, chama `resumo`, `periodo`, `dias_no_intervalo`, `situacao_exibida`, `dominados_por_materia`, `listar_nomes` e `existe_revisao`;
  - os DTOs `Evolucao`, `CalendarioEstudo`, `DiaCalendario`, `DominadosAtuais` e `DominadosMateria` em `app/evolucao/dtos.py`, que reaproveitam o DTO `ResumoGamificacao` da 006;
  - `app/evolucao/mapeadores.py` e `app/evolucao/excecoes.py`, este com o erro de invariante;
  - `GET /api/v1/evolucao` em `app/evolucao/rotas.py`, registrado no roteador da aplicação, com `Cache-Control: no-store`;
  - o log `evolucao_consultada` (duração, quantidades e `possuiRevisoes`, sem nomes).
- [ ] T015 [US1] Ampliar `tests/integration/test_contrato_openapi.py`:
  - o OpenAPI gerado contém `docs/specs/007-evolucao/contracts/openapi.yaml`;
  - `ResumoGamificacao`, `ProgressoMeta` e `Sequencia` da 007 são iguais aos da 006;
  - o enum `Erro.codigo` não perdeu códigos.

  Regenerar `backend/openapi.json` e rodar `npm run gerar:api`. **Verificação:** o teste passa, e a integração contínua não acusa arquivo gerado desatualizado.

### Frontend

- [ ] T016 [P] [US1] Criar os tokens `dia-estudado`, `dia-nao-estudado`, `dia-neutro` e `dia-andamento`, nos temas claro e escuro, em `frontend/src/estilos/`, e o teste `frontend/src/estilos/contraste.test.ts` ([DTEC 067](research.md#decisão-dtec-067-calendário-acessível-e-responsivo)). O teste calcula a razão de contraste da WCAG e exige 3:1 em cada tema:
  - (a) indicador de cada situação contra o fundo;
  - (b) preenchimento de estudado contra o fundo das células sem preenchimento;
  - (c) glifo contra o preenchimento da célula.
- [ ] T017 [P] [US1] Criar `frontend/src/funcionalidades/evolucao/CalendarioEstudo.test.tsx` (RQ-001), com dados do MSW:
  - `role="grid"`, cabeçalhos de coluna (domingo a sábado) e de linha;
  - a semana corrente na primeira linha;
  - cada célula com dado anuncia a data e a situação ("domingo, 12 de outubro de 2026: estudado"), sem deslocamento de fuso (teste com `TZ` diferente de `America/Sao_Paulo`);
  - uma parada de Tab com foco inicial em hoje; as setas, Home, End, Ctrl+Home e Ctrl+End;
  - o foco nunca para em célula vazia; as células vazias têm `aria-hidden`;
  - cada situação tem um glifo e uma forma distintos, visíveis sem cor;
  - a legenda está presente;
  - o total aparece em texto;
  - `vitest-axe` sem violações.
- [ ] T018 [US1] Implementar `CalendarioEstudo` e `LegendaCalendario` em `frontend/src/funcionalidades/evolucao/`, com os utilitários de foco e teclado do `react-aria` e os tokens da T016, até que as T016 e T017 passem.
- [ ] T019 [P] [US1] Criar `frontend/src/funcionalidades/evolucao/TelaEvolucao.test.tsx`:
  - **Indicadores (RF-002, RF-004):** XP total, sequência atual com "hoje falta", recorde e dominados em texto, todos vindos da resposta;
  - **Carregando:** esqueleto sem números enquanto a resposta não chega (MSW atrasado);
  - **Lista por matéria (RF-003):** nomes longos quebram linha, o rótulo é "cartões dominados", e a frase do critério vem de `limiarDias`;
  - **Estado vazio (RF-005):** com `possuiRevisoes = false`, há o texto e o botão para a trilha, sem números nem grade;
  - **Erro:** `500` mostra "Tentar de novo", e `401` redireciona ao login (001);
  - **320 px (RQ-002):** nenhum elemento mais largo que a janela;
  - **Medida:** as marcas `evolucao-inicio` e `evolucao-pronta` e a medida `evolucao-carregada` existem;
  - `vitest-axe` sem violações na tela, no estado vazio e no erro.
- [ ] T020 [US1] Implementar a tela, até que a T019 passe:
  - a rota `frontend/src/rotas/_autenticado/evolucao.tsx`, com TanStack Query (`staleTime: 0`) e as marcas de desempenho;
  - `TelaEvolucao`, `IndicadoresEvolucao`, `ListaDominados` e `EstadoVazioEvolucao` em `frontend/src/funcionalidades/evolucao/`;
  - o item "Evolução" na navegação do layout autenticado ([design, seção 4](../../base-specs/design.md#4-navegação)), criando a navegação lateral e inferior se ela ainda não existir.
- [ ] T021 [US1] Executar a verificação da US1 no [quickstart](quickstart.md) (passos 1 a 8) e os testes `functional`, `security` e `adversarial` da evolução, e registrar a evidência (saída dos testes e o teste independente do CS-001).

## Fase final Qualidade transversal

- [ ] T022 Criar `tests/functional/desempenho/test_evolucao.py` (CS-002, servidor): com o cenário `um-ano` da T008, `GET /evolucao` repetido 50 vezes sobre Postgres real, com o p95 abaixo de 300 ms. Se reprovar, registrar a medida e abrir a contingência da DTEC 066 (índice ou consulta ajustada, com migração) como tarefa nova, sem afrouxar o limite.
- [ ] T023 Executar nos contêineres as suítes completas do backend e do frontend (inclusive as da 001 a 006), a qualidade estática e a verificação do contrato, e confirmar a integração contínua aprovada na `develop`. Registrar as contagens de testes e a cobertura.
- [ ] T024 Revisar e registrar as evidências manuais (passos 5 a 7 e 9 do quickstart):
  - leitor de tela (NVDA ou Orca) e teclado no calendário;
  - simulação de acromatopsia;
  - 320 px;
  - contraste nos temas claro e escuro;
  - p95 da tela abaixo de 1 s com o cenário `um-ano` (CS-002, tela).
- [ ] T025 Atualizar a documentação:
  - o [quickstart](quickstart.md), com os comandos realmente verificados;
  - `docs/skills/padroes-implementacao.md`, com `transacao_leitura_consistente` para leituras consolidadas e a exceção `evolucao` → `revisao.consultas`;
  - `docs/skills/padroes-interface.md`, com o padrão de calendário em *grid* e a marcação por forma além da cor;
  - o "Mapa do repositório" do `.agents/AGENTS.md`, com o domínio `evolucao`.
- [ ] T026 Atualizar o [traceability.md](traceability.md) com os nomes reais dos testes e corrigir requisitos sem teste ou tarefa.

## Dependências

- **Specs anteriores:** as T001 a T045 da 006 e as T001 a T051 da 002 bloqueiam toda esta lista.
- **Preparação e base:**
  - a T001 vem antes de tudo;
  - a T002 bloqueia a T003;
  - a T004 bloqueia a T005;
  - as T006, T007 e T008 não dependem entre si;
  - a Fase 2 (T004 a T008) e a T003 bloqueiam a história.
- **US1, backend:** T009 → T010; T011, T012 e T013 (depois da T008) → T014 (depois das T003, T005 e T010) → T015.
- **US1, frontend:** T016 e T017 → T018; T019 → T020 (depois das T015 e T018) → T021.
- **Fase final:** a T022 depende das T008 e T014; as demais dependem da história completa.

## Pontos de paralelismo

- **Base:** T002, T004, T006, T007 e T008 alteram arquivos distintos.
- **Backend:** T009, T011, T012 e T013 podem ser escritos em paralelo.
- **Frontend:** T016, T017 e T019 avançam em paralelo ao backend, com o MSW a partir do contrato. Só a T020 precisa dos tipos gerados (T015).

## Estratégia de incremento

1. **Base completa:** transação de leitura, consultas nos domínios donos, recorte de `dias_no_intervalo`, arquitetura e fábricas.
2. **Corte mínimo, se o prazo apertar (suposição da spec):** com a T014 e a T020 sem o calendário, a tela mostra os indicadores (XP, sequência e dominados) e o estado vazio. O calendário (T016 a T018) entra em seguida, sem mudar o contrato.
3. **P1 completa:** o calendário acessível e a verificação do teste independente (T021). É o que entra na apresentação de 15/10/2026.
4. **Verificação final:** desempenho, evidências manuais e documentação. Nenhum merge na `main` acontece sem todos os testes passando (regra 17).
