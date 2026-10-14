# Guia de validação local

**Funcionalidade:** 001-conta-acesso (conta, sessão, isolamento e preferências)

Este guia descreve como outra pessoa prepara o ambiente e verifica o incremento sem depender de explicações orais. Os comandos abaixo foram executados na implementação (registro da sessão de 14/10/2026); o que ficou sem execução está na seção "Falhas conhecidas". Todo serviço roda em contêiner (regra 11): não é preciso Python nem Node no computador.

## Pré-requisitos

- Docker Engine 27 ou mais recente (ou Docker Desktop) com o Compose v2 (`docker compose version`).
- Git.
- Navegador atual (Chrome, Firefox ou Edge) para a verificação manual.
- Portas livres: `5173` (interface) e `8000` (API, Swagger UI). O banco não publica porta no computador.
- Variáveis obrigatórias, sem valores no repositório: `POSTGRES_PASSWORD` e `SEGREDO_APLICACAO`. As demais têm padrão no `.env.example` (ver a tabela no [plano](plan.md#variáveis-de-ambiente-envexample)).

## Configuração

```bash
git clone https://github.com/AAPW-Systems/plataforma-estudo-gamificada.git
cd plataforma-estudo-gamificada
git switch develop
cp .env.example .env
```

Preencha no `.env` apenas as credenciais do ambiente local:

- `POSTGRES_PASSWORD`: qualquer senha local.
- `SEGREDO_APLICACAO`: no mínimo 32 bytes aleatórios. Para gerar um, rode:

  ```bash
  docker run --rm python:3.13-slim python -c "import secrets; print(secrets.token_urlsafe(48))"
  ```

Nunca faça commit do `.env` (ele está no `.gitignore`).

## Execução

```bash
docker compose up -d --build --wait
```

O Compose sobe `db`, aplica as migrações (`migrate`, que roda uma vez e termina) e depois sobe `api`, `worker` e `web`. O comando só retorna quando `db`, `api`, `worker` e `web` estão saudáveis (`docker compose ps`); o `migrate` aparece como `Exited (0)`. Na primeira vez, a construção das imagens leva alguns minutos.

| Endereço | O que é |
|---|---|
| http://localhost:5173 | Interface |
| http://localhost:5173/api/docs | Swagger UI (somente em `desenvolvimento`) |
| http://localhost:8000/health/ready | Saúde da API (banco e fila) |

Para parar: `docker compose down`. Para apagar também os dados locais: `docker compose down -v`.

## Testes

```bash
# Backend: o banco precisa estar de pé
docker compose up -d --wait db

# Backend: suíte completa (unit, integration, functional, security, adversarial)
docker compose run --rm --no-deps api uv run --frozen pytest

# Backend: um tipo de teste, por marcador, ou a cobertura
docker compose run --rm --no-deps api uv run --frozen pytest -m security
docker compose run --rm --no-deps api uv run --frozen pytest --cov --cov-report=term

# Backend: qualidade estática
docker compose run --rm --no-deps api uv run --frozen ruff format --check .
docker compose run --rm --no-deps api uv run --frozen ruff check .
docker compose run --rm --no-deps api uv run --frozen mypy

# Frontend, com o ambiente de pé (o contêiner `web` já existe, então use exec)
docker compose exec web npm run format:check
docker compose exec web npm run lint
docker compose exec web npm run typecheck
docker compose exec web npm run test:cobertura

# Contrato: OpenAPI e tipos gerados devem estar atualizados (sem diferença no git)
docker compose run --rm --no-deps api uv run --frozen python -m app.exportar_openapi
docker compose exec web npm run gerar:api
git diff --exit-code backend/openapi.json frontend/src/api/
```

A suíte do backend usa o banco `plataforma_teste`, criado e migrado automaticamente no mesmo contêiner do Postgres, sem tocar nos dados de desenvolvimento. A integração contínua executa os mesmos comandos ([DTEC 017](../../research.md#decisão-dtec-017-integração-contínua-e-verificação-local)). O `web` tem endereço fixo na rede interna (`172.28.0.10`, para o proxy do Vite ser confiável): por isso `docker compose run web ...` falha com `Address already in use` enquanto o `web` está de pé, e os comandos do frontend acima usam `exec`. O CI usa `run --no-deps` porque não sobe o `web`, e lá o `--user root` existe porque o diretório montado pertence a outro usuário do *runner*. No Linux, se faltar permissão para gravar `coverage/` ou `src/api/` com `exec`, acrescente `--user root`.

## Verificação das histórias

### US1 Criar conta e entrar (P1)

Use apenas dados fictícios (regra 10), por exemplo o e-mail `ana.teste@exemplo.com`.

1. Abra http://localhost:5173. **Esperado:** redirecionamento para a tela de entrada, porque não há sessão.
2. Vá para o cadastro. **Esperado:** aviso curto de privacidade visível, sem caixa de aceite (cenário 8, RF-013).
3. Tente cadastrar com a senha `12345678`. **Esperado:** recusa junto do campo de senha (senha comum), com nome e e-mail preservados (cenário 2).
4. Cadastre com nome `Ana Teste`, o e-mail acima e uma senha longa e incomum. **Esperado:** você entra direto na trilha, ainda vazia até a spec 005 (cenário 1).
5. Abra o perfil. **Esperado:**
   - Papel estudante, fuso igual ao do navegador.
   - Meta 20, lição 10, novos por dia 20 e retenção 0,90 (D-001).
6. Nas ferramentas do navegador (Application → Cookies), confira o cookie `__Host-sessao`. **Esperado:** cookie `HttpOnly`, `Secure` e `SameSite=Lax`. Rodar `document.cookie` no console **não** mostra a sessão (RQ-001).
7. Saia. Em seguida, use o botão "voltar" do navegador e recarregue. **Esperado:** nova tela de entrada; a sessão antiga não vale mais no servidor (cenário 5).
8. Entre com a senha errada e depois com um e-mail inexistente. **Esperado:** a mesma mensagem nos dois casos (cenário 4).
9. Erre a senha mais quatro vezes (cinco no total) e tente de novo com a senha **correta**. **Esperado:** recusa temporária com indicação de tentar mais tarde (cenário 6). Para liberar sem esperar 15 minutos:

   ```bash
   docker compose exec db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "delete from tentativas_acesso;"'
   ```

10. Tente cadastrar de novo `ANA.TESTE@exemplo.com`. **Esperado:** "e-mail já em uso", sem criar conta (cenário 7).

**Evidência observável:**

- Os testes `functional` da US1 passam (`docker compose run --rm --no-deps api uv run --frozen pytest tests/functional/identidade/test_us1_conta_entrada.py`).
- O log da `api` mostra os eventos `conta_criada`, `entrada_recusada`, `bloqueio_aplicado` e `sessao_revogada`, com `idRequisicao` e sem senha, e-mail, nome ou cookie (RQ-002):

  ```bash
  docker compose logs api | grep -E "conta_criada|entrada_recusada|bloqueio_aplicado|sessao_revogada"
  ```

### US2 Acessar somente meus dados (P1)

1. Rode `docker compose run --rm --no-deps api uv run --frozen pytest -m security`. **Esperado:** todos passam, inclusive o teste que percorre as rotas (DTEC 019).
2. Sem sessão, rode `curl -i http://localhost:5173/api/v1/perfil`. **Esperado:** `401` com o corpo `Erro` (`nao_autenticado`), sem dados.
3. Com sessão aberta, rode `fetch("/api/v1/perfil", {method: "PATCH", body: "{}"})` no console do navegador, sem o cabeçalho `X-CSRF-Token`. **Esperado:** `403 csrf_invalido` (cenário 3).

### US3 Ajustar meu perfil e ritmo de estudo (P2)

1. Entre e abra o perfil. **Esperado:** nome, e-mail, fuso e as preferências atuais (meta 20, lição 10, novos por dia 20, retenção 0,90), com a retenção explicada em linguagem simples (cenário 1).
2. Informe meta `0` ou retenção `0,99` e salve. **Esperado:** recusa junto do campo, foco nele e nada gravado (cenário 2).
3. Salve meta 35, lição 12 e novos 7. **Esperado:** valores gravados, sem nova versão do FSRS. Salve de novo sem mudar nada: aparece "Nada para salvar" (cenários 2 e 3).
4. Altere a retenção para `0,85`. **Esperado:** nova versão dos parâmetros do FSRS; a versão 1 continua com `0.90` (cenário 3):

   ```bash
   docker compose exec db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "select versao, retencao_desejada from parametros_fsrs order by versao;"'
   ```

5. Troque o fuso para `Asia/Tokyo` e depois para um nome inválido. **Esperado:** o primeiro é salvo; o segundo é recusado junto do campo, com o valor preservado (cenário 4).

**Evidência observável:** `pytest tests/functional/identidade/test_us3_perfil.py` e os testes concorrentes de `tests/adversarial/identidade/test_perfil_adversarial.py` (versões sem lacuna nem repetição).

### US4 Trocar a senha e excluir a conta (P3)

1. No perfil, troque a senha com a senha atual errada. **Esperado:** erro junto do campo, foco nele, nenhuma sessão encerrada (cenário 2).
2. Troque com a senha atual certa e uma senha nova válida, tendo outra sessão aberta em outra janela. **Esperado:** aviso de que as outras sessões foram encerradas; a outra janela volta à entrada ao recarregar; a senha antiga não entra mais (cenário 1).
3. Clique em "Excluir conta". **Esperado:** diálogo que explica que a exclusão é definitiva e o que é apagado, com o foco preso no diálogo; `Esc` fecha sem excluir (cenário 3).
4. Confirme com a senha certa. **Esperado:** você volta ao cadastro; o mesmo e-mail pode ser cadastrado de novo (cenário 4).
5. Confira que nada restou:

   ```bash
   docker compose exec db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "select (select count(*) from usuarios) as usuarios, (select count(*) from sessoes) as sessoes, (select count(*) from parametros_fsrs) as parametros;"'
   docker compose logs worker | grep objetos_do_usuario_apagados
   ```

**Evidência observável:** `pytest tests/functional/identidade/test_us4_senha_exclusao.py tests/security/identidade/test_exclusao_completa.py` (o segundo percorre o catálogo do PostgreSQL e o armazenamento).

## Falhas conhecidas

- **Trilha vazia:** a trilha exibida depois da entrada fica vazia até a spec 005. Nesta spec, ela só comprova o redirecionamento para a área do estudante.
- **Prefixo `__Host-` em `http://localhost`:** alguns navegadores não aceitam o prefixo nesse endereço. Se a sessão não persistir, defina `COOKIE_SESSAO_NOME=sessao` e `COOKIE_CSRF_NOME=csrf` no `.env`. Em produção, o prefixo é obrigatório.
- **Arquivos na exclusão:** a exclusão da conta enfileira a remoção de arquivos, mas a 001 ainda não grava arquivos. O efeito sobre arquivos é verificado pelos testes de integração com o adaptador de disco (e, no ensaio real, com arquivos criados à mão sob `usuarios/{public_id}/`) e passa a valer na prática com a spec 002.
- **Leitor de tela e teste guiado:** o uso com leitor de tela (RQ-004) e o teste com três pessoas (CS-001, T063) dependem de pessoas e ainda não foram feitos; o que foi verificado automaticamente está no [registro da sessão](../../prompts/2026-10-13-001-conta-acesso-implementacao-4.md).
- **Cabeçalhos CSP e HSTS:** a `api` e a imagem estática da interface enviam `X-Content-Type-Options`, `Referrer-Policy` e `X-Frame-Options`; CSP e HSTS ficam no Caddy de borda do final acadêmico (arquitetura, seções 5.2 e 8).
- **Sem recuperação de senha:** não há recuperação de senha no MVP ([spec 008](../008-recuperacao-senha/spec.md)). Quem esquecer a senha de uma conta fictícia deve criar outra.
