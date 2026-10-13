# Esquema inicial do banco em DBML e adaptação dos documentos ao FSRS

**Data:** 2026-10-12
**Autor:** Artur Lins
**Agente e modelo:** Claude Code / claude-opus-5-5
**Etapa SDD:** esclarecer
**Funcionalidade:** projeto

## Contexto fornecido

- `.agents/AGENTS.md`, `docs/base-specs/spec.md`, `docs/produto/backlog.md`, `docs/produto/pendencias.md` (QA-21, QA-24), `docs/arquitetura/README.md`, `docs/research.md` (DTEC 005, 010, 012)
- Código-fonte da biblioteca `fsrs` (py-fsrs) no GitHub, consultado em 12/10/2026: campos de `Card` (`state`, `step`, `stability`, `difficulty`, `due`, `last_review`), de `ReviewLog` (`rating`, `review_datetime`, `review_duration`) e parâmetros do `Scheduler` (21 pesos, `desired_retention` 0,9, `learning_steps` 1 e 10 min, `relearning_steps` 10 min, `maximum_interval` 36500, `enable_fuzzing`)

## Prompts

### Prompt 1

```text
estamos na branch develop, vamos criar agora uma estrutura inicial do esquema do banco de dados relacional (postgres) a ser escrita em DBML, irei fazer a visualização usando o site dbdiagrams. Pontos importantes: cuidado com constraints desnecessárias, especialmente em chaves primárias. Vamos usar o big serial como id, tendo também, um públic id que será do tipo uuid, a ser exibido nas rotas, a fim de preservar os id's originários do banco de dados de enumeração de usuários. Coloque o nome das tabelas em português. na tabela usuários, coloque o campo do role/papel (para que usuários e admins usem a mesma tabela/login). As imagens e fontes de cada usuário serão armazenadas num bucket do cloudfare R2, então precisam ser do tipo varchar para constar a url deles. Um usuário terá um deck de flashcards, com a separação de qual matéria ele pertence. Um usuário pode criar inúmeras matérias, que poderão conter inúmeras fontes e inúmeros flashcards criados. todos os flashcards, de todas as matérias, ficarão juntos, num deck de flashcards, podendo ser filtrado por matéria. Cada usuário tem uma XP que vai se incrementando. Cada usuário tem o registro dos dias seguidos estudados (daily streaks), sendo contado qual o streak mais alto alcançado e qual o streak atual. Cada flashcard tem uma pergunta, um campo de imagem opcional (a ser aramazenado no cloudfare R2, ficando a URL no banco), a resposta, o score conforme a metodologia do algoritmo FSRS (Free Spaced Repetition Scheduler) e uma explicação a ser mostrada junto da resposta, especialmente quando o usuário erra a questão. Essa é a estrutura inicial, me entreviste para tirar dúvidas antes de gerar a documentação
```

### Resposta a esclarecimento 1 (rodada 1, Q1 a Q11)

```text
O agente apontou dois conflitos com documentos aprovados (fontes no R2 x DTEC 010; papel admin x RF-01) e perguntou sobre URL x chave do objeto, bigserial x identity, uso e versão do public_id, tabela de deck, usuario_id redundante com FK composta, estado do FSRS, XP e sequência, abrangência do esquema e detalhes (enums, unicidade do nome, preferências, exclusão). ->
Q1 - b, se as fontes forem muitas, vai lotar o container com o tempo
Q2 - sua recomendação
Q3 - sua recomendação, precisaremos implementar um painel administrativo simples na versão pós-mvp
Q4 - a partir de qual versão do postgres isso tá disponível? eu sempre trabalhei com serial como PK. Mas se for um formato moderno, podemos usar
Q5, Q6, Q7, Q9, Q10, Q11 - sua recomendação
Q8 - sua recomendação. o algoritmo do FSRS (Free Spaced Repetition Scheduler) deve ser soberano, boa parte da documentação foi escrita sem levar ele em consideração, então precisamos adaptar tanto o banco quanto os demais documentos a essa realidade
```

### Resposta a esclarecimento 2 (rodada 2, Q12 a Q19)

```text
O agente respondeu que colunas identity existem desde o PostgreSQL 10 e, após consultar a biblioteca fsrs, perguntou sobre lição x passos curtos de aprendizado, definição de "devido hoje", lições extras sem revisão antecipada, parâmetros do FSRS por usuário, estado antes e depois em cada revisão, edição de cartão já revisado, abrangência da adaptação dos documentos e estágio do painel administrativo. ->
Q12-Q18: sua recomendação
Q19:"a", na versão final acadêmica, pois é uma funcionalidade essencial, se ela ficar de fora, podemos ser penalizados na matéria
```

## Decisões consolidadas

| Tema | Decisão |
|---|---|
| Armazenamento | Fontes e imagens no Cloudflare R2 desde o MVP (DTEC 010 revisada). O banco guarda a **chave do objeto** (`varchar`); a API gera URL assinada de curta duração |
| Identificadores | PK `bigint generated always as identity` (PostgreSQL 10+). `public_id uuid` v4 só nas tabelas expostas em rotas |
| Papel | Enum `papel` (`estudante`, `admin`) em `usuarios`, padrão `estudante`. Painel administrativo simples no **final acadêmico** (F-17), a validar com o PO |
| Deck | Sem tabela: o deck é o conjunto de `cartoes` do usuário, filtrável por matéria |
| Isolamento | `usuario_id` também em `fontes` e `cartoes`, com FK composta para `materias (id, usuario_id)` |
| FSRS | Soberano. Estado do algoritmo em colunas de `cartoes` (`aprendizado`, `revisao`, `reaprendizado`; "novo" é derivado de `ultima_revisao` nula). `revisoes` é log imutável com estado antes e depois. `parametros_fsrs` versionado por usuário |
| Lição | Sessão de estudo: cartões com passo curto vencido voltam na mesma lição |
| Devido hoje | `vencimento` anterior à próxima virada das 4h no fuso do estudante. *Fuzzing* ligado |
| Lição extra | Só com cartões devidos ou novos dentro do limite; nunca revisão antecipada |
| Edição | Editar não reinicia o estado do FSRS; "reiniciar aprendizado" fica como incremento |
| XP e sequência | Totais em cache em `usuarios` + `eventos_xp` + `dias_estudo` |
| Abrangência | MVP completo; tabelas do final acadêmico em grupo separado (`vector(1024)`) |

## Saída aceita

| Artefato | Ação |
|---|---|
| `docs/prompts/2026-10-12-esquema-inicial-banco.md` | criado |
| `docs/prompts/README.md` | alterado (índice) |

## Alterações humanas

Pendente de revisão.

## Verificação

Em andamento.

## Pendências

- Em andamento.
