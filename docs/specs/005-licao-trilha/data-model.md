# Modelo de dados

**Funcionalidade:** 005-licao-trilha (lição com repetição espaçada e trilha de progressão)  
**Spec:** [spec.md](spec.md)  
**Base:** [esquema inicial](../../arquitetura/esquema-inicial.dbml) (grupo `revisao_fsrs`), atualizado nesta sessão:

- `licoes`: `numero` atribuído na conclusão, `encerrada_em`, uma lição aberta por estudante;
- tabelas novas `licoes_cartoes` e `apresentacoes`;
- `revisoes`: `apresentacao_public_id`, `semente_fuzz`, `versao_regras`, `primeira_do_dia`, `tornou_dominado` e `duracao_ms` obrigatória;
- FKs compostas com o dono, e o índice `(id, usuario_id)` em `cartoes` como alvo.

Este documento descreve as entidades e regras que a spec 005 cria, todas pela migração `0006_licoes_revisoes`. Os tipos de banco aparecem só quando definem uma regra. A spec cria:

- as tabelas `licoes`, `licoes_cartoes`, `apresentacoes` e `revisoes`;
- o enum `nota_revisao` (o `estado_fsrs` já existe desde a 003);
- a coluna `dominado_em` e o índice único `cartoes_id_usuario` em `cartoes`.

`parametros_fsrs` já existe desde a 001 e não muda. Todas as chaves primárias `id` são `bigint generated always as identity` e nunca saem da API.

## Entidade Licao (`licoes`)

**Finalidade:** sessão de estudo montada pelo servidor e nó da trilha (RF-001, RF-010, RF-011).

| Campo | Significado | Obrigatório | Regras |
|---|---|---:|---|
| `public_id` | Identificador público | sim | UUID v4; é o `{licaoId}` das rotas |
| `usuario_id` | Dono | sim | FK → `usuarios` |
| `numero` | Posição do nó na trilha | não | Atribuído só na conclusão: `max + 1` do estudante (DTEC 056); presente se e somente se `concluida_em` (`CHECK`) |
| `dia_estudo` | Dia de estudo do início | sim | `dia_estudo(iniciada_em, usuarios.fuso)` (DTEC 048) |
| `extra` | Lição extra | sim | Verdadeiro se já havia lição concluída no mesmo `dia_estudo` (RF-012) |
| `tamanho_alvo` | Cartões distintos previstos no limite | sim | `usuarios.tamanho_licao` no início; mudar a preferência vale para a próxima lição |
| `iniciada_em` | Início | sim | |
| `concluida_em` | Conclusão; acende o nó | não | Critério do D-004 (DTEC 054) |
| `encerrada_em` | Encerramento sem nó | não | Lição aberta de dia anterior (D-005, DTEC 050); nunca junto com `concluida_em` (`CHECK`) |

**Estados derivados:** `em_andamento` (sem `concluida_em` e sem `encerrada_em`), `concluida` e `encerrada`. Transições: `em_andamento → concluida` (escolha do próximo sem candidatos) e `em_andamento → encerrada` (`POST /licoes` num dia de estudo posterior). Os dois estados finais são definitivos.

**Índices:**

- `licoes_numero`: único `(usuario_id, numero) where numero is not null`; paginação da trilha;
- `licoes_uma_aberta`: único `(usuario_id) where concluida_em is null and encerrada_em is null`;
- único `(id, usuario_id)`, alvo das FKs compostas.

## Entidade CartaoPrevisto (`licoes_cartoes`)

**Finalidade:** os cartões fixados na montagem da lição, sua ordem e o progresso de cada um (RF-001, RF-006, RF-011).

| Campo | Significado | Obrigatório | Regras |
|---|---|---:|---|
| `licao_id`, `cartao_id` | Chave primária | sim | FKs compostas com `usuario_id` → `licoes` e `cartoes`, ambas `on delete cascade` (exceção justificada no plano) |
| `usuario_id` | Dono | sim | Igual ao da lição e ao do cartão (garantido pelas FKs) |
| `posicao` | Ordem de montagem | sim | Única por lição; devidos do vencimento mais antigo ao mais recente, depois novos por `entrada_estudo_em` |
| `novo` | Era novo na montagem | sim | `ultima_revisao` nula na montagem |
| `revisado_em` | Primeira revisão nesta lição | não | Gravado uma vez |
| `retirado_em` | Saiu sem revisão | não | Cartão fora de `ativo` ou limite de novos atingido (DTEC 050 e 051); nunca junto com `revisado_em` (`CHECK`) |

