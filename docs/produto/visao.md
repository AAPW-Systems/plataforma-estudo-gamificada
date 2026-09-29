# Visão do produto

**Versão:** 0.2 (rascunho)
**Data:** 29/09/2026
**Status:** decisões do brainstorming aprofundado registradas por Artur Lins; recorte do MVP pendente de validação com a equipe e com o professor (PO)
**Origem:** brainstorming inicial ([`../init/`](../init/README.md)), sessão de estruturação ([registro](../prompts/2026-09-29-estruturacao-projeto.md)) e brainstorming aprofundado ([registro](../prompts/2026-09-29-brainstorming-aprofundado.md))

Este documento descreve a plataforma completa em nível de produto, sem escolher tecnologia. Ele orienta o [backlog](backlog.md) e não substitui as specs: o comportamento verificável de cada funcionalidade é definido em `docs/specs/NNN-nome-curto/spec.md`.

## Problema

Materiais de estudo extensos e dispersos (editais, apostilas, livros, anotações) dificultam transformar conteúdo em prática ativa e manter a regularidade. Ferramentas de flashcards com repetição espaçada, como o Anki, são eficazes, mas exigem criar os cartões à mão e oferecem pouca motivação para voltar todos os dias. Aplicativos gamificados, como o Duolingo, criam hábito, mas não trabalham sobre o material do próprio estudante.

## Proposta

Uma plataforma web em que o estudante envia seus materiais e a IA os transforma em flashcards rastreáveis até o trecho de origem. A revisão segue repetição espaçada, e o ritmo de estudo é ditado por mecânicas de jogo: XP, sequência diária e uma rota visual de progressão. O estudante também conversa com seus materiais por meio de um chat que responde apenas com base nas fontes enviadas, com citações, numa versão simplificada do NotebookLM.

## Diferencial

O produto não pode ser uma cópia de uma solução existente (requisito da disciplina). O diferencial frente às inspirações é:

| Solução existente | O que falta ao estudante | O que a plataforma faz |
|---|---|---|
| Anki | A repetição espaçada funciona bem, mas a experiência é uma fila crua de cartões, sem recompensa nem visão clara de progresso | A revisão acontece dentro de uma estrutura gamificada: lições curtas com fechamento, XP, meta diária, sequência, dias estudados e tempo dedicado |
| NotebookLM | Gera flashcards e quizzes, mas eles ficam isolados em cada caderno, e o estudante precisa visitar cada um com frequência, o que não escala para muitas matérias | Uma **rotina diária única** reúne os cartões devidos de todas as matérias, com cartões rastreáveis até o trecho de origem |

**Hipótese de valor do MVP:** com uma rotina diária unificada e recompensas que não punem quem está em dia, o estudante mantém a regularidade de revisão em várias matérias. A forma de medição (ex.: dias estudados por semana, cumprimento da meta) será definida no acordo do MVP com o professor.

**Direção para o projeto final:** o estudante envia um edital e a plataforma cria um plano de estudos e aponta os tópicos sem material de apoio (F-13 e F-14 do [backlog](backlog.md)).

## Princípio de gamificação

Toda regra de gamificação segue três critérios, nesta ordem:

1. **Recompensar esforço honesto.** O XP premia a revisão concluída e o domínio medido pelo algoritmo, e nunca a nota que o próprio estudante se atribui.
2. **Nunca punir quem está em dia.** Um dia sem cartões disponíveis não quebra a sequência, e revisar tudo o que havia conta como dia estudado.
3. **Tirar o máximo de frustração possível**, sem criar atalhos que tornem os números desonestos (ex.: dias "de graça").

As specs de F-05, F-09, F-10 e F-12 citam este princípio como critério para casos de borda.

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
- Organização de materiais e cartões por matérias.
- Geração de flashcards por IA restrita aos materiais, com validação antes da publicação.
- Criação, edição, suspensão e exclusão manual de flashcards, com a origem de cada cartão sempre visível.
- Revisão de flashcards com repetição espaçada, numa rotina diária que reúne todas as matérias.
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

