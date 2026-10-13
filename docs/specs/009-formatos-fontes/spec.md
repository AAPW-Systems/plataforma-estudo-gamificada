# Especificação: novos formatos de fonte e envio múltiplo

**Identificador:** 009-formatos-fontes
**Estágio:** Final acadêmico
**Funcionalidade do backlog:** [F-02](../../produto/backlog.md#funcionalidades-candidatas), incremento do final acadêmico (a parte do MVP está em [002-materias-fontes](../002-materias-fontes/spec.md))
**Criada em:** 12/10/2026
**Status:** Rascunho
**Origem:** backlog ("formatos SRT, VTT, DOCX e envio múltiplo no Final"), [base de especificação](../../base-specs/spec.md) (RN-02, RN-03, RN-05, CB-04) e [sessão de 12/10/2026](../../prompts/2026-10-12-specs-funcionalidades.md)

## Problema e resultado esperado

**Usuário prioritário:** estudante que estuda também por videoaulas e documentos de texto editáveis.
**Situação:** o estudante tem legendas de aulas gravadas e apostilas em DOCX, além de PDFs.
**Problema observável:** no MVP, ele precisa converter esses arquivos antes de enviar e enviá-los um a um.
**Resultado esperado:** o estudante envia legendas (SRT e VTT) e documentos DOCX, e vários arquivos de uma vez. Os cartões gerados de uma legenda mostram o momento da aula em que o conteúdo aparece.
**Alternativa atual:** converter para PDF ou TXT e enviar um por vez.

## Escopo

### Incluído

- Formatos SRT, VTT e DOCX, além dos do MVP.
- Envio de mais de um arquivo por vez, com resultado individual por arquivo.
- Novos limites de tamanho por arquivo, de arquivos por envio e de cota (Q-001).
- Localização do trecho por tempo nas legendas (Q-002).

### Fora do escopo

- OCR de PDF digitalizado e de imagens dentro do DOCX, XLSX e PPTX: referência pós-acadêmica.
- Envio de vídeo ou áudio, e transcrição automática.
- Importar a partir de um endereço da internet.

## Cenários de usuário e testes

### História de usuário 1 Enviar legendas e documentos DOCX P1

Como estudante, quero enviar legendas de aulas e documentos DOCX, para estudar todo o meu material sem convertê-lo.

**Motivo da prioridade:** amplia a base de fontes, que alimenta a geração e o chat.
**Teste independente:** enviar um SRT, um VTT e um DOCX fictícios, conferir que chegam a `concluido` e que os trechos das legendas têm o intervalo de tempo e os do DOCX não têm página.

**Cenários de aceitação**

1. **Dado** um arquivo SRT ou VTT válido, **quando** o estudante o envia, **então** a fonte chega a `concluido`, o texto é extraído sem as marcações de tempo e de estilo, e cada trecho guarda o intervalo de tempo de origem.
2. **Dado** um DOCX válido, **quando** o estudante o envia, **então** a fonte chega a `concluido` com o texto dos parágrafos, títulos, listas e tabelas, sem página (que não é conhecida no DOCX).
3. **Dado** um cartão gerado de uma legenda, **quando** o estudante abre a evidência, **então** vê o intervalo de tempo do trecho (por exemplo, "12:34 a 13:05").
4. **Dado** um DOCX com macros, objetos incorporados ou imagens, **quando** ele é processado, **então** apenas o texto é extraído, nada é executado e as imagens são ignoradas.

### História de usuário 2 Enviar vários arquivos de uma vez P2

Como estudante, quero enviar vários arquivos de uma vez, para montar o acervo de uma matéria rapidamente.

**Motivo da prioridade:** conveniência; a US1 já entrega os formatos.
**Teste independente:** enviar 5 arquivos, sendo um inválido, e confirmar que os 4 válidos são aceitos e o inválido é recusado com explicação, sem afetar os outros.

**Cenários de aceitação**

1. **Dado** vários arquivos selecionados, **quando** o estudante os envia, **então** cada um aparece com seu próprio estado e seu próprio resultado.
2. **Dado** um arquivo inválido entre válidos, **quando** o envio termina, **então** só o inválido é recusado, com a explicação específica.
3. **Dado** um envio que ultrapassaria a cota, **quando** ele é feito, **então** os arquivos que cabem na cota são aceitos na ordem de seleção, e os demais são recusados com a explicação da cota.

## Casos de borda

- SRT ou VTT com numeração ou tempos inválidos, codificação inválida ou sem texto.
- Legendas com linhas repetidas consecutivas (comuns em legendas automáticas): o texto repetido não gera trechos duplicados.
- DOCX corrompido, protegido por senha ou que é outro arquivo com a extensão trocada.
- DOCX compactado que se expande para um tamanho muito maior que o arquivo (bomba de descompactação): recusado.
- Envio interrompido no meio de vários arquivos: os completos seguem; os incompletos não são processados (CB-04).
- Arquivos com o mesmo nome no mesmo envio.

## Requisitos funcionais

- **RF-001:** O sistema deverá aceitar SRT, VTT e DOCX, além de PDF com texto, TXT e Markdown, com as mesmas validações de extensão, tipo real, tamanho e integridade do MVP (deriva de RN-02 da base).
- **RF-002:** Nas legendas, cada trecho deverá guardar o intervalo de tempo de origem, exibido na evidência no lugar da página (Q-002).
- **RF-003:** No DOCX, o sistema deverá extrair somente texto, sem executar macros, abrir objetos incorporados ou processar imagens, e não deverá registrar página.
- **RF-004:** O estudante deverá conseguir enviar até o limite de arquivos por envio (Q-001), com validação, estado e resultado independentes por arquivo.
- **RF-005:** Os limites de tamanho, de arquivos por envio e de cota deverão ser configuráveis por ambiente e iguais na interface e na API.
- **RF-006:** O sistema deverá recusar arquivos compactados cujo conteúdo expandido ultrapasse um limite configurável.

## Entidades principais

- **Fonte:** passa a admitir os tipos SRT, VTT e DOCX.
- **Trecho:** passa a admitir uma localização por intervalo de tempo, além da página.

## Critérios de sucesso

- **CS-001:** Com um conjunto de 10 arquivos fictícios por formato novo, todos chegam a `concluido`, e os intervalos de tempo dos trechos das legendas conferem com os arquivos.
- **CS-002:** Com um conjunto de arquivos adversariais (DOCX com macro, bomba de descompactação, tipo trocado, legenda malformada), nenhum é executado, nenhum derruba o processamento de outras fontes, e todos recebem explicação.

## Requisitos de qualidade

- **RQ-001:** O processamento de um arquivo malicioso não afeta o processamento das fontes de outros estudantes.
- **RQ-002:** O processamento cabe no limite de memória do serviço de processamento definido para a VPS ([arquitetura](../../arquitetura/README.md)).
- **RQ-003:** O envio múltiplo opera por teclado e anuncia o resultado de cada arquivo a tecnologias assistivas.

## Suposições e dependências

- **Dependência:** [002-materias-fontes](../002-materias-fontes/spec.md).
- **Dependência:** biblioteca de extração de DOCX e de legendas, escolhida no plano ([DTEC 009](../../research.md#decisão-dtec-009-extração-de-texto)).
- **Dependência:** a exibição do intervalo de tempo na evidência altera a tela de evidência de [004](../004-geracao-cartoes/spec.md) e as citações de [014](../014-chat-fontes/spec.md).

## Questões abertas

- **Q-001:** Quais os novos limites do final acadêmico ([RN-02](../../base-specs/spec.md#rn-02-admissão-de-fontes): "a definir pela equipe")? **Recomendação:** até 5 MB por arquivo, até 5 arquivos por envio e cota de 200 MB por estudante, compatíveis com o disco da VPS e com a camada gratuita do armazenamento ([DTEC 010](../../research.md#decisão-dtec-010-armazenamento-de-arquivos)). — **Responsável:** equipe — **Prazo:** 31/10/2026
- **Q-002:** A localização por intervalo de tempo nas legendas substitui a página na evidência e nas citações? **Recomendação:** sim, porque é a única localização conhecida numa legenda, e a regra "nunca inventar a localização" (RN-05) continua valendo. — **Responsável:** equipe — **Prazo:** 31/10/2026

## Decisões confirmadas

- **D-001:** SRT, VTT, DOCX e envio múltiplo entram no final acadêmico; OCR, XLSX e PPTX ficam na referência pós-acadêmica, pelo custo na VPS. — **Confirmada por:** equipe, no [backlog](../../produto/backlog.md#final-acadêmico) — **Data:** 12/10/2026

## Exigências do PO

Nenhuma exigência (EX-01 a EX-05) toca esta funcionalidade diretamente.

## Verificação da constituição

| Princípio | Como a spec atende |
|---|---|
| I Fontes exclusivas | Localização só quando conhecida (RF-002, RF-003) |
| II Proteção e isolamento | RF-003, RF-006, RQ-001 |
| III Verificação humana | Q-001 e Q-002 ficam com a equipe |
| IV Servidor autoritativo | Validação e estados no servidor |
| V Qualidade verificável | CS-001 e CS-002 com arquivos adversariais |
| VI Entrega incremental | US1 demonstrável sem a US2 |
| VII Rastreabilidade | IDs da base citados; sessão registrada |