## Entidade Apresentacao (`apresentacoes`)

**Finalidade:** cada exibição de um cartão na lição, inclusive as reapresentações (RF-003, RF-006, CB-22).

| Campo | Significado | Obrigatório | Regras |
|---|---|---:|---|
| `public_id` | Identificador público | sim | UUID v4; é o `{apresentacaoId}` das rotas |
| `usuario_id`, `licao_id`, `cartao_id` | Dono, lição e cartão | sim | FKs compostas com `usuario_id`, `on delete cascade` |
| `revendo` | Reapresentação por passo curto vencido | sim | Exibido como "revendo" (design 9.7) |
| `exibida_em` | Criação da apresentação | sim | Base do limite da duração (DTEC 052) |
| `revelada_em` | Primeira revelação | não | Pré-condição da avaliação |
| `avaliada_em` | Avaliação | não | Só com `revelada_em` (`CHECK`) |

**Índices:** `apresentacoes_uma_pendente`, único `(licao_id) where avaliada_em is null`; `cartao_id` (cobre a FK).

## Entidade Revisao (`revisoes`)

**Finalidade:** evento imutável de autoavaliação, com o necessário para reproduzir o agendamento (RF-007, RQ-004) e para a gamificação da 006.

| Campo | Significado | Obrigatório | Regras |
|---|---|---:|---|
| `usuario_id` | Dono | sim | FK → `usuarios` |
| `cartao_id` | Cartão revisado | não | FK composta `(cartao_id, usuario_id)` → `cartoes`, `ON DELETE SET NULL (cartao_id)` (obrigação da 003) |
| `licao_id` | Lição | sim | FK composta `(licao_id, usuario_id)` → `licoes` |
| `apresentacao_public_id` | Apresentação avaliada | sim | Valor sem FK; único (uma revisão por apresentação) |
| `parametros_fsrs_id` | Versão dos parâmetros usada | sim | FK → `parametros_fsrs`; a maior versão do estudante no instante |
| `chave_idempotencia` | Identificador do cliente (RF-008) | sim | UUID; único por `usuario_id` |
| `nota` | `errei`, `dificil`, `bom` ou `facil` | sim | Enum `nota_revisao` = `Rating.Again` a `Rating.Easy` |
| `revisada_em` | Instante da revisão | sim | Instante do servidor; `review_datetime` passado à biblioteca |
| `duracao_ms` | Da exibição da frente à nota (D-006) | sim | Valor do cliente limitado a `[0, (revisada_em − exibida_em) + 2000]` |
| `dia_estudo` | Dia de estudo da revisão | sim | Fuso vigente no instante (CB-25, DTEC 048) |
| `semente_fuzz` | Semente do *fuzz* | sim | `secrets.randbits(63)` (DTEC 053) |
| `versao_regras` | Versão das regras da revisão | sim | `VERSAO_REGRAS` de `revisao/regras.py` (DTEC 055) |
| `primeira_do_dia` | Primeira revisão do cartão no dia de estudo | sim | Base do XP da 006 (RN-18) |
| `tornou_dominado` | Esta revisão preencheu `dominado_em` | sim | Base do bônus da 006 |
| `estado_antes`, `passo_antes`, `estabilidade_antes`, `dificuldade_antes`, `vencimento_antes`, `ultima_revisao_antes` | Estado do cartão antes | `estado_antes` e `vencimento_antes` | Espelho do `fsrs.Card`; `ultima_revisao_antes` nula = primeira revisão do cartão |
| `estado_depois`, `passo_depois`, `estabilidade_depois`, `dificuldade_depois`, `vencimento_depois` | Estado depois | todos menos `passo_depois` | Resultado de `review_card` |

