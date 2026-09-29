# Especificação da plataforma de estudos gamificada

Versão documental: 0.1
Estado: base para refinamento, decisões pendentes impedem considerar a especificação integralmente pronta para implementação 
Data: 25/09/2026

Referências: [SKILL.md](SKILL.md), [DESIGN.md](DESIGN.md), [Plan.md](Plan.md) e [Tasks.md](Tasks.md).

Este documento define o que construir e como aceitar o resultado, o arquivo Plan.md define a abordagem técnica, o Tasks.md decompõe a execução do sistema em fases, os arquivos SKILL.md e DESIGN.md são a base de princípios existente, denominada “constituição” no plano.
Não é necessário criar um sexto arquivo. A solicitação desta revisão autoriza atualizar SKILL.md e DESIGN.md para a política de IA com fontes exclusivas. Essa autorização não se estende a mudanças não relacionadas. Se uma decisão exigir alterá-los, deve ser apresentada a mudança e solicitada a autorização antes.

Requisitos derivados abaixo operacionalizam o resumo e os arquivos existentes, não representam aprovação de escolhas ainda abertas. 
IDs RF, RN, HU, CB, RQ, CS e QA permitem rastrear requisitos, regras, histórias, bordas, qualidade, sucesso e questões abertas. Mudanças futuras devem atualizar os três documentos mantendo seus IDs estáveis.

## 1. Problema e resultado esperado

Materiais de estudo extensos e dispersos dificultam organizar uma sequência de aprendizagem e acompanhar o que foi aprendido. O estudante precisa transformar seus materiais em atividades praticáveis e visualizar sua evolução.

Resultado esperado: um estudante envia um material, acompanha seu processamento, acessa uma trilha estruturada, responde questões com explicações, revisa flashcards associados e consulta desempenho, pontos, progresso e conquistas. A evolução deve ser confiável mesmo com falhas de rede e reenvios.

## 2. Escopo

### Incluído

- Materiais classificados como edital, apostila ou livro, com envio, listagem, consulta e gerenciamento dentro da política a definir.
- Processamento acompanhado por estados, geração de trilhas ordenadas, questões de escolha única e flashcards relacionados.
- Referências obrigatórias ao material, versão e trecho de origem; página quando disponível.
- Registro de tentativas, correção, explicação e histórico preservado.
- Pontos, progresso e conquistas calculados pelo servidor, conforme regras a confirmar.
- Interface web responsiva em português, validações locais e de servidor, isolamento entre usuários e API documentada.

### Fora do Escopo

- Ranking público, rede social, compartilhamento de materiais, equipes e disputas entre usuários.
- Pagamentos, assinaturas, comércio de conteúdo, aplicativos móveis nativos e modo offline.
- Questões discursivas ou de múltiplas respostas corretas, tutoria conversacional e provas oficiais certificadas.
- Repetição espaçada, sequências diárias e notificações: dependem de futura inclusão expressa.
- Painel administrativo, edição manual de conteúdo gerado e revisão humana obrigatória: não presumidos; avaliar QA-04 e QA-05.

A IA será usada para interpretar e gerar conteúdo exclusivamente com base nos materiais enviados. Modelo, provedor, OCR e forma de execução permanecem em aberto. Pesquisa na internet, bases externas e complementação de lacunas com conhecimento geral do modelo estão fora do escopo. Edital/apostila/livro são categorias de conteúdo, não formatos de arquivo permitidos.

## 3. Histórias de usuário e cenários de teste

Os cenários são critérios de aceitação, não resultados de testes já executados. Os cenários dependentes de regras em aberto usam os valores que forem aprovados, nunca números inventados.

