# Pauta com o PO

**Criada em:** 12/10/2026 ([registro da sessão](../prompts/2026-10-12-alinhamento-produto-arquitetura.md))
**PO:** professor Aldo Nunes
**Responsável por levar a pauta:** a definir pela equipe

Itens que dependem de uma resposta do PO. Cada item traz a posição da equipe e uma alternativa, para que a reunião termine com uma decisão. A resposta é registrada no item, com data, e propagada para a [visão](visao.md), o [backlog](backlog.md), a [constituição](../constitution.md) ou as [pendências](pendencias.md), conforme o caso. Enquanto não houver resposta, vale a posição da equipe, marcada como provisória.

| ID | Tema | Exigência ou pendência | Situação |
|---|---|---|---|
| [PO-01](#po-01-níveis-de-dificuldade-ex-05) | Níveis de dificuldade | EX-05, QA-26 | Aguardando o PO |
| [PO-02](#po-02-pesquisa-externa-ex-01) | Pesquisa externa | EX-01, QA-27 | Aguardando o PO |
| [PO-03](#po-03-novo-recorte-do-mvp) | Novo recorte do MVP | VAL-01 | Aguardando o PO |
| [PO-04](#po-04-três-estágios-do-produto) | Três estágios do produto | — | Aguardando o PO |
| [PO-05](#po-05-revisão-humana-dos-cartões-gerados) | Revisão humana dos cartões gerados | QA-23, QA-04 | Aguardando o PO |

## PO-01 Níveis de dificuldade (EX-05)

**Exigência:** "Definição de dificuldades (fácil, médio e difícil)".

**Posição da equipe:** escolher ou filtrar cartões por um nível de dificuldade fixo é **incompatível** com a repetição espaçada. O algoritmo FSRS decide quais cartões aparecem em cada dia com base no desempenho do estudante em cada um. Se o estudante pudesse escolher só os cartões "fáceis", os difíceis ficariam atrasados, e o agendamento perderia o sentido. Além disso, a revisão já tem os botões de autoavaliação "Difícil" e "Fácil", e usar as mesmas palavras para outra coisa confunde.

**Proposta:** o FSRS já calcula, para cada cartão, um valor de **dificuldade** a partir das respostas do estudante. A plataforma pode **exibir** essa dificuldade em três faixas (por exemplo, "cartão tranquilo", "cartão moderado", "cartão desafiador"), sem alterar o agendamento. No final acadêmico, a evolução pode mostrar quantos cartões estão em cada faixa por matéria.

**Pergunta ao PO:** a proposta atende à intenção da EX-05? Se não, qual era o objetivo da exigência?

## PO-02 Pesquisa externa (EX-01)

**Exigência:** "IA faça pesquisa sobre o assunto e traga o material".

**Posição da equipe:** consideramos a exigência **incompatível** com o princípio central do produto: a IA responde **somente** com base nas fontes enviadas pelo estudante, com citação (Princípio I da [constituição](../constitution.md)). Trazer conteúdo externo aumenta o risco de informação errada ou desalinhada com o que o estudante precisa estudar (ex.: o edital ou a bibliografia da disciplina), e o estudante pode tomar como verificado algo que não veio das suas fontes.

**Proposta:** retirar a pesquisa externa dos estágios acadêmicos. Ela fica registrada como possibilidade na evolução pós-acadêmica.

**Alternativa, se o PO mantiver a exigência:** a regra já prevista na constituição v0.3, válida apenas no tira-dúvidas de um cartão (final acadêmico): acionada explicitamente pelo estudante a cada pergunta, com a parte externa separada visualmente da parte das fontes, toda afirmação externa com a fonte citada, e nada externo vira cartão verificado nem entra no índice das fontes. As regras detalhadas estão em [QA-27](pendencias.md#qa-27-regras-da-consulta-externa).

**Pergunta ao PO:** aceita a retirada? Se não, a alternativa acima é suficiente?

## PO-03 Novo recorte do MVP

O recorte apresentado em 29/09/2026 incluía o chat com os materiais no MVP. A equipe propõe:

| Capacidade do MVP | Funcionalidades |
|---|---|
| 1. Fontes em cartões revisados pelo estudante | F-01, F-02, F-03, F-04 |
| 2. Revisão com repetição espaçada numa trilha unificada | F-05, F-07 (trilha de lições) |
| 3. Gamificação | F-09, F-10, parte de F-12 |

- **Sai do MVP e vai para o final acadêmico:** o chat com as fontes (F-06) e o tira-dúvidas do cartão (F-16, que atende à EX-04).
- **Motivo:** o MVP precisa de uma jornada completa em cerca de três semanas. O chat exige embeddings, busca híbrida e streaming, que são a parte mais pesada do RAG e merecem ser bem construídos no final acadêmico, com avaliação.
- **O MVP continua com IA no fluxo principal:** a geração de cartões a partir das fontes, com evidência e explicação do erro (EX-02 e EX-03).

**Pergunta ao PO:** aprova o novo recorte (acordo do MVP)?

## PO-04 Três estágios do produto

A equipe vai apresentar o produto em três estágios:

1. **MVP:** roda localmente.
2. **Final acadêmico:** publicado com HTTPS numa VPS paga pela equipe, com RAG completo (busca híbrida, reranking, citações, avaliação) e agentes.
3. **Referência pós-acadêmica:** a arquitetura que o produto adotaria se crescesse (provedor de identidade dedicado, modelos locais, filas distribuídas, observabilidade própria, OCR). Fica **documentada, não implementada**, com o custo e o gatilho de cada tecnologia ([referência](../arquitetura/referencia-pos-academica.md)).

**Motivo:** o deploy é obrigatório e mantido pela equipe. A pilha completa exigiria uma VPS de 6 a 9 GB de RAM; a pilha do final acadêmico cabe em 2 a 4 GB, sem perder nenhuma das capacidades avaliadas na disciplina.

**Pergunta ao PO:** a referência documentada é aceita como demonstração de conhecimento das tecnologias não adotadas?

## PO-05 Revisão humana dos cartões gerados

Os cartões gerados pela IA não entram direto no estudo: o estudante aceita, edita ou recusa cada um (ou aceita todos). Os recusados ficam registrados e geram a **taxa de aceitação**, usada como métrica de qualidade da IA, junto do conjunto de casos de avaliação (Princípio V).

**Pergunta ao PO:** a taxa de aceitação é aceita como uma das métricas de avaliação da IA?
