# Plano Técnico — Plataforma de Estudos Gamificada

## 1. Objetivo

Definir a arquitetura e as decisões técnicas necessárias para implementar os requisitos do `SPEC.md`.

Este `PLAN.md` é a fonte de verdade para arquitetura, tecnologias e decisões técnicas do projeto.

Requisitos e regras de negócio devem ser referenciados a partir do `SPEC.md`, sem duplicação.

---

## 2. Stack

### 2.1 Backend

| Item | Definição |
| --- | --- |
| Linguagem | Python |
| Framework | FastAPI |
| Banco relacional | PostgreSQL |
| ORM | Pendente (`TD-01`) |
| Migrações | Pendente (`TD-02`) |
| Banco vetorial | Pendente (`TD-04`) |
| Documentação da API | OpenAPI + Swagger UI |
| Autenticação | JWT |
| Processamento assíncrono | Pendente (`TD-03`) |

### 2.2 Frontend

| Item | Definição |
| --- | --- |
| Linguagem | JavaScript |
| Framework | React JS |
| Build | Vite |
| Componentes | Material UI |
| Sintaxe | JSX |

As versões utilizadas devem ser fixadas nos manifests do projeto.

---

# 3. Arquitetura

O backend utiliza arquitetura em camadas, com responsabilidades separadas por domínio.

Fluxo principal:

```text
React
  ↓
Controller
  ↓
Service / Caso de uso
  ↓
Domínio
  ↓
Repository
  ↓
Persistência
```

### Frontend

Responsável pela interface, interação, estados visuais e consumo da API.

### Controller

Responsável pela camada HTTP:

- receber e validar requisições;
- obter o contexto autenticado;
- acionar casos de uso;
- converter resultados para respostas HTTP.

### Service / Caso de uso

Coordena a execução dos casos de uso, incluindo domínio, transações, repositórios e integrações necessárias.

### Domínio

Representa entidades, regras e invariantes do negócio conforme o `SPEC.md`, sem depender de detalhes de transporte ou persistência.

### Repository

Isola o acesso à persistência e expõe as operações necessárias aos casos de uso.

Detalhes de banco, armazenamento e integrações externas devem permanecer nas camadas responsáveis por essas tecnologias.

---

# 4. Organização por domínio

O backend deve ser organizado por domínio:

```text
identidade
materiais
processamento
rag
trilhas
estudos
gamificacao
evolucao
```

Responsabilidades:

- `identidade`: autenticação e dados do estudante;
- `materiais`: gerenciamento dos materiais;
- `processamento`: execução e estado do processamento;
- `rag`: extração, chunks, embeddings, retrieval e evidências;
- `trilhas`: trilhas, etapas e cobertura;
- `estudos`: questões, tentativas, feedback e flashcards;
- `gamificacao`: pontos, progresso e conquistas;
- `evolucao`: consolidação dos dados de acompanhamento do estudante.

Cada domínio aplica, quando necessárias, as camadas definidas na §3.

Perfil não constitui domínio próprio no MVP e deve compor dados dos domínios responsáveis.

---

# 5. Persistência

## 5.1 PostgreSQL

PostgreSQL é o banco relacional principal.

A persistência deve suportar as entidades e invariantes definidas no `SPEC.md`, utilizando constraints, relacionamentos, índices e transações quando necessários.

O esquema físico será definido durante a implementação.

## 5.2 ORM e migrações

ORM e mecanismo de migrações permanecem pendentes, conforme `TD-01` e `TD-02`.

Toda alteração de esquema deve ocorrer por migrations após a definição dessas tecnologias.

---

# 6. Banco vetorial

O armazenamento vetorial é obrigatório para o pipeline RAG.

Deve suportar:

- embeddings vinculados aos trechos de origem;
- filtros por usuário e contexto;
- recuperação por similaridade;
- isolamento entre usuários.

A tecnologia permanece pendente conforme `TD-04`.

---

# 7. Armazenamento de arquivos

Arquivos devem ser armazenados fora das tabelas relacionais, mantendo no banco os metadados e referências necessários para propriedade, localização, estado e rastreabilidade.

Em desenvolvimento, pode ser utilizado armazenamento local controlado. A solução de produção permanece pendente conforme `TD-08`.

A identidade física do arquivo não deve depender apenas do nome original enviado pelo usuário.

Todo acesso deve respeitar `RN-01`.