> Itens do escopo incluído **não** estão automaticamente no MVP. O recorte do MVP (QA-12) está no [backlog](backlog.md#recorte-do-mvp).

## Mudanças em relação ao brainstorming inicial

| Tema | Brainstorming inicial | Direção atual | Situação |
|---|---|---|---|
| Repetição espaçada | Fora do escopo | Pilar central (Anki) | Confirmada pelo PO em 29/09/2026 |
| Sequência diária | Fora do escopo | Pilar central (Duolingo) | Confirmada pelo PO em 29/09/2026 |
| Chat com os materiais (RAG) | Não previsto; tutoria conversacional fora do escopo | Pilar (NotebookLM simplificado) | Confirmada pelo PO em 29/09/2026 |
| Trilha | Lista ordenada de etapas | Rota visual de progressão | Confirmada como intenção; forma em QA-15 |
| Questões de escolha única | Atividade principal | Absorvidas pelos flashcards (cada cartão funciona como uma pergunta com resposta) | Decidida em 29/09/2026 (QA-17) |
| Docker | Não mencionado | Obrigatório | Confirmada pelo PO em 29/09/2026 |
| Tema visual | Claro, azul `#2563EB` | Claro por padrão, escuro disponível desde o MVP; paleta a definir | Parcial (QA-19) |
| Edição manual de conteúdo | Não presumida | Permitida, com origem visível | Decidida em 29/09/2026 (QA-20) |
| Organização | Trilhas por material | Matérias, com rotina diária unificada | Decidida em 29/09/2026 |
| Product Owner | Não definido | O professor Aldo Nunes é o PO; representante interno a decidir ([VAL-04](pendencias.md#val-04-representante-interno-do-po)) | Decidida em 29/09/2026 |

> Na coluna "Situação", as decisões de 29/09/2026 no brainstorming aprofundado foram tomadas por Artur Lins e dependem da validação do recorte com o professor ([VAL-01](pendencias.md#val-01-validação-do-mvp-com-o-professor)).

## Decisões do brainstorming aprofundado

Decisões tomadas em 29/09/2026 ([registro](../prompts/2026-09-29-brainstorming-aprofundado.md)). Itens marcados como **provisórios** valem para escrever as specs, mas aguardam confirmação da equipe ([pendências](pendencias.md)). O comportamento verificável de cada item será definido na spec da funcionalidade indicada.

### Conta e acesso (F-01)

- Conta obrigatória, com e-mail e senha. Recuperação de senha e login social são oferecidos pelo provedor de identidade escolhido para o projeto. A tecnologia fica registrada no plano.
- Não existe uso sem conta.

### Materiais (F-02, F-03)

- **MVP:** PDF com camada de texto (sem OCR), TXT e Markdown; um arquivo por envio. PDF sem texto é recusado com explicação (CB-01 do init).
- **Projeto final:** DOCX, PPTX, SRT e VTT. OCR ainda não definido.
- **Limites iniciais, configuráveis por ambiente:** arquivo de até 20 MB; até 50 materiais e 200 MB por usuário; título do material de 1 a 120 caracteres; nome da matéria de 1 a 60 caracteres.
- **Exclusão:** antes de excluir, a interface mostra o impacto (quantidade de cartões e conversas afetadas). O usuário escolhe manter os cartões, que passam a exibir "fonte removida" e perdem o selo de verificado, ou excluí-los junto. Histórico de revisões, XP e sequência já conquistados nunca são removidos. Citações do chat a esse material passam a exibir "fonte removida".

### Flashcards (F-04)

- Cada cartão tem uma origem visível:
  - **gerado e verificado:** criado pela IA e sustentado por trechos;
  - **editado por você:** mantém o vínculo com o trecho, sem o selo de verificado;
  - **criado por você:** fonte opcional.
- Só os cartões gerados entram na avaliação de qualidade da IA.
- O usuário pode criar, editar, suspender e excluir cartões. Cartões manuais permitem construir e testar a revisão antes do pipeline de IA.
- **Provisório:** cartões gerados que passam na verificação são publicados automaticamente como novos, sem caixa de entrada.

### Revisão e rotina diária (F-05)

- Autoavaliação com quatro botões: Errei, Difícil, Bom, Fácil. Agendamento pelo algoritmo **FSRS**.
- **Rotina unificada:** a sessão do dia mistura os cartões devidos de todas as matérias. Também é possível estudar uma matéria isolada.
- **Formato padrão:** lições curtas (proposta: 10 cartões) com tela de fechamento (XP ganho, sequência, cartões dominados) e opção de continuar. O tamanho é configurável. O usuário pode optar pela fila contínua, estilo Anki.
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

### Chat (F-06), provisório

- Pergunta sobre uma matéria (padrão) ou sobre todas.
- Histórico de conversas salvo.
- Resposta em streaming, com citações clicáveis que abrem o trecho e a página.
- Quando não há evidência, a resposta diz explicitamente que não encontrou a informação nos materiais.
- Apenas um limite técnico de uso por usuário.
- "Criar flashcard a partir da resposta" fica para depois do MVP (F-15).

### Deploy

- O MVP pode rodar localmente.
- O projeto final exige deploy numa VPS com HTTPS: Docker Compose com proxy reverso, ou Coolify. Kubernetes só se houver tempo.
- VPS e dimensionamento estão pendentes ([QA-11](pendencias.md#qa-11-vps-e-operação-do-deploy)).

## Questões

As questões QA-01 a QA-11 do [init](../init/Spec.md#12-questões-em-aberto) continuam válidas e mantêm seus IDs. As novas questões seguem a numeração. As questões de produto são respondidas pelo PO. As técnicas seguem para `research.md` da funcionalidade ou do projeto. O detalhamento das questões em aberto, com opções e impactos, está em [`pendencias.md`](pendencias.md).

### Situação das questões do init após o brainstorming aprofundado

| ID | Situação |
|---|---|
| QA-01 | Parcial: Python, React e Postgres decididos; framework do backend em QA-18 |
| QA-02 | Respondida: conta obrigatória com e-mail e senha; recuperação e login social pelo provedor de identidade |
| QA-03 | Respondida para o MVP (ver [Materiais](#materiais-f-02-f-03)) |
| QA-04 | Parcial: verificação antes da publicação decidida; método, volume e reprocessamento na spec de F-04 |
| QA-05 | Respondida (ver [Materiais](#materiais-f-02-f-03)) |
| QA-06 | Adiada com F-07; progresso do MVP em [Evolução](#evolução-parte-de-f-12-no-mvp) |
| QA-07 | Parcial: idempotência e regra de XP decididas; valores em QA-24 |
| QA-08 | Adiada com F-11 |
| QA-09 | Parcial: fuso e virada do dia decididos; períodos e filtros na spec de F-12 |
| QA-10 | Respondida: questões absorvidas pelos flashcards; a revisão gera XP |
| QA-11 | Parcial: forma do deploy decidida; VPS e dimensionamento pendentes |

### Questões do brainstorming

| ID | Questão | Tipo | Bloqueia | Situação |
|---|---|---|---|---|
| QA-12 | Quais funcionalidades do backlog compõem o MVP e em que ordem? | Produto | Primeira spec | Respondida por Artur Lins; validar com o professor ([VAL-01](pendencias.md#val-01-validação-do-mvp-com-o-professor)) |
| QA-13 | Como o estudante avalia cada revisão (ex.: errei, difícil, bom, fácil)? Qual algoritmo de repetição espaçada será usado (ex.: SM-2, FSRS)? | Produto e técnica | F-05 | Respondida: quatro botões e FSRS |
| QA-14 | O que conta como "dia de estudo" para a sequência? Existe meta diária configurável ou proteção da sequência? | Produto | F-10 | Respondida (ver [XP, meta e sequência](#xp-meta-e-sequência-f-09-f-10)) |
| QA-15 | Como a rota é estruturada (por material, por assunto, por unidade)? Há desbloqueio sequencial? | Produto | F-07 | Adiada com F-07 |
| QA-16 | Qual o escopo do chat: histórico de conversas, seleção de materiais consultados, limite de perguntas? | Produto | F-06 | Provisória, a confirmar pela equipe |
| QA-17 | Questões de escolha única permanecem no produto? Se sim, como se relacionam com os flashcards? | Produto | F-08 | Respondida: absorvidas pelos flashcards |
| QA-18 | Front e backend serão separados? Qual stack, banco de dados e organização dos contêineres? | Técnica | Primeiro plano | Parcial: separados, React e Postgres; FastAPI ou Django pendente |
| QA-19 | Qual a identidade visual (nome, tema claro ou escuro, paleta, tipografia)? | Produto | Primeira interface | Parcial: claro por padrão com escuro disponível; nome, paleta e tipografia pendentes |
| QA-20 | O estudante pode editar, excluir ou criar flashcards manualmente? | Produto | F-04, F-05 | Respondida: sim, com origem visível |
| QA-21 | Qual o esquema inicial do banco de dados? | Técnica | Primeiro plano | Aberta; depende de QA-18 e QA-22 |
| QA-22 | Qual provedor e modelo de IA (LLM e embeddings) serão usados, e com qual custo? Refina QA-04. | Técnica | F-03, F-04, F-06 | Aberta, em discussão pela equipe |
| QA-23 | Cartões gerados são publicados automaticamente ou passam por aprovação? Qual o limite padrão de novos cartões por dia? | Produto | F-04, F-05 | Provisória: publicação automática, limite configurável |
| QA-24 | Quais os valores de XP, o limiar de "cartão dominado" e os padrões de meta, lição e teto de tempo? | Produto | F-05, F-09, F-10 | Aberta, definir na spec de F-09 |
| QA-25 | A sessão no navegador migra para o padrão BFF (cookie httpOnly) antes do deploy final? | Técnica | Deploy final | Aberta |
