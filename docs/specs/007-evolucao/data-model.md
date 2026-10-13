# Modelo de dados

**Funcionalidade:** 007-evolucao (evolução mínima)  
**Spec:** [spec.md](spec.md)  
**Base:** [esquema inicial](../../arquitetura/esquema-inicial.dbml), **sem alteração** nesta sessão

A spec 007 **não cria tabelas, colunas, enums nem índices**, e por isso não há migração `0008`. O "Resumo da evolução" da spec é uma visão calculada na leitura, que não grava nada (DTEC 061 e 064). Este documento descreve:

- o que a visão lê e de onde;
- as entidades calculadas que a API devolve;
- as regras de cada valor.

A próxima migração continua sendo a `0008`, para a primeira spec que precisar dela.

## Origem de cada valor

Todas as leituras acontecem numa única transação `REPEATABLE READ, READ ONLY` (DTEC 064), sempre filtradas pelo estudante da sessão (DTEC 019).

| Valor | Consulta | Tabelas lidas (pelo domínio dono) | Índice usado |
|---|---|---|---|
| XP total, sequência atual e recorde, dia de estudo de hoje | `gamificacao.consultas.resumo` (006, DTEC 063) | `usuarios`, `dias_estudo` e, pelo provedor da DTEC 057, `cartoes` e `revisoes` | PK de `usuarios`; PK `(usuario_id, dia)` de `dias_estudo` |
| Situação de cada data do período | `gamificacao.consultas.dias_no_intervalo` (006, esclarecida pela DTEC 065) | `dias_estudo`, `usuarios` e o provedor, para as datas ainda não liquidadas | PK `(usuario_id, dia)`, por intervalo |
| Dominados atuais por matéria | `revisao.consultas.dominados_por_materia` → `cartoes.consultas.contar_dominados_por_materia` (DTEC 066) | `cartoes` | `cartoes_devidos` `(usuario_id, situacao, …)` |
| Nomes das matérias | `materias.consultas.listar_nomes` | `materias` | `materias_nome_unico_por_usuario` |
| Existência de revisão (estado vazio) | `revisao.consultas.existe_revisao` | `revisoes` | `(usuario_id, dia_estudo)` |

Nenhuma tabela é lida diretamente pelo domínio `evolucao`. Em especial, `dias_estudo` só é lida por `gamificacao`, e a sequência nunca é recalculada (obrigação da 006).

## Entidade calculada ResumoEvolucao

**Finalidade:** tudo o que a tela de evolução mostra, numa resposta (`Evolucao` no contrato).

| Campo | Significado | Obrigatório | Regras |
|---|---|---:|---|
| `possuiRevisoes` | O estudante tem pelo menos uma revisão | sim | `existe_revisao`; revisões de cartões excluídos contam (RN-14). Falso leva a interface ao estado vazio (RF-005) |
| `gamificacao` | XP total, meta e sequência | sim | O `ResumoGamificacao` da 006, sem transformação (RF-002) |
| `calendario` | Período e situação de cada dia | sim | Entidade abaixo (RF-001) |
| `dominados` | Dominados atuais, no total e por matéria | sim | Entidade abaixo (RF-003) |

Com `possuiRevisoes` falso, os demais campos continuam presentes, com valores reais (zeros e dias não estudados ou neutros). A interface não os exibe (estado vazio, "sem números fictícios").

## Entidade calculada CalendarioEstudo

| Campo | Significado | Obrigatório | Regras |
|---|---|---:|---|
| `inicio` | Primeiro dia da grade | sim | Domingo de 25 semanas antes da semana de hoje (DTEC 065) |
| `fim` | Último dia da grade | sim | Sábado da semana de hoje; pode ser posterior a hoje |
| `totalEstudados` | Dias estudados no período | sim | Contagem de `estudado` em `dias`; `>= 0` e `<= 182` |
| `dias` | Datas com situação | sim | De `max(inicio, primeiro dia do estudante)` até hoje, contíguas e crescentes; nunca vazia (hoje sempre está) |

**DiaCalendario:**

