# Modelo de dados

**Funcionalidade:** 004-geracao-cartoes (geração de cartões pela IA e revisão dos gerados)  
**Spec:** [spec.md](spec.md)  
**Base:** [esquema inicial](../../arquitetura/esquema-inicial.dbml) (grupo `cartoes_e_ia`), atualizado nesta sessão:

- `geracoes`: `codigo_falha` no lugar de `motivo_falha`, FK composta para a fonte, uma geração em andamento por fonte;
- tabelas novas `geracoes_trechos`, `cartoes_descartados` e `ciencias_aviso_ia`;
- `motivo_recusa` em `cartoes`;
- deslocamentos da citação em `evidencias_cartoes`.

Este documento descreve as entidades e regras que a spec 004 cria, todas pela migração `0005_geracao_cartoes`. Os tipos de banco aparecem só quando definem uma regra. A spec cria:

- as tabelas `geracoes`, `geracoes_trechos`, `evidencias_cartoes`, `cartoes_descartados`, `consumo_ia` e `ciencias_aviso_ia`;
- os enums `estado_geracao`, `codigo_falha_geracao`, `motivo_recusa` e `motivo_descarte`;
- os valores `aguardando_revisao` e `recusado` de `situacao_cartao`;
- as colunas `geracao_id` e `motivo_recusa` de `cartoes`.

Todas as chaves primárias `id` são `bigint generated always as identity` e nunca saem da API.

## Entidade Geracao (`geracoes`)

**Finalidade:** um pedido de até 10 cartões de uma fonte, com estado visível (RF-001, RF-003) e o registro do que permite avaliar a IA (RF-017).

