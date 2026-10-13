# Modelo de dados

**Funcionalidade:** 006-xp-meta-sequencia (XP, meta diária e sequência)  
**Spec:** [spec.md](spec.md)  
**Base:** [esquema inicial](../../arquitetura/esquema-inicial.dbml) (grupo `gamificacao`), atualizado nesta sessão:

- enum novo `situacao_dia`;
- `eventos_xp`: `versao_regra` como `smallint`, índice único `(revisao_id, tipo)` no lugar de `(cartao_id, dia_estudo, tipo)` e FKs compostas com o dono;
- `dias_estudo`: `situacao`, `meta_diaria`, `data_pulada` e `liquidado_em`; meta efetiva e cumprimento como registro da última avaliação;
- `usuarios`: `dias_liquidados_ate`;
- `revisoes`: índice único `revisoes_id_usuario`, alvo da FK composta.

Este documento descreve as entidades e regras que a spec 006 cria, todas pela migração `0007_gamificacao`. Os tipos de banco aparecem só quando definem uma regra. A spec cria:

- os enums `tipo_evento_xp` e `situacao_dia`;
- as tabelas `eventos_xp` e `dias_estudo`;
- as colunas de gamificação de `usuarios` (`xp_total`, `sequencia_atual`, `sequencia_recorde`, `ultimo_dia_estudado` e `dias_liquidados_ate`), que a 001 deixou para esta spec;
- o índice único `revisoes_id_usuario`.

`meta_diaria` e `fuso` já existem desde a 001 e não mudam. Toda chave primária `id` é `bigint generated always as identity` e nunca sai da API. Nenhuma tabela desta spec é exposta em rotas, e por isso nenhuma tem `public_id`.

## Regra de valores (código, não tabela)

| Elemento | Onde | Regra |
|---|---|---|
| Valores de XP | `gamificacao/regras.py`: `PUBLICADAS = {1: RegraXp(versao=1, xp_revisao=10, xp_dominado=25)}`, `VIGENTE` | Versão publicada nunca muda; mudar um valor cria a versão seguinte (DTEC 058) |
| Limiar de dominado | `revisao/regras.py` da 005: `VERSAO_REGRAS`, `LIMIAR_DOMINADO_DIAS = 21` | Inalterado; a versão aplicada fica em `revisoes.versao_regras` |
| Rastreio | `eventos_xp.versao_regra` com `revisoes.versao_regras` (por `revisao_id`) | O par responde com quais valores e limiar o XP foi concedido (RQ-004) |

## Entidade EventoXp (`eventos_xp`)

**Finalidade:** registro imutável de cada XP concedido, ligado à revisão de origem (RF-003).

| Campo | Significado | Obrigatório | Regras |
|---|---|---:|---|
| `usuario_id` | Dono | sim | FK → `usuarios` |
| `revisao_id` | Revisão de origem | sim | FK composta `(revisao_id, usuario_id)` → `revisoes (id, usuario_id)` |
| `cartao_id` | Cartão revisado | não | FK composta `(cartao_id, usuario_id)` → `cartoes (id, usuario_id)`, `ON DELETE SET NULL (cartao_id)` (obrigação da 003) |
| `tipo` | `revisao` ou `cartao_dominado` | sim | `revisao` só quando a revisão tem `primeira_do_dia`; `cartao_dominado` só quando tem `tornou_dominado` |
| `quantidade` | XP concedido | sim | `CHECK (quantidade > 0)`; valor da `RegraXp` vigente no instante |
| `versao_regra` | Versão dos valores | sim | `smallint`; chave de `PUBLICADAS` |
| `dia_estudo` | Dia de estudo | sim | Copiado de `revisoes.dia_estudo` |
| `concedido_em` | Instante | sim | Copiado de `revisoes.revisada_em` |

**Índices:**

- único `eventos_xp_revisao_tipo (revisao_id, tipo)`: um evento por fato (DTEC 059);
- `(usuario_id, dia_estudo)`: XP por dia (leitura da 007);
- `cartao_id`: cobre o `SET NULL`.

**Imutabilidade:** só inserção e leitura. A única mudança possível é o `SET NULL` do `cartao_id`. Um teste de arquitetura verifica que o repositório não tem `update` nem `delete`, salvo `apagar_dados_usuario`.

## Entidade DiaEstudo (`dias_estudo`)

**Finalidade:** situação de cada data de estudo do estudante, desde a primeira liquidação: o dia corrente com revisões e cada data já classificada (RF-004 a RF-008, DTEC 060 e 061).

| Campo | Significado | Obrigatório | Regras |
|---|---|---:|---|
| `usuario_id`, `dia` | Estudante e data de estudo | sim | PK `(usuario_id, dia)`; `dia` calculado só por `nucleo/dia_estudo.py` (DTEC 048) |
| `situacao` | `pendente`, `estudado`, `nao_estudado` ou `neutro` | sim | Transições abaixo |
| `fuso` | Fuso vigente | sim | Nome IANA de `usuarios.fuso` na última escrita da linha (CB-25) |
| `cartoes_revisados` | Cartões distintos revisados | sim | Soma 1 por revisão com `primeira_do_dia`; `>= 0` |
| `meta_diaria` | Meta vigente | não | Cópia de `usuarios.meta_diaria` na última avaliação; nula em dia liquidado sem atividade |
| `meta_efetiva` | Meta efetiva | não | `min(meta_diaria, revisados + restantes)` na última avaliação (RF-005); 0 no `neutro`; nula em `nao_estudado` sem atividade |
| `meta_cumprida_em` | Instante do cumprimento | não | Presente se e somente se `estudado` |
| `data_pulada` | Data pulada pela mudança de fuso | sim | Padrão falso; verdadeiro só com `neutro` (D-003, DTEC 062) |
| `liquidado_em` | Instante da liquidação | não | Preenchido quando a data é liquidada |