| Campo | Significado | Obrigatório | Regras |
|---|---|---:|---|
| `data` | Data de estudo | sim | `YYYY-MM-DD`, a data atribuída pela 006 (DTEC 048 e 062) |
| `situacao` | Situação exibida | sim | `estudado`, `nao_estudado`, `neutro` ou `em_andamento` (mapeamento abaixo) |

**Mapeamento das situações** (função pura `situacao_exibida`, DTEC 065):

```text
data < hoje:  estudado ─> estudado
              nao_estudado (gravada ou calculada) ─> nao_estudado
              neutro (com ou sem data_pulada) ─> neutro
              pendente ─> erro de invariante (dias_no_intervalo sempre liquida em memória)
data = hoje:  estudado ─> estudado
              pendente ou sem linha ─> em_andamento
```

- `em_andamento` aparece só em hoje, e hoje nunca aparece como `nao_estudado` (caso de borda da spec).
- Nenhuma data anterior ao primeiro dia do estudante aparece (caso de borda "dias anteriores à criação da conta").

## Entidade calculada DominadosAtuais

| Campo | Significado | Obrigatório | Regras |
|---|---|---:|---|
| `limiarDias` | Estabilidade mínima, em dias, para dominado | sim | `LIMIAR_DOMINADO_DIAS` vigente em `revisao/regras.py` (21, DTEC 055) |
| `total` | Dominados atuais no total | sim | Soma de `porMateria[].dominados` |
| `porMateria` | Uma entrada por matéria do estudante | sim | Todas as matérias, inclusive com 0; ordenadas por nome, como na lista da 002; no máximo 50 |

**DominadosMateria:** `materiaId` (`public_id`), `nome` e `dominados` (`>= 0`).

**Regra de dominado atual** (DTEC 066), aplicada só em `revisao/consultas.py`:

```text
situacao in (ativo, suspenso)  e  estabilidade is not null  e  estabilidade >= LIMIAR_DOMINADO_DIAS
```

- **Distinto de `cartoes.dominado_em`:** `dominado_em` registra a primeira vez e garante o bônus único da 006. O dominado atual pode deixar de valer depois de um Errei, sem tirar o bônus.
- **Excluído:** não existe mais em `cartoes` e não conta; o XP permanece em `eventos_xp` e `usuarios.xp_total` (US1-4).
- **Suspenso:** conta (caso de borda da spec). `aguardando_revisao` e `recusado` não contam.

## Relacionamentos

- Um **Usuario** tem um **ResumoEvolucao** calculado a cada leitura, sem persistência.
- **DominadosMateria** referencia uma **Materia** do mesmo estudante, só pelo `public_id`.

## Validações transversais

- **Sem entrada:** `GET /evolucao` não tem parâmetros nem corpo; período, limiar e ordem são definidos no servidor.
- **Isolamento:** todas as consultas recebem `usuario_id` da sessão (DTEC 019). A rota não tem identificador no caminho.
- **Sem efeito colateral:** a transação de leitura é `READ ONLY`, e um teste verifica que nenhuma linha de `dias_estudo` ou `usuarios` muda depois da leitura, inclusive com dias não liquidados.
- **Retenção:** nada é gravado. A exclusão da conta (DTEC 021) não ganha participante novo.

## Dados de teste

- **CS-001 (30 dias):** conta `@exemplo.com`, 2 matérias e cartões fictícios. O histórico é gerado pelos serviços da 005 e da 006 com relógio controlado (`tests/fabricas_gamificacao.py`) e combina:
  - dias estudados, não estudados, neutros (sem cartão disponível) e um dia ainda não liquidado;
  - cartões dominados em cada matéria, um que perdeu estabilidade, um suspenso dominado e um excluído dominado.

  Os valores esperados ficam escritos à mão no teste.
- **CS-002 (um ano):** a fábrica em massa `tests/fabricas_evolucao.py`, só para desempenho, insere diretamente, respeitando os `CHECK` da 006:
  - 365 dias liquidados e 30 dias ainda não liquidados;
  - 3 mil cartões em 10 matérias;
  - cerca de 30 mil revisões e os eventos de XP correspondentes.
