# Especificação da triagem de solicitações acadêmicas

**Identificador:** 002-triagem-solicitacoes  
**Criada em:** 24 de setembro de 2026  
**Status:** Aprovada para planejamento

## Problema e resultado esperado

Estudantes nem sempre sabem qual setor recebe uma solicitação. A funcionalidade deve sugerir uma categoria e um setor com base em uma descrição curta. O estudante confirma ou corrige a sugestão antes de copiar as informações para o canal oficial.

## Escopo

### Incluído

- descrições em português com até 1000 caracteres;
- categorias `matricula`, `documentos`, `financeiro` e `outros`;
- sugestão acompanhada de justificativa curta;
- confirmação ou correção pelo usuário;
- tratamento de baixa confiança e indisponibilidade.

### Fora do escopo

- enviar a solicitação;
- consultar situação individual;
- persistir o texto informado;
- aprender automaticamente com correções;
- prometer prazo de atendimento.

## Cenários de usuário e testes

### História de usuário 1 Receber sugestão de destino P1

Como estudante, quero descrever minha necessidade para saber qual categoria e setor devo procurar.

**Teste independente:** informar um caso rotulado como matrícula e verificar categoria, setor, justificativa e opção de correção.

**Cenários de aceitação**

1. **Dado** um texto válido e compatível com matrícula, **quando** a análise termina, **então** o sistema sugere `matricula`, apresenta o setor configurado e permite confirmar ou corrigir.
2. **Dado** que o estudante corrige a categoria, **quando** confirma a correção, **então** a interface apresenta a escolha final sem enviar a solicitação.

### História de usuário 2 Tratar classificação incerta P2

Como estudante, quero saber quando a descrição não permite uma sugestão confiável para complementar a informação.

**Teste independente:** informar “preciso resolver uma pendência” e confirmar que o sistema pede assunto e contexto sem escolher um setor.

**Cenários de aceitação**

1. **Dado** um resultado abaixo do limiar configurado, **quando** a análise termina, **então** o sistema pede uma descrição mais específica e não apresenta setor como correto.

## Casos de borda

- Entrada vazia, acima de 1000 caracteres ou somente com dados pessoais.
- Duas categorias com pontuações próximas.
- Categoria válida sem setor configurado.
- Serviço de classificação indisponível.

## Requisitos funcionais

- **RF-001:** O sistema deverá aceitar texto em português entre 10 e 1000 caracteres após normalização de espaços.
- **RF-002:** O sistema deverá retornar categoria, setor, justificativa e estado de confiança para resultados acima do limiar.
- **RF-003:** O sistema deverá permitir confirmar ou corrigir a categoria antes de qualquer próxima ação.
- **RF-004:** O sistema não deverá enviar a solicitação nem afirmar que ela foi protocolada.
- **RF-005:** Abaixo do limiar, o sistema deverá solicitar contexto adicional sem sugerir um setor como fato.
- **RF-006:** Em indisponibilidade, o sistema deverá exibir os setores e suas descrições para escolha manual.
- **RF-007:** O texto da solicitação não deverá ser persistido nem escrito em logs.

## Critérios de sucesso

- **CS-001:** A categoria sugerida coincide com o gabarito em pelo menos 12 dos 15 casos de desenvolvimento.
- **CS-002:** Nos cinco casos reservados, o relatório apresenta acertos, erros e casos recusados sem alterar o sistema durante a execução.
- **CS-003:** Quatro de cinco estudantes concluem a escolha de setor em até dois minutos no teste guiado.
- **CS-004:** Nenhum dos testes de interface apresenta mensagem de protocolo ou envio concluído.

## Suposições e dependências

- O PO mantém o mapa entre categorias e setores.
- O conjunto de 20 casos não contém dados pessoais reais.
- O limiar será definido no plano e ajustado somente com os 15 casos de desenvolvimento.
