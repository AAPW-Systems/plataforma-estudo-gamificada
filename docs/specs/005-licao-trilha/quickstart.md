# Guia de validação local

**Funcionalidade:** 005-licao-trilha (lição com repetição espaçada e trilha de progressão)

Este guia descreve como outra pessoa verifica o incremento sem depender de explicações orais. Ele parte do ambiente das specs [001](../001-conta-acesso/quickstart.md) a [004](../004-geracao-cartoes/quickstart.md): mesmos pré-requisitos, mesmos comandos de execução e de testes. Os passos abaixo passam a funcionar depois das tarefas da US1 e da US2 da 005 (`tasks.md`, etapa 6). Todo serviço roda em contêiner (regra 11).

## Pré-requisitos

- O ambiente da 003 funcionando (`docker compose up --build`, serviços saudáveis em `docker compose ps`) e a migração `0006_licoes_revisoes` aplicada (a API aplica as migrações ao subir).
- Uma conta fictícia (ex.: `ana.teste@exemplo.com`, regra 10), com as preferências padrão: lição de 10 cartões e limite de 20 novos por dia.
- Para a US2 com cartão gerado: o provedor simulado da 004 (`IA_PROVEDOR=teste`), sem rede nem chave.

## Dados de exemplo

O comando abaixo cria, na conta indicada, a matéria `Biologia` com 12 cartões manuais novos e 3 cartões já revisados que vencem hoje, todos com textos fictícios. Ele só roda com `APP_AMBIENTE=desenvolvimento` e recusa contas fora do domínio `exemplo.com` (regra 10):

```bash
docker compose run --rm api uv run python -m tests.fabricas_revisao --email ana.teste@exemplo.com
```

Para os cartões devidos, o comando grava estados do FSRS fabricados (em revisão, com vencimento anterior à próxima virada), como fariam revisões em dias passados.

## Testes

Os comandos da 001 valem sem mudança. Para rodar só os testes da 005 e as reverificações das specs 003 e 004:

```bash
docker compose run --rm api uv run pytest tests -k "revisao or licao or trilha or dia_estudo or fsrs or cartoes or geracao"
docker compose run --rm web npm test -- licao trilha
```

O teste de contrato da biblioteca (CS-001) roda na suíte normal (`tests/contrato/fsrs`). Se ele falhar depois de uma atualização da `fsrs`, a atualização não entra (DTEC 053).

## Verificação das histórias P1

### US1 Fazer a lição do dia

1. Abra a trilha. **Esperado:** "Começar lição", com 13 cartões disponíveis (3 devidos e 10 novos dentro do tamanho).
2. Acione "Começar lição". **Esperado:** a posição "1 de 10" e a frente de um dos 3 devidos; os botões de avaliação indisponíveis. Nas ferramentas do navegador, a resposta de `POST /api/v1/licoes` não contém o verso (cenários 1 e 2).
3. Pressione Espaço. **Esperado:** o verso aparece, e os quatro botões ficam disponíveis, com os atalhos 1 a 4 visíveis.
4. Pressione 3 (Bom). **Esperado:** o próximo cartão aparece sem espera perceptível (cenário 3).
5. Continue até o primeiro cartão novo e pressione 1 (Errei). Siga com os demais. **Esperado:** depois de um minuto, o cartão marcado Errei volta sinalizado como "revendo", e a posição não avança por causa dele (cenário 4).
6. Termine a lição. **Esperado:** o fechamento mostra as revisões feitas, os cartões distintos, os dominados (nenhum numa conta nova) e, se algum cartão ficou em passo curto não vencido, quantos voltam e a que horas (cenários 5 e 6).
7. **Esperado (teste independente):** a ordem foi devidos (mais atrasado primeiro) e depois novos na ordem de criação, e cada cartão tem um novo vencimento. Confira no banco:

   ```bash
   docker compose exec db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "select nota, estado_antes, estado_depois, vencimento_depois, primeira_do_dia, semente_fuzz from revisoes order by revisada_em;"'
   ```

8. Feche a aba no meio de uma lição nova e volte à trilha. **Esperado:** "Continuar lição", e a lição recomeça no cartão em que parou (CB-28).

### US2 Entender o erro

1. Com um cartão gerado (geração simulada da 004) na lição, pressione Errei. **Esperado:** a explicação aparece antes do próximo cartão, com "Ver evidência" recolhido; ao expandir, a fonte, o trecho e a página, quando conhecida (cenário 1).
2. Pressione Enter. **Esperado:** o próximo cartão aparece.
3. Com um cartão manual sem explicação, pressione Errei. **Esperado:** o próximo cartão aparece direto, sem área de explicação nem mensagem de erro (cenário 2).
4. **Esperado:** o log da API não mostra nenhum evento `chamada_ia` durante a lição (cenário 3).

**Evidência observável:** revisões em `revisoes` com estado antes e depois, versão dos parâmetros e semente; nó aceso na trilha; logs `licao_iniciada`, `revisao_registrada` e `licao_concluida`, sem texto dos cartões.

## Verificação das demais histórias

- **US3:** numa conta nova, a trilha mostra o convite para criar a matéria e enviar a fonte, sem nós. Depois de três lições, três nós alcançados, o nó atual e o próximo passo. Sem cartões disponíveis, nenhuma lição e o horário do próximo vencimento no fuso da conta.
- **US4:** no fechamento com cartões restantes, "Continuar" monta uma lição extra, que vira um novo nó. Esgotados os disponíveis, "Continuar" não aparece e o fechamento mostra o próximo vencimento.

## Medição do CS-004 (300 ms no percentil 95)

1. Rode o frontend em modo de produção local (`docker compose up web` com a imagem de produção) e abra a lição com 10 cartões.
2. Faça a lição inteira **só com o teclado** (Espaço e 1 a 4). Isso cobre a parte de operação do CS-004.
3. No console do navegador, execute:

   ```js
   performance.getEntriesByName('transicao-cartao').map(e => e.duration)
   ```

   A interface grava a medida `transicao-cartao` entre a nota e a exibição da frente seguinte (`performance.mark` e `performance.measure`).
4. Repita três lições (30 transições) e calcule o percentil 95. **Esperado:** até 300 ms. Registre o valor, a máquina e a data no registro da sessão de implementação.

A parte do servidor (150 ms no percentil 95 para avaliar e revelar) é verificada pelo teste `tests/functional/desempenho`.

## Runbook

- **Reproduzir uma revisão (RQ-004):** com o `id` da revisão, `docker compose run --rm api uv run python -m app.revisao.reproduzir <id>` refaz o cálculo a partir do estado antes, da versão dos parâmetros e da semente, e compara com o estado depois gravado. Diferença indica mudança da biblioteca ou dos parâmetros.
- **Lição aberta de dia anterior:** é encerrada no próximo "Começar lição" (D-005). Nenhuma ação manual é necessária.
- **Conferir o limite de novos do dia:**

  ```bash
  docker compose exec db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "select dia_estudo, count(*) from revisoes where ultima_revisao_antes is null group by 1 order by 1 desc limit 3;"'
  ```
