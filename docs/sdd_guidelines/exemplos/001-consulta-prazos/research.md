# Pesquisa e decisões técnicas da consulta de prazos

**Data:** 24 de setembro de 2026

## Decisão DTEC 001 API e validação

**Questão:** qual estrutura permite expor o contrato, validar entradas e testar a API com pouco código?  
**Critérios:** experiência básica da turma com Python, documentação do contrato, testes automatizados e tempo do projeto.  
**Alternativas consideradas:** FastAPI com Pydantic; Flask com validação manual; biblioteca padrão com servidor HTTP.

**Decisão:** usar Python 3.12, FastAPI e Pydantic.  
**Justificativa:** o contrato OpenAPI e a validação de entrada ficam visíveis, e o ecossistema possui suporte direto a testes HTTP.  
**Consequências:** a equipe precisará fixar versões e aprender dependências assíncronas apenas quando necessárias.  
**Condição para revisão:** incompatibilidade com o ambiente de implantação fornecido pela disciplina.

## Decisão DTEC 002 Recuperação inicial

**Questão:** qual mecanismo de recuperação permite demonstrar a primeira história sem introduzir um serviço externo?  
**Critérios:** reprodutibilidade local, inspeção dos resultados, corpus de até 20 documentos e possibilidade de evolução.  
**Alternativas consideradas:** SQLite FTS5; busca por embeddings em serviço vetorial; envio de todos os documentos ao modelo.

**Decisão:** usar SQLite FTS5 como linha de base e esconder a busca atrás de uma interface `Retriever`.  
**Justificativa:** a coleção é pequena, a busca funciona offline e os testes são determinísticos. A interface permite adicionar busca semântica em outra iteração.  
**Consequências:** sinônimos podem falhar; os casos que falharem serão preservados para comparar a futura busca vetorial.  
**Condição para revisão:** mais de 20 por cento das consultas respondíveis não recuperarem a fonte esperada no conjunto de avaliação.

## Decisão DTEC 003 Resposta inicial

**Questão:** o primeiro incremento depende de um modelo de linguagem?  
**Critérios:** fidelidade à fonte, custo, disponibilidade e isolamento da falha de recuperação.  
**Alternativas consideradas:** resposta extrativa; modelo remoto; modelo local.

**Decisão:** iniciar com resposta extrativa e contrato de gerador.  
**Justificativa:** a equipe consegue validar recuperação, ausência e referências antes de introduzir variabilidade de geração.  
**Consequências:** a redação será menos natural. Uma integração com LLM poderá ser adicionada depois, mantendo os testes de evidência.  
**Condição para revisão:** aprovação dos casos de recuperação e disponibilidade de orçamento para o modelo.

## Decisão DTEC 004 Persistência e logs

**Questão:** onde armazenar documentos, trechos e registros de execução no ambiente didático?  
**Critérios:** configuração simples, rastreabilidade e ausência de infraestrutura externa.  
**Alternativas consideradas:** SQLite; PostgreSQL; arquivos JSON.

**Decisão:** usar SQLite com migrações.  
**Justificativa:** atende a escala inicial e oferece transações e consultas suficientes.  
**Consequências:** implantação com várias réplicas exigirá revisão do armazenamento.  
**Condição para revisão:** execução concorrente em mais de uma instância ou crescimento incompatível com arquivo local.

## Fontes consultadas

- Documentação oficial do FastAPI para validação, testes e OpenAPI.
- Documentação oficial do SQLite sobre FTS5.
- Experimento local com o corpus de avaliação da disciplina.