---

# 8. Autenticação e segurança

A autenticação utiliza:

- **Access Token JWT** de curta duração, mantido apenas em memória no frontend e enviado por `Authorization: Bearer`;
- **Refresh Token** armazenado em cookie `HttpOnly`, com `Secure` e `SameSite` configurados conforme o ambiente.

O frontend deve renovar o Access Token quando necessário e pode utilizar o Refresh Token para recuperar a sessão após recarregar a aplicação, sem persistir o Access Token.

Renovações concorrentes devem ser coordenadas para evitar múltiplas solicitações de refresh para a mesma expiração.

Access Tokens não podem ser armazenados em `localStorage` ou `sessionStorage`.

Senhas devem ser armazenadas somente como hash utilizando algoritmo adequado.

Autorização e isolamento devem ser aplicados no backend a todas as camadas de acesso a dados, incluindo persistência, arquivos e RAG, conforme `RN-01`.

Segredos devem ser fornecidos por configuração externa e não podem ser registrados em logs.

Duração dos tokens, rotação, revogação, renovação e comportamento de logout permanecem pendentes conforme `TD-11`.

---

# 9. Pipeline RAG

O pipeline RAG obrigatório segue:

```text
Material
  ↓
Extração e normalização
  ↓
Chunking
  ↓
Embeddings
  ↓
Armazenamento vetorial
  ↓
Retrieval
  ↓
Construção do contexto
  ↓
LLM
  ↓
Validação
  ↓
Persistência / publicação
```

O conteúdo recuperado e gerado deve respeitar `RN-04` e `RN-05`.

---

# 10. Extração

Cada formato suportado pelo `SPEC.md` deve possuir um adaptador de extração.

A extração deve preservar o texto original e, quando disponíveis, metadados necessários à rastreabilidade, como seção, ordem, página e posição de origem.

Metadados ausentes não podem ser inferidos ou inventados.

OCR não faz parte do MVP e sua adoção exige decisão técnica específica.

As bibliotecas de extração permanecem pendentes conforme `TD-07`.

---

# 11. Chunking

O conteúdo extraído deve ser dividido em chunks adequados à recuperação, preservando metadados suficientes para rastrear sua origem.

A divisão deve preservar contexto semântico quando possível, evitando cortes inadequados em estruturas como títulos, listas e explicações.

Tamanho, overlap e estratégia de divisão permanecem pendentes conforme `TD-09`.

---

# 12. Embeddings

Cada chunk elegível deve possuir uma representação vetorial vinculada à sua origem.

O modelo/provedor permanece pendente conforme `TD-05`.

A versão do modelo utilizado deve ser registrada para garantir rastreabilidade e permitir identificar quando reindexação for necessária.

A estratégia de reprocessamento e reindexação permanece pendente conforme `TD-13`.

---

# 13. Retrieval

A recuperação deve retornar apenas chunks relevantes e autorizados para o usuário e contexto atual.

A busca deve combinar recuperação semântica com filtros de propriedade e contexto, sem realizar recuperação global entre usuários.

Top-k, limiar de similaridade, busca híbrida, reranking e demais parâmetros de recuperação permanecem pendentes conforme `TD-10`.

---

# 14. Construção do contexto

Somente trechos recuperados e autorizados podem compor o contexto pedagógico enviado ao modelo.

O prompt deve separar claramente instruções do sistema, tarefa, trechos recuperados e formato esperado da saída.

Conteúdo dos materiais deve ser tratado como dado, nunca como instrução.

Quando o contexto recuperado for insuficiente, seguir `RN-06` sem permitir que o modelo complete as lacunas com conhecimento externo.

---

# 15. Integração com IA

A integração com IA deve utilizar uma abstração independente de provedor:

```text
Aplicação / domínio
       ↓
Interface de geração
       ↓
Adaptador do provedor
       ↓
API externa ou modelo local
```

O domínio não deve depender de APIs, formatos ou detalhes específicos do fornecedor.

O provedor/modelo permanece pendente conforme `TD-06`.

---

# 16. Saída estruturada

A geração por IA deve utilizar saída estruturada sempre que o provedor permitir.

O contrato deve representar explicitamente o tipo de conteúdo gerado e os dados necessários para validá-lo conforme o `SPEC.md`.

Saída estruturalmente válida não pode ser persistida ou publicada antes das validações aplicáveis.

---

