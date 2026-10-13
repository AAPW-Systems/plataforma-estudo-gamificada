# syntax=docker/dockerfile:1.10
# Imagens base fixadas por digest (plano da 001, "Contexto técnico").
ARG IMAGEM_PYTHON=python:3.13-slim-trixie@sha256:70729b46c69b4f1e97c4822c1af3df53a1476cf5ddc6c087c0c10bc3a5678c2f
ARG IMAGEM_UV=ghcr.io/astral-sh/uv:0.13.0@sha256:cdc6093146eb3ff6a40107b38f008b789e050e77ad87865e381d9917da55a168

FROM ${IMAGEM_UV} AS uv

# --- base: Python, uv e ambiente virtual fora de /app (o código é montado por volume no dev)
FROM ${IMAGEM_PYTHON} AS base
COPY --from=uv /uv /uvx /usr/local/bin/
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:${PATH}"
WORKDIR /app

# --- dev: dependências de desenvolvimento, recarga automática e ferramentas de teste
FROM base AS dev
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project
COPY . .
RUN --mount=type=cache,target=/root/.cache/uv uv sync --locked
EXPOSE 8000
CMD ["uvicorn", "app.principal:criar_aplicacao", "--factory", "--host", "0.0.0.0", "--port", "8000", "--reload", "--reload-dir", "src", "--no-proxy-headers"]

# --- construcao: só as dependências de produção
FROM base AS construcao
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-dev --no-install-project
COPY pyproject.toml uv.lock ./
COPY src ./src
RUN --mount=type=cache,target=/root/.cache/uv uv sync --locked --no-dev --no-editable

# --- prod: sem uv nem ferramentas de desenvolvimento, usuário sem privilégios.
# --no-proxy-headers: o X-Forwarded-For é resolvido só por app.nucleo.rede (DTEC 020).
FROM ${IMAGEM_PYTHON} AS prod
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:${PATH}"
RUN groupadd --system --gid 10001 app \
    && useradd --system --uid 10001 --gid app --no-create-home --shell /usr/sbin/nologin app
WORKDIR /app
COPY --from=construcao /opt/venv /opt/venv
COPY alembic.ini ./
COPY migracoes ./migracoes
USER app
EXPOSE 8000
CMD ["uvicorn", "app.principal:criar_aplicacao", "--factory", "--host", "0.0.0.0", "--port", "8000", "--no-proxy-headers"]
