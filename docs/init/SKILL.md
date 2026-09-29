---
name: plataforma-estudos
description: Criar e evoluir uma plataforma de estudos gamificada com materiais, trilhas, questões, flashcards e acompanhamento de desempenho, seguindo MVC e as regras técnicas deste documento.
---

# Plataforma de estudos — instruções de implementação

## Como usar

Leia este arquivo antes de implementar o sistema e leia [DESIGN.md](DESIGN.md) ao criar ou alterar interfaces. Os campos `[PREENCHER]` são configurações intencionais. Preserve as escolhas já definidas no projeto; pergunte apenas pelas decisões pendentes que bloqueiem a implementação solicitada. Não transforme sugestões em requisitos confirmados.

## Configuração técnica

| Item | Definição |
| --- | --- |
| Linguagem e versão do backend | [PREENCHER] |
| Framework e versão do backend | [PREENCHER] |
| Banco de dados e ferramenta de persistência | [PREENCHER] |
| Linguagem do frontend | JavaScript, com JSX nas interfaces; confirmar em DESIGN.md |
| Framework do frontend | React, preferência inicial; confirmar em DESIGN.md |
| Arquitetura | MVC obrigatório, com separação explícita de Model, View e Controller |
| Autenticação e perfis de acesso | [PREENCHER] |
| Armazenamento dos arquivos | [PREENCHER] |
| Processamento de materiais e geração de conteúdo | [PREENCHER: mecanismo, execução local/externa e eventual provedor] |
| Fuso usado para dias de estudo e conquistas | [PREENCHER] |
| Formatos, tamanho máximo e quantidade de arquivos | [PREENCHER] |
| Limites dos campos e da paginação | [PREENCHER] |
| Pontuação, conclusão de trilhas e critérios de conquistas | [PREENCHER] |

Usar IA para interpretar os materiais e propor trilhas, questões e flashcards, exclusivamente a partir dos arquivos enviados pelo usuário. Modelo, provedor e execução local ou externa permanecem a definir. Não pressupor OCR, serviço pago, ranking público ou repetição espaçada. Definir esses recursos apenas quando solicitados ou necessários ao escopo confirmado.

## Produto e fluxo principal

Construir uma plataforma em que o usuário envie e gerencie editais, apostilas e livros, transforme esses materiais em trilhas de aprendizagem e estude com questões e flashcards associados. Registrar tentativas, desempenho, pontos, progresso e conquistas.

Fluxo: enviar material → acompanhar processamento → acessar trilha estruturada → estudar questões e flashcards → consultar evolução.

Representar, conforme a persistência escolhida:

- **Material:** proprietário, título, tipo, arquivo, estado de processamento e motivo de falha quando houver.
- **Trilha e etapa:** organização e ordem dos assuntos, materiais de origem e critérios de conclusão.
- **Questão e alternativa:** enunciado, opções, uma resposta correta e explicação, no modelo inicial de escolha única.
- **Flashcard:** frente, verso e vínculo com a questão ou conceito estudado. A questão guarda alternativas e gabarito; o flashcard oferece a revisão correspondente.
- **Tentativa:** usuário, questão, alternativa escolhida, resultado e instante da resposta.
- **Progresso, registro de pontos e conquista:** evolução por usuário e trilha, origem de cada pontuação e critérios atendidos.

Manter referência verificável ao material, à sua versão e aos trechos que sustentam cada questão, explicação e flashcard. Incluir página quando disponível; nunca inventar paginação. Não publicar conteúdo sem suporte suficiente nos trechos enviados.

Usar o edital para identificar assuntos e organizar a cobertura. Uma simples menção a um assunto não fundamenta questões: marcar o tópico como “aguardando material de apoio” e solicitar arquivo complementar. Proibir pesquisa na internet, bases externas e preenchimento de lacunas com conhecimento geral do modelo. Permitir reformulação e exercícios derivados apenas quando verificáveis a partir dos materiais. O conteúdo do modelo não constitui evidência.

Extrair texto preservando origem e estrutura; processar por seções quando necessário. OCR ou análise visual dependem dos formatos aprovados. Separar erro técnico de leitura de insuficiência de conteúdo. Gerar saída estruturada, validar formato pelo código e verificar sustentação semântica antes da publicação. Uma segunda análise por IA ajuda, mas não comprova correção; avaliar também com amostras revisadas por pessoa responsável. Guardar versão do modelo e das instruções usadas.