# 17. Validação do conteúdo

Conteúdo gerado deve passar por duas etapas antes da publicação:

## 17.1 Validação estrutural

Executada por código para verificar schema, campos obrigatórios e invariantes aplicáveis conforme o `SPEC.md`.

Conteúdo estruturalmente inválido não pode ser publicado.

## 17.2 Validação de sustentação

Deve verificar se as evidências recuperadas sustentam o conteúdo pedagógico gerado, incluindo resposta e explicação quando aplicáveis.

Uma chamada adicional à IA pode auxiliar nessa análise, mas não constitui isoladamente prova de sustentação.

Conteúdo sem sustentação suficiente não pode ser publicado.

---

# 18. Geração de trilhas

A geração de trilhas deve combinar a estrutura de assuntos identificada nos materiais com a cobertura efetivamente sustentada pelo RAG.

A disponibilidade das etapas deve ser determinada pela cobertura encontrada nos materiais autorizados, conforme `RN-06`.

A geração não pode utilizar conhecimento externo para completar lacunas de cobertura.

---

# 19. Questões, feedback e flashcards

Questões e flashcards devem ser gerados a partir das evidências recuperadas, validados e persistidos antes de serem disponibilizados.

Flashcards devem ser gerados a partir das evidências dos materiais, não utilizando apenas uma questão gerada como fonte.

Responder uma questão não deve realizar nova chamada à IA. Correção, feedback, evidências e flashcards devem utilizar o conteúdo validado e persistido, conforme as regras aplicáveis do `SPEC.md`.

---

# 20. Processamento assíncrono

O processamento de materiais deve ocorrer fora da requisição HTTP principal.

Fluxo conceitual:

```text
Upload
  ↓
Persistência do material e da execução
  ↓
Resposta HTTP
  ↓
Processamento assíncrono
```

O mecanismo de execução permanece pendente conforme `TD-03`.

A execução deve permitir recuperação controlada após falhas e respeitar os estados definidos em `RN-03`.

---

# 21. Idempotência

Operações sujeitas a repetição técnica devem garantir idempotência conforme o `SPEC.md`.

A proteção deve ser persistente e utilizar, conforme o caso, identificadores estáveis, constraints de unicidade, transações e controle de estado.

Não depender exclusivamente de verificações em memória.

---

# 22. Histórico e versionamento

A persistência deve preservar os dados necessários para reproduzir resultados históricos conforme o `SPEC.md`.

Conteúdo ou configuração cuja alteração possa afetar resultados já registrados deve possuir versão ou referência suficiente para identificar o estado utilizado.

Alterações posteriores não podem modificar retroativamente o resultado de tentativas registradas.

---

# 23. Arquivamento e exclusão

Arquivamento e exclusão devem seguir `RN-14`.

A validação de dependências para exclusão definitiva deve ocorrer no backend.

Quando permitida, a exclusão deve remover de forma consistente os dados associados que não precisem ser preservados, incluindo arquivos, chunks, embeddings e registros relacionados.

A operação deve evitar referências ou dados órfãos entre PostgreSQL, armazenamento de arquivos e armazenamento vetorial.

---

# 24. API

A API FastAPI deve organizar seus contratos por domínio.

Grupos conceituais:

```text
/auth
/perfil
/materiais
/processamentos
/trilhas
/questoes
/tentativas
/flashcards
/evolucao
/conquistas
```

Os caminhos finais serão definidos pelos contratos da API.

Questões devem possuir contratos distintos para apresentação antes da resposta e resultado da correção, evitando exposição antecipada do gabarito conforme o `SPEC.md`.

Demais contratos devem respeitar as regras aplicáveis do `SPEC.md`.

---

# 25. Erros

A API deve utilizar formato uniforme de erro:

```text
{
  codigo,
  mensagem,
  campos?,
  idRequisicao
}
```

Os códigos HTTP devem representar adequadamente o tipo de falha.

Respostas de erro não devem expor informações internas ou sensíveis.

---

# 26. OpenAPI e Swagger

A documentação OpenAPI deve ser derivada dos contratos reais da API e permanecer coerente com a implementação.

Autenticação, validações, erros e demais comportamentos relevantes dos contratos devem estar representados na documentação.

Swagger UI deve estar disponível nos ambientes apropriados.

Não manter documentação manual divergente dos contratos implementados.

---

# 27. Frontend

