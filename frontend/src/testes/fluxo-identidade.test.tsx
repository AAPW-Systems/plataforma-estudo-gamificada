import { cleanup, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { afterAll, afterEach, beforeAll, beforeEach, expect, it } from "vitest";
import { axe } from "vitest-axe";

import { perfilFicticio } from "./perfil";
import { renderizarComRoteador } from "./renderizar";
import { servidor } from "./servidor";

beforeAll(() => {
  servidor.listen({ onUnhandledFrame: "error" });
});
beforeEach(() => {
  document.cookie = "__Host-csrf=token-de-teste; Path=/; Secure";
});
afterEach(() => {
  cleanup();
  servidor.resetHandlers();
  document.cookie = "__Host-csrf=; Max-Age=0; Path=/; Secure";
});
afterAll(() => {
  servidor.close();
});

/** O perfil só existe depois da entrada ou do cadastro, como no servidor. */
function simularSessao() {
  let aberta = false;
  servidor.use(
    http.get("https://teste/api/v1/perfil", () =>
      aberta
        ? HttpResponse.json(perfilFicticio())
        : HttpResponse.json(
            {
              codigo: "nao_autenticado",
              mensagem: "Sua sessão terminou. Entre novamente.",
              idRequisicao: "00000000-0000-4000-8000-000000000001",
            },
            { status: 401 },
          ),
    ),
    http.post("https://teste/api/v1/auth/cadastro", () => {
      aberta = true;
      return HttpResponse.json(perfilFicticio(), { status: 201 });
    }),
    http.post("https://teste/api/v1/auth/entrada", () => {
      aberta = true;
      return HttpResponse.json(perfilFicticio());
    }),
    http.post("https://teste/api/v1/auth/saida", () => {
      aberta = false;
      return new HttpResponse(null, { status: 204 });
    }),
  );
}

it("T039: entrar leva à trilha vazia e sair volta à entrada", async () => {
  simularSessao();
  const usuario = userEvent.setup();
  const { roteador } = renderizarComRoteador("/entrar");

  await usuario.type(await screen.findByLabelText(/^E-mail/), "estudante@exemplo.com");
  await usuario.type(screen.getByLabelText(/^Senha/), "uma frase longa e incomum");
  await usuario.click(screen.getByRole("button", { name: "Entrar" }));

  expect(await screen.findByRole("heading", { name: "Seus estudos" })).toBeInTheDocument();
  expect(screen.getByText(/ainda não tem cartões/i)).toBeInTheDocument();
  expect(roteador.state.location.pathname).toBe("/");

  await usuario.click(screen.getByRole("button", { name: "Sair" }));
  expect(await screen.findByRole("heading", { name: "Entrar" })).toBeInTheDocument();
  expect(roteador.state.location.pathname).toBe("/entrar");

  // O cache foi limpo: voltar à área protegida pergunta de novo ao servidor e é barrado.
  await roteador.navigate({ to: "/" });
  await waitFor(() => {
    expect(roteador.state.location.pathname).toBe("/entrar");
  });
});

it("T039: cadastrar leva à trilha vazia", async () => {
  simularSessao();
  const usuario = userEvent.setup();
  const { roteador } = renderizarComRoteador("/cadastro");

  await usuario.type(await screen.findByLabelText(/^Nome/), "Estudante Exemplo");
  await usuario.type(screen.getByLabelText(/^E-mail/), "estudante@exemplo.com");
  await usuario.type(screen.getByLabelText(/^Senha/), "uma frase longa e incomum");
  await usuario.click(screen.getByRole("button", { name: "Criar conta" }));

  expect(await screen.findByRole("heading", { name: "Seus estudos" })).toBeInTheDocument();
  expect(roteador.state.location.pathname).toBe("/");
});

it("T039: as telas públicas se ligam e têm o título e o aviso de privacidade esperados", async () => {
  simularSessao();
  const usuario = userEvent.setup();
  renderizarComRoteador("/entrar");

  expect(await screen.findByRole("heading", { name: "Entrar" })).toBeInTheDocument();
  await usuario.click(screen.getByRole("link", { name: /criar conta/i }));
  expect(await screen.findByRole("heading", { name: "Criar conta" })).toBeInTheDocument();
  expect(screen.getByRole("note", { name: /privacidade/i })).toBeInTheDocument();
  await usuario.click(screen.getByRole("link", { name: /já tenho conta/i }));
  expect(await screen.findByRole("heading", { name: "Entrar" })).toBeInTheDocument();
});

it("T039 / RQ-004: as telas de entrada, de cadastro e a trilha vazia não têm violações do axe", async () => {
  simularSessao();
  const usuario = userEvent.setup();
  const { container, roteador } = renderizarComRoteador("/entrar");
  await screen.findByRole("heading", { name: "Entrar" });
  expect((await axe(container)).violations).toEqual([]);

  await roteador.navigate({ to: "/cadastro" });
  await screen.findByRole("heading", { name: "Criar conta" });
  expect((await axe(container)).violations).toEqual([]);

  await usuario.type(screen.getByLabelText(/^Nome/), "Estudante Exemplo");
  await usuario.type(screen.getByLabelText(/^E-mail/), "estudante@exemplo.com");
  await usuario.type(screen.getByLabelText(/^Senha/), "uma frase longa e incomum");
  await usuario.click(screen.getByRole("button", { name: "Criar conta" }));
  await screen.findByRole("heading", { name: "Seus estudos" });
  expect((await axe(container)).violations).toEqual([]);
});

it("T039: falha ao sair mantém o estudante na área e avisa", async () => {
  simularSessao();
  servidor.use(
    http.post("https://teste/api/v1/auth/saida", () => new HttpResponse(null, { status: 503 })),
  );
  const usuario = userEvent.setup();
  const { roteador } = renderizarComRoteador("/");
  await screen.findByRole("heading", { name: "Entrar" });
  await usuario.type(screen.getByLabelText(/^E-mail/), "estudante@exemplo.com");
  await usuario.type(screen.getByLabelText(/^Senha/), "uma frase longa e incomum");
  await usuario.click(screen.getByRole("button", { name: "Entrar" }));
  await screen.findByRole("heading", { name: "Seus estudos" });

  await usuario.click(screen.getByRole("button", { name: "Sair" }));
  expect(await screen.findByRole("alert")).toHaveTextContent(/não foi possível sair/i);
  expect(roteador.state.location.pathname).toBe("/");
});

it("T051: a tela de perfil carrega, salva só o que mudou e invalida a consulta do perfil", async () => {
  let atual = perfilFicticio();
  let leituras = 0;
  const recebidos: unknown[] = [];
  servidor.use(
    http.get("https://teste/api/v1/perfil", () => {
      leituras += 1;
      return HttpResponse.json(atual);
    }),
    http.patch("https://teste/api/v1/perfil", async ({ request }) => {
      const corpo = (await request.json()) as Record<string, unknown>;
      recebidos.push(corpo);
      atual = { ...atual, ...corpo };
      return HttpResponse.json(atual);
    }),
  );
  const usuario = userEvent.setup();
  const { roteador } = renderizarComRoteador("/");
  await screen.findByRole("heading", { name: "Seus estudos" });

  await usuario.click(screen.getByRole("link", { name: "Perfil" }));
  expect(await screen.findByRole("heading", { name: "Perfil" })).toBeInTheDocument();
  expect(roteador.state.location.pathname).toBe("/perfil");
  const campo = await screen.findByLabelText(/^Cartões por lição/);
  expect(campo).toHaveValue("10");

  const antes = leituras;
  await usuario.clear(campo);
  await usuario.type(campo, "12");
  await usuario.click(screen.getByRole("button", { name: "Salvar alterações" }));

  expect(await screen.findByRole("status")).toHaveTextContent("Alterações salvas.");
  expect(recebidos).toEqual([{ tamanhoLicao: 12 }]);
  await waitFor(() => {
    expect(leituras).toBeGreaterThan(antes);
  });
  expect(screen.getByLabelText(/^Cartões por lição/)).toHaveValue("12");
});

it("T051 / RQ-004: a tela de perfil não tem violações do axe", async () => {
  servidor.use(http.get("https://teste/api/v1/perfil", () => HttpResponse.json(perfilFicticio())));
  const { container } = renderizarComRoteador("/perfil");
  await screen.findByRole("heading", { name: "Perfil" });
  await screen.findByLabelText(/^Meta diária/);
  expect((await axe(container)).violations).toEqual([]);
});

it("T058: trocar a senha pela tela de perfil avisa o resultado", async () => {
  simularSessao();
  let corpo: unknown;
  servidor.use(
    http.post("https://teste/api/v1/perfil/senha", async ({ request }) => {
      corpo = await request.json();
      return new HttpResponse(null, { status: 204 });
    }),
  );
  const usuario = userEvent.setup();
  renderizarComRoteador("/entrar");
  await usuario.type(await screen.findByLabelText(/^E-mail/), "estudante@exemplo.com");
  await usuario.type(screen.getByLabelText(/^Senha/), "uma frase longa e incomum");
  await usuario.click(screen.getByRole("button", { name: "Entrar" }));
  await screen.findByRole("heading", { name: "Seus estudos" });

  await usuario.click(screen.getByRole("link", { name: "Perfil" }));
  const secao = await screen.findByRole("region", { name: "Segurança" });
  await usuario.type(within(secao).getByLabelText(/^Senha atual/), "uma frase longa e incomum");
  await usuario.type(within(secao).getByLabelText(/^Nova senha/), "outra frase longa e incomum");
  await usuario.click(within(secao).getByRole("button", { name: "Trocar senha" }));

  expect(await within(secao).findByRole("status")).toHaveTextContent(/sessões foram encerradas/i);
  expect(corpo).toEqual({
    senhaAtual: "uma frase longa e incomum",
    novaSenha: "outra frase longa e incomum",
  });
});

it("T058: excluir a conta limpa o cache e leva ao cadastro", async () => {
  simularSessao();
  servidor.use(
    http.post(
      "https://teste/api/v1/perfil/exclusao",
      () => new HttpResponse(null, { status: 204 }),
    ),
  );
  const usuario = userEvent.setup();
  const { roteador } = renderizarComRoteador("/entrar");
  await usuario.type(await screen.findByLabelText(/^E-mail/), "estudante@exemplo.com");
  await usuario.type(screen.getByLabelText(/^Senha/), "uma frase longa e incomum");
  await usuario.click(screen.getByRole("button", { name: "Entrar" }));
  await screen.findByRole("heading", { name: "Seus estudos" });
  await usuario.click(screen.getByRole("link", { name: "Perfil" }));
  await screen.findByRole("heading", { name: "Perfil" });
  const { queryClient } = roteador.options.context;
  expect(queryClient.getQueryData(["perfil"])).toBeDefined();

  await usuario.click(screen.getByRole("button", { name: "Excluir conta" }));
  const dialogo = await screen.findByRole("dialog");
  await usuario.type(within(dialogo).getByLabelText(/^Senha atual/), "uma frase longa e incomum");
  await usuario.click(within(dialogo).getByRole("button", { name: "Excluir definitivamente" }));

  expect(await screen.findByRole("heading", { name: "Criar conta" })).toBeInTheDocument();
  expect(roteador.state.location.pathname).toBe("/cadastro");
  expect(queryClient.getQueryData(["perfil"])).toBeUndefined();
});
