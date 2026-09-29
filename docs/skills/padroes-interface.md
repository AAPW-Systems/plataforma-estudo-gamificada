# Guia: padrões de interface

**Origem:** seções agnósticas de stack e de identidade visual de [`../init/DESIGN.md`](../init/DESIGN.md), migradas em 29/09/2026.
**Pendente:** biblioteca de interface, solução de estilos, ícones, nome do produto, tema, paleta e tipografia (QA-18 e QA-19). Os valores de tema claro e azul `#2563EB` do init **não** foram adotados.

## Princípios de interface

- O foco é o estudo. A gamificação motiva sem competir visualmente com o conteúdo do cartão ou da resposta.
- A cor principal é reservada para ações e seleção. Cores semânticas indicam sucesso, atenção e erro, sempre acompanhadas de texto ou ícone.
- Os valores visuais (espaçamento, tipografia, cantos, cores, elevação) vivem em *tokens* centralizados. Nenhum valor mágico fica solto em componentes.
- Os componentes são reutilizados. Não misture bibliotecas com estilos concorrentes.

## Componentes e estados

| Componente | Regras |
|---|---|
| Campos | Rótulo persistente (o *placeholder* não substitui o rótulo), indicação de obrigatório e erro junto ao campo |
| Botões | Variantes primária, secundária, discreta e destrutiva. Uma ação principal por área, com verbos claros ("Enviar material", "Revelar resposta") |
| Upload | Seleção por botão além de arrastar e soltar, formatos e limites visíveis e estado individual por arquivo |
| Flashcard | Ação explícita "Revelar resposta", operável por teclado e sem depender de gesto ou animação. O verso mostra a resposta e a referência ao trecho de origem |
| Chat | Cada resposta exibe as citações navegáveis até o trecho. Quando não há evidência, isso é dito claramente |
| Progresso e XP | Valor textual junto de qualquer barra ou gráfico. Os valores vêm do servidor e nunca são exibidos antes da confirmação |
| Diálogos | Título, ação inequívoca, foco controlado e retorno do foco ao acionador. Confirmação para exclusões com impacto |
| Listas | Paginação ou carregamento incremental conforme o contrato, e estado vazio explicativo |

Todo componente interativo prevê os estados padrão, foco, *hover*, selecionado, desabilitado, carregando, erro e sucesso. Durante um envio, o andamento aparece e a ação não pode ser duplicada. Uma ação indisponível explica o motivo quando isso não for evidente.

## Estados de página

Cada tela prevê os estados de carregamento, vazio inicial, nenhum resultado, falha e acesso negado, cada um com explicação e uma ação útil. Durante o processamento sem progresso mensurável, use um indicador indeterminado, nunca um percentual artificial. Dados demonstrativos são identificados como tais.

## Validações na interface

- Os limites são os mesmos do contrato do backend, com valores centralizados.
- Valide após a interação ou a tentativa de envio, e não antes de o usuário começar a digitar.
- Preserve os valores quando o servidor rejeitar o formulário. Foque o primeiro campo inválido.
- Exiba os erros do servidor em português e ofereça nova tentativa quando a falha for recuperável.

## Acessibilidade (WCAG 2.2 AA)

- Elementos semânticos, ordem lógica de títulos, rótulos associados, nomes acessíveis em ícones e foco visível.
- Operação completa por teclado: menus, formulários, flashcards, chat e diálogos.
- Contraste mínimo de 4,5:1 para texto comum e de 3:1 para texto grande e elementos essenciais, validado na paleta final.
- Atualizações relevantes (resultado, XP ganho, conquista) são anunciadas a tecnologias assistivas sem excesso.
- A preferência por movimento reduzido é respeitada. Não há sons automáticos nem animações prolongadas.

## Responsividade

Verifique a partir de 320 px, no desktop e com texto ampliado. A página nunca tem rolagem horizontal. Textos longos quebram sem cortar o conteúdo de estudo.

## Revisão antes de concluir uma tela

Verifique a consistência de campos e botões, a hierarquia, os espaçamentos, a legibilidade de conteúdo longo, o uso por teclado, os estados vazio e de erro, os limites iguais aos da API e a ausência de exposição prematura de respostas. Confira no celular e no desktop.
