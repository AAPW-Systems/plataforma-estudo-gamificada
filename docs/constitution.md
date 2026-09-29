# Constituição do projeto

**Projeto:** Plataforma de estudos gamificada
**Versão:** 0.2 (rascunho)
**Aprovada em:** pendente
**Responsáveis pela aprovação:** equipe do projeto (Arthur Moura, Artur Lins, Pedro Paulo Lucena e William Johnson). O professor Aldo Nunes é o PO do produto.

Este documento registra princípios estáveis que valem para todas as funcionalidades. Decisões específicas de uma funcionalidade ficam em sua spec, plano ou `research.md`, e não aqui. Os princípios foram extraídos do brainstorming inicial ([`init/SKILL.md`](init/SKILL.md), [`init/DESIGN.md`](init/DESIGN.md) e [`init/Spec.md`](init/Spec.md)) e das decisões confirmadas na sessão de estruturação ([registro](prompts/2026-09-29-estruturacao-projeto.md)).

## Princípios

### I Fontes exclusivas e evidência antes de afirmação

A IA gera conteúdo e responde perguntas **somente** a partir dos materiais enviados pelo próprio usuário. Não há pesquisa na internet, bases externas nem complementação de lacunas com conhecimento geral do modelo.

- Todo flashcard, questão, explicação ou resposta do chat **gerado pela IA** aponta para o material, a versão e o trecho que o sustenta. A página aparece apenas quando for efetivamente conhecida e nunca é inventada.
- Conteúdo criado ou editado pelo usuário é permitido, mas sempre exibe sua origem e nunca é apresentado como verificado pela fonte. Esse conteúdo não entra na avaliação de qualidade da IA.
- Uma referência existente não prova sustentação. O conteúdo gerado passa por validação estrutural e de sustentação antes de ser publicado.
- Na ausência de evidência suficiente, o sistema declara a limitação e não apresenta o conteúdo como fato.
- Reformulações e derivações são permitidas quando verificáveis a partir da fonte.

Origem: DC-09, RN-11, RN-12 e RN-13 do init.

### II Proteção e isolamento de dados

- Todo recurso (material, trecho, flashcard, revisão, tentativa, pontos, sequência, conversa) pertence a um único usuário. Conhecer um identificador não concede acesso.
- Segredos nunca aparecem no código, nos logs, nos exemplos de contrato ou nos registros de prompt. Configuração sensível vem de variáveis de ambiente, com arquivo `.env.example` sem valores reais.
- Logs não registram o conteúdo bruto dos materiais, perguntas do chat ou dados pessoais além do necessário ao diagnóstico.
- O conteúdo dos materiais é tratado como dado e nunca como instrução ao sistema. Instruções embutidas em um arquivo não alteram as regras do processamento (defesa contra *prompt injection*).
- Testes, exemplos e demonstrações não usam dados pessoais reais.

Origem: RN-01, RQ-01, CB-14 e SKILL.md (Textos, Validações) do init.

### III Verificação humana

- Decisões de produto pertencem ao PO e à equipe. Um agente pode estruturar opções e consequências, mas não transforma ausência de resposta em aprovação.
- Nenhum artefato avança automaticamente: a spec é revisada antes do plano, e o plano antes das tarefas.
- Ações destrutivas ou com impacto no histórico do usuário exigem confirmação explícita na interface.

Origem: guidelines SDD (`sdd_guidelines/00_COMECE_AQUI.md`, "Regra de trabalho").

### IV Servidor autoritativo e consistência

- Correção de respostas, XP, pontos, sequência diária (*streak*), agendamento de revisões, progresso e conquistas são calculados no servidor. A interface nunca apresenta esses valores como confirmados antes da resposta do servidor.
- Reenvios de um mesmo evento são idempotentes: a mesma identidade com o mesmo conteúdo produz o mesmo resultado, sem crédito repetido. A mesma identidade com conteúdo divergente gera conflito.
- O histórico é preservado: alterar ou reprocessar conteúdo não muda resultados já registrados.
- Instantes são persistidos em UTC e transportados em ISO 8601 com fuso explícito. Agregações por dia usam o fuso configurado do usuário.