Gerar questão e flashcard usando os mesmos trechos originais, sem usar apenas a questão gerada como fonte do flashcard. Persistir os resultados aprovados e corrigir alternativas pelo gabarito salvo, sem nova chamada de IA a cada resposta. Manter integração e credenciais no backend. O uso de um provedor externo de processamento não autoriza consulta a fontes externas.

## Arquitetura MVC obrigatória

| Camada | Responsabilidade | Limite |
| --- | --- | --- |
| Model | Entidades, invariantes e regras de domínio; acesso aos dados por mecanismos adequados ao framework | Não depender de componentes visuais ou de detalhes HTTP |
| View | Interface React, apresentação, interação e validações de experiência | Não acessar banco nem decidir pontuação ou autorização |
| Controller | Receber requisições, validar entrada, acionar casos de uso e devolver respostas | Não concentrar processamento de arquivos ou regras de negócio |

Em uma aplicação com API e frontend separados, o frontend constitui a View; não criar páginas de servidor apenas para satisfazer MVC. Serviços podem organizar casos de uso e repositórios podem isolar persistência quando isso reduzir acoplamento. Essas divisões complementam MVC e não substituem suas camadas.

Organizar módulos por domínio, como materiais, trilhas, estudos e conquistas, mantendo as responsabilidades MVC identificáveis. Seguir convenções obrigatórias do framework escolhido e registrar o mapeamento das camadas no projeto.

## Código e nomenclatura

- Escrever funções, variáveis, classes e nomes próprios do domínio em português, sem acentos nos identificadores e seguindo a convenção de caixa da linguagem.
- Usar nomes curtos que revelem intenção: `enviarMaterial`, `validarResposta`, `calcularProgresso`, `pontos`, `trilhaAtual`, `estaConcluida`. Evitar abreviações obscuras, nomes genéricos e frases longas.
- Preservar nomes exigidos por bibliotecas, protocolos e contratos externos, como hooks do React e campos padronizados do OpenAPI. Não traduzir APIs de terceiros.
- Manter funções coesas, dependências explícitas e regras reutilizadas em um único lugar. Evitar abstrações sem uso concreto e duplicação de regras de negócio.
- Comentar apenas decisões não evidentes, invariantes delicadas ou limitações externas. Explicar o motivo; não narrar o código. Não adicionar comentários em todas as funções.
- Manter textos de interface e erros destinados ao usuário em português. Nunca incluir segredos no código.

## Padrões críticos

### Textos

Usar UTF-8 e normalização Unicode NFC. Remover espaços nas extremidades dos campos simples; reduzir espaços internos apenas quando a regra do campo permitir. Preservar parágrafos, acentos, fórmulas e formatação relevante de materiais, questões e explicações.

Preservar o texto original para exibição. Aplicar comparação sem diferença de caixa ou acentos somente em chaves de busca que precisem disso. Não remover acentos indiscriminadamente nem normalizar senhas. Tratar conteúdo de arquivos como dado; se houver geração por IA, instruções contidas nos materiais não podem alterar as regras do processamento.

### Datas

Persistir instantes em UTC e transportar em ISO 8601 com fuso explícito. Usar `YYYY-MM-DD` para datas sem horário. Exibir datas no padrão brasileiro e no fuso configurado. Não interpretar strings ambíguas como `03/04/2026` no contrato da API. Calcular dias consecutivos e viradas de dia no fuso definido, com testes de fronteira.

### Validações e limites

Validar obrigatoriedade, tipo, comprimento, intervalo e vínculo entre entidades no backend. Replicar na interface os limites relevantes, conforme DESIGN.md. Centralizar constantes e contratos ou gerar tipos/esquemas quando a tecnologia permitir.

Verificar propriedade e autorização em cada operação. Validar arquivo por extensão permitida, tipo e conteúdo compatíveis, tamanho e quantidade; não confiar apenas no navegador. Guardar arquivos com identificadores internos e acesso controlado.