| ID | História | Cenário de aceitação (Dado / Quando / Então) | Vínculo |
| --- | --- | --- | --- |
| HU-01 | Como estudante, quero acessar apenas meus dados | Dado dois usuários com materiais, quando um consulta ou altera recurso do outro, então o acesso é negado sem divulgar conteúdo | RF-01, RF-03; RN-01 |
| HU-02 | Quero enviar material para iniciar meus estudos | Dado arquivo permitido e campos válidos, quando envio, então recebo identificação e estado; dado arquivo acima do limite, então obtenho erro e não há processamento ativo | RF-02; RN-02 |
| HU-03 | Quero saber se o material está pronto | Dado material aceito, quando o processamento termina com conteúdo válido, então vejo concluído e acesso a trilha; se o extrator falha, vejo falhou e ação de recuperação permitida | RF-04; RN-03 |
| HU-04 | Quero estudar em uma sequência organizada | Dada trilha concluída, quando a abro, então vejo etapas ordenadas e referências; conteúdo inválido não aparece como disponível | RF-05; RN-04 |
| HU-05 | Quero responder e entender meus erros | Dada questão disponível, quando abro, não recebo gabarito; quando confirmo alternativa incorreta, então recebo resultado, correta e explicação e uma tentativa é registrada | RF-06, RF-07; RN-05 |
| HU-06 | Quero que uma falha de rede não distorça meus pontos | Dada tentativa já aceita, quando reenviada com mesma identidade e conteúdo, então retorno é consistente e total de pontos não aumenta novamente; conteúdo divergente gera conflito | RF-07, RF-09; RN-06 |
| HU-07 | Quero revisar o conteúdo com flashcards | Dado flashcard da etapa, quando aciono revelar pelo teclado, então acesso verso e explicação disponível; revisão isolada não concede pontos sem regra aprovada | RF-08; QA-10 |
| HU-08 | Quero compreender minha evolução | Dados resultados conhecidos, quando consulto Evolução, então tentativas e acertos conferem com o histórico e progresso segue a fórmula aprovada; sem atividade vejo estado vazio | RF-10, RF-12; RN-07 |
| HU-09 | Quero receber conquistas quando cumprir objetivos | Dado critério aprovado, quando evento elegível o completa, então uma concessão é registrada; repetição ou concorrência não concede novamente | RF-11; RN-08 |
| HU-10 | Quero gerenciar materiais sem perder clareza sobre meu histórico | Dado material com trilha e tentativas, quando solicito exclusão, então o impacto é explicado e a operação segue a política aprovada preservando as garantias históricas | RF-03; RN-09 |
| HU-11 | Quero continuar de onde parei | Dado estudo anterior, quando retorno ao Início, então a ação continuar abre o destino definido em QA-06; na ausência de estudo, vejo orientação inicial | RF-12; QA-06 |
| HU-13 | Quero saber quais assuntos ainda precisam de material | Dado edital que lista porcentagem e apostila que cobre apenas frações, quando processo os materiais, então o sistema sinaliza porcentagem como aguardando apoio e não gera questões sobre ela com conhecimento externo | RF-14; RN-11/12 |
| HU-14 | Quero conferir a origem das atividades | Dada questão ou flashcard gerado, quando consulto sua evidência no momento permitido, então vejo trecho real de versão do meu material; referência inexistente ou que não sustenta a resposta impede publicação | RF-15; RN-11/13 |
| HU-12 | Como integrador, quero contratos confiáveis | Dada API implementada, quando comparo exemplos e esquemas OpenAPI com respostas reais de sucesso e erro, então formatos, limites e autenticação coincidem | RF-14 | Identificar assuntos sem suporte suficiente, sinalizar “aguardando material de apoio” e permitir solicitar/envio de complemento conforme vínculo aprovado | RN-11/12; QA-04/06 |
| RF-15 | Rastrear cada questão, explicação e flashcard até trechos de versões dos materiais do próprio usuário e verificar sustentação antes de publicar | RN-11/13; QA-04 |
| RF-13 |

## 4. Casos de borda

