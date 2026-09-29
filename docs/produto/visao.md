# Visão do produto

**Versão:** 0.1 (rascunho)
**Data:** 29/09/2026
**Status:** base para o brainstorming aprofundado, sem aprovação do PO
**Origem:** brainstorming inicial ([`../init/`](../init/README.md)) e sessão de estruturação ([registro](../prompts/2026-09-29-estruturacao-projeto.md))

Este documento descreve a plataforma completa em nível de produto, sem escolher tecnologia. Ele orienta o [backlog](backlog.md) e não substitui as specs: o comportamento verificável de cada funcionalidade é definido em `docs/specs/NNN-nome-curto/spec.md`.

## Problema

Materiais de estudo extensos e dispersos (editais, apostilas, livros, anotações) dificultam transformar conteúdo em prática ativa e manter a regularidade. Ferramentas de flashcards com repetição espaçada, como o Anki, são eficazes, mas exigem criar os cartões à mão e oferecem pouca motivação para voltar todos os dias. Aplicativos gamificados, como o Duolingo, criam hábito, mas não trabalham sobre o material do próprio estudante.

## Proposta

Uma plataforma web em que o estudante envia seus materiais e a IA os transforma em flashcards rastreáveis até o trecho de origem. A revisão segue repetição espaçada, e o ritmo de estudo é ditado por mecânicas de jogo: XP, sequência diária e uma rota visual de progressão. O estudante também conversa com seus materiais por meio de um chat que responde apenas com base nas fontes enviadas, com citações, numa versão simplificada do NotebookLM.

## Usuário prioritário

Estudante individual (concurseiro, universitário ou autodidata) que possui materiais próprios e quer estudar com regularidade. Papéis adicionais, como professor ou administrador, não estão previstos (SUP-01 do init).

## Pilares da plataforma completa

| Pilar | Inspiração | O que entrega ao estudante |
|---|---|---|
| Materiais e processamento | — | Enviar, acompanhar e gerenciar os materiais que alimentam todo o resto |
| Flashcards gerados por IA | Anki | Cartões criados a partir dos materiais, com referência verificável ao trecho de origem |
| Repetição espaçada | Anki | Revisão no momento certo, conforme o desempenho do estudante em cada cartão |
| Chat com os materiais (RAG) | NotebookLM | Perguntas respondidas apenas com base nos materiais, com citações |
| Rota de progressão | Duolingo | Caminho visual por unidades e assuntos que mostra onde o estudante está e o que vem a seguir |
| Ritmo gamificado | Duolingo | XP, sequência diária, meta diária e conquistas que incentivam a constância |
| Evolução | — | Painel de desempenho, histórico e progresso por assunto |

## Jornada principal

```text
envia material -> acompanha processamento -> recebe flashcards e rota
      -> estuda a lição do dia (revisões + novos cartões) -> ganha XP e mantém a sequência
      -> tira dúvidas no chat com citações -> acompanha a evolução
```

## Escopo da plataforma completa

### Incluído

- Conta própria e isolamento total dos dados entre usuários.
- Envio, listagem, consulta e exclusão de materiais, com estados de processamento visíveis.
- Extração do conteúdo preservando a origem (material, versão, trecho e página quando conhecida).
- Geração de flashcards por IA restrita aos materiais, com validação antes da publicação.
- Revisão de flashcards com repetição espaçada.
- Chat sobre os materiais do usuário, com respostas citando os trechos usados e declarando quando não houver evidência.
- Rota de progressão por unidades e assuntos derivados dos materiais.
- XP, sequência diária, meta diária e conquistas calculados pelo servidor.
- Painel de evolução com histórico e desempenho.
- Identificação de assuntos sem material de apoio suficiente, como assuntos listados em um edital sem conteúdo correspondente.
- Interface web responsiva em português e API documentada.

### Fora do escopo

- Pesquisa na internet, bases externas ou uso do conhecimento geral do modelo como fonte (Princípio I da [constituição](../constitution.md)).
- Ranking público, ligas, rede social, compartilhamento de materiais e disputas entre usuários.
- Pagamentos, assinaturas e comércio de conteúdo.
- Aplicativos móveis nativos e modo offline.
- Tutoria por voz e provas oficiais certificadas.
- Painel administrativo.

> Itens do escopo incluído **não** estão automaticamente no MVP. O recorte do MVP é a questão QA-12.

## Mudanças em relação ao brainstorming inicial

| Tema | Brainstorming inicial | Direção atual | Situação |
|---|---|---|---|
| Repetição espaçada | Fora do escopo | Pilar central (Anki) | Confirmada pelo PO em 29/09/2026 |
| Sequência diária | Fora do escopo | Pilar central (Duolingo) | Confirmada pelo PO em 29/09/2026 |
| Chat com os materiais (RAG) | Não previsto; tutoria conversacional fora do escopo | Pilar (NotebookLM simplificado) | Confirmada pelo PO em 29/09/2026 |
| Trilha | Lista ordenada de etapas | Rota visual de progressão | Confirmada como intenção; forma em QA-15 |
| Questões de escolha única | Atividade principal | Candidata a manter como complemento | Aberta (QA-17) |
| Docker | Não mencionado | Obrigatório | Confirmada pelo PO em 29/09/2026 |
| Tema visual | Claro, azul `#2563EB` | A decidir | Aberta (QA-19) |

## Questões abertas para o brainstorming aprofundado

As questões QA-01 a QA-11 do [init](../init/Spec.md#12-questões-em-aberto) continuam válidas e mantêm seus IDs. As novas questões seguem a numeração. As questões de produto são respondidas pelo PO. As técnicas seguem para `research.md` da funcionalidade ou do projeto.

| ID | Questão | Tipo | Bloqueia |
|---|---|---|---|
| QA-12 | Quais funcionalidades do backlog compõem o MVP e em que ordem? | Produto | Primeira spec |
| QA-13 | Como o estudante avalia cada revisão (ex.: errei, difícil, bom, fácil)? Qual algoritmo de repetição espaçada será usado (ex.: SM-2, FSRS)? | Produto e técnica | F-05 |
| QA-14 | O que conta como "dia de estudo" para a sequência? Existe meta diária configurável ou proteção da sequência? | Produto | F-10 |
| QA-15 | Como a rota é estruturada (por material, por assunto, por unidade)? Há desbloqueio sequencial? | Produto | F-07 |
| QA-16 | Qual o escopo do chat: histórico de conversas, seleção de materiais consultados, limite de perguntas? | Produto | F-06 |
| QA-17 | Questões de escolha única permanecem no produto? Se sim, como se relacionam com os flashcards? | Produto | F-08 |
| QA-18 | Front e backend serão separados? Qual stack, banco de dados e organização dos contêineres? | Técnica | Primeiro plano |
| QA-19 | Qual a identidade visual (nome, tema claro ou escuro, paleta, tipografia)? | Produto | Primeira interface |
| QA-20 | O estudante pode editar, excluir ou criar flashcards manualmente? | Produto | F-04, F-05 |
| QA-21 | Qual o esquema inicial do banco de dados? | Técnica | Primeiro plano |
| QA-22 | Qual provedor e modelo de IA (LLM e embeddings) serão usados, e com qual custo? Refina QA-04. | Técnica | F-03, F-04, F-06 |
