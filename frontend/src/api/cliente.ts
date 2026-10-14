import createClient, { type Middleware } from "openapi-fetch";

import type { paths } from "./esquema.gerado";
import { lerErro } from "./erros";

const ESCRITAS = new Set(["POST", "PUT", "PATCH", "DELETE"]);

function tokenCsrf(): string | undefined {
  return document.cookie
    .split(";")
    .map((parte) => parte.trim())
    .find((parte) => parte.startsWith("__Host-csrf="))
    ?.slice("__Host-csrf=".length);
}

export function criarCliente<Contrato extends object = paths>({
  baseUrl = window.location.origin,
}: { baseUrl?: string } = {}) {
  const cliente = createClient<Contrato>({
    baseUrl,
    credentials: "same-origin",
    // Resolve o fetch a cada chamada: quem o substitui depois (o MSW nos testes) é respeitado.
    fetch: (requisicao) => globalThis.fetch(requisicao),
  });
  const copias = new WeakMap<Request, Request>();
  let renovacao: Promise<void> | undefined;

  async function renovarCsrf(): Promise<void> {
    renovacao ??= (async () => {
      const resposta = await fetch(`${baseUrl}/api/v1/auth/csrf`, { credentials: "same-origin" });
      if (!resposta.ok) throw await lerErro(resposta);
    })().finally(() => {
      renovacao = undefined;
    });
    await renovacao;
  }

  const protecao: Middleware = {
    async onRequest({ request }) {
      if (ESCRITAS.has(request.method)) {
        if (!tokenCsrf()) await renovarCsrf();
        request.headers.set("X-CSRF-Token", tokenCsrf() ?? "");
        copias.set(request, request.clone());
      }
      return request;
    },
    async onResponse({ request, response }) {
      let resposta = response;
      const copia = copias.get(request);
      copias.delete(request);
      if (
        resposta.status === 403 &&
        copia &&
        (await lerErro(resposta)).codigo === "csrf_invalido"
      ) {
        await renovarCsrf();
        copia.headers.set("X-CSRF-Token", tokenCsrf() ?? "");
        // Fetch direto evita reentrar no middleware: no máximo uma repetição.
        resposta = await fetch(copia);
      }
      if (!resposta.ok) throw await lerErro(resposta);
      return resposta;
    },
  };
  cliente.use(protecao);
  return cliente;
}

export const cliente = criarCliente();
