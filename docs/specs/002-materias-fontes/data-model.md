# Modelo de dados

**Funcionalidade:** 002-materias-fontes (matérias, envio e processamento de fontes)  
**Spec:** [spec.md](spec.md)  
**Base:** [esquema inicial](../../arquitetura/esquema-inicial.dbml) (grupo `acervo`), atualizado nesta sessão: `fontes` ganhou `codigo_falha` (no lugar de `motivo_falha`), `versao_extracao`, `total_trechos`, o título com até 120 caracteres e o índice de conteúdo único por matéria.

Este documento descreve as entidades e regras que a spec 002 cria. Os tipos de banco aparecem só quando definem uma regra. A spec cria somente as próprias tabelas (`materias`, `fontes`, `trechos`) e o enum `estado_fonte` e `codigo_falha_fonte`. Cartões, evidências e gerações são das specs 003 e 004 e participam da exclusão pelo registro da [DTEC 027](../../research.md#decisão-dtec-027-participantes-da-exclusão-de-fontes-e-matérias).

## Entidade Materia (`materias`)

**Finalidade:** o contêiner de estudo do estudante (RN-23).

| Campo | Significado | Obrigatório | Regras |
|---|---|---:|---|
| `id` | Identificador interno | sim | `bigint generated always as identity`; nunca sai da API |
| `public_id` | Identificador público | sim | UUID v4 gerado pelo banco; único; é o `{id}` das rotas |
| `usuario_id` | Dono | sim | FK para `usuarios`; todo acesso filtra por ele (DTEC 019) |
| `nome` | Nome exibido | sim | NFC, sem espaços nas extremidades, sem caracteres de controle, de 1 a 60 caracteres (RF-001); único por estudante sem diferenciar maiúsculas e minúsculas |
| `criado_em` | Criação | sim | UTC |
| `atualizado_em` | Última alteração | sim | UTC; atualizado pela aplicação |

**Índices:** único `(usuario_id, lower(nome))` (`materias_nome_unico_por_usuario`); único `(id, usuario_id)`, alvo das FKs compostas de `fontes` e, depois, de `cartoes` e `geracoes`.

## Entidade Fonte (`fontes`)

**Finalidade:** um arquivo enviado a uma matéria, com o estado do processamento (RF-003 a RF-009).

| Campo | Significado | Obrigatório | Regras |
|---|---|---:|---|
| `id` | Identificador interno | sim | Nunca sai da API; usado como argumento da tarefa da fila |
| `public_id` | Identificador público | sim | UUID v4; único |
| `usuario_id` | Dono | sim | Igual ao dono da matéria, garantido pela FK composta |
| `materia_id` | Matéria | sim | FK composta `(materia_id, usuario_id)` para `materias(id, usuario_id)`, `on delete restrict` |
| `titulo` | Título exibido | sim | NFC, sem espaços nas extremidades, de 1 a 120 caracteres; padrão: nome do arquivo sem a extensão (RF-003); renomeável (RF-015) |
| `nome_arquivo` | Nome enviado | sim | Último segmento do nome, sem caracteres de controle nem bidirecionais, até 255 caracteres; só exibido (RQ-001, DTEC 028) |
| `chave_objeto` | Chave no armazenamento | sim | `usuarios/{public_id_usuario}/fontes/{uuid4}` (DTEC 021); única; nunca sai da API |
| `tipo_midia` | Tipo real | sim | `application/pdf`, `text/plain` ou `text/markdown`, conforme o conteúdo verificado (DTEC 028) |
| `tamanho_bytes` | Tamanho | sim | De 1 a `FONTE_TAMANHO_MAX_BYTES` (RF-004) |
| `hash_sha256` | Resumo do conteúdo | sim | 32 bytes; único por matéria (D-004) |
| `estado` | Estado do processamento | sim | `pendente`, `processando`, `concluido` ou `falhou` (RF-005); padrão `pendente` |
| `codigo_falha` | Motivo da falha | não | `falha_tecnica`, `sem_texto` ou `conteudo_invalido`; presente se e somente se `estado = falhou` (`CHECK`) |
| `total_paginas` | Páginas | não | Só em PDF, de 1 a `PDF_MAX_PAGINAS`; nulo em TXT e MD |
| `total_trechos` | Quantidade de trechos | não | Gravado com os trechos; presente se e somente se `estado = concluido` (`CHECK`) |
| `versao_extracao` | Versão do extrator e dos parâmetros | não | Presente se e somente se `estado = concluido` (DTEC 029) |
| `processada_em` | Fim do processamento | não | UTC; gravado ao chegar a `concluido` |
| `criado_em` | Envio | sim | UTC; é a "data do envio" exibida e copiada para os cartões (RN-05) |
| `atualizado_em` | Última alteração | sim | UTC |

**Índices:** `(materia_id, usuario_id)` (FK e listagem por matéria); único `(materia_id, hash_sha256)` (`fontes_conteudo_unico_por_materia`); `usuario_id` (soma da cota de armazenamento).

## Entidade Trecho (`trechos`)

**Finalidade:** parte ordenada do texto de uma fonte, base da geração ([004](../004-geracao-cartoes/spec.md)) e da evidência (RF-006).

| Campo | Significado | Obrigatório | Regras |
|---|---|---:|---|
| `id` | Identificador interno | sim | Apontado por `evidencias_cartoes.trecho_id` (004), com `on delete set null` |
| `public_id` | Identificador público | sim | UUID v4; exposto só pela consulta da evidência (004) |
| `fonte_id` | Fonte | sim | FK para `fontes`, `on delete cascade` |
| `ordem` | Posição | sim | Começa em 0, contígua; única por fonte |
| `texto` | Conteúdo | sim | Texto normalizado, de 1 a `TRECHO_TAMANHO_MAXIMO` caracteres (DTEC 029); tratado sempre como dado, nunca como instrução (CB-15) |
| `pagina` | Página física | não | Em trechos de PDF, de 1 a `total_paginas`; nula em TXT e MD; nunca inventada (RN-05) |
| `inicio_caractere` | Início no texto da fonte | sim | `>= 0` |
| `fim_caractere` | Fim no texto da fonte | sim | `> inicio_caractere`; `fim - inicio = comprimento do texto` |
| `criado_em` | Criação | sim | UTC |

**Índice:** único `(fonte_id, ordem)`. O trecho não tem `usuario_id`: o dono vem da fonte, e toda consulta de trecho junta `fontes` filtrando o dono (DTEC 019).

## Relacionamentos

- Um **Usuario** tem de zero a `COTA_MATERIAS` **Materias**.
- Uma **Materia** tem de zero a `COTA_FONTES_POR_MATERIA` **Fontes**; a FK composta impede uma fonte numa matéria de outro dono (RN-01).
- Uma **Fonte** tem zero ou mais **Trechos** (zero até `concluido`).
- Cada **Fonte** tem exatamente um objeto no armazenamento, sob `usuarios/{public_id_usuario}/fontes/` (DTEC 021 e DTEC 025).
- **Cartões** (003, 004) pertencem a uma matéria e podem citar uma fonte ou trechos. As contagens e os efeitos sobre eles na exclusão vêm dos participantes (DTEC 027), nunca de consultas da 002 às tabelas deles.

## Estados e transições

### Fonte

```text
pendente ──> processando ──> concluido
                  │
                  └──> falhou (sem_texto | conteudo_invalido | falha_tecnica)
falhou (falha_tecnica) ──nova tentativa──> pendente
```

- **pendente → processando:** o worker começa, com a fonte travada (`FOR UPDATE`).
- **processando → processando:** nova tentativa automática de erro transitório ou job travado reenfileirado (DTEC 030); idempotente.
- **processando → concluido:** trechos gravados na mesma transação que grava `total_trechos`, `total_paginas`, `versao_extracao` e `processada_em`.
- **processando → falhou:** sem texto extraível (`sem_texto`, CB-23), arquivo ilegível nos limites de tempo e memória (`conteudo_invalido`) ou tentativas automáticas esgotadas (`falha_tecnica`).
- **falhou → pendente:** só por pedido do estudante e só com `falha_tecnica` (RF-007). Com `sem_texto` ou `conteudo_invalido`, é recusada (`409 reprocessamento_indisponivel`).
- **concluido** é final: nenhuma execução posterior substitui os trechos (RF-008).
- **Exclusão:** possível em qualquer estado. Se acontecer durante o processamento, o worker termina sem gravar nada (CB-16, RF-013).

### Matéria

```text
inexistente -> ativa -> excluída (física, em cascata, com confirmação pelo nome)
```

- A criação é recusada se exceder `COTA_MATERIAS` ou repetir um nome do estudante sem diferenciar maiúsculas e minúsculas.
- A exclusão apaga fontes (objetos antes das linhas), trechos e, pelos participantes, cartões e gerações. Revisões, XP e sequência permanecem (D-002).

## Validações transversais

- **Isolamento (RQ-003, DTEC 019):** todo método de repositório recebe `usuario_id`. Uma matéria ou fonte de outro estudante gera `404 recurso_nao_encontrado`, com corpo idêntico ao de um identificador inexistente. Rotas com `{id}` entram na tabela do teste de isolamento.
- **Cotas (RF-012, D-003, D-010):** verificadas sob *advisory lock* por estudante (DTEC 032). Fontes em qualquer estado, inclusive `falhou`, contam nas cotas de fontes e de armazenamento até serem excluídas.
- **Duplicata (RF-014, D-004):** índice único `(materia_id, hash_sha256)`. O mesmo arquivo em matérias diferentes é aceito.
- **Coerência do estado:** `CHECK ((estado = 'falhou') = (codigo_falha IS NOT NULL))` e `CHECK ((estado = 'concluido') = (total_trechos IS NOT NULL AND versao_extracao IS NOT NULL))`.
- **Armazenamento:** a linha só existe depois que o objeto existe. Objetos sem linha são removidos pela reconciliação (DTEC 025).
- **Exclusão da conta (DTEC 021):** a 002 registra `apagar_dados_usuario` no registro de exclusão. A função apaga as fontes (os trechos vão em cascata) e as matérias do usuário, depois dos participantes de cartões e gerações. Os objetos são apagados pela tarefa `apagar_objetos_usuario`, que já existe.
- **Privacidade (RQ-002):** nenhum log registra o texto dos trechos, o conteúdo do arquivo ou o nome do arquivo.
- **Descrição da origem (RN-05, D-005):** renomear a fonte só altera `fontes.titulo`. As cópias em `evidencias_cartoes` (004) e nos cartões que citam a fonte (003) não mudam.
