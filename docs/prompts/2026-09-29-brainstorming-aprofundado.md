# Brainstorming aprofundado: diferencial, recorte do MVP e decisões de produto

**Data:** 2026-09-29
**Autor:** Artur Lins
**Agente e modelo:** Claude Code / claude-opus-5-5, com o skill `grill-me` (entrevista em rodadas com recomendação por questão)
**Etapa SDD:** esclarecer (anterior à primeira spec)
**Funcionalidade:** projeto

## Contexto fornecido

- `docs/constitution.md` (v0.1), `docs/produto/visao.md` e `docs/produto/backlog.md`
- `docs/init/Spec.md` (questões QA-01 a QA-11)
- `docs/sdd_guidelines/detalhes_projeto.md` (requisitos da disciplina: RAG, Docker, deploy, evals, professor como PO)

## Prompts

### Prompt 1

```text
/mattpocock-skills:grill-me
```

O agente conduziu a entrevista em cinco rodadas. Cada rodada trouxe questões numeradas com uma recomendação. As perguntas estão resumidas abaixo, e as respostas são literais.

### Resposta a esclarecimento 1 (rodada 1)

```text
[Agente] Q1 restrições (prazo, equipe, orçamento de IA, onde roda, critérios da disciplina); Q2 autenticação; Q3 formatos de material; Q4 avaliação da revisão e algoritmo; Q5 questões de escolha única; Q6 edição manual de flashcards; Q7 dia de estudo e congelamento; Q8 identidade visual.

[Resposta] Q1- a) MVP 3 semanas, plataforma final em novembro
b) 4 pessoas, o PO inicialmente sou eu. Vamos usar python por ser mais fácil de integrar com ferramentas de IA provavelmente será fastapi+react, mas é possível que prefiram django, isso será decidido posteriormente. Banco postgres
c) vamos tentar usar inicialmente provedores gratuitos como o groq, mas se for necessário, a gente pega alguma api paga
d) o mvp pode ser local, mas o projeto final será em deploy obrigatório, ainda não decidimos qual será o vps
e) os detalhes do projeto estão em  "D:\\Workspaces\\Python\\plataforma-estudo-gamificada\\docs\\sdd_guidelines\\detalhes_projeto.md", precisa ter RAG, docker, deploy. O produto não pode ser uma cópia de algo que já existe, caso contrário, o professor irá avaliar comparando com a solução existente, logo, temos que focar no diferencial.

Q2 - a) email + senha com JWT, usaremos o keycloak, ele tem recuperação de senha e OAuth. Não é possível usar sem conta/senha

Q3 - pro mvp PDF sem OCR, txt, md. Pro produto final, docx, pptx, srt e vtt. O OCR não temos definido, talvez no futuro usar algo como o docling

Q4 - Botões A, Algoritmo A 

Q5 - Os flashcards meio que funcionam como uma pergunta única (geralmente é uma pergunta com uma resposta), o chat seria numa interface diferente. O fluxo principal será importar materiais, com base nele, a IA cria flashcards a serem revisados mediante o sistema da gamificação (o anki não tem gamificação, faz isso de forma mais crua, só ordenando a ordem de revisão, a plataforma irá ter a revisão mediante a estrutura gamificada). A parte do chat será para justificar o RAG, seria uma forma mais simples de se fazer perguntas de alguns materiais

Q6 - C, o fluxo principal será pensado para ser feito de forma automática com as fontes, mas não faz sentido bloquear do usuário a possibilidade de edição, exclusão e criação manual.

Q7 - A, congelamento não fará parte do MVP, mas sim no projetyo final

Q8 - claro first, mas com opção para escuro desde o mvp. O esquema de cores em si ainda não foi definido
```

### Resposta a esclarecimento 2 (rodada 2)

```text
[Agente] Q1 quem é o PO de fato (as guidelines colocam o professor); Q2 diferencial e hipótese de valor (A revisão gamificada sobre cartões verificados, B edital -> rota -> lacunas); Q3 XP em revisão autoavaliada; Q4 cartões manuais e o Princípio I; Q5 stack de IA (LLM, embeddings, busca híbrida); Q6 Keycloak e onde fica o token; Q7 prazo para decidir FastAPI vs. Django.

[Resposta] Q1 - A

Q2 - um misto de A com B, no projeto final temos a ideia de poder jogar um edital para criação de planos de estudo. Inicialmente o principal diferencial seria a questão da revisão espaçada gamificada. O anki faz o sistema de revisões muito bem, mas é só um monte de flashcard atrás de outro, sem um sistema de recompensa ou que deixe mais claro o progresso (como dias estudados, tempo dedicado, etc). O notebook lm cria flashcards e quizzes, mas eles ficam meio isolados, exige que o usuário fique acessando o caderno frequentemente, o que é complicado de ser feito quando se tem muitas matérias pra estudar

Q3 - C

Q4 - A

Q5 - essa parte ainda precisa ser melhor discutida com a equipe pra ser definida, é algo pra ir pro backlog

Q6 - pode ser sua sugestão

Q7 - vou conversar com a equipe hoje sobre isso e a Q5
```

