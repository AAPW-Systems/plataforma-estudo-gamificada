# Design — plataforma de estudos gamificada

## Objetivo

Criar uma interface limpa, consistente e responsiva para organizar materiais, percorrer trilhas, responder questões, revisar flashcards e acompanhar evolução. Priorizar leitura e foco no estudo. Usar gamificação com discrição, sem competir visualmente com o conteúdo.

Este documento complementa [SKILL.md](SKILL.md). As regras de negócio e os limites devem concordar com o backend. Valores indicados como sugestões podem ser ajustados; campos `[PREENCHER]` devem ser definidos antes de implementar a funcionalidade correspondente.

## Tecnologia e identidade

| Item | Definição |
| --- | --- |
| Linguagem | JavaScript |
| Sintaxe dos componentes | JSX |
| Framework/biblioteca de interface | React, preferência inicial |
| Versão e ferramenta de build | [PREENCHER] |
| Biblioteca de componentes | [PREENCHER: nome, versão ou “componentes próprios”] |
| Solução de estilos | [PREENCHER] |
| Biblioteca de ícones | [PREENCHER] |
| Nome exibido do produto | [PREENCHER] |
| Fonte | [PREENCHER; sugestão: fonte de sistema sem serifa] |
| Cor principal | [PREENCHER; sugestão inicial: azul #2563EB] |
| Tema | Claro inicialmente; escuro somente se definido no escopo |
| Idioma | Português brasileiro |

Se houver alteração da linguagem ou framework, atualizar também SKILL.md. Usar a biblioteca escolhida de forma consistente; não misturar bibliotecas com estilos concorrentes sem necessidade. Escrever componentes, funções e variáveis do projeto em português, com nomes curtos e claros, preservando APIs exigidas pelo React. Comentar somente decisões não evidentes.

## Organização visual

Usar fundo neutro, superfícies claras, bordas discretas, boa hierarquia tipográfica e espaço em branco. Evitar excesso de gradientes, sombras, contornos e cores. Reservar a cor principal para ações e seleção; usar cores semânticas para sucesso, atenção e erro.

No desktop, usar navegação lateral compacta e conteúdo central; no celular, transformar a navegação em menu acessível. Destacar a área atual. Oferecer acesso a Início, Materiais, Trilhas e Evolução. Exibir conquistas dentro de Evolução e flashcards no contexto da trilha, salvo necessidade confirmada de telas próprias.

Na tela de estudo, reduzir distrações e priorizar enunciado, alternativas, explicação e navegação. Garantir que textos longos quebrem corretamente, sem cortes no conteúdo de estudo.

## Padrões de estilo

Centralizar valores em tokens ou tema da biblioteca. Valores iniciais sugeridos:

| Elemento | Padrão |
| --- | --- |
| Espaçamento | Escala de 4, 8, 12, 16, 24, 32 e 48 px |
| Texto de leitura | 16 px, entrelinha próxima de 1,5 |
| Títulos | Hierarquia consistente de 24 a 32 px, sem excesso de pesos |
| Cantos | 8 px em campos e botões; 12 px em cartões |
| Controles | Altura mínima de 44 px para facilitar toque |
| Conteúdo de leitura | Largura confortável próxima de 65 a 75 caracteres por linha |
| Contêiner geral | Largura máxima sugerida de 1200 px, com margens responsivas |
| Elevação | Sombra leve apenas quando comunicar sobreposição |

Validar contraste da paleta final. Não usar a cor principal automaticamente em textos pequenos sem verificar legibilidade. Definir cores de texto, fundo, borda, foco, seleção, desabilitado e estados semânticos no mesmo tema.

## Componentes e estados

| Componente | Regras |
| --- | --- |
| Campos | Rótulo persistente, ajuda quando necessária, indicação de obrigatório e erro junto ao campo; placeholder não substitui rótulo |
| Botões | Variantes primária, secundária, discreta e destrutiva; uma ação principal por área; verbos claros como “Enviar material” e “Confirmar resposta” |
| Seleções | Aparência e comportamento consistentes em selects, radios e checkboxes; área clicável inclui o rótulo |
| Cartões | Título, informação essencial e ação clara; não transformar toda informação em um cartão |
| Upload | Seleção por botão além de arrastar e soltar, formatos e limites visíveis, lista de arquivos e estado individual |
| Progresso | Barra acompanhada de valor textual e descrição, com cálculo vindo do servidor |
| Avisos | Mensagem no contexto da ação; notificações temporárias apenas para eventos simples |
| Diálogos | Título, ação inequívoca, foco controlado e fechamento acessível; usar confirmação para exclusões com impacto |
| Listas | Paginação ou carregamento incremental conforme o contrato, busca quando útil e estado vazio explicativo |

Prever estados padrão, foco, hover quando aplicável, selecionado, desabilitado, carregando, erro e sucesso. Durante envios, mostrar andamento e bloquear duplicação da ação. Explicar por que uma ação está indisponível quando isso não for evidente.

## Telas e fluxos

### Início

Exibir uma ação “Continuar estudo”, resumo de progresso, pontos e atividade recente. Para novos usuários, orientar o envio do primeiro material. Não exibir métricas fictícias em telas integradas; dados demonstrativos devem estar claramente identificados.

### Materiais

Permitir listar, enviar, consultar e gerenciar materiais. Exibir título, tipo e estado de processamento. Distinguir pendente, processando, concluído e falhou. Mostrar separadamente a suficiência do conteúdo: um processamento concluído pode identificar assuntos sem material de apoio. Informar “As atividades são geradas apenas a partir dos materiais enviados”. Não oferecer pesquisa externa como recuperação de lacunas. Oferecer recuperação de falha quando disponível e explicar efeitos da exclusão antes de confirmá-la.

### Trilhas

Apresentar etapas em sequência, assunto, situação e progresso. Distinguir assunto pronto para estudo de assunto “aguardando material de apoio”; este último deve explicar a lacuna e oferecer envio de material complementar, sem questões inventadas nem indicação de conclusão. A associação do novo arquivo à trilha segue a política a definir em Spec.md. Distinguir etapa disponível e concluída; mostrar bloqueios apenas se a regra de negócio os exigir. Acessar questões e flashcards a partir da etapa e indicar os materiais de origem.

### Questões

Mostrar enunciado e alternativas legíveis com seleção única. Exigir seleção antes de confirmar. Após a resposta validada pelo servidor, indicar resultado com texto e ícone, destacar a alternativa correta e apresentar explicação e referência disponível. Não revelar o gabarito antes da confirmação. Exibir na correção a referência ao material e ao trecho que sustenta a resposta, com página apenas quando conhecida. Não exibir antes da resposta um trecho de evidência que entregue o gabarito.

Manter o feedback visível até o usuário avançar. Exibir posição da questão no conjunto e oferecer próxima etapa sem avanço automático inesperado.

### Flashcards

Mostrar frente com ação explícita “Revelar resposta”. No verso, apresentar resposta, explicação disponível e referência ao trecho de origem. Não usar a questão gerada como única fonte do flashcard. Garantir uso por teclado, sem depender de gesto ou animação de virar. Autoavaliação e agendamento de revisão só aparecem se essas regras estiverem implementadas e definidas.

### Evolução e conquistas

Exibir acertos, tentativas, progresso por trilha e pontos com período e definição compreensíveis. Diferenciar percentual de acertos de percentual de conclusão. Mostrar critérios das conquistas, estado obtido ou pendente e data quando aplicável. Não depender exclusivamente de gráficos ou cores para comunicar os dados.

## Validações e limites na interface

Preencher a tabela com os mesmos valores dos contratos do backend. Nenhum valor pendente deve virar limite arbitrário no código.

| Entrada/ação | Limite a configurar | Comportamento |
| --- | --- | --- |
| Título do material ou trilha | [PREENCHER: mínimo e máximo] | Remover espaços nas extremidades e informar erro de comprimento |
| Descrição | [PREENCHER: máximo] | Mostrar contador próximo do limite |
| Arquivo | [PREENCHER: formatos e tamanho máximo] | Informar restrições antes do envio e rejeitar incompatibilidades detectáveis |
| Envio em lote | [PREENCHER: quantidade máxima] | Informar excedente e permitir ajustar seleção |
| Busca | [PREENCHER: máximo e eventual mínimo] | Evitar requisições a cada tecla sem controle |
| Resposta de questão | Uma alternativa válida | Não confirmar sem seleção nem aceitar novo envio enquanto a tentativa estiver pendente |
| Listagem | [PREENCHER: tamanho de página permitido] | Respeitar limites da API e manter navegação compreensível |

Validar campos após interação ou tentativa de envio, evitando erros antes de o usuário começar a preencher. Preservar valores quando o servidor rejeitar o formulário. Associar cada erro ao campo correspondente e focar o primeiro campo inválido após envio, quando apropriado.

As validações locais melhoram a experiência; a API continua responsável por autorizar, validar e calcular resultados. Mostrar erros retornados pelo servidor em português e oferecer nova tentativa em falhas recuperáveis. Não apresentar pontos ou conquistas como confirmados antes da resposta do servidor.

## Acessibilidade, responsividade e estados de página

- Usar elementos semânticos, ordem lógica de títulos, rótulos associados, nomes acessíveis em ícones e foco visível.
- Permitir operar menus, formulários, alternativas, flashcards e diálogos inteiramente por teclado. Devolver foco ao acionador ao fechar diálogos.
- Usar contraste mínimo de 4,5:1 em texto comum e 3:1 em texto grande e elementos visuais essenciais; validar na composição final.
- Comunicar erros e resultados também por texto. Anunciar atualizações relevantes a tecnologias assistivas sem excesso de interrupções.
- Respeitar preferência por movimento reduzido. Evitar animações prolongadas, sons automáticos ou efeitos que prejudiquem concentração.
- Adaptar listas e painéis sem rolagem horizontal na página. Verificar telas pequenas a partir de 320 px, desktop e ampliação de texto.
- Prever carregamento, vazio inicial, nenhum resultado, falha e acesso negado. Cada estado deve explicar a situação e oferecer uma ação útil quando houver.
- Não usar percentuais artificiais durante processamento sem progresso mensurável; mostrar estado indeterminado.

## Critérios de revisão visual

Antes de concluir uma interface, verificar consistência de campos e botões, hierarquia, espaçamento, legibilidade de conteúdo longo e funcionamento por teclado. Conferir os fluxos de envio, processamento com falha, resposta correta/incorreta e visualização de progresso, em celular e desktop.

Confirmar que os limites coincidem com a API, que estados vazios e erros estão presentes e que nenhuma informação sensível ou resposta correta aparece prematuramente. Entregar uma interface simples, com ações claras e componentes reutilizados.