| Campo | Significado | Obrigatório | Regras |
|---|---|---:|---|
| `public_id` | Identificador público | sim | UUID v4; é o `{geracaoId}` das rotas |
| `usuario_id`, `materia_id` | Dono e matéria | sim | FK composta `(materia_id, usuario_id)` → `materias`, `on delete cascade` |
| `fonte_id` | Fonte pedida | não | FK composta `(fonte_id, materia_id, usuario_id)` → `fontes(id, materia_id, usuario_id)`, `ON DELETE SET NULL (fonte_id)`; nula depois da exclusão da fonte |
| `chave_idempotencia` | Identificador do cliente (RF-004) | sim | UUID; único por `usuario_id` |
| `estado` | `pendente`, `processando`, `concluida` ou `falhou` | sim | Transições na [DTEC 043](research.md#decisão-dtec-043-execução-estados-e-falhas-da-geração) |
| `codigo_falha` | Motivo técnico da falha | não | Presente se e somente se `estado = 'falhou'` (`CHECK`); mensagem do catálogo da aplicação |
| `provedor`, `modelo`, `versao_instrucoes` | Rastreabilidade (RF-017, RQ-006) | não | Gravados ao iniciar; ex.: `gemini`, o modelo configurado e `gerador-v1+juiza-v1` |
| `quantidade_gerada` | Cartões devolvidos pelo modelo | sim | ≥ 0 |
| `quantidade_aprovada` | Cartões publicados (aguardando revisão) | sim | De 0 a `GERACAO_CARTOES_MAX` (10); ≤ `quantidade_gerada` (`CHECK`) |
| `pontos_contraditorios` | Pontos contraditórios declarados (CB-09) | sim | ≥ 0; nunca viram cartão |
| `criado_em` | Pedido | sim | Conta no limite do dia de estudo em que caiu (D-005) |
| `iniciada_em`, `concluida_em` | Início e fim | não | `concluida_em` em `concluida` e `falhou` |

**Índices:**

| Índice | Uso |
|---|---|
| único `(usuario_id, chave_idempotencia)` | Reenvio (RN-10) |
| único parcial `geracoes_fonte_em_andamento` `(fonte_id) WHERE estado IN ('pendente', 'processando')` | Uma geração em andamento por fonte (caso de borda) |
| `(usuario_id, criado_em)` | Limite diário (DTEC 044) |
| `(materia_id, usuario_id)` | FK composta e gerações da matéria |

## Entidade TrechoDaGeracao (`geracoes_trechos`)

**Finalidade:** registrar a janela enviada ao modelo (RF-017) e calcular a cobertura da fonte ([DTEC 041](research.md#decisão-dtec-041-janela-de-trechos-cobertura-e-não-repetição)).

| Campo | Regras |
|---|---|
| `geracao_id` | FK → `geracoes`, `on delete cascade` |
| `trecho_id` | FK → `trechos`, `on delete cascade` |

- **Chave primária:** `(geracao_id, trecho_id)`. O índice em `trecho_id` serve à consulta de cobertura.
- **Trecho coberto:** existe numa geração `concluida`. Uma geração `falhou` não cobre nada.

## Alterações em Cartao (`cartoes`, criada pela 003)

| Campo | Significado | Obrigatório | Regras |
|---|---|---:|---|
| `geracao_id` | Geração de origem | não | FK → `geracoes`, `on delete set null`; nula nos cartões `criado` |
| `motivo_recusa` | Motivo opcional da recusa (RF-020, D-007) | não | `incorreto`, `irrelevante`, `repetido` ou `mal_escrito`; só em `recusado` |

**Valores novos de `situacao_cartao`:** `aguardando_revisao` e `recusado`, com `ALTER TYPE ... ADD VALUE`, num bloco *autocommit* antes dos `CHECK`.

**`CHECK` novos:**

- `origem = 'criado'` → `geracao_id IS NULL`.
- `situacao IN ('aguardando_revisao', 'recusado')` → `origem = 'gerado_verificado'`. Um cartão só sai da revisão como `ativo` ou `recusado`, e a edição antes de aceitar acontece na própria aceitação.
- `motivo_recusa IS NULL OR situacao = 'recusado'`.
- `origem <> 'gerado_verificado' OR explicacao IS NOT NULL` (explicação obrigatória nos gerados, RF-008).
- Continua valendo o da 003: `(entrada_estudo_em IS NOT NULL) = (situacao IN ('ativo', 'suspenso'))`. Aguardando revisão e recusado não têm entrada no estudo.

**Índice novo:** `geracao_id`, para a revisão, o resumo e o participante.

**Estado do FSRS:**

- Na publicação, o cartão recebe o estado inicial de `fsrs.Card()`, como na 003 (DTEC 037).
- Na aceitação, `entrada_estudo_em` e `vencimento` recebem o instante da aceitação. O cartão nunca foi revisado, então isso não altera agendamento nenhum (RN-26).

## Entidade Evidencia (`evidencias_cartoes`)

**Finalidade:** ligar o cartão gerado ao trecho que o sustenta (RN-05, RF-009, RF-018).

| Campo | Significado | Obrigatório | Regras |
|---|---|---:|---|
| `cartao_id` | Cartão | sim | FK → `cartoes`, `on delete cascade` |
| `trecho_id` | Trecho | não | FK → `trechos`, `on delete set null`; nulo depois da exclusão da fonte |
| `fonte_titulo`, `fonte_nome_arquivo`, `fonte_enviada_em` | Cópia da descrição da origem | sim | Copiadas na publicação; nunca atualizadas (RN-05, D-005 da 002) |
| `pagina` | Página | não | A do trecho, só quando conhecida |
| `citacao_inicio`, `citacao_fim` | Posição da citação literal no texto do trecho | sim | `0 ≤ inicio < fim ≤ char_length(trecho.texto)`, conferido na publicação; só para o destaque, sem copiar o texto |

- **Único:** `(cartao_id, trecho_id)`.
- **Pelo menos uma evidência por cartão gerado:** inserida na mesma transação da publicação, conferida por teste de integração (um `CHECK` não alcança outra tabela).

## Entidade CartaoDescartado (`cartoes_descartados`)

**Finalidade:** guardar a saída do modelo reprovada nas validações, com o motivo (RF-007), só para análise ([DTEC 046](research.md#decisão-dtec-046-participante-da-exclusão-descartes-e-retenção)).

| Campo | Regras |
|---|---|
| `geracao_id` | FK → `geracoes`, `on delete cascade` |
| `usuario_id` | FK → `usuarios`; apagado por `apagar_dados_usuario` |
| `motivo` | `estrutura_invalida`, `sem_evidencia`, `citacao_nao_encontrada`, `cobertura_insuficiente`, `reprovado_verificador`, `repetido` ou `excedente` |
| `detalhe` | Código curto, até 100 caracteres (ex.: `contradicao`), nunca texto da fonte |
| `frente`, `verso`, `explicacao` | Como vieram do modelo, truncados nos tetos da 003 (4.000, 8.000 e 4.000); anuláveis |
| `criado_em` | UTC |

Nunca aparece em rota nenhuma, e nunca vai para log.

## Entidade ConsumoIa (`consumo_ia`)

**Finalidade:** uma linha por chamada ao provedor, com sucesso ou falha, sem conteúdo ([DTEC 040](../../research.md#decisão-dtec-040-consumo-orçamento-e-limites-operacionais-da-ia)).

| Campo | Regras |
|---|---|
| `usuario_id` | FK → `usuarios`; apagado por `apagar_dados_usuario` |
| `geracao_id` | FK → `geracoes`, `on delete set null` |
| `operacao` | `gerar_cartoes` ou `verificar_cartoes` (no final acadêmico, `responder_chat` e outras) |
| `provedor`, `modelo`, `versao_instrucoes` | Rastreabilidade |
| `tokens_entrada`, `tokens_saida` | Os informados pelo provedor; nulos quando ele não informa |
| `latencia_ms`, `sucesso` | Obrigatórios |
| `custo_estimado` | Nulo na camada gratuita |
| `criado_em` | Índice `(usuario_id, criado_em)` para o orçamento do dia de estudo |

## Entidade CienciaAvisoIa (`ciencias_aviso_ia`)

**Finalidade:** registrar a ciência do envio de trechos ao provedor configurado (RF-002, [DTEC 039](../../research.md#decisão-dtec-039-aviso-e-ciência-do-uso-de-provedor-de-ia-externo)).

| Campo | Regras |
|---|---|
| `usuario_id` | FK → `usuarios` |
| `versao_aviso` | Até 50 caracteres; ex.: `gemini-v1` |
| `confirmada_em` | UTC |

Chave primária: `(usuario_id, versao_aviso)`.

## Valores derivados (não gravados)

| Valor | Regra | Exibição |
|---|---|---|
| `fonteApagada` (gerado) | `geracao_id` não nulo e `geracoes.fonte_id` nulo | "Fonte apagada" com a descrição da origem, sem o trecho (US3-2) |
| `verificado` | `origem = 'gerado_verificado' AND NOT fonteApagada` (emenda a derivação da 003, [DTEC 045](research.md#decisão-dtec-045-revisão-dos-cartões-gerados)) | Selo "Gerado e verificado" |
| Trecho coberto | Presente em `geracoes_trechos` de uma geração `concluida` | Não exibido; decide a janela e o CB-26 |
| Resumo da geração | `geradosPublicados` = `quantidade_aprovada`; `aceitos` = cartões da geração em `ativo` ou `suspenso`; `recusados`; `aguardandoRevisao` | Cartão de resumo (RF-012) |
| Taxa de aceitação | aceitos / (aceitos + recusados), por geração, fonte e total | Relatório de avaliação (CS-005) |
| Gerações do dia | `estado <> 'falhou'` e `criado_em` desde a última virada das 4h no fuso do estudante | Limite diário (RF-019) |

## Relacionamentos

- Uma **Materia** tem zero ou mais **Geracoes**, que saem em cascata com ela.
- Uma **Fonte** tem zero ou mais **Geracoes**. Ao ser excluída, as gerações ficam com `fonte_id` nulo, e o participante trata os cartões delas.
- Uma **Geracao** tem:
  - zero ou mais **TrechosDaGeracao**;
  - de zero a 10 **Cartoes** publicados;
  - zero ou mais **CartoesDescartados**;
  - zero ou mais registros de **ConsumoIa**.
- Um **Cartao** gerado tem uma ou mais **Evidencias**, cada uma ligada a um **Trecho** da mesma fonte, ou a nenhum, depois da exclusão dela.
- Um **Usuario** tem zero ou mais **CienciasAvisoIa**, uma por versão aceita.

## Estados e transições

### Geração

```text
pendente ──worker inicia──> processando ──publicação (0 a 10)──> concluida
   │                            │
   │                            └── falha técnica ou orçamento ──> falhou (codigo_falha)
   └──── fonte excluída (participante) ──> falhou (fonte_excluida)  [também a partir de processando]
```

- Não há transição a partir de `concluida` nem de `falhou`. "Tentar de novo" e "Gerar mais" criam uma nova geração.
- Em `concluida` com `quantidade_aprovada = 0`, a mensagem é "não foi possível gerar cartões sustentados" (US4-6).

### Cartão gerado

```text
(publicação) ──> aguardando_revisao ──aceitar──────────> ativo (gerado_verificado)
                        │            ──editar e aceitar─> ativo (editado; ou gerado_verificado sem mudança)
                        └────────────recusar───────────> recusado (motivo opcional)
ativo <──> suspenso   (rotas da 003)
```

- Aceitar e recusar são idempotentes pelo estado. Uma decisão oposta a uma já tomada responde `409 cartao_ja_decidido`.
- `recusado` é final e invisível ao estudante (RF-014).
- Na exclusão da fonte:
  - `aguardando_revisao` e `recusado` são apagados;
  - `ativo` e `suspenso` seguem o modo escolhido.

## Validações transversais

- **Isolamento (DTEC 019):** todo método de repositório recebe `usuario_id`. Uma geração, um cartão ou uma fonte de outro estudante gera `404` idêntico ao de inexistente. As FKs compostas impedem uma geração com fonte de outra matéria ou de outro dono.
- **Texto:** todo texto de cartão publicado ou editado passa por `normalizar_texto_cartao` e `validar_limites` da 003 (DTEC 036). É exibido sempre como texto.
- **Idempotência (RN-10):** índice único da chave, índice único parcial por fonte e transições pelo estado.
- **Concorrência:**
  - *advisory lock* do estudante no pedido (`geracoes`) e na publicação (`publicacao_cartoes`);
  - `FOR SHARE` na fonte ao pedir e ao publicar (DTEC 031);
  - `FOR UPDATE` no cartão nas ações da revisão.
- **Exclusão da fonte (DTEC 027 e 046):** o participante `geracoes_cartoes` roda na transação da exclusão, antes do de `fontes`.
- **Exclusão da conta (DTEC 021):**
  - `apagar_dados_usuario` das gerações roda depois do dos cartões e antes do de `fontes` e do de `materias`;
  - o do domínio `ia` apaga o consumo e as ciências;
  - o teste de catálogo da 001 confere todas as tabelas novas.
- **Privacidade (RQ-003):** nenhum log, nenhuma linha de `consumo_ia` e nenhuma resposta de erro contém texto de trechos, cartões, citações ou instruções.