Exigir alternativas distintas, exatamente uma correta e explicação não vazia para questões de escolha única. Impedir respostas a questões indisponíveis e referências entre entidades de usuários diferentes. Definir a política de exclusão de materiais que já sustentam trilhas e histórico antes de permitir essa exclusão.

### Exceções e respostas

Tratar erros de domínio explicitamente e converter exceções HTTP em um ponto central. Adotar resposta consistente com `codigo`, `mensagem`, `campos` quando aplicável e `idRequisicao`. Não retornar stack trace, credenciais ou detalhes internos ao usuário.

Usar códigos HTTP coerentes: 400 para requisição malformada, 401 para ausência de autenticação, 403 para acesso negado, 404 para recurso não encontrado, 409 para conflito, 422 para entrada semanticamente inválida e 500 para falha inesperada. Registrar contexto suficiente para diagnóstico sem armazenar dados sensíveis desnecessários. Nunca esconder falha retornando sucesso vazio.

### Processamento e gamificação

Representar estados de processamento como pendente, processando, concluído e falhou. Não bloquear uma requisição durante trabalhos longos; escolher tarefa em segundo plano conforme a infraestrutura. Permitir reprocessamento controlado sem duplicar trilhas ou questões.

Calcular resultado, progresso, pontos e conquistas no servidor. Tornar reenvios da mesma tentativa idempotentes; uma nova tentativa legítima deve ter identidade própria. Registrar a tentativa e seus efeitos de forma consistente, usando transação quando aplicável. Não conceder a mesma conquista repetidamente.

Definir explicitamente quais tentativas geram pontos, como progresso é calculado e como alterações na trilha afetam seu denominador. Preservar o histórico com versão ou retrato suficiente da questão e do gabarito para que edições futuras não mudem resultados antigos. Antes da resposta, não enviar gabarito em campos ocultos da API ou do frontend.

## API e Swagger/OpenAPI

Criar e manter uma especificação OpenAPI compatível com a versão e as ferramentas escolhidas, com visualização interativa por Swagger UI. Preferir geração a partir dos contratos reais quando o framework oferecer suporte.

Documentar autenticação, operações de materiais, processamento, trilhas, questões, tentativas, flashcards, progresso e conquistas. Incluir esquemas, exemplos, limites, enumerações, paginação, upload multipart, respostas de erro e consulta do estado de tarefas assíncronas. Separar o contrato de questão antes da resposta do retorno de correção.

Registrar no projeto:

- Versão OpenAPI: [PREENCHER]
- Endereço da especificação: [PREENCHER]
- Endereço do Swagger UI: [PREENCHER]
- Comando de geração/validação: [PREENCHER]

Não expor credenciais reais em exemplos. Definir acesso à documentação conforme o ambiente.

## Comandos úteis

Preencher com comandos realmente disponíveis após escolher a stack. Informar o diretório de execução e manter esta tabela atualizada; não inventar comandos nem declarar execução sem evidência.

| Ação | Diretório | Comando |
| --- | --- | --- |
| Instalar dependências | [PREENCHER] | [PREENCHER] |
| Configurar ambiente local | [PREENCHER] | [PREENCHER] |
| Aplicar migrações | [PREENCHER] | [PREENCHER] |
| Run — iniciar backend | [PREENCHER] | [PREENCHER] |
| Run — iniciar frontend | [PREENCHER] | [PREENCHER] |
| Iniciar processamento em segundo plano, se utilizado | [PREENCHER] | [PREENCHER] |
| Build | [PREENCHER] | [PREENCHER] |
| Test — executar testes | [PREENCHER] | [PREENCHER] |
| Verificar estilo e formatação | [PREENCHER] | [PREENCHER] |
| Gerar/validar OpenAPI | [PREENCHER] | [PREENCHER] |

## Verificação da entrega

Implementar por fluxos completos, com interface, API e persistência integradas. Verificar especialmente autorização por usuário, validações, falhas de processamento, correção das respostas, reenvio de tentativas, pontuação e progresso. Testar os limites e invariantes de negócio; evitar testes que apenas reproduzam a implementação.

Executar build, testes e verificações disponíveis, revisar a documentação OpenAPI e conferir a interface conforme DESIGN.md. Relatar o que foi implementado, como foi verificado e quais configurações ou decisões ainda estão pendentes.
