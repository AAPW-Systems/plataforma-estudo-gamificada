import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";

export const servidor = setupServer(
  http.get("https://teste/api/v1/perfil", () =>
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
