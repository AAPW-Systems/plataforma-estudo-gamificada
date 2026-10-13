# Guia de validação local

**Funcionalidade:** 006-xp-meta-sequencia (XP, meta diária e sequência)

Este guia descreve como outra pessoa verifica o incremento sem depender de explicações orais. Ele parte do ambiente das specs [001](../001-conta-acesso/quickstart.md) a [005](../005-licao-trilha/quickstart.md): mesmos pré-requisitos, comandos de execução e testes. Os passos abaixo passam a funcionar depois das tarefas da US1 e da US2 da 006 (`tasks.md`, etapa 6). Todo serviço roda em contêiner (regra 11).

## Pré-requisitos

- O ambiente da 005 funcionando (`docker compose up --build`, serviços saudáveis em `docker compose ps`), com a migração `0007_gamificacao` aplicada (a API aplica as migrações ao subir).
- Uma conta fictícia (ex.: `ana.teste@exemplo.com`, regra 10), com a meta diária padrão de 20 cartões, lição de 10 e limite de 20 novos por dia.

## Dados de exemplo

O comando da 005 cria a matéria `Biologia` com 12 cartões manuais novos e 3 devidos hoje. A 006 acrescenta a ele as opções `--novos` e `--devidos` (padrões 12 e 3, o comportamento da 005). A opção `--novos 5 --devidos 0` cria só 5 novos, para a US1, e `--novos 8 --devidos 0`, só 8, para a US2:

```bash
docker compose run --rm api uv run python -m tests.fabricas_revisao --email ana.teste@exemplo.com --novos 5 --devidos 0
```

O comando só roda com `APP_AMBIENTE=desenvolvimento` e recusa contas fora do domínio `exemplo.com` (regra 10).

## Testes

Os comandos da 001 valem sem mudança. Para rodar só os testes da 006, o da 005 que ela altera e a reverificação da 003:

```bash
docker compose run --rm api uv run pytest tests -k "gamificacao or disponibilidade or licao or trilha or cartoes or perfil"
docker compose run --rm web npm test -- gamificacao trilha licao
```

O CS-002 (virada, fuso e horário de verão) é verificado pelos testes de propriedade com oráculo e pelos funcionais com relógio controlado, em `tests/unit/gamificacao` e `tests/functional/gamificacao`. A passagem de dias não é simulada manualmente: a aplicação não tem relógio ajustável fora dos testes.

## Verificação das histórias P1

### US1 Ganhar XP ao revisar

1. Com 5 cartões novos, abra a trilha. **Esperado:** XP total 0, "0 de 5 cartões hoje" (meta efetiva 5: só há 5 disponíveis) e sequência 0 com "hoje falta".
2. Comece a lição. No primeiro cartão, revele e marque **Errei**. **Esperado:** o anúncio "Mais 10 de XP" é lido pelo leitor de tela, sem som; o foco vai para o cartão seguinte.
3. Revise os outros 4 cartões com qualquer nota. Quando o primeiro cartão voltar ("revendo"), marque **Bom**. **Esperado:** nenhum anúncio de XP na reapresentação.
4. No fechamento: **esperado** 50 de XP ganhos na lição (não 60), meta cumprida e sequência 1.
5. Reenvio: na aba de rede do navegador, reenvie a última requisição de avaliação. **Esperado:** `200`, `xpGanho` igual ao original e XP total inalterado.
6. Exclua um dos cartões revisados (lista da matéria, com confirmação). **Esperado:** a trilha continua com 50 de XP.

### US2 Cumprir a meta diária

1. Numa conta nova com 8 cartões novos e meta 20, abra a trilha. **Esperado:** "0 de 8 cartões hoje", com a indicação de que a meta de hoje é 8 porque todos os disponíveis contam.
2. Revise os 8. **Esperado:** no oitavo, o anúncio "Meta de hoje cumprida. Sequência de 1 dia." e, no fechamento, meta cumprida.
3. Crie mais 3 cartões e abra a trilha. **Esperado:** a meta continua cumprida (o dia não deixa de ser estudado), com "8 de 11".
4. Faça a lição extra ("Continuar"). **Esperado:** o progresso sobe para 11, a sequência continua 1, e o novo nó aparece marcado como "depois da meta".

## Verificação da US3

A US3 depende da passagem de dias e é verificada pelos testes (`-k "gamificacao and sequencia"`). O teste independente ("estudado, estudado, neutro, estudado, não estudado, estudado" → atual 1, recorde 3) aparece com esse nome na saída do pytest. Na interface, depois de um dia sem estudo com cartões disponíveis, a trilha do dia seguinte mostra sequência 0 e o recorde mantido. Num dia sem nenhum cartão disponível, a sequência é mantida.

## Runbook

- **Conferir o XP total (CS-001):**

  ```bash
  docker compose exec db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "select u.public_id, u.xp_total, coalesce(sum(e.quantidade), 0) as soma from usuarios u left join eventos_xp e on e.usuario_id = u.id group by u.id having u.xp_total <> coalesce(sum(e.quantidade), 0);"'
  ```

  **Esperado:** nenhuma linha.
- **Dias de um estudante:**

  ```bash
  docker compose exec db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "select dia, situacao, cartoes_revisados, meta_efetiva, data_pulada from dias_estudo d join usuarios u on u.id = d.usuario_id where u.email = '"'"'ana.teste@exemplo.com'"'"' order by dia desc limit 14;"'
  ```

- **Mudança dos valores de XP:** crie a versão seguinte em `gamificacao/regras.py` (as anteriores ficam) e rode o teste de regras publicadas. Alterar uma versão existente faz o teste falhar (DTEC 058).
- **Dias passados não liquidados:** são liquidados na próxima revisão, retirada de cartão ou mudança de preferência. Nenhuma ação manual é necessária (DTEC 061).
