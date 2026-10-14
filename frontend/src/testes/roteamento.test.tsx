import { cleanup, screen } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { afterAll, afterEach, beforeAll, expect, it } from "vitest";

import { perfilFicticio } from "./perfil";
import { cliente } from "../api/cliente";
import { servidor } from "./servidor";
import { renderizarComRoteador } from "./renderizar";

beforeAll(() => {
  servidor.listen({ onUnhandledFrame: "error" });
});
afterEach(() => {
  cleanup();
  servidor.resetHandlers();
});
afterAll(() => {
  servidor.close();
});

it("T026: rota protegida sem sessão redireciona para entrar", async () => {
  const { roteador } = renderizarComRoteador("/");
  expect(await screen.findByRole("heading", { name: "Entrar" })).toBeInTheDocument();
  expect(roteador.state.location.pathname).toBe("/entrar");
});

it("T026: perfil autenticado permite a área do estudante", async () => {
  servidor.use(http.get("https://teste/api/v1/perfil", () => HttpResponse.json(perfilFicticio())));
  renderizarComRoteador("/");
  expect(await screen.findByRole("heading", { name: "Seus estudos" })).toBeInTheDocument();
});

it("T026: falha do servidor não é tratada como sessão encerrada", async () => {
  servidor.use(
    http.get("https://teste/api/v1/perfil", () => new HttpResponse(null, { status: 503 })),
  );
  const { roteador } = renderizarComRoteador("/");
  expect(await screen.findByRole("alert")).toHaveTextContent("Não foi possível carregar");
  expect(roteador.state.location.pathname).toBe("/");
});

it("T044: sessão que termina durante o uso limpa o cache e leva à entrada", async () => {
  servidor.use(http.get("https://teste/api/v1/perfil", () => HttpResponse.json(perfilFicticio())));
  const { roteador } = renderizarComRoteador("/");
  expect(await screen.findByRole("heading", { name: "Seus estudos" })).toBeInTheDocument();
  const { queryClient } = roteador.options.context;
  expect(queryClient.getQueryData(["perfil"])).toBeDefined();

  // O servidor passa a recusar a sessão (expirou, ou foi encerrada em outra aba).
  servidor.use(
    http.get("https://teste/api/v1/outra-leitura", () =>
      HttpResponse.json(
        {
          codigo: "nao_autenticado",
          mensagem: "Sua sessão terminou. Entre novamente.",
          idRequisicao: "00000000-0000-4000-8000-000000000001",
        },
        { status: 401 },
      ),
    ),
  );
  await expect(
    (cliente as unknown as { GET: (caminho: string) => Promise<unknown> }).GET(
      "/api/v1/outra-leitura",
    ),
  ).rejects.toMatchObject({ status: 401 });

  expect(await screen.findByRole("heading", { name: "Entrar" })).toBeInTheDocument();
  expect(roteador.state.location.pathname).toBe("/entrar");
  expect(queryClient.getQueryData(["perfil"])).toBeUndefined();
});
