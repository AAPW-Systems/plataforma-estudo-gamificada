import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { afterAll, afterEach, beforeAll, beforeEach, describe, expect, it, vi } from "vitest";
import { axe } from "vitest-axe";

import { servidor } from "../../testes/servidor";
import { perfilFicticio } from "../../testes/perfil";
import { FormularioEntrada } from "./FormularioEntrada";

const URL_ENTRADA = "https://teste/api/v1/auth/entrada";

function erro(codigo: string, mensagem: string) {
  return { codigo, mensagem, idRequisicao: "00000000-0000-4000-8000-000000000001" };
}

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

async function preencher(
  usuario: ReturnType<typeof userEvent.setup>,
  senha = "uma frase longa e incomum",
) {
  await usuario.type(screen.getByLabelText(/^E-mail/), "estudante@exemplo.com");
  await usuario.type(screen.getByLabelText(/^Senha/), senha);
}

describe("FormularioEntrada (T038; US1)", () => {
  it("cenário 3: envia e-mail e senha e entrega o perfil", async () => {
    const usuario = userEvent.setup();
    const aoConcluir = vi.fn();
    let corpo: unknown;
    servidor.use(
      http.post(URL_ENTRADA, async ({ request }) => {
        corpo = await request.json();
        return HttpResponse.json(perfilFicticio());
      }),
    );
    render(<FormularioEntrada aoConcluir={aoConcluir} />);
    await preencher(usuario);
    await usuario.click(screen.getByRole("button", { name: "Entrar" }));

    await waitFor(() => {
      expect(aoConcluir).toHaveBeenCalledWith(perfilFicticio());
    });
    expect(corpo).toEqual({ email: "estudante@exemplo.com", senha: "uma frase longa e incomum" });
  });

  it("cenário 4: o 401 mostra uma mensagem neutra, sem apontar o e-mail nem a senha", async () => {
    const usuario = userEvent.setup();
    servidor.use(
      http.post(URL_ENTRADA, () =>
        HttpResponse.json(erro("credenciais_invalidas", "E-mail ou senha incorretos."), {
          status: 401,
        }),
      ),
    );
    render(<FormularioEntrada aoConcluir={vi.fn()} />);
    await preencher(usuario, "senha-incorreta-123");
    await usuario.click(screen.getByRole("button", { name: "Entrar" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("E-mail ou senha incorretos.");
    expect(screen.getByLabelText(/^E-mail/)).toBeValid();
    expect(screen.getByLabelText(/^Senha/)).toBeValid();
    expect(screen.getByLabelText(/^E-mail/)).toHaveValue("estudante@exemplo.com");
    expect(screen.getByLabelText(/^Senha/)).toHaveFocus();
  });

  it("a mensagem do 401 é a mesma para qualquer e-mail", async () => {
    const usuario = userEvent.setup();
    servidor.use(
      http.post(URL_ENTRADA, () =>
        HttpResponse.json(erro("credenciais_invalidas", "E-mail ou senha incorretos."), {
          status: 401,
        }),
      ),
    );
    render(<FormularioEntrada aoConcluir={vi.fn()} />);
    const mensagens: (string | null)[] = [];
    for (const email of ["existe@exemplo.com", "nao.existe@exemplo.com"]) {
      await usuario.clear(screen.getByLabelText(/^E-mail/));
      await usuario.type(screen.getByLabelText(/^E-mail/), email);
      await usuario.clear(screen.getByLabelText(/^Senha/));
      await usuario.type(screen.getByLabelText(/^Senha/), "senha-incorreta-123");
      await usuario.click(screen.getByRole("button", { name: "Entrar" }));
      mensagens.push((await screen.findByRole("alert")).textContent);
    }
    expect(mensagens[0]).toBe(mensagens[1]);
  });

  it("cenário 6: o 429 indica que é preciso tentar mais tarde", async () => {
    const usuario = userEvent.setup();
    servidor.use(
      http.post(URL_ENTRADA, () =>
        HttpResponse.json(
          erro("muitas_tentativas", "Muitas tentativas. Tente de novo em alguns minutos."),
          { status: 429, headers: { "Retry-After": "900" } },
        ),
      ),
    );
    render(<FormularioEntrada aoConcluir={vi.fn()} />);
    await preencher(usuario);
    await usuario.click(screen.getByRole("button", { name: "Entrar" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(/tente de novo em alguns minutos/i);
    expect(screen.getByLabelText(/^E-mail/)).toHaveValue("estudante@exemplo.com");
  });

  it("valida no envio sem chamar a API e foca o primeiro campo com erro", async () => {
    const usuario = userEvent.setup();
    const chamadas = vi.fn();
    servidor.use(
      http.post(URL_ENTRADA, () => {
        chamadas();
        return HttpResponse.json(perfilFicticio());
      }),
    );
    render(<FormularioEntrada aoConcluir={vi.fn()} />);
    await usuario.click(screen.getByRole("button", { name: "Entrar" }));

    expect(await screen.findAllByText(/informe/i)).not.toHaveLength(0);
    expect(screen.getByLabelText(/^E-mail/)).toHaveFocus();
    expect(screen.getByLabelText(/^E-mail/)).toBeInvalid();
    expect(chamadas).not.toHaveBeenCalled();
  });

  it("falha do servidor mostra uma mensagem e permite tentar de novo", async () => {
    const usuario = userEvent.setup();
    servidor.use(http.post(URL_ENTRADA, () => new HttpResponse(null, { status: 503 })));
    render(<FormularioEntrada aoConcluir={vi.fn()} />);
    await preencher(usuario);
    await usuario.click(screen.getByRole("button", { name: "Entrar" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(/não foi possível/i);
    expect(screen.getByRole("button", { name: "Entrar" })).toBeEnabled();
  });

  it("RQ-004: não tem violações do axe, vazio nem com erro", async () => {
    const usuario = userEvent.setup();
    const { container } = render(<FormularioEntrada aoConcluir={vi.fn()} />);
    expect((await axe(container)).violations).toEqual([]);

    await usuario.click(screen.getByRole("button", { name: "Entrar" }));
    await screen.findAllByText(/informe/i);
    expect((await axe(container)).violations).toEqual([]);
  });
});
