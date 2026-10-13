# Modelo de dados

**Funcionalidade:** 001-conta-acesso (conta, sessão, isolamento e preferências)  
**Spec:** [spec.md](spec.md)  
**Base:** [esquema inicial](../../arquitetura/esquema-inicial.dbml) (grupo `identidade` e tabela `parametros_fsrs`), atualizado nesta sessão com a tabela `tentativas_acesso` e o limite de 100 caracteres do nome.

Este documento descreve as entidades e regras que a spec 001 cria. Os tipos de banco aparecem só quando definem uma regra; o resto fica na migração. Cada spec cria somente as colunas que usa: as colunas de gamificação de `usuarios` (`xp_total`, `sequencia_atual`, `sequencia_recorde`, `ultimo_dia_estudado`) são criadas pela migração da [spec 006](../006-xp-meta-sequencia/spec.md).

## Entidade Usuario (`usuarios`)

**Finalidade:** a conta do estudante, com identificação e preferências de ritmo.

| Campo | Significado | Obrigatório | Regras |
|---|---|---:|---|
| `id` | Identificador interno | sim | `bigint generated always as identity`; nunca sai da API |
| `public_id` | Identificador público | sim | UUID v4 gerado pelo banco; único |
| `nome` | Nome exibido | sim | NFC, sem espaços nas extremidades, de 1 a 100 caracteres, sem caracteres de controle (RF-001) |
| `email` | E-mail de acesso | sim | NFC, sem espaços nas extremidades, em minúsculas, formato válido, até 254 caracteres; único por `lower(email)` (RF-001, RF-012) |
| `senha_hash` | Hash da senha | sim | Argon2id no formato PHC (DTEC 023); a senha nunca é gravada (RQ-001) |
| `papel` | Papel da conta | sim | `estudante` em todo cadastro público; nenhuma rota do usuário altera (RF-003) |
| `fuso` | Fuso do estudante | sim | Nome IANA válido na base `tzdata`; no cadastro, o detectado no navegador ou `America/Sao_Paulo` (RF-009) |
| `meta_diaria` | Cartões distintos por dia | sim | De 1 a 200; padrão 20 (D-001) |
| `tamanho_licao` | Cartões distintos por lição | sim | De 5 a 50; padrão 10 (D-001) |
| `limite_novos_dia` | Cartões novos por dia, global | sim | De 0 a 100; padrão 20 (D-001) |
| `criado_em` | Instante do cadastro | sim | UTC |
| `atualizado_em` | Instante da última alteração | sim | UTC; atualizado pela aplicação |

Os padrões e limites de D-001 ficam num único módulo versionado (`backend/src/app/identidade/preferencias.py`). O banco repete os limites como `CHECK`, para que nenhum caminho de escrita os contorne.

## Entidade Sessao (`sessoes`)

**Finalidade:** o vínculo entre um navegador e uma conta (DTEC 003 e DTEC 023).

| Campo | Significado | Obrigatório | Regras |
|---|---|---:|---|
| `id` | Identificador interno | sim | Nunca sai da API |
| `usuario_id` | Dono da sessão | sim | FK para `usuarios`, `on delete cascade` |
| `token_hash` | SHA-256 do identificador do cookie | sim | Único; o identificador em si nunca é gravado (RQ-001) |
| `criada_em` | Início (entrada ou cadastro) | sim | UTC |
| `ultimo_uso_em` | Último uso registrado | sim | Atualizado no máximo uma vez por minuto |
| `expira_em` | Expiração absoluta | sim | `criada_em` + 30 dias (RF-006, configurável) |
| `revogada_em` | Revogação | não | Saída, troca de senha (outras sessões) ou exclusão da conta |
| `ip` | Endereço de rede no início | não | Diagnóstico; nunca exposto ao estudante no MVP |
| `agente_usuario` | Navegador no início | não | Até 512 caracteres, truncado |

## Entidade ParametrosFsrs (`parametros_fsrs`)

**Finalidade:** versão imutável dos parâmetros do agendador FSRS do estudante (RF-010, RN-26, CB-29). A spec 001 cria a versão inicial e as versões causadas pela troca da retenção desejada; a [spec 005](../005-licao-trilha/spec.md) as usa nas revisões.

| Campo | Significado | Obrigatório | Regras |
|---|---|---:|---|
| `id` | Identificador interno | sim | Apontado por `revisoes.parametros_fsrs_id` (spec 005) |
| `usuario_id` | Dono | sim | FK para `usuarios` |
| `versao` | Número da versão | sim | Começa em 1; a vigente é a maior; único por `(usuario_id, versao)` |
| `origem` | Origem dos pesos | sim | `padrao` no MVP (`otimizado` fica para depois) |
| `pesos` | Os 21 pesos do modelo | sim | Copiados de `Scheduler().parameters` da versão fixada da biblioteca `fsrs`; exatamente 21 valores |
| `retencao_desejada` | Retenção desejada | sim | De 0,70 a 0,97, com duas casas; padrão 0,90 (D-001) |
| `passos_aprendizado_s` | Passos de aprendizado | sim | Padrão da biblioteca: `{60, 600}` |
| `passos_reaprendizado_s` | Passos de reaprendizado | sim | Padrão da biblioteca: `{600}` |
| `intervalo_maximo_dias` | Intervalo máximo | sim | Padrão 36500 |
| `fuzzing` | *Fuzzing* do intervalo | sim | Padrão `true` |
| `versao_biblioteca` | Versão da biblioteca `fsrs` | sim | Lida dos metadados do pacote instalado |
| `criado_em` | Criação da versão | sim | UTC |