**Imutabilidade:** nenhum `UPDATE` é feito pela aplicação (a única mudança possível é o `SET NULL` do `cartao_id`). Um teste de arquitetura verifica que o repositório de revisões só tem inserção e leitura.

**Índices:**

- único `(usuario_id, chave_idempotencia)` e único `apresentacao_public_id`;
- `(usuario_id, dia_estudo)`;
- `revisoes_novos_dia`: `(usuario_id, dia_estudo) where ultima_revisao_antes is null` (limite de novos, RF-002);
- `revisoes_primeira_do_dia`: único `(usuario_id, cartao_id, dia_estudo) where primeira_do_dia`;
- `cartao_id` e `licao_id` (cobrem as FKs).

## Alterações em `cartoes`

| Campo | Regra |
|---|---|
| `dominado_em` | Primeira revisão com `estabilidade_depois >= LIMIAR_DOMINADO_DIAS` (21, D-003); nunca volta a nulo |
| Colunas do FSRS (`estado_fsrs`, `passo`, `estabilidade`, `dificuldade`, `vencimento`, `ultima_revisao`) | Escritas **só** pela revisão (DTEC 037); a edição da 003 nunca as toca |
| Índice único `cartoes_id_usuario (id, usuario_id)` | Alvo das FKs compostas |

## Leituras que a 005 expõe a outras specs

| Para | O quê | Onde |
|---|---|---|
| 006 | Evento `RevisaoRegistrada` com `primeira_do_dia`, `tornou_dominado`, `dia_estudo`, nota e `versao_regras`, na mesma transação | `nucleo/eventos_revisao.py` (DTEC 055) |
| 006 | Lições concluídas por dia de estudo e `extra` | `revisao/consultas.py` |
| 007 | Revisões por dia, `dominado_em` e estabilidade atual | Tabelas `revisoes` e `cartoes` (leitura pelo domínio `evolucao`) |

## Migração `0006_licoes_revisoes`

- Cria o enum `nota_revisao`, as quatro tabelas, os `CHECK`, os índices parciais e as FKs compostas. A FK de `revisoes` para `cartoes` usa `ON DELETE SET NULL (cartao_id)` (PostgreSQL 15 ou superior, já usado pela 004).
- Acrescenta `cartoes.dominado_em` e o índice único `cartoes_id_usuario`.
- A descida remove o que foi criado. Ela recusa a descida se houver revisões, para não perder histórico em silêncio.

## Exclusões

- **Cartão** (003, inclusive pela fonte ou pela matéria): `licoes_cartoes` e `apresentacoes` saem em cascata; `revisoes.cartao_id` vira nulo e o histórico fica (CB-27, RN-14). Nenhum participante novo de exclusão de acervo é necessário (DTEC 027): a lição não tem contagem própria a mostrar no diálogo.
- **Conta (DTEC 021):** `apagar_dados_usuario` do domínio `revisao` apaga, nesta ordem, `apresentacoes`, `licoes_cartoes`, `revisoes` e `licoes`, antes de `parametros_fsrs` (001) e dos cartões (003). O teste de catálogo da 001 cobre as tabelas novas.

## Validações de entrada

| Entrada | Regra | Erro |
|---|---|---|
| `chaveIdempotencia` | UUID | `422 dados_invalidos` |
| `nota` | `errei`, `dificil`, `bom` ou `facil` | `422 dados_invalidos` |
| `duracaoMs` | Inteiro de 0 a 86.400.000; depois limitado pelo servidor (DTEC 052) | `422 dados_invalidos` fora do intervalo |
| Campos extras | `extra="forbid"` | `422 dados_invalidos` |
| `cursor`, `limite` da trilha | DTEC 034 | `422 cursor_invalido`, `422 dados_invalidos` |

## Dados de teste

- Cartões manuais fictícios ("Qual organela produz ATP?" / "A mitocôndria."), criados por fábrica em contas `@exemplo.com` (regra 10).
- Estados do FSRS fabricados diretamente (devidos, em passo curto, em revisão com intervalo longo) para os testes de elegibilidade e do CS-003.
- Relógio controlado (`agora` injetado no serviço) para a virada das 4h, o passo curto e o fuso.
