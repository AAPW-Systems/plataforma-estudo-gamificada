import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { afterAll, afterEach, beforeAll, beforeEach, describe, expect, it, vi } from "vitest";
import { axe } from "vitest-axe";

import { servidor } from "../../testes/servidor";
import { FormularioSenha } from "./FormularioSenha";

const URL_SENHA = "https://teste/api/v1/perfil/senha";

function erro(codigo: string, mensagem: string, campos?: { campo: string; mensagem: string }[]) {
  return {
    codigo,
    mensagem,
    ...(campos ? { campos } : {}),
    idRequisicao: "00000000-0000-4000-8000-000000000001",
  };
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
  atual = "senha atual do estudante",
  nova = "uma senha nova bem longa",
) {
  await usuario.type(screen.getByLabelText(/^Senha atual/), atual);
  await usuario.type(screen.getByLabelText(/^Nova senha/), nova);
}

describe("FormularioSenha (T057; US4)", () => {
  it("cenário 1: envia as duas senhas, avisa que as outras sessões terminaram e limpa os campos", async () => {
    const usuario = userEvent.setup();
    let corpo: unknown;
    servidor.use(
      http.post(URL_SENHA, async ({ request }) => {
        corpo = await request.json();
        return new HttpResponse(null, { status: 204 });
      }),
    );
    const aoTrocar = vi.fn();
    render(<FormularioSenha aoTrocar={aoTrocar} />);
    await preencher(usuario);
    await usuario.click(screen.getByRole("button", { name: "Trocar senha" }));

    expect(await screen.findByRole("status")).toHaveTextContent(/outras sessões foram encerradas/i);
    expect(corpo).toEqual({
      senhaAtual: "senha atual do estudante",
      novaSenha: "uma senha nova bem longa",
    });
    expect(aoTrocar).toHaveBeenCalledTimes(1);
    expect(screen.getByLabelText(/^Senha atual/)).toHaveValue("");
    expect(screen.getByLabelText(/^Nova senha/)).toHaveValue("");
  });

  it("cenário 2: senha atual incorreta aparece junto do campo, com foco, e a nova senha é mantida", async () => {
    const usuario = userEvent.setup();
    servidor.use(
      http.post(URL_SENHA, () =>
        HttpResponse.json(
          erro("senha_atual_incorreta", "A senha atual está incorreta.", [
            { campo: "senhaAtual", mensagem: "A senha atual está incorreta." },
          ]),
          { status: 422 },
        ),
      ),
    );
    const aoTrocar = vi.fn();
    render(<FormularioSenha aoTrocar={aoTrocar} />);
    await preencher(usuario, "errada-errada-1");
    await usuario.click(screen.getByRole("button", { name: "Trocar senha" }));

    const atual = await screen.findByLabelText(/^Senha atual/);
    await waitFor(() => expect(atual).toHaveAccessibleDescription(/está incorreta/i));
    await waitFor(() => expect(atual).toHaveFocus());
    expect(screen.getByLabelText(/^Nova senha/)).toHaveValue("uma senha nova bem longa");
    expect(aoTrocar).not.toHaveBeenCalled();
    expect(screen.queryByRole("status")).not.toBeInTheDocument();
  });

  it("nova senha recusada pelo servidor aparece junto do campo da nova senha", async () => {
    const usuario = userEvent.setup();
    servidor.use(
      http.post(URL_SENHA, () =>
        HttpResponse.json(
          erro("dados_invalidos", "Alguns campos precisam de correção.", [
            { campo: "novaSenha", mensagem: "Esta senha é muito comum. Escolha outra." },
          ]),
          { status: 422 },
        ),
      ),
    );
    render(<FormularioSenha aoTrocar={vi.fn()} />);
    await preencher(usuario, "senha atual do estudante", "senhasenha123");
    await usuario.click(screen.getByRole("button", { name: "Trocar senha" }));

    const nova = await screen.findByLabelText(/^Nova senha/);
    await waitFor(() => expect(nova).toHaveAccessibleDescription(/muito comum/i));
    await waitFor(() => expect(nova).toHaveFocus());
  });

  it("valida no envio sem chamar a API: obrigatórias e limites de tamanho do contrato", async () => {
    const usuario = userEvent.setup();
    const chamadas = vi.fn();
    servidor.use(
      http.post(URL_SENHA, () => {
        chamadas();
        return new HttpResponse(null, { status: 204 });
      }),
    );
    render(<FormularioSenha aoTrocar={vi.fn()} />);
    await usuario.click(screen.getByRole("button", { name: "Trocar senha" }));
    expect(await screen.findByText("Informe a senha atual.")).toBeInTheDocument();
    expect(screen.getByLabelText(/^Senha atual/)).toHaveFocus();

    await usuario.type(screen.getByLabelText(/^Senha atual/), "qualquer");
    await usuario.type(screen.getByLabelText(/^Nova senha/), "1234567");
    await usuario.click(screen.getByRole("button", { name: "Trocar senha" }));
    expect(await screen.findByText("Use pelo menos 8 caracteres.")).toBeInTheDocument();
    expect(chamadas).not.toHaveBeenCalled();
  });

  it("o 429 indica que é preciso tentar mais tarde", async () => {
    const usuario = userEvent.setup();
    servidor.use(
      http.post(URL_SENHA, () =>
        HttpResponse.json(
          erro("muitas_tentativas", "Muitas tentativas. Tente de novo em alguns minutos."),
          { status: 429, headers: { "Retry-After": "600" } },
        ),
      ),
    );
    render(<FormularioSenha aoTrocar={vi.fn()} />);
    await preencher(usuario);
    await usuario.click(screen.getByRole("button", { name: "Trocar senha" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(/tente de novo em alguns minutos/i);
  });

  it("os campos de senha são do tipo senha e usam o preenchimento certo do navegador", () => {
    render(<FormularioSenha aoTrocar={vi.fn()} />);
    const atual = screen.getByLabelText(/^Senha atual/);
    const nova = screen.getByLabelText(/^Nova senha/);
    expect(atual).toHaveAttribute("type", "password");
    expect(atual).toHaveAttribute("autocomplete", "current-password");
    expect(nova).toHaveAttribute("type", "password");
    expect(nova).toHaveAttribute("autocomplete", "new-password");
  });

  it("RQ-004: não tem violações do axe, vazio nem com erros", async () => {
    const usuario = userEvent.setup();
    const { container } = render(<FormularioSenha aoTrocar={vi.fn()} />);
    expect((await axe(container)).violations).toEqual([]);
    await usuario.click(screen.getByRole("button", { name: "Trocar senha" }));
    await screen.findByText("Informe a senha atual.");
    expect((await axe(container)).violations).toEqual([]);
  });
});