**Transições** (nenhuma outra é permitida):

```text
(sem linha) ──primeira revisão do dia──────────────────────> pendente
(sem linha) ──primeira revisão que já atinge a meta efetiva─> estudado
pendente ──revisados >= max(1, meta_efetiva)───────────────> estudado     (definitivo, RF-006)
pendente ──liquidação, data passada────────────────────────> nao_estudado
(sem linha) ──liquidação, sem disponível na virada──────────> neutro
(sem linha) ──liquidação, com disponível na virada──────────> nao_estudado
(sem linha) ──mudança de fuso, data pulada──────────────────> neutro (data_pulada)
```

Linhas `estudado`, `nao_estudado` e `neutro` nunca mudam de situação. `estudado` continua somando revisados (lições extras, US2-3). `nao_estudado` e `neutro` não mudam mais nenhuma coluna, nem quando uma data repetida pela mudança de fuso recebe revisões (DTEC 062).

**`CHECK`:**

- `(situacao = 'estudado') = (meta_cumprida_em is not null)`;
- `situacao <> 'estudado' or cartoes_revisados >= 1`;
- `situacao <> 'neutro' or cartoes_revisados = 0`;
- `not data_pulada or situacao = 'neutro'`;
- `cartoes_revisados >= 0`, `meta_efetiva >= 0` e `meta_diaria between 1 and 200`.

## Alterações em `usuarios`

| Campo | Regra |
|---|---|
| `xp_total` | `integer not null default 0`, `CHECK (xp_total >= 0)`; cache de `sum(eventos_xp.quantidade)`, atualizado na mesma transação (DTEC 059) |
| `sequencia_atual` | `integer not null default 0`, `>= 0`; sequência vigente na última liquidação ou marcação (DTEC 061) |
| `sequencia_recorde` | `integer not null default 0`; `CHECK (sequencia_recorde >= sequencia_atual)` |
| `ultimo_dia_estudado` | `date`; último dia `estudado` |
| `dias_liquidados_ate` | `date`; último dia liquidado; nulo antes da primeira liquidação, quando o intervalo começa no dia de estudo de `criado_em` |

**Trava:** toda escrita da gamificação começa com `SELECT ... FOR NO KEY UPDATE` na linha do estudante. Essa trava vem depois das travas de quem chama (lição, apresentação e cartão na 005; cartão, fonte e matéria nos ganchos; nenhuma no `PATCH /perfil`, que já trava a mesma linha) (DTEC 057 e 060).

## Alterações em `revisoes`

| Elemento | Regra |
|---|---|
| Índice único `revisoes_id_usuario (id, usuario_id)` | Alvo da FK composta de `eventos_xp` (DTEC 019). Nenhuma coluna nova; a revisão continua imutável |

## Leituras que a 006 expõe a outras specs

| Para | O quê | Onde |
|---|---|---|
| 005 (composição das respostas) | `resumo(sessao, usuario_id, agora)`, `xp_da_revisao(revisao_id)`, `xp_da_licao(licao_id)`, `meta_cumprida_em(dia)` | `gamificacao/consultas.py` (DTEC 063) |
| 007 | Dias por intervalo com a situação (persistida e, para as datas ainda não liquidadas, calculada sem gravar), XP por dia | `gamificacao/consultas.py` (`dias_no_intervalo`, `xp_por_dia`) |

## Migração `0007_gamificacao`

- Cria os enums `tipo_evento_xp` e `situacao_dia`, as tabelas `eventos_xp` e `dias_estudo` com os `CHECK` e índices, as FKs compostas (a de `cartoes` com `ON DELETE SET NULL (cartao_id)`) e o índice único `revisoes_id_usuario`.
- Acrescenta as cinco colunas de `usuarios`, com os padrões e `CHECK`. Contas existentes ficam com XP e sequência zerados e `dias_liquidados_ate` nulo.
- A descida remove o que foi criado e é recusada se houver eventos de XP, para não perder histórico em silêncio (mesmo critério da `0006`).

## Exclusões

- **Cartão** (003, inclusive pela fonte ou pela matéria): `eventos_xp.cartao_id` fica nulo e o XP permanece (US1-5; US3-3 da 003). Os ganchos da DTEC 057 liquidam antes e reavaliam o dia depois. Nenhum participante novo de exclusão de acervo é necessário: o XP não aparece no diálogo de impacto (DTEC 027).
- **Conta (DTEC 021):** `apagar_dados_usuario` do domínio `gamificacao` apaga `eventos_xp` e `dias_estudo` antes do domínio `revisao` (que apaga `revisoes`). As colunas de `usuarios` saem com a linha. O teste de catálogo da 001 cobre as tabelas novas.

## Validações de entrada

Nenhuma entrada nova: a 006 não cria rotas nem campos de requisição. A meta diária e o fuso continuam validados pela 001 (de 1 a 200; nome IANA válido).

## Dados de teste

- Contas `@exemplo.com` e cartões manuais fictícios das fábricas da 003 e da 005 (regra 10).
- Relógio controlado (`agora` injetado) para a virada das 4h, a passagem de dias, as mudanças de fuso e o horário de verão.
- Histórico de dias gerado pela fábrica `fabricas_gamificacao.py`, por meio do próprio serviço (revisões e liquidações com o relógio avançando), nunca por inserção direta de situações.
