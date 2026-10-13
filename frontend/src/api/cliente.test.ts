import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";
import { afterAll, afterEach, beforeAll, expect, it } from "vitest";

import { criarCliente } from "./cliente";
import { ErroApi } from "./erros";

interface ContratoTeste {
  "/teste": {
    post: {
      requestBody: { content: { "application/json": { nome: string } } };
      responses: { 204: { content: never } };
    };
  };
}

const servidor = setupServer();
beforeAll(() => {
  servidor.listen({ onUnhandledFrame: "error" });
});
afterEach(() => {
  servidor.resetHandlers();
  document.cookie = "__Host-csrf=; Max-Age=0; Path=/; Secure";
});
afterAll(() => {
  servidor.close();
});

function erro(codigo: string) {
  return {
    codigo,
    mensagem: "Confira a requisição.",
    idRequisicao: "00000000-0000-4000-8000-000000000001",
  };
}

it("T025: obtém CSRF e preserva o corpo em uma única repetição", async () => {
  let tokens = 0;
  const recebidos: string[] = [];
  servidor.use(
    http.get("https://teste/api/v1/auth/csrf", () => {
      tokens += 1;
      document.cookie = `__Host-csrf=token${tokens}; Path=/; Secure`;
      return new HttpResponse(null, { status: 204 });
    }),
    http.post("https://teste/teste", async ({ request }) => {
      recebidos.push(await request.text());
      expect(request.headers.get("X-CSRF-Token")).toBe(`token${recebidos.length}`);
      return recebidos.length === 1
        ? HttpResponse.json(erro("csrf_invalido"), { status: 403 })
        : new HttpResponse(null, { status: 204 });
    }),
  );
  const cliente = criarCliente<ContratoTeste>({ baseUrl: "https://teste" });
  await cliente.POST("/teste", { body: { nome: "Exemplo" } });
  expect(recebidos).toEqual(['{"nome":"Exemplo"}', '{"nome":"Exemplo"}']);
  expect(tokens).toBe(2);
});

it.each(["csrf_invalido", "origem_nao_permitida"])(
  "T025: não repete indefinidamente o erro %s",
  async (codigo) => {
    let chamadas = 0;
    servidor.use(
      http.get("https://teste/api/v1/auth/csrf", () => {
        document.cookie = "__Host-csrf=token; Path=/; Secure";
        return new HttpResponse(null, { status: 204 });
      }),
      http.post("https://teste/teste", () => {
        chamadas += 1;
        return HttpResponse.json(erro(codigo), { status: 403 });
      }),
    );
    const cliente = criarCliente<ContratoTeste>({ baseUrl: "https://teste" });
    await expect(cliente.POST("/teste", { body: { nome: "Exemplo" } })).rejects.toMatchObject({
      status: 403,
      codigo,
    });
    expect(chamadas).toBe(codigo === "csrf_invalido" ? 2 : 1);
  },
);

it("T025: falha sem JSON vira erro seguro e tipado", async () => {
  servidor.use(
    http.get(
      "https://teste/api/v1/auth/csrf",
      () => new HttpResponse("detalhes internos", { status: 502 }),
    ),
  );
  const cliente = criarCliente<ContratoTeste>({ baseUrl: "https://teste" });
  await expect(cliente.POST("/teste", { body: { nome: "Exemplo" } })).rejects.toBeInstanceOf(
    ErroApi,
  );
});
