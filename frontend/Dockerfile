# syntax=docker/dockerfile:1.10
# Imagens base fixadas por digest (plano da 001, "Contexto técnico").
ARG IMAGEM_NODE=node:24-trixie-slim@sha256:173f125896c3b47ddf056734c7ea789d04595a6a08769a8f78e0df642781fb66
ARG IMAGEM_CADDY=caddy:2.11-alpine@sha256:d8542f48d34a9cf4e4c11a478865229840e87e4c96ea3f439101f31a5d35f75f

# --- deps: dependências exatamente como no package-lock.json
FROM ${IMAGEM_NODE} AS deps
WORKDIR /app
RUN --mount=type=cache,target=/root/.npm \
    --mount=type=bind,source=package.json,target=package.json \
    --mount=type=bind,source=package-lock.json,target=package-lock.json \
    --mount=type=bind,source=.npmrc,target=.npmrc \
    npm ci --no-audit --no-fund

# --- dev: servidor do Vite com recarga; o código é montado por volume no Compose
FROM deps AS dev
COPY . .
USER node
EXPOSE 5173
CMD ["npm", "run", "dev"]

# --- build: estáticos otimizados
FROM deps AS build
COPY . .
RUN npm run build

# --- prod: só os estáticos, servidos pelo Caddy (arquitetura, seção 5.2)
FROM ${IMAGEM_CADDY} AS prod
COPY Caddyfile /etc/caddy/Caddyfile
COPY --from=build /app/dist /srv
EXPOSE 8080
USER 10001:10001
