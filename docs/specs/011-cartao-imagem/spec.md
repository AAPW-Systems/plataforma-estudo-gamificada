# Especificação: cartão com imagem na frente

**Identificador:** 011-cartao-imagem
**Estágio:** Final acadêmico
**Funcionalidade do backlog:** [F-04](../../produto/backlog.md#funcionalidades-candidatas), incremento do final acadêmico (os cartões manuais do MVP estão em [003-cartoes-manuais](../003-cartoes-manuais/spec.md))
**Criada em:** 12/10/2026
**Status:** Rascunho
**Origem:** backlog ("cartão com imagem, manual, até 3 MB"), [base de especificação](../../base-specs/spec.md) (RF-27, RN-08) e [sessão de 12/10/2026](../../prompts/2026-10-12-specs-funcionalidades.md)

## Problema e resultado esperado

**Usuário prioritário:** estudante de conteúdos visuais (anatomia, mapas, diagramas, vocabulário com figuras).
**Situação:** o estudante quer perguntar algo a partir de uma imagem, como "Que estrutura está indicada?" sobre um diagrama.
**Problema observável:** com frente só em texto, ele precisa descrever a imagem, o que entrega a resposta ou perde o sentido.
**Resultado esperado:** o estudante adiciona uma imagem à frente de um cartão que ele cria ou edita, com uma descrição para tecnologias assistivas, e a imagem aparece na lição.
**Alternativa atual:** descrever a imagem em texto ou estudar a figura fora da plataforma.

## Escopo

### Incluído

- Adicionar, trocar e remover uma imagem na frente de um cartão do estudante (criado ou editado).
- Formatos JPEG, PNG e WebP, de até 3 MB (RN-08).
- Texto alternativo obrigatório para a imagem.
- Exibição da imagem na lista de cartões e na lição.

### Fora do escopo

- Imagem no verso ou na explicação.
- Imagens geradas ou extraídas pela IA, e geração de cartões a partir de imagens.
- Edição da imagem (recorte, anotação).
- Formatos animados.

## Cenários de usuário e testes

### História de usuário 1 Criar um cartão com imagem P1

Como estudante, quero colocar uma imagem na frente de um cartão, para estudar conteúdos visuais.

**Motivo da prioridade:** é a única história desta spec.
**Teste independente:** criar um cartão com uma imagem PNG fictícia e texto alternativo, conferir a imagem na lição e remover a imagem; tentar enviar um arquivo de 4 MB e um arquivo que não é imagem com extensão `.png`.

**Cenários de aceitação**

1. **Dado** o formulário de cartão, **quando** o estudante adiciona uma imagem JPEG, PNG ou WebP de até 3 MB, com texto alternativo, e salva, **então** o cartão mostra a imagem na frente, na lista e na lição.
2. **Dado** uma imagem sem texto alternativo, **quando** o estudante tenta salvar, **então** o salvamento é recusado com a explicação junto do campo.
3. **Dado** um arquivo acima de 3 MB, de outro formato ou que não é uma imagem válida, **quando** o estudante tenta adicioná-lo, **então** é recusado com explicação específica.
4. **Dado** um cartão com imagem, **quando** o estudante troca ou remove a imagem, **então** a imagem anterior é apagada, e o agendamento do cartão não muda.
5. **Dado** um cartão "Gerado e verificado", **quando** o estudante adiciona uma imagem, **então** a origem passa a "Editado por você" ([003](../003-cartoes-manuais/spec.md), RF-006).

## Casos de borda

- Imagem com metadados de localização ou de câmera: os metadados são removidos antes de guardar.
- Imagem com dimensões muito grandes, mesmo abaixo de 3 MB (por exemplo, 20.000 × 20.000 pixels): recusada.
- Imagem cuja extensão não corresponde ao conteúdo real.
- Cartão excluído ou matéria excluída: a imagem é apagada junto.
- Imagem que não carrega na lição: a frente mostra o texto alternativo, e a lição segue.

## Requisitos funcionais

- **RF-001:** O estudante deverá conseguir adicionar, trocar e remover uma imagem na frente de um cartão seu, nos formatos JPEG, PNG ou WebP, de até 3 MB, verificando o tipo real do conteúdo (deriva de RN-08 e RF-27 da base).
- **RF-002:** A imagem deverá exigir um texto alternativo de 1 a 250 caracteres.
- **RF-003:** O sistema deverá remover os metadados da imagem antes de guardá-la e recusar imagens acima de um limite de dimensões configurável.
- **RF-004:** A imagem deverá ser servida apenas ao estudante dono do cartão.
- **RF-005:** Trocar ou remover a imagem, ou excluir o cartão, deverá apagar a imagem anterior.
- **RF-006:** O tamanho das imagens deverá contar para a cota de armazenamento do estudante ([002](../002-materias-fontes/spec.md), D-003, ou o novo valor de [009](../009-formatos-fontes/spec.md), Q-001).

## Entidades principais

- **Cartão:** passa a ter, opcionalmente, uma imagem na frente com texto alternativo.

## Critérios de sucesso

- **CS-001:** Em 100% dos testes, a imagem de um estudante não é acessível por outro, nem por quem conhece o endereço sem estar conectado.
- **CS-002:** Em 100% dos testes com imagens com metadados de localização, a imagem guardada não os contém.

## Requisitos de qualidade

- **RQ-001:** A imagem na lição se ajusta à largura a partir de 320 px, sem rolagem horizontal.
- **RQ-002:** O texto alternativo é lido por tecnologias assistivas na lição.
- **RQ-003:** O armazenamento das imagens segue o adaptador por ambiente ([DTEC 010](../../research.md#decisão-dtec-010-armazenamento-de-arquivos)).

## Suposições e dependências

- **Dependência:** [003-cartoes-manuais](../003-cartoes-manuais/spec.md) e [005-licao-trilha](../005-licao-trilha/spec.md).
- **Suposição:** o limite de 250 caracteres do texto alternativo é proposto pelo agente, configurável.

## Questões abertas

Nenhuma questão impede o planejamento.

## Decisões confirmadas

- **D-001:** O cartão com imagem é manual, com imagem só na frente, em JPEG, PNG ou WebP de até 3 MB (RN-08 da base). — **Confirmada por:** equipe, no [backlog](../../produto/backlog.md#final-acadêmico) — **Data:** 12/10/2026

## Exigências do PO

Nenhuma exigência (EX-01 a EX-05) toca esta funcionalidade.

## Verificação da constituição

| Princípio | Como a spec atende |
|---|---|
| I Fontes exclusivas | A imagem é conteúdo do estudante e nunca recebe selo de verificado |
| II Proteção e isolamento | RF-003, RF-004, CS-001, CS-002 |
| III Verificação humana | Troca e remoção por ação explícita |
| IV Servidor autoritativo | Validação no servidor; agendamento preservado |
| V Qualidade verificável | CS-001, CS-002; RQ-001, RQ-002 |
| VI Entrega incremental | História única, sobre 003 |
| VII Rastreabilidade | IDs da base citados; sessão registrada |