Origem: RN-05, RN-06, RN-08, RN-10 e DC-08 do init.

### V Qualidade verificável

- Cada história possui critérios de aceitação observáveis e teste correspondente. Uma tarefa só é marcada como concluída após a verificação.
- A API é documentada por uma especificação OpenAPI coerente com as respostas reais, incluindo erros.
- A interface atende WCAG 2.2 nível AA: operação completa por teclado, contraste mínimo de 4,5:1 e uso a partir de 320 px sem rolagem horizontal.
- O comportamento variável da IA é avaliado com um conjunto de casos revisado por pessoa responsável. Uma segunda chamada de IA não é prova de correção.

Origem: RF-13, RQ-03, RQ-07 e CS-05 do init.

### VI Entrega incremental

- As funcionalidades são especificadas e entregues uma de cada vez, a partir do [backlog](produto/backlog.md).
- A história P1 de cada funcionalidade é demonstrável isoladamente, antes das histórias seguintes.
- As tarefas são organizadas por história de usuário, e não por camada técnica.

### VII Rastreabilidade do uso de agentes

- Toda sessão com agente de programação que produza ou altere artefatos é registrada em [`docs/prompts/`](prompts/README.md), com o prompt literal, o contexto, a saída aceita e as alterações humanas.
- Requisitos, cenários, testes e tarefas mantêm identificadores estáveis e são ligados por `traceability.md`.

Origem: apostila SDD, seção 11 ("Preserve autoria e evidência").

## Restrições do projeto

- **Docker obrigatório:** todos os serviços do sistema executam em contêineres, e o ambiente completo sobe com um único comando documentado.
- **IA é parte essencial do produto:** o projeto é avaliado na disciplina de IA do curso de Sistemas de Informação. Geração de flashcards e chat sobre os materiais (RAG) são capacidades centrais.
- **Arquitetura MVC:** Model, View e Controller são identificáveis no código (DC-02 do init). Se front e backend forem separados, o frontend constitui a View.
- **Idioma:** interface, mensagens de erro e documentação em português brasileiro. Identificadores do domínio em português, sem acentos, seguindo a convenção de caixa da linguagem (DC-03 do init). Nomes exigidos por bibliotecas e protocolos são preservados.
- **Stack, banco de dados e separação entre front e backend:** direção definida no brainstorming aprofundado (backend em Python, frontend em React, PostgreSQL, front e backend separados). Framework do backend e stack de IA pendentes ([pendências](produto/pendencias.md)). A decisão final é registrada em `research.md` e ADR (QA-01, QA-18, QA-22).
- **Processo:** as guidelines em [`sdd_guidelines/`](sdd_guidelines/00_COMECE_AQUI.md) devem ser seguidas integralmente.

## Governança

- Alterações neste documento exigem acordo da equipe e registro em [`docs/prompts/`](prompts/README.md) quando feitas com agente. Cada mudança incrementa a versão e é anotada no histórico abaixo.
- Specs e planos registram, na seção "Verificação da constituição", como atendem cada princípio.
- Exceções explicam o motivo, o risco, a alternativa rejeitada e o prazo de revisão, na seção "Complexidade e exceções" do plano.

## Histórico

| Versão | Data | Mudança |
|---|---|---|
| 0.1 | 29/09/2026 | Rascunho inicial extraído do brainstorming inicial e da sessão de estruturação |
| 0.2 | 29/09/2026 | Princípio I restrito ao conteúdo gerado pela IA, com regra para conteúdo do usuário (QA-20); professor Aldo Nunes registrado como PO; equipe nomeada ([registro](prompts/2026-09-29-brainstorming-aprofundado.md)) |