| ID | Situação | Comportamento exigido ou decisão necessária |
| --- | --- | --- |
| CB-01 | Arquivo vazio, corrompido, protegido por senha ou imagem sem texto | Não marcar como concluído sem conteúdo válido; explicar impossibilidade. Suporte a OCR/senha depende de QA-03/04 |
| CB-02 | Tamanho ou campo exatamente no limite e um acima | Aceitar fronteira válida e rejeitar excedente igualmente na interface e servidor |
| CB-03 | Upload interrompido ou armazenamento falha | Não iniciar processamento de arquivo incompleto; limpar resíduos segundo política operacional |
| CB-04 | Trabalhador para após salvar dados e antes de confirmar tarefa | Recuperação não publica duplicatas; estado eventualmente reflete o resultado persistido |
| CB-05 | Geração vazia, alternativas repetidas ou duas corretas | Reprovar validação; não publicar questão inválida |
| CB-06 | Mesmo arquivo enviado novamente ou duas execuções simultâneas | Distinguir novo envio legítimo de repetição técnica; deduplicação por conteúdo é decisão QA-04 |
| CB-07 | Duplo clique, duas abas ou timeout após aceitar resposta | Mesma tentativa tem efeito único; novas tentativas seguem política de elegibilidade |
| CB-08 | Questão alterada/desativada entre leitura e resposta | Detectar versão; comportamento de aceitar versão lida ou rejeitar conflito deve ser definido em QA-07; nunca corrigir silenciosamente com outro gabarito |
| CB-09 | Trilha sem questões ou com total alterado | Não dividir por zero nem exibir conclusão indevida; definir efeito em QA-06 |
| CB-10 | Virada de dia, mudança de fuso e períodos sem tentativas | Agregações usam regra aprovada e ausência de dados não vira acerto ou progresso fictício |
| CB-11 | Tentativa de revelar gabarito por payload, flashcard ou outro endpoint | Contrato pré-resposta não contém segredo; decidir acesso intencional ao flashcard antes da resposta em QA-10 |
| CB-12 | Exclusão em paralelo com processamento ou resposta | Aplicar política e consistência definidas, sem órfãos acessíveis ou histórico alterado |
| CB-13 | Textos muito longos, caracteres Unicode e tela de 320 px | Preservar conteúdo relevante, aplicar limites de entrada e manter leitura sem rolagem horizontal da página |
| CB-15 | Edital apenas lista um assunto, trecho é insuficiente ou materiais se contradizem | Não preencher lacuna por conhecimento do modelo; sinalizar falta de apoio ou conflito e manter atividades afetadas indisponíveis |
| CB-16 | IA fornece referência real, porém sem suporte à resposta, ou inventa página | Reprovar atividade; verificar existência e sustentação, sem confiar apenas no identificador retornado |
| CB-14 | Provedor indisponível ou material contém instruções maliciosas | Se houver provedor/IA, falhar de forma controlada e tratar material como dados, não instruções do sistema |

## 5. Requisitos funcionais

Todos os RF abaixo pertencem ao escopo base. Quando houver QA associada, a funcionalidade só pode ser encerrada após resolver a decisão correspondente.

| ID | Requisito e resultado observável | Regras/pendências |
| --- | --- | --- |
| RF-01 | Identificar o estudante e restringir operações e consultas aos seus recursos | RN-01; QA-02 define entrada, conta e sessão |
| RF-02 | Enviar material com título, categoria e arquivo; devolver identificação e estado de recebimento | RN-02; QA-03 |
| RF-03 | Listar e consultar materiais e executar as operações de gerenciamento aprovadas; informar impacto antes de exclusão | RN-01, RN-09; QA-03, QA-05 |
| RF-04 | Processar material e expor pendente, processando, concluído ou falhou; oferecer reprocessamento controlado | RN-03; QA-04 |
| RF-05 | Disponibilizar trilhas com etapas ordenadas, assuntos, referências e situação de estudo | RN-04, RN-07; QA-04, QA-06 |
| RF-06 | Exibir questão com alternativas sem gabarito e receber uma alternativa válida | RN-04, RN-05; QA-07 |
| RF-07 | Registrar tentativa e devolver resultado, resposta correta e explicação; preservar o resultado histórico | RN-05, RN-06; QA-07 |
| RF-08 | Exibir flashcard relacionado ao conteúdo e permitir revelar frente/verso de forma acessível | RN-04; QA-10 |
| RF-09 | Calcular e exibir pontos com origem rastreável, sem duplicação por reenvio | RN-06; QA-07 |
| RF-10 | Apresentar progresso e situação de conclusão por etapa e trilha | RN-07; QA-06 |
| RF-11 | Conceder e exibir conquistas com critérios e data, sem concessão duplicada | RN-08; QA-08 |
| RF-12 | Exibir tentativas, acertos e evolução com definição clara e período aplicável; oferecer continuação do estudo | RN-07, RN-10; QA-06, QA-09 |
| RF-14 | Identificar assuntos sem suporte suficiente, sinalizar “aguardando material de apoio” e permitir solicitar/envio de complemento conforme vínculo aprovado | RN-11/12; QA-04/06 |
| RF-15 | Rastrear cada questão, explicação e flashcard até trechos de versões dos materiais do próprio usuário e verificar sustentação antes de publicar | RN-11/13; QA-04 |
| RF-13 | Disponibilizar especificação OpenAPI e Swagger UI coerentes com operações, validações e erros reais | SKILL.md; QA-01, QA-11 |

