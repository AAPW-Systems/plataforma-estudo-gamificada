import { cleanup, screen } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { afterAll, afterEach, beforeAll, expect, it } from "vitest";

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
  servidor.use(
    http.get("https://teste/api/v1/perfil", () => HttpResponse.json({ nome: "Estudante Exemplo" })),
  );
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