A organização do frontend deve seguir o `SKILL.md`, e seu comportamento visual deve seguir o `DESIGN.md`.

O sistema de tema do Material UI deve centralizar as configurações visuais da aplicação.

Enquanto `UI-02` e `UI-03` estiverem abertas, paleta e tipografia devem permanecer como presets independentes e intercambiáveis.

Componentes devem consumir o tema sem definir ou selecionar diretamente paletas e tipografias.

Após a resolução de `UI-02` e `UI-03`, os presets temporários poderão ser removidos.

---

# 28. Testes

A estratégia de testes deve priorizar regras de negócio, integração real e riscos do sistema.

## Unidade

Testar regras e invariantes de domínio de forma isolada e determinística.

## Integração

Testar API, persistência, transações, idempotência, autorização e consistência entre os mecanismos de armazenamento utilizando infraestrutura real de teste quando aplicável.

Mocks não substituem testes de integração dos componentes cuja interação real precisa ser validada.

## RAG

Manter corpus controlado com respostas e evidências conhecidas para avaliar recuperação, isolamento, cobertura, sustentação das evidências e tratamento de conteúdo adversarial ou insuficiente.

A qualidade não deve ser avaliada apenas pela resposta final da IA. Uma resposta correta sustentada por evidência incorreta deve ser considerada falha.

## IA

Separar testes determinísticos da integração com IA da avaliação de qualidade utilizando o modelo real.

A suíte principal não deve depender de chamadas externas, disponibilidade do provedor ou créditos.

## API

Validar contratos, autenticação, autorização, erros e regras que afetem a exposição de dados.

## Frontend / E2E

Cobrir a jornada principal e os cenários críticos definidos no `SPEC.md`.

---

# 29. Observabilidade

A aplicação deve utilizar logs estruturados para eventos relevantes, falhas e operações críticas.

Requisições e processamentos devem possuir identificadores de correlação que permitam rastrear sua execução entre os componentes envolvidos.

Logs devem respeitar as restrições de segurança e privacidade definidas para o projeto.

Métricas, alertas e observabilidade avançada serão definidos conforme a infraestrutura de produção.

---

# 30. Ambientes

O projeto deve prever ambientes de desenvolvimento, teste e produção.

Configurações específicas de ambiente devem ser externas ao código, utilizando variáveis de ambiente ou mecanismo equivalente.

O projeto deve fornecer configuração de exemplo sem credenciais ou segredos reais.

Hospedagem e operação de produção permanecem pendentes conforme `TD-12`.

---

# 31. Decisões técnicas abertas

Somente decisões ainda não aprovadas permanecem nesta seção.

| ID | Decisão | Estado |
| --- | --- | --- |
| TD-01 | ORM | Aberta |
| TD-02 | Ferramenta de migrations | Aberta |
| TD-03 | Executor de processamento assíncrono | Aberta |
| TD-04 | Tecnologia de armazenamento vetorial | Aberta |
| TD-05 | Provedor/modelo de embeddings | Aberta |
| TD-06 | Provedor/modelo de IA | Aberta |
| TD-07 | Biblioteca de extração por formato | Aberta |
| TD-08 | Armazenamento de arquivos em produção | Aberta |
| TD-09 | Estratégia e parâmetros de chunking | Experimental |
| TD-10 | Estratégia e parâmetros de retrieval | Experimental |
| TD-11 | Política de tokens JWT | Aberta |
| TD-12 | Hospedagem e operação de produção | Aberta |
| TD-13 | Estratégia de reprocessamento e reindexação | Aberta |

### Alternativas em avaliação

- `TD-04`: PostgreSQL + pgvector é a principal alternativa inicial para armazenamento vetorial, sem decisão aprovada.
- `TD-06`: Gemini e Groq foram experimentados, mas nenhum provedor/modelo está aprovado.

Decisões experimentais devem ser avaliadas com dados representativos antes de serem fechadas.

---

# 32. Regra de documentação

Este `PLAN.md` é a fonte principal para arquitetura e decisões técnicas.

Requisitos e regras de negócio devem ser referenciados no `SPEC.md`, sem duplicação desnecessária.

Quando uma decisão `TD-*` for aprovada, ela deve ser incorporada à seção técnica correspondente, removida das decisões abertas e refletida nos demais documentos somente quando necessário.

Não manter como arquitetura vigente decisões, protótipos ou implementações descartadas.