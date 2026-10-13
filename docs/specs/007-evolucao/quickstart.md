# Guia de validação local

**Funcionalidade:** 007-evolucao (evolução mínima)

Este guia descreve como outra pessoa verifica o incremento sem depender de explicações orais. Ele parte do ambiente das specs [001](../001-conta-acesso/quickstart.md) a [006](../006-xp-meta-sequencia/quickstart.md): os pré-requisitos, os comandos de execução e os testes são os mesmos. Os passos abaixo passam a funcionar depois das tarefas da US1 da 007 (`tasks.md`, etapa 6). Todo serviço roda em contêiner (regra 11).

## Pré-requisitos

- O ambiente da 006 funcionando (`docker compose up --build`, com os serviços saudáveis em `docker compose ps`). A 007 não tem migração nova.
- Contas fictícias do domínio `exemplo.com` (regra 10).

## Dados de exemplo

A fábrica da 007 só roda com `APP_AMBIENTE=desenvolvimento` e recusa contas fora do domínio `exemplo.com` (regra 10). Ela tem dois cenários:

```bash
# CS-001: 30 dias pelos serviços da 005 e da 006 com relógio controlado; imprime os valores esperados
docker compose run --rm api uv run python -m tests.fabricas_evolucao --email ana.teste@exemplo.com --cenario trinta-dias

# CS-002: um ano de histórico em massa (365 dias liquidados, 30 não liquidados, 3 mil cartões, 10 matérias)
docker compose run --rm api uv run python -m tests.fabricas_evolucao --email bia.teste@exemplo.com --cenario um-ano
```

O cenário `trinta-dias` cria a conta com a data de criação 30 dias no passado, 2 matérias (`Biologia` e `História`) e um histórico com:

- dias estudados, não estudados e neutros, mais um dia ainda não liquidado;
- cartões dominados nas duas matérias;
- um cartão que perdeu estabilidade, um suspenso dominado e um excluído dominado.

Ao final, a fábrica imprime a tabela de valores esperados, a mesma do teste funcional do CS-001.

## Testes

Os comandos da 001 valem sem mudança. Para rodar só os testes da 007 e as consultas que ela acrescenta a outros domínios:

```bash
docker compose run --rm api uv run pytest tests -k "evolucao or dominados or existe_revisao or listar_nomes or dias_no_intervalo"
docker compose run --rm web npm test -- evolucao
```

O teste de desempenho do servidor (CS-002) está em `tests/functional/desempenho/` e roda na suíte completa.

## Verificação da história P1

### US1 Ver minha evolução

1. **Estado vazio (US1-3, RF-005):** cadastre uma conta nova (ex.: `caio.teste@exemplo.com`), crie uma matéria e um cartão sem revisar e abra **Evolução** na navegação.
   - **Esperado:** o texto "Sua evolução começa na primeira lição" e um botão para a trilha.
   - **Esperado:** nenhum número, nenhuma grade, nenhum zero.
2. **Valores (US1-1, US1-2, CS-001):** entre com `ana.teste@exemplo.com` (cenário `trinta-dias`) e abra **Evolução**.
   - **Esperado:** XP total, sequência atual, recorde e dominados (total, `Biologia` e `História`) iguais à tabela impressa pela fábrica.
   - **Esperado:** "N dias estudados nas últimas 26 semanas" igual à tabela.
3. **Igualdade com a trilha (RF-002):** abra a **Trilha**.
   - **Esperado:** XP total, sequência e recorde idênticos aos da evolução.
4. **Calendário (RF-001, casos de borda):**
   - **Esperado:** só as últimas 30 datas têm marcação; as anteriores à conta e as posteriores a hoje são células vazias.
   - **Esperado:** hoje aparece como "em andamento" (contorno tracejado).
   - **Esperado:** cada situação aparece com a forma da legenda.
5. **Teclado e leitor de tela (RQ-001):** com o NVDA ou o Orca, chegue à grade com Tab.
   - **Esperado:** o foco começa em hoje, e o leitor anuncia algo como "terça-feira, 13 de outubro de 2026: em andamento".
   - **Esperado:** as setas mudam de dia e de semana; Home, End, Ctrl+Home e Ctrl+End funcionam; o foco nunca para numa célula vazia.
   - **Esperado:** um único Tab sai da grade.
6. **Sem depender de cor (RQ-001):** ative a simulação de acromatopsia nas ferramentas do navegador.
   - **Esperado:** as quatro situações continuam distinguíveis pela forma.
7. **320 px (RQ-002):** abra as ferramentas do navegador com a largura de 320 px.
   - **Esperado:** a página não rola na horizontal, e a grade, os indicadores e a lista cabem na largura.
8. **Cartão dominado excluído (US1-4):** na matéria `Biologia`, exclua um cartão contado como dominado e volte à **Evolução**.
   - **Esperado:** dominados de `Biologia` e o total diminuem 1, e o XP total não muda.
9. **Desempenho (CS-002):** entre com `bia.teste@exemplo.com` (cenário `um-ano`). Abra **Evolução** 20 vezes (recarregando a página) e, no console, leia as medidas com `performance.getEntriesByName('evolucao-carregada')`.
   - **Esperado:** o p95 das 20 medidas abaixo de 1.000 ms.

## Runbook

Conferência por SQL de leitura (substitua o e-mail):

```bash
docker compose exec db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "select m.nome, count(c.id) filter (where c.situacao in ('"'"'ativo'"'"', '"'"'suspenso'"'"') and c.estabilidade >= 21) as dominados from materias m join usuarios u on u.id = m.usuario_id left join cartoes c on c.materia_id = m.id where u.email = '"'"'ana.teste@exemplo.com'"'"' group by m.nome order by m.nome;"'
```

O limiar `21` é o de `revisao/regras.py` na versão vigente. Se a versão mudar, use o valor novo. O total de dias estudados não é conferido por SQL: as datas ainda não liquidadas só existem na leitura (DTEC 061). Use a tabela da fábrica.

## Falhas conhecidas

- A medida de 1 s (CS-002, tela) é manual no MVP. A automação com o Playwright entra no final acadêmico (DTEC 014).
- A aplicação não tem relógio ajustável fora dos testes. A passagem de dias só é demonstrada pelos cenários da fábrica.
