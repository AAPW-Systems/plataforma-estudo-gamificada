# Visão do produto

**Versão:** 0.3 (rascunho)
**Data:** 29/09/2026; atualizada em 12/10/2026
**Status:** decisões do brainstorming aprofundado e do alinhamento de 12/10/2026 registradas por Artur Lins; recorte do MVP pendente de validação com a equipe e com o professor (PO), conforme a [pauta](pauta-po.md)
**Origem:** brainstorming inicial (hoje [`../base-specs/`](../base-specs/README.md)), sessão de estruturação ([registro](../prompts/2026-09-29-estruturacao-projeto.md)), brainstorming aprofundado ([registro](../prompts/2026-09-29-brainstorming-aprofundado.md)) e alinhamento do produto e da arquitetura ([registro](../prompts/2026-10-12-alinhamento-produto-arquitetura.md))

Este documento descreve a plataforma completa em nível de produto, sem escolher tecnologia. Ele orienta o [backlog](backlog.md), é complementado pelas [exigências do PO](exigencias_po.md) e pela [base de especificação](../base-specs/spec.md), que reúne as regras, e não substitui as specs: o comportamento verificável de cada funcionalidade é definido em `docs/specs/NNN-nome-curto/spec.md`.

## Problema

Materiais de estudo extensos e dispersos (editais, apostilas, livros, anotações) dificultam transformar conteúdo em prática ativa e manter a regularidade. Ferramentas de flashcards com repetição espaçada são eficazes, mas exigem criar os cartões à mão e oferecem pouca motivação para voltar todos os dias. Aplicativos de aprendizado gamificados criam hábito, mas não trabalham sobre o material do próprio estudante.

## Proposta

Uma plataforma web que funde **repetição espaçada** com uma **trilha visual de progressão**. O estudante organiza os estudos em **matérias** (ex.: Matemática, Biologia, Redação). Em cada matéria, ele guarda suas **fontes** e cria flashcards à mão ou pede à IA que os gere a partir das fontes, com referência ao trecho de origem. O estudante revisa os cartões gerados e decide quais entram no seu baralho. Os cartões são respondidos numa **trilha unificada**, cujas lições são montadas pelo algoritmo FSRS, e o ritmo é sustentado por XP, meta diária e sequência. No final acadêmico, cada matéria ganha um chat ao lado das fontes, que responde apenas com base nelas, com citações.

### Estágios

| Estágio | O que entrega |
|---|---|
| **MVP** (local) | Matérias, fontes, cartões manuais e gerados pela IA com revisão do estudante, trilha unificada com FSRS, XP, meta, sequência e evolução mínima |
| **Final acadêmico** (publicado) | MVP + chat com as fontes da matéria, tira-dúvidas do cartão, cartão com imagem, filtro e domínio por matéria, mais formatos de fonte |
| **Referência pós-acadêmica** (documentada) | Evolução técnica que o produto adotaria se crescesse ([referência](../arquitetura/referencia-pos-academica.md)) |

## Diferencial

O produto não pode ser uma cópia de uma solução existente (requisito da disciplina). O diferencial frente às categorias de solução disponíveis é:

| Categoria de solução | O que falta ao estudante | O que a plataforma faz |
|---|---|---|
| Aplicativos de flashcards com repetição espaçada | A repetição espaçada funciona bem, mas a experiência é uma fila crua de cartões, sem recompensa nem visão clara de progresso | A revisão acontece dentro de uma estrutura gamificada: lições curtas com fechamento, XP, meta diária, sequência, dias estudados e tempo dedicado |
| Assistentes de IA que estudam sobre documentos | Geram flashcards e quizzes, mas eles ficam isolados em cada coleção de documentos, e o estudante precisa visitar cada uma com frequência, o que não escala para muitas matérias | Uma **rotina diária única** reúne os cartões devidos de todas as matérias, com cartões rastreáveis até o trecho de origem |

**Hipótese de valor do MVP:** com uma rotina diária unificada e recompensas que não punem quem está em dia, o estudante mantém a regularidade de revisão em várias matérias. A forma de medição (ex.: dias estudados por semana, cumprimento da meta) será definida no acordo do MVP com o professor.

**Direção para o projeto final:** o estudante envia um edital e a plataforma cria um plano de estudos e aponta os tópicos sem material de apoio (F-13 e F-14 do [backlog](backlog.md)).

