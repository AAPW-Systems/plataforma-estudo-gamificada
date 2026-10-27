# Modelo de dados

**Funcionalidade:** 003-cartoes-manuais (cartões criados e gerenciados pelo estudante)  
**Spec:** [spec.md](spec.md)  
**Base:** [esquema inicial](../../arquitetura/esquema-inicial.dbml) (grupo `cartoes_e_ia`), atualizado nesta sessão. Em `cartoes`: referência opcional à fonte com cópia da origem, `entrada_estudo_em` no lugar de `aceito_em`, índice da listagem paginada e a marcação da spec que cria cada coluna. Em `fontes`: índice único `(id, materia_id, usuario_id)`.

Este documento descreve as entidades e regras que a spec 003 cria. Os tipos de banco aparecem só quando definem uma regra. A spec cria a tabela `cartoes` (sem as colunas da 004, da 005 e da 011), os enums `origem_cartao`, `situacao_cartao` (só `ativo` e `suspenso`) e `estado_fsrs`, a extensão `unaccent` ([DTEC 033](../../research.md#decisão-dtec-033-busca-sem-diferenciar-maiúsculas-e-acentos)) e um índice em `fontes`. Evidências, gerações e revisões são da 004 e da 005.

## Entidade Cartao (`cartoes`)

**Finalidade:** o cartão de estudo do estudante numa matéria (RN-08), com o conteúdo, a origem, a situação e o estado do FSRS.

### Colunas criadas pela 003 (migração `0004_cartoes`)

| Campo | Significado | Obrigatório | Regras |
|---|---|---:|---|
| `id` | Identificador interno | sim | `bigint generated always as identity`; nunca sai da API; desempate da ordem da listagem |
| `public_id` | Identificador público | sim | UUID v4 gerado pelo banco; único; é o `{cartaoId}` das rotas |
| `usuario_id` | Dono | sim | Igual ao dono da matéria, pela FK composta; todo acesso filtra por ele (DTEC 019) |
| `materia_id` | Matéria | sim | FK composta `(materia_id, usuario_id)` → `materias(id, usuario_id)`, `on delete restrict` |
| `frente` | Pergunta | sim | Texto normalizado ([DTEC 036](research.md#decisão-dtec-036-texto-limites-e-validação-dos-cartões)), de 1 a `CARTAO_FRENTE_MAX` (1.000); `CHECK` de 1 a 4.000 (teto) |
| `verso` | Resposta | sim | Idem, de 1 a `CARTAO_VERSO_MAX` (2.000); `CHECK` de 1 a 8.000 |
| `explicacao` | Explicação curta (RN-16, EX-03) | não | Idem, até `CARTAO_EXPLICACAO_MAX` (1.000); vazia vira `NULL`; `CHECK` de 1 a 4.000 quando presente |
| `origem` | Origem exibida | sim | `criado` em todo cartão criado pela 003; `gerado_verificado` → `editado` pela regra da [DTEC 038](research.md#decisão-dtec-038-fronteira-com-a-spec-004-e-participante-da-exclusão) |
| `situacao` | Situação | sim | `ativo` ou `suspenso` (a 004 acrescenta `aguardando_revisao` e `recusado`) |
| `entrada_estudo_em` | Entrada no estudo | não | Instante da criação (manual) ou da aceitação (gerado, 004); presente se e somente se `situacao` é `ativo` ou `suspenso` (`CHECK`); ordem dos novos (RN-20) |
| `fonte_id` | Fonte citada como referência | não | FK composta `(fonte_id, materia_id, usuario_id)` → `fontes(id, materia_id, usuario_id)`, `on delete restrict`; anulada na exclusão da fonte ([DTEC 035](research.md#decisão-dtec-035-referência-de-um-cartão-manual-a-uma-fonte)) |
| `referencia_titulo` | Cópia do título da fonte | não | Até 120 caracteres; copiado na criação; nunca atualizado (D-005 da 002) |
| `referencia_nome_arquivo` | Cópia do nome do arquivo | não | Até 255 caracteres |
| `referencia_enviada_em` | Cópia da data do envio | não | `fontes.criado_em` no momento da criação |
| `estado_fsrs` | `Card.state` | sim | Novo: `aprendizado` |
| `passo` | `Card.step` | não | Novo: 0; nulo em `revisao` |
| `estabilidade` | `Card.stability` | não | Nula até a primeira revisão |
| `dificuldade` | `Card.difficulty` | não | Nula até a primeira revisão; de 1 a 10 |
| `vencimento` | `Card.due` | sim | Novo: instante da criação (UTC) |
| `ultima_revisao` | `Card.last_review` | não | Nula = cartão novo |
| `criado_em` | Criação | sim | UTC; ordem da listagem |
| `atualizado_em` | Última alteração de conteúdo ou situação | sim | UTC; não muda numa edição sem mudança efetiva |

Os valores iniciais do FSRS vêm de `fsrs.Card()` na criação ([DTEC 037](research.md#decisão-dtec-037-estado-de-agendamento-edição-e-situação-do-cartão)). Depois disso, só a revisão (005) escreve nessas colunas.

### Colunas criadas por outras specs

| Campo | Spec | Motivo |
|---|---|---|
| `geracao_id` | 004 | Vínculo com a geração; nulo nos cartões manuais |
| `dominado_em` | 005 | Primeira vez que a estabilidade passou do limiar (D-003 da 005) |
| `chave_imagem` | 011 | Imagem da frente (final acadêmico) |

### Restrições (`CHECK`)

- `char_length(frente) BETWEEN 1 AND 4000`, `char_length(verso) BETWEEN 1 AND 8000`, `explicacao IS NULL OR char_length(explicacao) BETWEEN 1 AND 4000`.
- `dificuldade IS NULL OR dificuldade BETWEEN 1 AND 10` (a faixa já constava da descrição da coluna; o `CHECK` a impõe no banco, incluído na migração `0004`).
- Cópias da referência juntas: `(referencia_titulo IS NULL) = (referencia_nome_arquivo IS NULL) AND (referencia_titulo IS NULL) = (referencia_enviada_em IS NULL)`.
- `fonte_id IS NULL OR referencia_titulo IS NOT NULL`.
- Referência só em cartão manual: `referencia_titulo IS NULL OR origem = 'criado'`.
- `(entrada_estudo_em IS NOT NULL) = (situacao IN ('ativo', 'suspenso'))`. A 004 mantém a regra quando acrescentar os outros valores.

### Índices

| Índice | Uso |
|---|---|
| `cartoes_devidos` `(usuario_id, situacao, vencimento)` | Montagem da lição (005); criado já na 003 porque as colunas são dela |
| `cartoes_novos` `(usuario_id, situacao, entrada_estudo_em)` | Novos na ordem de entrada (005, RN-20) |
| `cartoes_materia` `(materia_id, usuario_id, criado_em, id)` | FK composta, contagens por matéria e listagem paginada por cursor ([DTEC 034](../../research.md#decisão-dtec-034-paginação-das-listagens-por-cursor)) |
| `fonte_id` | Impacto e marcação na exclusão da fonte; verificação do `restrict` |

### Índice novo em `fontes`

`fontes_id_materia_usuario`: único `(id, materia_id, usuario_id)`, alvo da FK composta da referência. Ele não muda nenhuma regra da 002.

## Valores derivados (não gravados)

| Valor | Regra | Exibição |
|---|---|---|
| `verificado` | `origem = 'gerado_verificado'`; desde o plano da 004, também com a fonte da geração existente ([DTEC 045](../004-geracao-cartoes/research.md#decisão-dtec-045-revisão-dos-cartões-gerados)) | Selo "Gerado e verificado" (RF-009) |
| `fonteApagada` | `referencia_titulo IS NOT NULL AND fonte_id IS NULL` (manual). Nos cartões gerados, vem das evidências (004) | "Fonte apagada" junto da descrição da origem (RF-009, D-006) |
| Rótulo da origem | `criado` → "Criado por você"; `editado` → "Editado por você"; `gerado_verificado` → "Gerado e verificado" | Texto e ícone, nunca só cor (RQ-003) |

## Relacionamentos

- Uma **Materia** tem zero ou mais **Cartoes**. A FK composta impede um cartão numa matéria de outro dono (RN-01).
- Um **Cartao** manual cita zero ou uma **Fonte** da mesma matéria. A FK composta impede citar uma fonte de outra matéria ou de outro dono.
- Uma **Fonte** é citada por zero ou mais cartões. Ao ser excluída, os cartões que a citam ficam com `fonte_id` nulo e mantêm as cópias (D-006).
- **Revisões** e **eventos de XP** (005 e 006) apontam para o cartão com `on delete set null` (obrigação registrada no plano). **Evidências** (004) apontam com `on delete cascade`.

## Estados e transições

### Situação

```text
(criação) ──> ativo ──suspender──> suspenso
                 ^                     │
                 └──────reativar───────┘
ativo | suspenso ──excluir (confirmado)──> (removido)
```

- **criação → ativo:** grava o estado inicial do FSRS e `entrada_estudo_em`.
- **ativo → suspenso** e **suspenso → ativo:** alteram só `situacao` e `atualizado_em`. O estado do FSRS é preservado (RF-007). Repetir a transição não tem efeito.
- **excluir:** remoção física (RN-14). As revisões e o XP permanecem (RF-008, pelas FKs da 005 e da 006).
- **aguardando revisão e recusado (004):** fora de todas as rotas e listas da 003 (`404`).

### Origem

```text
criado ──────────────(edição)──────────────> criado
gerado_verificado ──(edição com mudança)──> editado ──(edição)──> editado
gerado_verificado ──(edição sem mudança)──> gerado_verificado
```

A origem nunca volta para `gerado_verificado`, e a 003 nunca cria cartões `gerado_verificado` (só a 004).

## Validações transversais

- **Isolamento (RQ-002, DTEC 019):** todo método do repositório recebe `usuario_id`. Um cartão ou uma matéria de outro estudante, ou um cartão aguardando revisão ou recusado, gera `404 recurso_nao_encontrado` com o corpo de um identificador inexistente. Uma fonte de referência inválida gera `422` no campo `fonteId`, com a mesma mensagem para inexistente, de outra matéria e de outro dono.
- **Texto (RF-011, RQ-001):** normalizado num único ponto e exibido sempre como texto.
- **Busca (RF-010, DTEC 033):** `lower(unaccent(frente))` ou `lower(unaccent(verso))` contendo `lower(unaccent(termo))`, com o termo escapado e de 1 a 100 caracteres.
- **Agendamento (RF-005, RN-26):** nenhuma operação da 003 escreve nas colunas do FSRS depois da criação.
- **Exclusão da fonte (DTEC 027 e 035):** o participante anula `fonte_id` na mesma transação, em qualquer modo.
- **Exclusão da matéria (DTEC 027):** o participante apaga os cartões antes de `fontes` e da matéria.
- **Exclusão da conta (DTEC 021):** `apagar_dados_usuario` dos cartões roda antes dos de `fontes` e `materias`. O teste de catálogo da 001 confere que `cartoes` fica vazia para a conta.
- **Privacidade:** nenhum log contém frente, verso, explicação, termo de busca ou cópia da referência.