## 6. Critérios de sucesso

- **CS-01:** HU-01 a HU-14 aprovadas com dados controlados, cobrindo RF-01 a RF-15; pendências aplicáveis resolvidas.
- **CS-02:** cenários de repetição, concorrência e recuperação não duplicam pontos, concessões ou conteúdo da mesma execução.
- **CS-03:** nenhuma consulta/alteração cruzada de usuário testada tem sucesso e nenhum contrato pré-resposta revela gabarito.
- **CS-04:** histórico reproduz a correção original após mudança de conteúdo e evolução coincide com os dados e fórmulas aprovados.
- **CS-05:** fluxo principal funciona por teclado e em tela de 320 px e desktop, com erros, vazios e carregamento compreensíveis.
- **CS-06:** build, testes de regras, integração e contrato passam; OpenAPI corresponde à implementação.
- **CS-07:** desempenho, qualidade do conteúdo e recuperação cumprem metas QA-04 e QA-11 aprovadas. Não é possível declarar esse critério atendido enquanto as metas estiverem abertas.

## 7. Suposições e dependências

- SUP-01: o usuário principal é um estudante individual; papéis adicionais não estão definidos.
- SUP-02: interface web requer conexão com o servidor; não há sincronização offline no escopo.
- SUP-03: materiais de teste representativos estarão disponíveis para avaliar extração, estrutura e qualidade das questões.
- SUP-04: o ambiente de execução oferecerá persistência e armazenamento adequados; sua escolha permanece aberta.
- DEP-01: mecanismo de identificação depende de QA-02; não construir cadastro ou recuperação de senha por suposição.
- DEP-02: geração depende de QA-04 e formatos de QA-03; credenciais e custos só existem se o mecanismo escolhido os exigir.
- DEP-03: indicadores dependem das fórmulas de QA-06/07/08/09/10.
- DEP-04: aceite operacional depende de volumes, infraestrutura, backups e metas de QA-11.

## 8. Decisões confirmadas e referência existente

| ID | Decisão/base | Origem e situação |
| --- | --- | --- |
| DC-01 | Plataforma de estudos com materiais, trilhas, questões, flashcards e gamificação | Resumo do usuário |
| DC-02 | Camadas MVC obrigatórias | Solicitação do usuário e SKILL.md |
| DC-03 | Código limpo; identificadores próprios em português, curtos e claros; poucos comentários | Solicitação do usuário e SKILL.md |
| DC-04 | Normalização, datas, validações, exceções e Swagger/OpenAPI | Solicitação do usuário; padrões detalhados em SKILL.md |
| DC-05 | Interface limpa, componentes consistentes, validações e limites | Solicitação do usuário e DESIGN.md |
| DC-06 | Preferência por React JSX | Preferência do usuário; JavaScript consta em DESIGN.md; versões não definidas |
| DC-07 | Três documentos novos, sem alterar a estrutura pedida nem os originais sem autorização | Solicitação atual |
| DC-09 | IA com fontes restritas aos materiais enviados; lacunas exigem material complementar; origem verificável por trecho | Decisão do usuário nesta revisão |
| DC-08 | Escolha única, idempotência, isolamento e preservação de histórico | Base técnica já registrada em SKILL.md; detalhada nesta especificação |