## Princípio de gamificação

Toda regra de gamificação segue três critérios, nesta ordem:

1. **Recompensar esforço honesto.** O XP premia a revisão concluída e o domínio medido pelo algoritmo, e nunca a nota que o próprio estudante se atribui.
2. **Nunca punir quem está em dia.** Um dia sem cartões disponíveis não quebra a sequência, e revisar tudo o que havia conta como dia estudado.
3. **Tirar o máximo de frustração possível**, sem criar atalhos que tornem os números desonestos (ex.: dias "de graça").

As specs de F-05, F-09, F-10 e F-12 citam este princípio como critério para casos de borda.

## Usuário prioritário

Estudante individual (concurseiro, universitário ou autodidata) que possui materiais próprios e quer estudar com regularidade. Papéis adicionais, como professor ou administrador, não estão previstos.

## Pilares da plataforma completa

| Pilar | O que entrega ao estudante | Estágio |
|---|---|---|
| Matérias e fontes | Organizar os estudos por matéria e guardar nelas as fontes que alimentam todo o resto | MVP |
| Flashcards | Cartões criados à mão ou gerados pela IA a partir das fontes, com referência verificável ao trecho de origem e revisados pelo estudante antes de entrar no baralho | MVP |
| Repetição espaçada | Revisão no momento certo, conforme o desempenho do estudante em cada cartão (FSRS) | MVP |
| Trilha de progressão | Caminho visual em que cada lição concluída é um passo, mostrando de onde o estudante veio e o que vem a seguir | MVP; domínio por matéria no final acadêmico |
| Ritmo gamificado | XP, meta diária e sequência que incentivam a constância | MVP; conquistas depois |
| Chat com as fontes (RAG) | Perguntas respondidas apenas com base nas fontes da matéria, com citações, inclusive a partir de um cartão durante a lição | Final acadêmico |
| Evolução | Dias estudados, XP, sequência, cartões dominados e tempo dedicado | MVP parcial; completo no final acadêmico |

## Jornada principal

```text
cria matéria -> envia fonte -> acompanha processamento -> pede cartões à IA
      -> revisa os cartões gerados (aceita, edita, recusa) -> faz a lição do dia na trilha
      -> ganha XP e mantém a sequência -> acompanha a evolução
```

No final acadêmico, o estudante conversa com as fontes ao lado delas, na página da matéria, e pode abrir o tira-dúvidas de um cartão durante a lição (F-16). O tira-dúvidas é um caminho opcional e não altera a jornada principal.

## Escopo da plataforma completa

### Incluído

- Conta própria e isolamento total dos dados entre usuários.
- Matérias criadas pelo estudante, cada uma com seu acervo de fontes e seus cartões.
- Envio, listagem e exclusão definitiva de fontes, com estados de processamento visíveis.
- Extração do conteúdo preservando a origem (fonte, trecho e página quando conhecida).
- Geração de flashcards por IA restrita às fontes, com validação, explicação do erro e revisão pelo estudante antes de entrar no baralho.
- Criação, edição, suspensão e exclusão manual de flashcards, com a origem de cada cartão sempre visível.
- Revisão com repetição espaçada numa trilha unificada que reúne todas as matérias.
- Chat ao lado das fontes de cada matéria, com respostas citando os trechos usados e declarando quando não houver evidência.
- Tira-dúvidas a partir de um flashcard, com referência às fontes.
- XP, sequência diária, meta diária e conquistas calculados pelo servidor.
- Painel de evolução com histórico e desempenho.
- Identificação de assuntos sem material de apoio suficiente, como assuntos listados em um edital sem conteúdo correspondente.
- Interface web responsiva em português e API documentada.

### Fora do escopo

