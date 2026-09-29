# Modelo de dados da consulta de prazos

## SourceDocument

Representa um documento autorizado do corpus.

| Campo | Tipo conceitual | Obrigatório | Regra |
|---|---|---:|---|
| `id` | identificador | sim | único e estável |
| `title` | texto | sim | 3 a 200 caracteres |
| `version` | texto | sim | não vazio |
| `status` | enum | sim | `draft`, `active` ou `retired` |
| `effective_from` | data | sim | início da vigência |
| `effective_until` | data | não | posterior ao início |
| `checksum` | texto | sim | muda quando o conteúdo muda |

## Passage

Representa um trecho pesquisável de uma fonte.

| Campo | Tipo conceitual | Obrigatório | Regra |
|---|---|---:|---|
| `id` | identificador | sim | único |
| `document_id` | referência | sim | aponta para `SourceDocument` |
| `section` | texto | sim | localização verificável |
| `content` | texto | sim | 1 a 4000 caracteres |
| `position` | inteiro | sim | zero ou positivo |

## Evidence

Representa um trecho recuperado para uma consulta.

| Campo | Tipo conceitual | Obrigatório | Regra |
|---|---|---:|---|
| `passage_id` | referência | sim | trecho existente |
| `score` | decimal | sim | valor produzido pelo recuperador |
| `document_title` | texto | sim | copiado para apresentação |
| `document_version` | texto | sim | versão usada na execução |
| `section` | texto | sim | localização usada na citação |

## QueryExecution

Representa a execução e seu resultado operacional.

| Campo | Tipo conceitual | Obrigatório | Regra |
|---|---|---:|---|
| `id` | identificador | sim | gerado pelo servidor |
| `status` | enum | sim | um dos estados do contrato |
| `corpus_version` | texto | sim | versão do índice consultado |
| `source_ids` | lista | sim | vazia quando não há evidência |
| `duration_ms` | inteiro | sim | zero ou positivo |
| `created_at` | instante | sim | UTC |

## Estados da consulta

```text
received -> needs_clarification
received -> searching -> answered
received -> searching -> insufficient_evidence
received -> searching -> source_conflict
received -> unavailable
```

- `answered` exige ao menos uma evidência completa.
- `insufficient_evidence` não pode conter fato de prazo, regra ou taxa.
- `source_conflict` exige duas ou mais evidências ativas que divergem sobre o mesmo fato.
- Estados finais não mudam. Uma pergunta complementada cria nova execução.