## 9. Regras de negócio e fluxo

### Regras

- **RN-01 — Propriedade:** toda cadeia de material, trilha, questão, tentativa e evolução pertence a um estudante. Conhecer um identificador não concede acesso. Não aceitar vínculos entre recursos de proprietários diferentes.
- **RN-02 — Admissão:** somente arquivos e campos conformes aos limites aprovados podem iniciar processamento. Nome/extensão informados pelo cliente não comprovam formato. Arquivo recusado não pode gerar conteúdo de estudo ativo.
- **RN-03 — Processamento:** pendente → processando → concluído ou falhou. Reprocessamento cria execução rastreável; não duplica conteúdo ativo em razão de repetição técnica. “Concluído” significa que o conjunto previsto para aquela execução foi persistido e validado. Política de resultados parciais e nova versão depende de QA-04.
- **RN-04 — Conteúdo válido:** questão de escolha única exige alternativas distintas, exatamente uma correta e explicação. Trilha exige ordenação e referência de origem; flashcard exige frente, verso e vínculo. Conteúdo inválido não fica disponível para estudo. Página/trecho só é apresentado se efetivamente conhecido.
- **RN-05 — Tentativa:** somente aceitar alternativa pertencente à versão disponível da questão e ao usuário autorizado. Corrigir no servidor. O contrato pré-resposta não contém gabarito nem explicação que o revele. Guardar versão ou retrato suficiente para reproduzir a correção histórica.
- **RN-06 — Consistência:** o mesmo identificador de tentativa com o mesmo conteúdo produz o mesmo resultado, sem nova pontuação. Reutilizar identificador com conteúdo diferente deve produzir conflito. Tentativa e seus efeitos devem ter resultado consistente mesmo em concorrência. Repetições legítimas usam novos identificadores, mas sua elegibilidade para pontos depende de QA-07.
- **RN-07 — Progresso:** percentual de acertos e percentual de conclusão são métricas distintas. Fórmula, unidade de conclusão, trilha vazia, retentativas e alteração do total dependem de QA-06. Não concluir trilha apenas porque foi aberta.
- **RN-08 — Conquistas:** avaliar critérios com dados persistidos no servidor. Uma conquista não pode ser concedida duas vezes ao mesmo usuário no mesmo contexto de concessão. Catálogo e contexto dependem de QA-08.
- **RN-09 — Ciclo de vida:** excluir ou reprocessar material não pode silenciosamente invalidar tentativas já registradas. Comportamento de exclusão, retenção, arquivamento e conteúdo derivado depende de QA-05.
- **RN-10 — Tempo e texto:** manter instantes em UTC, usar fuso configurado nas agregações por dia e preservar texto de estudo. Aplicar normalização e erros conforme SKILL.md; não modificar senhas por normalização.

- **RN-11 — Fontes exclusivas:** usar apenas materiais enviados pelo usuário e autorizados para aquela trilha. Não pesquisar na internet nem usar bases externas ou conhecimento geral do modelo para suprir fatos ausentes. Referência obrigatória identifica material, versão e trecho; página somente quando disponível. Reformulações e cálculos derivados são permitidos se verificáveis a partir da fonte. Alternativas incorretas podem representar erros sobre o conceito, mas sua incorreção deve ser justificável pelo conteúdo. Não é necessário haver cópia literal da questão no material.
- **RN-12 — Cobertura e lacunas:** edital pode definir os assuntos da trilha, mas a mera lista de tópicos não é suporte pedagógico suficiente. Registrar a situação “aguardando material de apoio” quando faltar conteúdo; não forçar quantidade de questões nem marcar o assunto como concluído. Suficiência é distinta do estado técnico do processamento: uma execução concluída pode produzir um mapa de lacunas. Efeito no denominador do progresso e vínculo de complementos permanecem em QA-06/04.
- **RN-13 — Validação da geração:** gerar questão e flashcard a partir dos mesmos trechos originais; validar estrutura e sustentação semântica antes da publicação. Referência existente não prova que o trecho sustenta o gabarito. Avaliar ambiguidade, explicação e consistência com a fonte; conteúdo contraditório ou insuficiente fica indisponível até resolução. Outra chamada de IA não é garantia de correção. Guardar modelo e versão das instruções; corrigir tentativas com gabarito persistido, sem geração a cada resposta.