- Pesquisa na internet, bases externas ou uso do conhecimento geral do modelo como fonte (Princípio I da [constituição](../constitution.md)). A consulta externa pedida pelo PO (EX-01) está em pauta: a equipe propõe retirá-la ([PO-02](pauta-po.md#po-02-pesquisa-externa-ex-01)).
- Quizzes e questões de múltipla escolha corrigidas automaticamente: todo cartão é respondido por autoavaliação.
- Ranking público, ligas, rede social, compartilhamento de materiais e disputas entre usuários.
- Pagamentos, assinaturas e comércio de conteúdo.
- Aplicativos móveis nativos e modo offline.
- Tutoria por voz e provas oficiais certificadas.
- Painel administrativo.

> Itens do escopo incluído **não** estão automaticamente no MVP. O recorte do MVP (QA-12) está no [backlog](backlog.md#recorte-do-mvp).

## Mudanças em relação ao brainstorming inicial

| Tema | Brainstorming inicial | Direção atual | Situação |
|---|---|---|---|
| Repetição espaçada | Fora do escopo | Pilar central | Confirmada pelo PO em 29/09/2026 |
| Sequência diária | Fora do escopo | Pilar central | Confirmada pelo PO em 29/09/2026 |
| Chat com os materiais (RAG) | Não previsto; tutoria conversacional fora do escopo | Pilar, restrito aos materiais e com citações | Confirmada pelo PO em 29/09/2026 |
| Trilha | Lista ordenada de etapas por material | Trilha unificada de lições montadas pelo FSRS, já no MVP | Decidida em 12/10/2026 (QA-15) |
| Questões de escolha única | Atividade principal | Absorvidas pelos flashcards (cada cartão funciona como uma pergunta com resposta) | Decidida em 29/09/2026 (QA-17) |
| Docker | Não mencionado | Obrigatório | Confirmada pelo PO em 29/09/2026 |
| Tema visual | Claro, azul `#2563EB` | Claro por padrão, escuro disponível desde o MVP; paleta a definir | Parcial (QA-19) |
| Edição manual de conteúdo | Não presumida | Permitida, com origem visível | Decidida em 29/09/2026 (QA-20) |
| Organização | Trilhas por material | Matérias, com rotina diária unificada | Decidida em 29/09/2026 |
| Pesquisa externa | Fora do escopo | Exigida pelo PO (EX-01); a equipe a considera incompatível com o Princípio I | Em pauta com o PO ([PO-02](pauta-po.md#po-02-pesquisa-externa-ex-01)) desde 12/10/2026 |
| Product Owner | Não definido | O professor Aldo Nunes é o PO; representante interno a decidir ([VAL-04](pendencias.md#val-04-representante-interno-do-po)) | Decidida em 29/09/2026 |
| Chat no MVP | — | Sai do MVP e vai para o final acadêmico, ao lado das fontes da matéria | Decidida em 12/10/2026; em pauta ([PO-03](pauta-po.md#po-03-novo-recorte-do-mvp)) |
| Publicação dos cartões gerados | — | Revisão pelo estudante (aceitar, editar, recusar, aceitar todos) | Decidida em 12/10/2026 (QA-23) |
| Exclusão de fontes | Arquivamento e restauração (versão de 07/10/2026) | Fontes guardadas no acervo da matéria; exclusão definitiva, com escolha sobre os cartões | Decidida em 12/10/2026 |
| Dificuldade | Pontos por dificuldade da questão (versão de 07/10/2026) | Seleção por dificuldade é incompatível com o FSRS; proposta de exibir a dificuldade calculada | Em pauta ([PO-01](pauta-po.md#po-01-níveis-de-dificuldade-ex-05)) |

> Na coluna "Situação", as decisões de 29/09/2026 e de 12/10/2026 foram tomadas por Artur Lins e dependem da validação da equipe e do professor ([VAL-01](pendencias.md#val-01-validação-do-mvp-com-o-professor), [pauta](pauta-po.md)).

## Decisões do brainstorming aprofundado

Decisões tomadas em 29/09/2026 ([registro](../prompts/2026-09-29-brainstorming-aprofundado.md)). Itens marcados como **provisórios** valem para escrever as specs, mas aguardam confirmação da equipe ([pendências](pendencias.md)). O comportamento verificável de cada item será definido na spec da funcionalidade indicada.

### Conta e acesso (F-01)

- Conta obrigatória, com nome, e-mail e senha. Recuperação de senha por e-mail no final acadêmico. Login social fora dos estágios acadêmicos. A tecnologia está no [`research.md`](../research.md#decisão-dtec-003-autenticação).
- Não existe uso sem conta.

### Matérias e fontes (F-02, F-03)

- A **matéria** é o contêiner criado pelo estudante. Toda fonte e todo cartão pertencem a uma matéria.
- As **fontes** ficam guardadas no acervo da matéria e alimentam a geração de cartões e, no final acadêmico, o chat.
- **MVP:** PDF com camada de texto (sem OCR), TXT e Markdown; até 2 MB; um arquivo por envio. PDF sem texto é recusado com explicação.
- **Final acadêmico:** SRT, VTT e DOCX; mais de um arquivo por envio; novos limites definidos pela equipe.
- **Fora dos estágios acadêmicos:** OCR, XLSX e PPTX, pelo custo de processamento na VPS.
- **Limites, configuráveis por ambiente:** título da fonte de 1 a 120 caracteres; nome da matéria de 1 a 60 caracteres; quantidade e volume por usuário definidos na spec de F-02.
- **Exclusão definitiva:** antes de excluir, a interface mostra o impacto (cartões aceitos e cartões aguardando revisão). O estudante escolhe **manter** os cartões aceitos, que passam a exibir "fonte apagada" com a descrição da origem (título, arquivo, página, data) e perdem o selo de verificado, ou **excluí-los junto**. Cartões aguardando revisão daquela fonte são sempre excluídos. Revisões, XP e sequência já conquistados nunca são removidos. Citações do chat a essa fonte passam a exibir "fonte apagada".

### Flashcards (F-04)

- Cada cartão tem uma origem visível:
  - **gerado e verificado:** criado pela IA e sustentado por trechos;
  - **editado por você:** mantém o vínculo com o trecho, sem o selo de verificado;
  - **criado por você:** fonte opcional.
- Só os cartões gerados entram na avaliação de qualidade da IA.
- **Modelo único de cartão:** frente (pergunta; no final acadêmico, pode ter uma imagem, ex.: a foto de um gato com "Como se chama este animal em inglês?"), verso (resposta) e explicação curta. Uma pergunta de "verdadeiro ou falso" é só uma forma de escrever a frente. Todos os cartões são respondidos da mesma forma.
- O usuário pode criar, editar, suspender e excluir cartões. Cartões manuais permitem construir e testar a revisão antes do pipeline de IA.
- **Revisão dos cartões gerados:** os cartões que passam na verificação ficam "aguardando revisão". O estudante aceita, edita e aceita, recusa ou aceita todos. Ao final, um resumo mostra quantos foram gerados, aceitos e recusados e oferece "Gerar mais". Os recusados não aparecem, mas ficam registrados para medir a qualidade da IA (taxa de aceitação).
- **Exigências do PO:** "Gerar mais" cria novos cartões sem repetir existentes nem recusados (EX-02); cada cartão gerado traz, criada junto com ele, uma explicação curta com citação, exibida quando o estudante erra (EX-03). A dificuldade (EX-05) está em pauta ([PO-01](pauta-po.md#po-01-níveis-de-dificuldade-ex-05)).
- Depois do MVP: avaliar se a quantidade de cartões gerados é coerente com o volume da fonte.

### Revisão e trilha (F-05, F-07)

- Autoavaliação com quatro botões, iguais para todos os cartões: Errei, Difícil, Bom, Fácil. Agendamento pelo algoritmo **FSRS** (*Free Spaced Repetition Scheduler*), que é o centro do produto: todas as regras de revisão, lição, XP e sequência se adaptam a ele.
- **Trilha unificada:** cada nó da trilha é uma lição montada pelo FSRS, que mistura os cartões devidos de todas as matérias e depois os novos. Concluir a lição acende o nó. **MVP sem filtro;** no final acadêmico, filtro por matéria e domínio por matéria.
- **Formato:** lições curtas (proposta: 10 cartões), com tela de fechamento (XP ganho, sequência, cartões dominados) e a opção de continuar com lições extras. O tamanho é configurável.
- **Novos cartões por dia:** limite configurável pelo usuário (ponto de partida: 10, reconhecidamente baixo para quem estuda muito).
- Cada revisão enviada leva um identificador gerado no cliente. O reenvio não duplica efeitos. O mesmo identificador com conteúdo diferente gera conflito (Princípio IV).
- Não há desfazer revisão no MVP.

### XP, meta e sequência (F-09, F-10)

- **XP:** concedido por revisão concluída, independente da nota, mais um bônus quando um cartão passa a ser considerado dominado (estabilidade do FSRS acima de um limiar). Valores em [QA-24](pendencias.md#qa-24-valores-da-gamificação).
- **Meta diária:** número de revisões, configurável. **Meta efetiva** = o menor valor entre a meta e os cartões disponíveis no dia.
- **Dia estudado:** o dia em que a meta efetiva é cumprida. Um dia sem nenhum cartão disponível é **neutro**: não conta como dia estudado e não quebra a sequência.
- **Congelamento da sequência:** fora do MVP, previsto para o projeto final.
- **Fuso:** configurável no perfil, detectado no cadastro, padrão `America/Sao_Paulo`. O dia de estudo vira às **4h** no horário local, para que quem estuda de madrugada não perca o dia.

### Evolução (parte de F-12 no MVP)

- **Dias estudados:** calendário no estilo *heatmap*.
- **Tempo dedicado:** soma do tempo por cartão, com teto por cartão (proposta: 60 s) para não contar abas esquecidas abertas.
- **Cartões dominados.**
- **XP total, sequência atual e sequência recorde.**
- Por matéria e no total. Todos os valores são calculados no servidor.

### Chat (F-06), final acadêmico, provisório

- Fica ao lado das fontes, na página da matéria.
- Pergunta sobre uma matéria (padrão) ou sobre todas.
- Histórico de conversas salvo.
- Resposta em streaming, com citações clicáveis que abrem o trecho e a página.
- Quando não há evidência, a resposta diz explicitamente que não encontrou a informação nos materiais.
- Apenas um limite técnico de uso por usuário.
- "Criar flashcard a partir da resposta" fica para depois do MVP (F-15).

### Tira-dúvidas do flashcard (F-16)

- Exigência do PO EX-04. Durante a lição, o estudante abre um chat com o cartão como contexto e pede explicações adicionais, com referência.
- **Final acadêmico:** apenas com as fontes, reaproveitando a busca e as citações de F-06.
- **Consulta externa (EX-01):** em pauta com o PO; a equipe propõe retirá-la ([PO-02](pauta-po.md#po-02-pesquisa-externa-ex-01)).
- É um caminho opcional: o fluxo principal da lição continua sendo avaliar o cartão e seguir para o próximo.

### Deploy

- O MVP roda localmente.
- O final acadêmico exige deploy numa VPS com HTTPS, com custo mantido pela equipe. Por isso, a arquitetura é simplificada para caber numa VPS de 2 a 4 GB ([arquitetura](../arquitetura/README.md)); a versão robusta fica documentada como [referência pós-acadêmica](../arquitetura/referencia-pos-academica.md).
- A escolha da VPS (provável Hetzner) e do domínio está pendente ([QA-11](pendencias.md#qa-11-vps-e-operação-do-deploy)).

## Questões

As questões QA-01 a QA-11 do brainstorming inicial (versão de 25/09/2026 de `docs/init/Spec.md`, disponível no histórico do git) continuam válidas e mantêm seus IDs. As novas questões seguem a numeração. As questões de produto são respondidas pelo PO. As técnicas seguem para `research.md` da funcionalidade ou do projeto. O detalhamento das questões em aberto, com opções e impactos, está em [`pendencias.md`](pendencias.md).

### Situação das questões do brainstorming inicial

| ID | Situação |
|---|---|
| QA-01 | Respondida em 12/10/2026: stack completa na [arquitetura](../arquitetura/README.md) e nas DTEC 002 a 014, aprovadas ([VAL-06](pendencias.md#val-06-aprovação-da-arquitetura-e-das-dtec-002-a-014)) |
| QA-02 | Respondida: conta obrigatória com e-mail e senha; recuperação de senha no final acadêmico; sem login social |
| QA-03 | Respondida para o MVP (ver [Materiais](#matérias-e-fontes-f-02-f-03)) |
| QA-04 | Parcial: verificação antes da publicação decidida; método, volume e reprocessamento na spec de F-04 |
| QA-05 | Respondida (ver [Materiais](#matérias-e-fontes-f-02-f-03)) |
| QA-06 | Respondida em 12/10/2026: o progresso aparece na trilha de lições (F-07) e na [evolução](#evolução-parte-de-f-12-no-mvp) |
| QA-07 | Parcial: idempotência e regra de XP decididas; valores em QA-24 |
| QA-08 | Adiada com F-11 |
| QA-09 | Parcial: fuso e virada do dia decididos; períodos e filtros na spec de F-12 |
| QA-10 | Respondida: questões absorvidas pelos flashcards; toda revisão gera XP |
| QA-11 | Parcial: Compose e Caddy numa VPS de 2 a 4 GB (DTEC 013); escolha da VPS e do domínio pendente |

### Questões do brainstorming

| ID | Questão | Tipo | Bloqueia | Situação |
|---|---|---|---|---|
| QA-12 | Quais funcionalidades do backlog compõem o MVP e em que ordem? | Produto | Primeira spec | Respondida por Artur Lins em 29/09/2026 e revista em 12/10/2026; validar com o professor ([PO-03](pauta-po.md#po-03-novo-recorte-do-mvp)) |
| QA-13 | Como o estudante avalia cada revisão (ex.: errei, difícil, bom, fácil)? Qual algoritmo de repetição espaçada será usado (ex.: SM-2, FSRS)? | Produto e técnica | F-05 | Respondida: quatro botões e FSRS |
| QA-14 | O que conta como "dia de estudo" para a sequência? Existe meta diária configurável ou proteção da sequência? | Produto | F-10 | Respondida (ver [XP, meta e sequência](#xp-meta-e-sequência-f-09-f-10)) |
| QA-15 | Como a rota é estruturada (por material, por assunto, por unidade)? Há desbloqueio sequencial? | Produto | F-07 | Respondida em 12/10/2026: trilha unificada de lições montadas pelo FSRS; domínio por matéria no final acadêmico |
| QA-16 | Qual o escopo do chat: histórico de conversas, seleção de materiais consultados, limite de perguntas? | Produto | F-06 | Provisória, a confirmar pela equipe; F-06 passou para o final acadêmico |
| QA-17 | Questões de escolha única permanecem no produto? Se sim, como se relacionam com os flashcards? | Produto | F-08 | Respondida: absorvidas pelos flashcards |
| QA-18 | Front e backend serão separados? Qual stack, banco de dados e organização dos contêineres? | Técnica | Primeiro plano | Respondida em 12/10/2026: FastAPI ([DTEC 002](../research.md#decisão-dtec-002-framework-do-backend)) e contêineres na [arquitetura](../arquitetura/README.md) |
| QA-19 | Qual a identidade visual (nome, tema claro ou escuro, paleta, tipografia)? | Produto | Primeira interface | Parcial: claro por padrão com escuro disponível; nome, paleta e tipografia pendentes |
| QA-20 | O estudante pode editar, excluir ou criar flashcards manualmente? | Produto | F-04, F-05 | Respondida: sim, com origem visível |
| QA-21 | Qual o esquema inicial do banco de dados? | Técnica | Primeiro plano | Respondida em 12/10/2026: [esquema inicial](../arquitetura/esquema-inicial.dbml) |
| QA-22 | Qual provedor e modelo de IA (LLM e embeddings) serão usados, e com qual custo? Refina QA-04. | Técnica | F-03, F-04, F-06 | Respondida em 12/10/2026: [DTEC 007](../research.md#decisão-dtec-007-llm-e-framework-de-agentes) e [DTEC 008](../research.md#decisão-dtec-008-embeddings-e-reranking) |
| QA-23 | Cartões gerados são publicados automaticamente ou passam por aprovação? Qual o limite padrão de novos cartões por dia? | Produto | F-04, F-05 | Respondida em 12/10/2026: revisão pelo estudante; limite configurável, valor padrão na spec de F-05 |
| QA-24 | Quais os valores de XP, o limiar de "cartão dominado" e os padrões de meta, lição e teto de tempo? | Produto | F-05, F-09, F-10 | Aberta, definir na spec de F-09 |
| QA-25 | A sessão no navegador migra para o padrão BFF (cookie httpOnly) antes do deploy final? | Técnica | Deploy final | Respondida em 12/10/2026: sessão em cookie HttpOnly desde o MVP ([DTEC 003](../research.md#decisão-dtec-003-autenticação)) |
| QA-26 | O que significam os níveis de dificuldade fácil, médio e difícil (EX-05)? | Produto | F-04 | Em pauta com o PO ([PO-01](pauta-po.md#po-01-níveis-de-dificuldade-ex-05)) |
| QA-27 | Quais as regras da consulta externa: fontes, apresentação, reaproveitamento, privacidade e custo (EX-01)? | Produto e técnica | Incremento de F-16 | Depende de [PO-02](pauta-po.md#po-02-pesquisa-externa-ex-01) |
| QA-31 | Os agentes do final acadêmico continuam no PydanticAI ou passam ao LangGraph? | Técnica | F-06, F-16 | Aberta ([pendências](pendencias.md#qa-31-framework-de-agentes-do-final-acadêmico)) |