## Entidade TentativaAcesso (`tentativas_acesso`, nova)

**Finalidade:** os eventos que alimentam os limites da RQ-003 (DTEC 020). É uma tabela operacional: não pertence a um usuário e não aparece na API.

| Campo | Significado | Obrigatório | Regras |
|---|---|---:|---|
| `id` | Identificador interno | sim | — |
| `tipo` | Tipo do evento | sim | `falha_entrada`, `falha_senha_atual` ou `cadastro` |
| `chave_conta` | HMAC-SHA-256 do e-mail normalizado | não | Nula em `cadastro`; o e-mail nunca é gravado em claro |
| `ip` | Endereço de rede da requisição | sim | Resolvido conforme os proxies confiáveis (DTEC 020) |
| `criado_em` | Instante do evento | sim | UTC; linhas com mais de 24 horas são apagadas |

Índices: `(chave_conta, criado_em)` e `(ip, tipo, criado_em)`.

## Relacionamentos

- Um **Usuario** tem zero ou mais **Sessoes** (exclusão em cascata).
- Um **Usuario** tem uma ou mais versões de **ParametrosFsrs**; a versão 1 nasce no cadastro, na mesma transação.
- **TentativaAcesso** não tem FK: a ligação com a conta é só pela chave HMAC, o que permite limitar e-mails sem conta (CS-003).
- Objetos do armazenamento (spec 002 em diante) ficam sob o prefixo `usuarios/{public_id}/` (DTEC 021).

## Estados e transições

### Sessão

```text
ativa -> revogada   (saída, troca de senha em outra sessão, exclusão da conta)
ativa -> expirada   (14 dias sem uso ou 30 dias desde a entrada)
```

- Uma sessão é **válida** quando `revogada_em` é nula, `agora < expira_em` e `agora < ultimo_uso_em + 14 dias`.
- Uma sessão revogada ou expirada nunca volta a valer. Usá-la gera `401` (`nao_autenticado`) e apaga os cookies.
- A sessão não muda de usuário: uma nova entrada cria uma nova sessão (DTEC 023).

### Conta

```text
inexistente -> ativa -> excluída (física; nenhuma linha nem objeto permanece)
```

- **Criação:** acontece só pelo cadastro, com e-mail livre, senha válida e dentro do limite de cadastros do endereço de rede.
- **Exclusão:** exige a senha atual correta e uma sessão válida. É recusada se a conta estiver bloqueada por tentativas (RQ-003).

### Parâmetros do FSRS

```text
versão n (vigente) -> versão n+1 (vigente); a versão n continua existindo e nunca é alterada
```

- Uma nova versão nasce quando a retenção desejada **muda de valor**. Salvar o mesmo valor não cria versão.
- Os demais campos são copiados da versão vigente.

## Validações transversais

- **Isolamento (RF-007):** toda leitura e escrita de dado de estudante passa por um repositório que recebe o `usuario_id` obrigatório (DTEC 019).
- **Unicidade do e-mail sem diferenciar caixa:** índice único em `lower(email)`. A corrida entre dois cadastros simultâneos é resolvida pelo índice; a violação vira `409 email_em_uso`.
- **Alteração das preferências (RF-008):** é tudo ou nada. Se algum campo é inválido, nada muda e a resposta lista todos os campos inválidos (`422`).
- **Concorrência no perfil:** a alteração trava a linha do usuário (`FOR UPDATE`), o que serializa as novas versões de `parametros_fsrs`.
- **Exclusão da conta (RF-015, CS-004):** numa transação, cada domínio apaga suas linhas na ordem do registro de exclusão, o usuário é apagado e a tarefa `apagar_objetos_usuario` é enfileirada (DTEC 021). Um teste verifica pelo catálogo que nenhuma tabela com `usuario_id` mantém linhas da conta.
- **Retenção:** sessões expiradas ou revogadas há mais de 30 dias e tentativas com mais de 24 horas são apagadas pela tarefa periódica `limpar_registros_expirados`.
- **Privacidade:** nenhuma tabela guarda senha, identificador de sessão ou e-mail de tentativa em claro (RQ-001).
- **Mudança de fuso:** só altera `usuarios.fuso`. Os dias de estudo já gravados (`dias_estudo.dia`, spec 006) guardam a data já calculada e não mudam (US3, cenário 4).