### Fluxo principal

1. Estudante é identificado e acessa Materiais.
2. Seleciona arquivo e informa metadados; interface verifica limites conhecidos e servidor valida novamente.
3. Sistema registra material aceito e execução; a interface acompanha estado real.
4. Processamento extrai conteúdo preservando origem, identifica assuntos e verifica cobertura. A IA gera atividades apenas para assuntos sustentados pelos materiais; os demais ficam aguardando apoio. Validar estrutura e sustentação dos resultados antes de publicar.
5. Conteúdo concluído torna-se disponível; falha apresenta motivo útil e recuperação permitida.
6. Estudante abre uma etapa, seleciona alternativa e confirma; servidor registra tentativa e efeitos.
7. Interface apresenta correção e explicação; estudante decide avançar ou revisar flashcard.
8. Evolução apresenta dados persistidos, critérios e progresso calculado.

Fluxos alternativos: arquivo inválido retorna correção no formulário; processamento falho permite recuperação conforme política; sessão inválida exige restabelecer acesso; timeout de resposta permite consultar ou repetir a mesma tentativa sem duplicá-la. Reprocessamento e exclusão seguem QA-04 e QA-05 antes de serem liberados.

## 10. Entidades principais

Modelo conceitual; tipos físicos, índices e tabelas pertencem ao plano após escolher persistência.

| Entidade | Dados e relações essenciais | Integridade |
| --- | --- | --- |
| Usuário | Identidade e configuração de fuso quando adotada | Identidade emitida/verificada pelo mecanismo aprovado |
| Material | Proprietário, título, categoria, referência do arquivo, estado | Sempre associado ao proprietário |
| Processamento | Material, identidade da execução, estado, início/fim, erro, versão resultante, modelo e versão das instruções | Separa repetição técnica de nova geração |
| Trilha | Proprietário, título, origem e versão | Cardinalidade material/trilha depende de QA-04 |
| Etapa | Trilha, assunto, ordem, situação de cobertura e motivo de insuficiência/conflito | Separar disponibilidade para estudar de conclusão pelo estudante |
| Trecho de origem | Material/versão, conteúdo extraído e localização disponível | Evidência imutável ou versionada, vinculada a questões, explicações e flashcards do mesmo usuário |
| Questão/versão | Etapa, enunciado, explicação, origem e disponibilidade | Gabarito da versão preservado |
| Alternativa | Questão/versão, texto e indicação de correta | Pertence a uma versão; uma correta por questão |
| Flashcard | Frente, verso, vínculo e origem | Cardinalidade com questão/conceito em QA-10 |
| Tentativa | Usuário, identidade idempotente, versão, escolha, resultado e instante | Identidade única no escopo aprovado; escolha da versão correta |
| Registro de pontos | Usuário, origem, valor e versão da regra | Mesma origem elegível não gera crédito repetido |
| Progresso | Usuário, trilha/versão e dados de conclusão | Pode ser derivado ou materializado; fórmula única |
| Conquista e concessão | Definição do critério; usuário, contexto e instante de obtenção | Concessão única por usuário, conquista e contexto |

## 11. Requisitos de qualidade

