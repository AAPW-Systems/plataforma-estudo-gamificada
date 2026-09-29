# Especificação da consulta de prazos acadêmicos

**Identificador:** 001-consulta-prazos  
**Criada em:** 24 de setembro de 2026  
**Status:** Aprovada para planejamento  
**Origem:** oficina de produto e revisão com o PO

## Problema e resultado esperado

Estudantes dos primeiros períodos precisam confirmar prazos, mas a informação está distribuída em calendários, regulamentos e comunicados. Eles devem conseguir formular uma pergunta em português, receber uma orientação apoiada por uma fonte aprovada e abrir a localização indicada para conferência.

A funcionalidade reduz o tempo de procura. Ela não substitui o documento oficial nem decide exceções individuais.

## Escopo

### Incluído

- perguntas em português sobre datas e prazos presentes no corpus aprovado;
- resposta com documento, seção e versão da fonte;
- declaração explícita quando não houver evidência suficiente;
- pedido de esclarecimento quando faltar o assunto do prazo;
- tratamento de indisponibilidade do serviço de consulta.

### Fora do escopo

- alterar matrícula, notas ou dados acadêmicos;
- decidir exceções para um estudante;
- pesquisar fontes externas ao corpus aprovado;
- receber documentos pessoais;
- enviar mensagens ou abrir protocolos.

## Cenários de usuário e testes

### História de usuário 1 Consultar um prazo com fonte P1

Como estudante, quero perguntar sobre um prazo acadêmico para localizar a data aplicável e conferir a fonte oficial.

**Motivo da prioridade:** esta jornada entrega o valor principal da funcionalidade.  
**Teste independente:** carregar um calendário fictício, perguntar pelo período de matrícula e confirmar que a resposta apresenta a data, o documento, a seção e a versão.

**Cenários de aceitação**

1. **Dado** que o corpus aprovado contém o período de matrícula, **quando** o estudante pergunta pela matrícula do segundo semestre, **então** o sistema informa o período e identifica documento, seção e versão.
2. **Dado** que uma fonte possui condição associada ao prazo, **quando** a resposta apresenta a data, **então** a condição aparece no mesmo resultado.

### História de usuário 2 Reconhecer ausência de evidência P2

Como estudante, quero saber quando a coleção não sustenta uma resposta para não agir com base em uma data inventada.

**Motivo da prioridade:** uma resposta plausível e incorreta pode causar a perda de um prazo.  
**Teste independente:** perguntar pela taxa de segunda via do diploma, assunto ausente do corpus, e confirmar que nenhuma taxa ou data é apresentada como fato.

**Cenários de aceitação**

1. **Dado** que nenhuma fonte aprovada sustenta a pergunta, **quando** a consulta é processada, **então** o sistema declara insuficiência de evidência e indica o canal acadêmico.
2. **Dado** que apenas um trecho com baixa relevância foi encontrado, **quando** o resultado não atinge o limiar configurado, **então** o sistema trata o caso como ausência de evidência.

### História de usuário 3 Esclarecer pergunta ambígua P3

Como estudante, quero informar o assunto que falta para receber uma resposta relacionada à minha dúvida.

**Motivo da prioridade:** perguntas como “qual é o prazo?” aparecem com frequência e não permitem escolher uma fonte com segurança.  
**Teste independente:** enviar uma pergunta sem assunto e confirmar que o sistema solicita somente a informação necessária.

**Cenários de aceitação**

1. **Dado** que a pergunta contém apenas “qual é o prazo?”, **quando** a consulta é recebida, **então** o sistema pergunta de qual procedimento ou atividade o estudante trata.
2. **Dado** que o estudante complementa a pergunta, **quando** a nova consulta é enviada, **então** o sistema a avalia como uma consulta independente.

## Casos de borda

- Pergunta vazia ou composta somente por espaços.
- Pergunta com mais de 500 caracteres.
- Duas fontes aprovadas apresentam datas diferentes para o mesmo evento.
- O trecho relevante foi recuperado, mas não possui versão ou seção.
- O serviço de consulta está indisponível.
- A pergunta inclui senha, CPF ou outro dado pessoal desnecessário.

## Requisitos funcionais

- **RF-001:** O sistema deverá aceitar uma pergunta em português com 3 a 500 caracteres depois da remoção de espaços nas extremidades.
- **RF-002:** O sistema deverá consultar somente documentos marcados como aprovados e ativos.
- **RF-003:** Toda resposta factual deverá apresentar título do documento, seção e versão da fonte usada.
- **RF-004:** Quando não houver evidência suficiente, o sistema deverá declarar a limitação e não apresentar data, taxa ou regra como fato.
- **RF-005:** Quando a pergunta não identificar o assunto do prazo, o sistema deverá solicitar o dado que falta antes de consultar o corpus.
- **RF-006:** Quando fontes ativas divergirem, o sistema deverá mostrar o conflito e encaminhar o estudante ao canal acadêmico, sem escolher uma data.
- **RF-007:** O sistema deverá rejeitar entrada vazia, entrada acima do limite e conteúdo que contenha padrão evidente de dado pessoal definido pela política do projeto.
- **RF-008:** Quando o serviço estiver indisponível, o sistema deverá informar a falha sem reutilizar uma resposta anterior como se fosse atual.
- **RF-009:** O sistema deverá registrar identificador da consulta, fontes recuperadas, estado final e duração, sem registrar dados pessoais detectados.

## Entidades principais

- **Documento de fonte:** conteúdo autorizado, título, versão, estado e data de vigência.
- **Trecho:** parte de um documento com seção e referência estável.
- **Consulta:** pergunta normalizada, identificador, instante e estado final.
- **Evidência:** trecho recuperado, pontuação e metadados da fonte.
- **Resposta:** texto, estado, evidências apresentadas e orientação de continuidade.

## Critérios de sucesso

- **CS-001:** Nos 10 casos respondíveis revisados pelo PO, todos apresentam a fonte esperada e nenhuma afirmação factual sem apoio no trecho citado.
- **CS-002:** Nos cinco casos sem resposta no corpus, nenhum apresenta data, taxa ou regra como fato.
- **CS-003:** Nos três casos ambíguos, o sistema solicita o assunto ausente sem sugerir uma resposta.
- **CS-004:** Em teste guiado, quatro de cinco estudantes concluem uma consulta e localizam a fonte em até dois minutos, sem ajuda do aplicador.

## Requisitos de qualidade

- **RQ-001:** A resposta deve ficar disponível em até três segundos no percentil 95 durante teste local com 20 requisições sequenciais.
- **RQ-002:** A jornada deve funcionar por teclado e expor rótulos acessíveis nos campos e estados da resposta.
- **RQ-003:** Segredos, conteúdo completo da pergunta e dados pessoais detectados não devem aparecer nos logs.
- **RQ-004:** A versão do corpus deve ser registrada em toda consulta concluída.

## Suposições e dependências

- O PO aprovará os documentos e resolverá conflitos de autoridade entre fontes.
- O corpus inicial terá até 20 documentos curtos em português.
- O canal acadêmico e seu endereço serão fornecidos antes da implementação da US2.
- A autenticação do portal não faz parte desta funcionalidade.

## Questões abertas

Nenhuma questão impede o planejamento desta versão. O canal acadêmico será configurável porque seu endereço ainda não foi definido.

## Decisões confirmadas

- **D-001:** A fonte deverá aparecer junto da resposta, e não apenas em uma tela separada — **Confirmada pelo PO em:** 23 de setembro de 2026.
- **D-002:** Conflito entre fontes será exibido e encaminhado, sem escolha automática — **Confirmada pelo PO em:** 23 de setembro de 2026.
