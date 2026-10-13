# Guia de validação local

**Funcionalidade:** 001-conta-acesso (conta, sessão, isolamento e preferências)

Este guia descreve como outra pessoa prepara o ambiente e verifica o incremento sem depender de explicações orais. Os comandos passam a funcionar depois das tarefas de estrutura base e da US1 (`tasks.md`, etapa 6). Todo serviço roda em contêiner (regra 11): não é preciso Python nem Node no computador.

## Pré-requisitos

- Docker Engine 27 ou mais recente (ou Docker Desktop) com o Compose v2 (`docker compose version`).
- Git.
- Navegador atual (Chrome, Firefox ou Edge) para a verificação manual.
- Portas livres: `5173` (interface), `8000` (API, Swagger UI) e `5432` (banco, opcional).
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
docker compose up --build
```

O Compose sobe `db`, aplica as migrações (`migrate`, que roda uma vez e termina) e depois sobe `api`, `worker` e `web`. O ambiente está pronto quando os serviços aparecem como saudáveis em `docker compose ps`.

| Endereço | O que é |
|---|---|
| http://localhost:5173 | Interface |
| http://localhost:5173/api/docs | Swagger UI (somente em `desenvolvimento`) |
| http://localhost:8000/health/ready | Saúde da API (banco e fila) |

Para parar: `docker compose down`. Para apagar também os dados locais: `docker compose down -v`.

## Testes

```bash
# Backend: suíte completa (unit, integration, functional, security, adversarial)
docker compose run --rm api uv run pytest

# Backend: um tipo de teste, por marcador
docker compose run --rm api uv run pytest -m security

# Backend: qualidade estática
docker compose run --rm api uv run ruff check .
docker compose run --rm api uv run ruff format --check .
docker compose run --rm api uv run mypy

# Frontend: testes, lint e tipos
docker compose run --rm web npm test
docker compose run --rm web npm run lint
docker compose run --rm web npm run typecheck

# Contrato: OpenAPI e tipos gerados devem estar atualizados (sem diferença no git)
docker compose run --rm api uv run python -m app.exportar_openapi
docker compose run --rm web npm run gerar:api
git diff --exit-code backend/openapi.json frontend/src/api/
```

A suíte do backend usa o banco `plataforma_teste`, criado e migrado automaticamente no mesmo contêiner do Postgres, sem tocar nos dados de desenvolvimento. A integração contínua executa os mesmos comandos ([DTEC 017](../../research.md#decisão-dtec-017-integração-contínua-e-verificação-local)).

## Verificação da história P1

### US1 Criar conta e entrar

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

- Os testes `functional` da US1 passam.
- O log da `api` mostra os eventos `conta_criada`, `entrada_recusada` e `bloqueio_aplicado`, com `idRequisicao` e sem senha, e-mail ou cookie (RQ-002):

  ```bash
  docker compose logs api | grep -E "conta_criada|entrada_recusada|bloqueio_aplicado"
  ```

### US2 Acessar somente meus dados

1. Rode `docker compose run --rm api uv run pytest -m security`. **Esperado:** todos passam, inclusive o teste que percorre as rotas (DTEC 019).
2. Sem sessão, rode `curl -i http://localhost:5173/api/v1/perfil`. **Esperado:** `401` com o corpo `Erro` (`nao_autenticado`), sem dados.
3. Com sessão aberta, rode `fetch("/api/v1/perfil", {method: "PATCH", body: "{}"})` no console do navegador, sem o cabeçalho `X-CSRF-Token`. **Esperado:** `403 csrf_invalido` (cenário 3).

## Falhas conhecidas

- **Trilha vazia:** a trilha exibida depois da entrada fica vazia até a spec 005. Nesta spec, ela só comprova o redirecionamento para a área do estudante.
- **Prefixo `__Host-` em `http://localhost`:** alguns navegadores não aceitam o prefixo nesse endereço. Se a sessão não persistir, defina `COOKIE_SESSAO_NOME=sessao` e `COOKIE_CSRF_NOME=csrf` no `.env`. Em produção, o prefixo é obrigatório.
- **Arquivos na exclusão:** a exclusão da conta enfileira a remoção de arquivos, mas a 001 ainda não grava arquivos. O efeito sobre arquivos é verificado pelos testes de integração com o adaptador de disco e passa a valer na prática com a spec 002.
- **Sem recuperação de senha:** não há recuperação de senha no MVP ([spec 008](../008-recuperacao-senha/spec.md)). Quem esquecer a senha de uma conta fictícia deve criar outra.
