# Pesquisa e decisões técnicas

**Funcionalidade:** 001-conta-acesso (conta, sessão, isolamento e preferências)  
**Data:** 12/10/2026 ([registro](../../prompts/2026-10-12-001-conta-acesso-plano.md))  
**Status:** DTEC 019 a 023 aprovadas em 12/10/2026 por Artur Lins, com o plano

Este arquivo registra apenas as dúvidas técnicas **novas** da spec 001. As decisões já tomadas não são reabertas: autenticação própria com Argon2id e sessão opaca (DTEC 003), banco (DTEC 005), fila (DTEC 006), armazenamento (DTEC 010), testes (DTEC 001 e 014) e as decisões transversais tomadas neste mesmo planejamento (emenda da DTEC 002 e DTEC 015 a 018), todas em [`../../research.md`](../../research.md). A numeração das DTEC é única no projeto.

| Decisão | Título |
|---|---|
| [DTEC 019](#decisão-dtec-019-garantia-do-isolamento-entre-estudantes) | Garantia do isolamento entre estudantes |
| [DTEC 020](#decisão-dtec-020-registro-e-limite-das-tentativas-de-acesso) | Registro e limite das tentativas de acesso |
| [DTEC 021](#decisão-dtec-021-exclusão-da-conta-e-chaves-de-armazenamento-por-usuário) | Exclusão da conta e chaves de armazenamento por usuário |
| [DTEC 022](#decisão-dtec-022-lista-local-de-senhas-comuns) | Lista local de senhas comuns |
| [DTEC 023](#decisão-dtec-023-detalhes-da-sessão-do-csrf-e-do-hash-de-senha) | Detalhes da sessão, do CSRF e do hash de senha |

## Decisão DTEC 019 Garantia do isolamento entre estudantes

**Questão:** como garantir que nenhuma operação, desta e das próximas specs, devolva, altere ou confirme a existência de um recurso de outro estudante (RF-007, US2, CS-002)?  
**Critérios:** cobertura de 100% das operações expostas (CS-002); resistência ao esquecimento quando uma rota nova for criada; custo de implementação até 15/10/2026; impacto no worker.  
**Alternativas consideradas:**

1. **Filtro obrigatório no repositório + FKs compostas + teste que percorre todas as rotas:** todo método de repositório que lê ou altera recurso de estudante recebe o `usuario_id` como parâmetro obrigatório e o aplica na própria consulta. As FKs compostas do [esquema](../../arquitetura/esquema-inicial.dbml) (`(materia_id, usuario_id)`) impedem vincular recurso a matéria de outro dono. Um teste de segurança lista as rotas da aplicação e falha se alguma rota com identificador no caminho não tiver caso no teste de duas contas.
2. **Alternativa 1 + Row-Level Security (RLS) no PostgreSQL:** segunda camada no banco, com políticas por tabela e `SET LOCAL` do usuário em cada transação. Exige cuidado com o worker, com as migrações e com o papel do banco usado pela aplicação, e acrescenta tempo de implementação e diagnóstico.
3. **Verificação no router (Controller):** espalha a regra e depende de cada rota lembrar de verificar.

**Decisão:** alternativa 1. A RLS é registrada como evolução na [referência pós-acadêmica](../../arquitetura/referencia-pos-academica.md).  
**Justificativa:** cumpre o CS-002 com uma regra num único lugar (o repositório, DTEC 018) e uma proteção automática contra esquecimento (o teste que percorre as rotas), dentro do prazo do MVP. A RLS protege contra erros que o teste automático já detecta, com custo desproporcional agora.  
**Consequências:**

- Um recurso de outro estudante é buscado com `WHERE public_id = :id AND usuario_id = :dono` e, se não houver linha, o serviço lança `RecursoNaoEncontrado` (404, `recurso_nao_encontrado`), com corpo idêntico ao de um identificador inexistente.
- Rotas recebem só `public_id` (UUID); o `id` interno nunca sai da API (convenção do esquema).
- O teste `tests/security/test_isolamento_rotas.py` exige que cada rota com parâmetro de caminho esteja numa tabela de casos; as specs 002 a 007 acrescentam suas rotas a essa tabela.
- Na 001, as rotas de estudante operam só sobre a própria conta (sem identificador no caminho). O teste de duas contas cobre o perfil, a senha, a exclusão e a saída, e a infraestrutura do teste fica pronta para as próximas specs.

**Condição para revisão:** um vazamento detectado fora dos testes, ou a passagem para a referência pós-acadêmica (RLS como segunda camada).

## Decisão DTEC 020 Registro e limite das tentativas de acesso

**Questão:** onde e como contar as falhas de entrada, as tentativas de cadastro e as falhas de senha atual para aplicar os limites da RQ-003, sem revelar se um e-mail tem conta (CS-003)?  
**Critérios:** persistência entre reinícios; funcionamento com mais de um processo; consistência sob concorrência; não enumeração de contas; nenhum serviço novo na VPS.  
**Alternativas consideradas:**

1. **Tabela `tentativas_acesso` no PostgreSQL:** uma linha por evento (falha de entrada, cadastro, falha de senha atual), com a chave da conta e o endereço de rede; contagem por janela de tempo com índice; serialização por chave com *advisory lock* da transação; limpeza periódica.
2. **Contadores em memória do processo:** zeram a cada reinício e não funcionam com mais de um processo da API.
3. **Redis:** contadores com expiração nativa, mas é um serviço residente a mais, o que a constituição e a DTEC 006 evitam.

**Decisão:** alternativa 1.  
**Justificativa:** atende a todos os critérios com o banco que já existe; o volume do projeto (dezenas de usuários) é irrelevante para o PostgreSQL.  
**Consequências:**

- **Chave da conta:** HMAC-SHA-256 do e-mail normalizado com o segredo da aplicação, e não o id do usuário. Assim o limite vale igualmente para e-mails com e sem conta, e a sexta tentativa não revela a existência da conta (CS-003). O e-mail não fica legível na tabela.
- **Regras (valores da RQ-003, configuráveis por ambiente):** 5 falhas de entrada (ou de senha atual) por chave da conta em 15 minutos bloqueiam a conta por 15 minutos; 20 falhas por endereço de rede em 15 minutos bloqueiam o endereço por 15 minutos; 10 cadastros por endereço de rede por hora. O bloqueio responde `429` com `Retry-After` e o código `muitas_tentativas`, inclusive com a senha correta.
- **Entrada bem-sucedida:** apaga as falhas daquela chave de conta, mas não as do endereço de rede.
- **Concorrência:** a verificação e o registro acontecem na mesma transação, sob `pg_advisory_xact_lock` da chave, para que rajadas paralelas não ultrapassem o limite.
- **Endereço de rede:** vem do cabeçalho `X-Forwarded-For` apenas quando a requisição chega de um proxy configurado como confiável (`PROXIES_CONFIAVEIS`: o servidor do Vite no MVP, o Caddy no final acadêmico); caso contrário, do endereço da conexão.
- **Retenção:** linhas com mais de 24 horas são apagadas por uma tarefa periódica do Procrastinate (`limpar_registros_expirados`), que também apaga sessões expiradas ou revogadas há mais de 30 dias.

**Condição para revisão:** ataque distribuído que exija limites globais ou desafio (ex.: CAPTCHA), o que seria decisão de produto.

## Decisão DTEC 021 Exclusão da conta e chaves de armazenamento por usuário

**Questão:** como excluir a conta com todos os dados e arquivos (RF-015, CS-004), com um único efeito mesmo com pedidos repetidos e sem deixar linhas apontando para arquivos já apagados, se a falha acontecer no meio?  
**Critérios:** atomicidade; idempotência; nenhum resíduo no banco nem no armazenamento (CS-004); compatibilidade com a regra do esquema "objetos antes das linhas" na exclusão de uma fonte isolada; interrupção dos processamentos em andamento.  
**Alternativas consideradas:**

1. **Transação única nas linhas + tarefa durável que apaga o prefixo do usuário no armazenamento:** a transação trava a linha do usuário, apaga todas as linhas da conta, na ordem das dependências, e enfileira na mesma transação (emenda da DTEC 002) a tarefa idempotente `apagar_objetos_usuario`, que remove tudo sob o prefixo `usuarios/{public_id_usuario}/`. Exige que **toda chave de objeto** comece por esse prefixo.
2. **Apagar os objetos de forma síncrona e depois as linhas:** se a transação falhar depois de apagar os objetos, sobram linhas apontando para arquivos inexistentes, e a conta fica corrompida.
3. **Exclusão lógica (marcar a conta como excluída) com limpeza posterior:** contraria a exclusão física definitiva (D-003, RN-14) e mantém dados pessoais por mais tempo.

**Decisão:** alternativa 1.  
**Justificativa:** as linhas somem de uma vez ou não somem; os objetos, já inacessíveis porque nenhuma linha aponta para eles, são removidos por uma tarefa que sobrevive a reinícios e pode ser repetida sem efeito colateral.  
**Consequências:**

- **Formato de chave (vale para as specs 002 e 011):** `usuarios/{public_id_usuario}/fontes/{uuid}` e `usuarios/{public_id_usuario}/imagens/{uuid}`. O nome enviado pelo usuário nunca compõe a chave (DTEC 010). A interface de armazenamento ganha a operação `apagar_prefixo`.
- **Exceção registrada:** na exclusão da **conta**, os objetos são apagados depois das linhas, pela tarefa. A regra "objetos antes das linhas" do esquema continua valendo para a exclusão de uma fonte ou imagem isolada.
- **Ordem das linhas:** cada domínio registra uma função `apagar_dados_usuario(sessao, usuario_id)` num registro de exclusão do núcleo, na ordem das dependências. Na 001 entram sessões, parâmetros do FSRS e o próprio usuário; as specs 002 a 007 acrescentam os seus. Um teste de integração verifica, pelo catálogo do PostgreSQL, que **toda** tabela com coluna `usuario_id` fica vazia para a conta excluída (CS-004), o que detecta um domínio esquecido.
- **Pedido repetido ou simultâneo:** a transação trava a linha do usuário (`SELECT ... FOR UPDATE`); o segundo pedido espera, encontra a sessão já apagada e recebe `401`. Há um único efeito.
- **Processamentos em andamento:** as tarefas das specs 002 e 004 verificam a existência do registro ao começar e ao gravar, e terminam sem efeito se ele não existir mais. Esse comportamento é exigido pelos planos dessas specs.
- **Tentativas de acesso:** as linhas de `tentativas_acesso` não guardam o id do usuário e expiram em 24 horas (DTEC 020); não há dado pessoal legível nelas.

**Condição para revisão:** um armazenamento que não permita listar e apagar por prefixo.

## Decisão DTEC 022 Lista local de senhas comuns

**Questão:** qual lista de senhas comuns ou vazadas o cadastro e a troca de senha consultam (RF-002, D-002), sem chamar serviço externo?  
**Critérios:** cobertura das senhas mais usadas, inclusive em português; licença compatível; funcionamento sem rede; memória.  
**Alternativas consideradas:**

1. **Lista "100k most used passwords" (NCSC) do repositório SecLists, licença MIT, mais uma lista curta de senhas comuns em português (nomes de times, palavras e sequências usuais) mantida pela equipe:** cerca de 100 mil entradas e de 1 MB em memória.
2. **Consulta à API de senhas vazadas por k-anonimato:** cobertura muito maior, mas envia dados a um terceiro e depende de rede, contrariando "lista local" (RF-002).
3. **Lista com milhões de entradas:** cobertura maior, com dezenas de MB de memória e imagem maior.

**Decisão:** alternativa 1, versionada em `backend/src/app/identidade/dados/senhas_comuns.txt` com a origem e a licença registradas no cabeçalho do arquivo, carregada uma vez ao iniciar num `frozenset` e comparada sem diferenciar maiúsculas e minúsculas.  
**Justificativa:** é a recomendação usual para políticas de senha sem regras de composição, com custo de memória desprezível e sem enviar nada a terceiros.  
**Consequências:** a mensagem de recusa não diz qual lista foi consultada; a lista em português é revisada pela equipe antes do merge.  
**Condição para revisão:** evolução para o final acadêmico com recuperação de senha, em que a consulta por k-anonimato pode ser reavaliada.

## Decisão DTEC 023 Detalhes da sessão, do CSRF e do hash de senha

**Questão:** quais parâmetros concretos implementam a DTEC 003 (sessão opaca, *double submit*, Argon2id) e os requisitos RF-006, RF-011, RQ-001 e CS-003?  
**Critérios:** recomendações da OWASP para sessão, CSRF e armazenamento de senhas; RFC 9106 (Argon2); memória numa VPS de 2 a 4 GB; não enumeração de contas pelo tempo de resposta.  
**Alternativas consideradas e decisões:**

| Tema | Alternativas | Decisão |
|---|---|---|
| Identificador da sessão | UUID; 256 bits aleatórios | **256 bits** de `secrets.token_bytes`, enviados em base64url no cookie; o banco guarda só o SHA-256 (`sessoes.token_hash`). |
| Expiração | Só absoluta; absoluta e por inatividade | **Ambas** (RF-006, D-006): 14 dias sem uso e 30 dias após a entrada, configuráveis. `ultimo_uso_em` é gravado no máximo uma vez por minuto, para não gerar uma escrita por requisição. |
| Cookie da sessão | `SameSite=Strict`; `Lax` | **`HttpOnly`, `Secure`, `SameSite=Lax`, `Path=/`**, nome `__Host-sessao` (o prefixo exige `Secure` e impede domínio amplo). O nome é configurável, para navegadores que não aceitam o prefixo em `http://localhost`. |
| Fixação de sessão | Reaproveitar o identificador; trocar | **Novo identificador a cada entrada e cadastro.** Na troca de senha, as **outras** sessões são revogadas e a atual continua (RF-014). |
| CSRF | *Double submit* simples; *double submit* assinado; token sincronizado no servidor | ***Double submit* assinado (padrão OWASP):** token = `aleatorio.HMAC(segredo, id_da_sessao + aleatorio)` no cookie `__Host-csrf` (legível pelo JavaScript, não `HttpOnly`) e repetido no cabeçalho `X-CSRF-Token` em todo `POST`, `PATCH`, `PUT` e `DELETE`. Antes de existir sessão (cadastro e entrada), o token é ligado a um identificador pré-sessão, o que também protege contra CSRF no login. |
| Defesa adicional | Nenhuma; verificar origem | **Verificar `Origin`** contra `ORIGENS_PERMITIDAS` e recusar `Sec-Fetch-Site` diferente de `same-origin` nas requisições que alteram estado. |
| Hash de senha | Perfil mínimo da OWASP (19 MiB); perfil de pouca memória da RFC 9106 (64 MiB) | **`argon2-cffi` com o perfil de pouca memória da RFC 9106** (t=3, m=64 MiB, p=4). O cálculo roda em *thread* separada, limitado por um semáforo (`ARGON2_CONCORRENCIA`, padrão 4), para que rajadas de login não esgotem a memória da VPS. O hash é refeito na entrada quando os parâmetros mudam (`check_needs_rehash`). |
| Tempo de resposta | Responder já quando o e-mail não existe; verificar contra um hash fictício | **Verificação contra um hash fictício** quando o e-mail não existe, para que o tempo da resposta não revele a conta (CS-003). |
| Normalização | Normalizar a senha (NFC); não normalizar | **A senha não é normalizada** (`padroes-implementacao.md`); o comprimento é contado em caracteres. Nome e e-mail são normalizados em NFC e sem espaços nas extremidades; o e-mail é guardado em minúsculas. |

**Justificativa:** cada parâmetro segue a recomendação de referência ou a decisão da spec, e o semáforo do Argon2 mantém o pico de memória previsível (4 × 64 MiB).  
**Consequências:** o segredo da aplicação (`SEGREDO_APLICACAO`, no mínimo 32 bytes aleatórios) assina o CSRF e a chave das tentativas, e sua troca invalida os tokens anti-CSRF em circulação (o cliente obtém um novo token e repete a requisição uma vez). Respostas de cadastro, entrada, saída e perfil têm `Cache-Control: no-store`.  
**Condição para revisão:** nova recomendação da OWASP ou da RFC; latência de entrada acima de 1 segundo na VPS, o que exigiria recalibrar o Argon2.

## Fontes consultadas

- OWASP Cheat Sheet Series: *Session Management*, *Cross-Site Request Forgery Prevention* (*signed double-submit cookie*), *Password Storage* e *Authentication*.
- RFC 9106 (Argon2), seção 4, perfis recomendados; documentação do `argon2-cffi` (perfis e `check_needs_rehash`).
- MDN: prefixos de cookie `__Host-`, `SameSite` e o cabeçalho `Sec-Fetch-Site`.
- Documentação do PostgreSQL: *advisory locks*, `SELECT ... FOR UPDATE` e Row-Level Security.
- Repositório SecLists (`Passwords/Common-Credentials`), licença MIT.
- Documentação do Procrastinate (conexão externa e tarefas periódicas), consultada em 12/10/2026.
