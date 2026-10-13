# Guia de validação local

**Funcionalidade:** 003-cartoes-manuais (cartões criados e gerenciados pelo estudante)

Este guia descreve como outra pessoa verifica o incremento sem depender de explicações orais. Ele parte do ambiente das specs [001](../001-conta-acesso/quickstart.md) e [002](../002-materias-fontes/quickstart.md): mesmos pré-requisitos, mesma configuração e mesmos comandos de execução e de testes. Os passos abaixo passam a funcionar depois das tarefas da US1 da 003 (`tasks.md`, etapa 6). Todo serviço roda em contêiner (regra 11).

## Pré-requisitos

- O ambiente da 002 funcionando (`docker compose up --build`, serviços saudáveis em `docker compose ps`) e a migração `0004_cartoes` aplicada (a API aplica as migrações ao subir, como na 001).
- Uma conta fictícia criada pela interface (ex.: `ana.teste@exemplo.com`, regra 10), com a matéria `Biologia` e a fonte `Citologia` concluída (passos 2 e 5 do quickstart da 002).
- Variáveis novas no `.env`: nenhuma é obrigatória, porque todas têm padrão no `.env.example` ([plano](plan.md#variáveis-de-ambiente-acréscimos-ao-envexample)).

## Dados de exemplo

Para a US4, o comando abaixo cria 120 cartões fictícios na matéria indicada da conta indicada. Os textos são gerados pela mesma fábrica dos testes, com acentos, cedilha e variação de maiúsculas, e uma parte dos cartões fica suspensa:

```bash
docker compose run --rm api uv run python -m tests.fabricas_cartoes --email ana.teste@exemplo.com --materia Biologia --quantidade 120
```

O comando só roda com `APP_AMBIENTE=desenvolvimento` e recusa contas fora do domínio `exemplo.com` (regra 10).

## Testes

Os comandos da 001 valem sem mudança. Para rodar só os testes da 003 e a reexecução dos testes de exclusão da 002 com cartões reais:

```bash
docker compose run --rm api uv run pytest tests -k "cartoes or exclusao_fonte or organizar"
docker compose run --rm web npm test -- cartoes
```

## Verificação da história P1

### US1 Criar um cartão

1. Abra **Matérias** → `Biologia` → aba **Cartões**. **Esperado:** estado vazio com a ação "Criar o primeiro cartão".
2. Acione "Criar cartão". **Esperado:** o painel abre com o foco na frente e mostra os contadores de caracteres (frente até 1.000, verso até 2.000, explicação até 1.000), com os limites vindos do servidor.
3. Preencha a frente `Qual organela produz ATP?`, o verso `A mitocôndria.` e, na explicação, duas linhas separadas por `Enter`. Salve com `Ctrl+Enter` (`⌘+Enter` no macOS), o atalho de "Salvar e criar outro". **Esperado:** o painel continua aberto, vazio e com o foco na frente, e o cartão aparece na lista como **Ativo**, com o selo "Criado por você" (texto e ícone) e a quebra de linha preservada (cenário 1).
4. Tente salvar um cartão com a frente só com espaços e outro com o verso acima do limite (cole um texto longo). **Esperado:** nada é criado; o erro aparece junto do campo; os valores digitados continuam no painel (cenário 2).
5. Crie um cartão indicando a fonte `Citologia` como referência. **Esperado:** "Criado por você" com o título `Citologia`, **sem** o selo "Gerado e verificado" (cenário 3).
6. Crie um cartão com a frente `<script>alert(1)</script>`. **Esperado:** o texto aparece literalmente, e nada é executado (RQ-001).
7. **CS-001:** com um cronômetro, crie 5 cartões seguidos só com o teclado, usando `Tab` entre os campos e `Ctrl+Enter` para "Salvar e criar outro"; feche o painel com `Esc` no fim. **Esperado:** em até 3 minutos, sem usar o mouse. O foco volta à frente depois de cada gravação.

**Evidência observável:**

- Os testes `functional` da US1 passam.
- O estado gravado do cartão é o de um cartão novo do FSRS, na ordem de criação:

  ```bash
  docker compose exec db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "select public_id, origem, situacao, estado_fsrs, passo, ultima_revisao, entrada_estudo_em from cartoes order by criado_em desc limit 5;"'
  ```

  **Esperado:** `criado`, `ativo`, `aprendizado`, `0`, `ultima_revisao` vazia e `entrada_estudo_em` crescente.
- O log mostra `cartao_criado` com `public_id` e sem nenhum texto do cartão:

  ```bash
  docker compose logs api | grep cartao_criado | tail -3
  ```

### US2, US3 e US4 (verificação complementar)

- **Editar (US2):** edite a frente de um cartão e salve. **Esperado:** o novo texto aparece, e a origem continua "Criado por você". Abra a edição e salve sem mudar nada. **Esperado:** nada muda, nem a data de atualização (cenário 3). Antes e depois da edição, `vencimento`, `estabilidade` e `estado_fsrs` são iguais na consulta acima (CS-002).
- **Editar cartão gerado (US2-2):** sem a 004, só pelos testes. O teste funcional usa um cartão `gerado_verificado` criado pela fábrica e confere a mudança para "Editado por você". A evidência mantida é verificada pela 004.
- **Suspender e reativar (US3-1, 2):** suspenda um cartão. **Esperado:** situação **Suspenso**, anunciada para o leitor de tela, com o mesmo `vencimento` no banco. Reative-o. **Esperado:** **Ativo**, com o mesmo `vencimento`. A ausência nas lições é verificada com a 005.
- **Excluir (US3-3):** exclua um cartão. **Esperado:** o diálogo avisa que a exclusão é definitiva, com o foco preso nele; depois de confirmado, o cartão some da lista.
- **"Fonte apagada" (D-006):** exclua a fonte `Citologia` escolhendo "Excluir os cartões junto". **Esperado:** o diálogo da 002 mostra 1 cartão de referência mantido; depois, o cartão do passo 5 continua na lista com `Citologia` e "Fonte apagada".
- **Exclusão da matéria (002 com cartões reais):** crie uma matéria `Química` com 2 cartões ativos e 1 suspenso. **Esperado:** a lista de matérias mostra 2 cartões ativos, e o diálogo de exclusão mostra 3 cartões que serão apagados (emenda da DTEC 027).
- **Encontrar (US4):** com os 120 cartões de exemplo, busque `celula`. **Esperado:** aparecem os cartões com "Célula", "CÉLULA" ou "célula" na frente ou no verso, com o total. Combine com o filtro **Suspenso** e com a origem **Criado por você**. Recarregue a página. **Esperado:** busca e filtros continuam aplicados. Busque `xyzw`. **Esperado:** "Nenhum cartão corresponde à busca", diferente do estado de matéria sem cartões (cenário 3). Role até "Carregar mais". **Esperado:** sem cartões repetidos.

## Falhas conhecidas

- **Entrada nas lições:** até a spec 005, "entra como cartão novo na próxima lição" e "suspenso não entra em lições" são verificados pelo estado gravado do cartão, não por uma lição real.
- **Cartões gerados:** até a spec 004, não há cartões "Gerado e verificado" pela interface. A RF-006 é verificada por testes com cartões da fábrica.
- **Revisões e XP preservados na exclusão (RF-008):** dependem das tabelas da 005 e da 006. Até lá, não há revisões nem XP a preservar.
- **Referência fixa:** a fonte de referência é escolhida só na criação; a edição altera frente, verso e explicação (escopo da spec).