### Resposta a esclarecimento 3 (rodada 3)

```text
[Agente] Q1 recorte e ordem do MVP; Q2 organização por matérias; Q3 como os cartões gerados entram na rotina; Q4 forma da sessão diária e regra da meta; Q5 métricas de progresso; Q6 escopo do chat; Q7 forma do deploy final.

[Resposta] Q1 - seguiremos sua recomedação

Q2 - A

Q3 - é algo que ainda precisa ser melhor discutido com a equipe, mas inicialmente iremos de A. O limite precisa ser configurável, 10 por dia é pouco pra um estudante heavy user, mas pode ser usado como um ponto de partida

Q4 - padrão A, mas com os limites configuráveis, sendo possível o usuário escolher o padrão B caso queira. i - sim, conta, a lógica da gamificação é tirar o máximo de frustração possível

Q5 - sua recomendação

Q6 - ainda precisa ser melhor discutida com a equipe essas questões, mas seria inicialmente como sua recomendação

Q7 - A, se não conseguirmos fazer o deploy de forma convencional, provavelmente usaremos o coolify. o kubernetes não sabemos se dará tempo. Vou ter que discutir melhor com a equipe essa questão, pois será uma vps cara pelo foi descrito. Talvez precisamos remover os modelos de embeddings locais
```

### Resposta a esclarecimento 4 (rodada 4)

```text
[Agente] Q1 dia com zero cartões disponíveis; Q2 registrar o princípio de gamificação; Q3 limites numéricos do MVP; Q4 exclusão de material e derivados; Q5 reenvio de revisões e fuso.

[Resposta] Q1 - A

Q2 - A

Q3 - sua recomendação

Q4 - A

Q5 - sua recomendação
```

### Prompt 2 (após o resumo consolidado)

```text
ok, pode seguir com os registros, crie em  "D:\\Workspaces\\Python\\plataforma-estudo-gamificada\\docs\\produto" um arquivo de pendencias.md, descrevendo de forma detalhada o que está pendente e os impactos das decisões, como os embeddings
```

### Prompt 3

```text
Atualize os membros da equipe (em ordem alfabética):

Arthur Moura
Artur Lins (eu)
Pedro Paulo Lucena
William Johnson

Professor: Aldo Nunes
```

### Prompt 4

```text
remova que sou proxy PO, ainda vamos decidir. o scrum master vai variar a cada semana, é um requisito obrigatório da matéria
```

## Análise registrada pelo agente

- `detalhes_projeto.md` define o professor como PO e limita o MVP a uma persona, uma jornada e até três capacidades essenciais, com uma hipótese de valor mensurável. O recorte foi ajustado a esse formato.
- O NotebookLM já gera flashcards e quizzes. Por isso o diferencial foi deslocado para a rotina diária gamificada que unifica várias matérias.
- Em revisão autoavaliada, dar XP por acerto incentiva a autoavaliação desonesta. O XP passou a premiar a revisão concluída e o domínio medido pelo FSRS.

## Saída aceita

| Artefato | Ação |
|---|---|
| `docs/prompts/2026-09-29-brainstorming-aprofundado.md` | criado (este registro) |
| `docs/prompts/README.md` | alterado (índice) |
| `docs/produto/pendencias.md` | criado (pendências, opções e impactos) |
| `docs/produto/visao.md` | alterado (v0.2: diferencial, princípio de gamificação, decisões e situação das questões) |
| `docs/produto/backlog.md` | alterado (recorte do MVP, F-08 absorvida, F-14 e F-15, incrementos pós-MVP, bloqueios) |
| `docs/constitution.md` | alterado (v0.2: Princípio I para conteúdo gerado pela IA e cartões manuais, PO) |
| `.agents/AGENTS.md` | alterado (estado atual e mapa) |
| `README.md` | alterado (estado, estrutura e seção "Equipe") |
| `docs/prompts/2026-09-29-estruturacao-projeto.md` | alterado (nome completo do autor) |

Equipe e professor nomeados (prompt 3) no `README.md`, na constituição, no `AGENTS.md`, na visão, nas pendências e no índice de prompts. A pendência VAL-03 (designação do Scrum Master, exigida pelas guidelines) foi adicionada.

Após o prompt 4, o papel de proxy PO foi removido de todos os documentos e virou a pendência VAL-04. VAL-03 passou a registrar o rodízio semanal de Scrum Master, com a escala pendente.

## Alterações humanas

Pendente de revisão.

## Verificação

- Links relativos dos arquivos alterados conferidos por script ao final da sessão.
- Nenhum segredo ou dado pessoal de terceiros incluído.
- Nenhum código, dependência ou spec criado (a stack continua pendente).

## Pendências

- Ver [`../produto/pendencias.md`](../produto/pendencias.md): stack de IA (QA-22), framework do backend (QA-18), VPS (QA-11), esquema do banco (QA-21) e a confirmação das decisões provisórias pela equipe.
- Validar o recorte do MVP com o professor (PO) na próxima review.
- Aprovação da constituição v0.2 pela equipe.