| ID | Requisito | Evidência esperada |
| --- | --- | --- |
| RQ-01 | Segurança e isolamento em API, tarefas e acesso ao arquivo; não registrar segredos | Testes negativos por usuário e inspeção de logs/contratos |
| RQ-02 | Consistência de tentativa, pontos, progresso e concessão sob falha e concorrência | Testes de integração com interrupção e reenvio |
| RQ-03 | Acessibilidade e responsividade conforme DESIGN.md, incluindo contraste e teclado | Verificações automáticas complementadas por revisão manual |
| RQ-04 | Desempenho e capacidade com metas mensuráveis a aprovar | Teste de carga com volume, percentis e ambiente registrados em QA-11 |
| RQ-05 | Manutenibilidade: MVC, nomes claros em português e comentários necessários | Revisão de dependências, organização e código |
| RQ-06 | Observabilidade sem exposição de dados; erros correlacionáveis | Traçar uma falha de interface/API até a execução correspondente |
| RQ-07 | Qualidade e sustentação exclusiva nos materiais enviados | HU-13/14 e CB-15/16; verificar trechos, ambiguidades e lacunas com corpus revisado. Validar formato ou consultar outra IA não prova correção pedagógica; patamar de qualidade em QA-04 |
| RQ-08 | Recuperação e retenção definidas | Restauração testada e política QA-05/11 documentada |

## 12. Questões em aberto

Registrar a resposta e sua data nesta seção quando decidida. O responsável pelas decisões de produto é o solicitante; escolhas técnicas podem ser propostas por quem implementar, sem apresentá-las como já aprovadas. Pendências bloqueiam somente as tarefas dependentes.

| ID | Questões a resolver | Por que importa / bloqueia |
| --- | --- | --- |
| QA-01 | Linguagem e versão do backend, framework, banco, persistência, versões do frontend, build, biblioteca visual e ferramentas de teste? | Inicialização executável, migrações e dependências |
| QA-02 | Como usuário entra? Há cadastro, provedor externo, recuperação de acesso, expiração e outros perfis? | Identidade, sessão, telas de acesso e isolamento ponta a ponta |
| QA-03 | Quais formatos, bytes por arquivo, arquivos por lote, tamanho de campos, paginação e cotas por usuário? | Contratos e testes de limite; esclarecer suporte a arquivos digitalizados |
| QA-04 | Qual modelo/provedor de IA será usado e como será executado? Haverá OCR? Fontes exclusivas já estão decididas; falta definir como associar material complementar aos assuntos pendentes. Quantos materiais por trilha, questões por etapa e alternativas por questão? A validação estrutural e de sustentação antes da publicação é obrigatória; haverá também revisão humana de cada item ou por amostra? Como tratar resultados parciais, reprocessamento e arquivo repetido? Qual conjunto e patamar de qualidade semântica? | Processamento, publicação, modelo e avaliação de conteúdo |
| QA-05 | Quais metadados podem ser editados? Exclusão física, arquivamento ou bloqueio? O que acontece com derivados, histórico e arquivos? Qual retenção? | Gerenciamento, concorrência e recuperação |
| QA-06 | O que conclui etapa/trilha: responder ou acertar? Qual fórmula, denominador e política para alterações/trilhas vazias e assuntos aguardando apoio? Qual destino de “Continuar estudo”? | Progresso e navegação |
| QA-07 | Quantos pontos por evento, há penalidade, repetição pontua, existe limite? Como responder versão desativada? Qual escopo e prazo de idempotência? | Correção, histórico, concorrência e pontos |
| QA-08 | Quais conquistas, critérios, contexto de unicidade e efeito de mudança de regra? | Concessões e sua apresentação |
| QA-09 | Qual fuso e política de alteração? Quais períodos/filtros e definição de acurácia: todas as tentativas ou subconjunto? | Datas, indicadores e agregações |
| QA-10 | Relação questão/flashcard é um para um ou outra? Flashcard pode ser visto antes da resposta? Revisão conta para progresso ou pontos? | Fluxo de estudo e possível exposição intencional da resposta |
| QA-11 | Onde executar? Quantos usuários simultâneos, materiais e armazenamento? Qual p95 de API, prazo de processamento por faixa de arquivo, disponibilidade, RPO/RTO e orçamento? Quem opera e recebe alertas? | Capacidade, arquitetura operacional, carga e aceite |

Não há necessidade identificada de mudar a estrutura solicitada. Após responder as pendências, revisar a consistência entre Spec → Plan → Tasks. Qualquer sincronização necessária com SKILL.md ou DESIGN.md requer autorização prévia do solicitante.
