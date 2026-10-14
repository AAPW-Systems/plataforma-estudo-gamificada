import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { afterAll, afterEach, beforeAll, beforeEach, describe, expect, it, vi } from "vitest";
import { axe } from "vitest-axe";

import { servidor } from "../../testes/servidor";
import { perfilFicticio } from "../../testes/perfil";
import { FormularioCadastro } from "./FormularioCadastro";

const URL_CADASTRO = "https://teste/api/v1/auth/cadastro";

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
  // O cliente só pede um novo token anti-CSRF quando o cookie não existe.
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
  await usuario.type(screen.getByLabelText(/^Nome/), "Estudante Exemplo");
  await usuario.type(screen.getByLabelText(/^E-mail/), "estudante@exemplo.com");
  await usuario.type(screen.getByLabelText(/^Senha/), senha);
}

describe("FormularioCadastro (T038; US1)", () => {
  it("RF-013 / cenário 8: mostra o aviso de privacidade, sem caixa de aceite", () => {
    render(<FormularioCadastro aoConcluir={vi.fn()} />);
    const aviso = screen.getByRole("note", { name: /privacidade/i });
    expect(aviso).toHaveTextContent(/guarda/i);
    expect(aviso).toHaveTextContent(/provedor de IA externo/i);
    expect(screen.queryByRole("checkbox")).not.toBeInTheDocument();
  });

  it("envia os dados com o fuso detectado no navegador e entrega o perfil", async () => {
    const usuario = userEvent.setup();
    const aoConcluir = vi.fn();
    let corpo: unknown;
    servidor.use(
      http.post(URL_CADASTRO, async ({ request }) => {
        corpo = await request.json();
        return HttpResponse.json(perfilFicticio(), { status: 201 });
      }),
    );
    render(<FormularioCadastro aoConcluir={aoConcluir} />);
    await preencher(usuario);
    await usuario.click(screen.getByRole("button", { name: "Criar conta" }));

    await waitFor(() => {
      expect(aoConcluir).toHaveBeenCalledWith(perfilFicticio());
    });
    expect(corpo).toEqual({
      nome: "Estudante Exemplo",
      email: "estudante@exemplo.com",
      senha: "uma frase longa e incomum",
      fuso: Intl.DateTimeFormat().resolvedOptions().timeZone,
    });
  });

  it("cenário 2: o 422 aparece junto do campo, com foco nele e os valores preservados", async () => {
    const usuario = userEvent.setup();
    servidor.use(
      http.post(URL_CADASTRO, () =>
        HttpResponse.json(
          erro("dados_invalidos", "Alguns campos precisam de correção.", [
            { campo: "senha", mensagem: "Esta senha é muito comum. Escolha outra." },
          ]),
          { status: 422 },
        ),
      ),
    );
    render(<FormularioCadastro aoConcluir={vi.fn()} />);
    await preencher(usuario, "senhasenha123");
    await usuario.click(screen.getByRole("button", { name: "Criar conta" }));

    const campoSenha = await screen.findByLabelText(/^Senha/);
    await waitFor(() => expect(campoSenha).toHaveFocus());
    expect(campoSenha).toBeInvalid();
    expect(campoSenha).toHaveAccessibleDescription(/muito comum/i);
    expect(screen.getByLabelText(/^Nome/)).toHaveValue("Estudante Exemplo");
    expect(screen.getByLabelText(/^E-mail/)).toHaveValue("estudante@exemplo.com");
    expect(campoSenha).toHaveValue("senhasenha123");
  });

  it("valida no envio sem chamar a API e foca o primeiro campo com erro", async () => {
    const usuario = userEvent.setup();
    const chamadas = vi.fn();
    servidor.use(
      http.post(URL_CADASTRO, () => {
        chamadas();
        return HttpResponse.json(perfilFicticio(), { status: 201 });
      }),
    );
    render(<FormularioCadastro aoConcluir={vi.fn()} />);
    await usuario.click(screen.getByRole("button", { name: "Criar conta" }));

    expect(await screen.findAllByText(/informe|use pelo menos/i)).not.toHaveLength(0);
    expect(screen.getByLabelText(/^Nome/)).toHaveFocus();
    expect(screen.getByLabelText(/^Nome/)).toBeInvalid();
    expect(screen.getByLabelText(/^E-mail/)).toBeInvalid();
    expect(screen.getByLabelText(/^Senha/)).toBeInvalid();
    expect(chamadas).not.toHaveBeenCalled();
  });

  it("os limites vêm do contrato: senha curta e nome longo são recusados na interface", async () => {
    const usuario = userEvent.setup();
    render(<FormularioCadastro aoConcluir={vi.fn()} />);
    await usuario.type(screen.getByLabelText(/^Nome/), "n".repeat(101));
    await usuario.type(screen.getByLabelText(/^E-mail/), "estudante@exemplo.com");
    await usuario.type(screen.getByLabelText(/^Senha/), "1234567");
    await usuario.click(screen.getByRole("button", { name: "Criar conta" }));

    expect(await screen.findByText("Use no máximo 100 caracteres.")).toBeInTheDocument();
    expect(screen.getByText("Use pelo menos 8 caracteres.")).toBeInTheDocument();
  });

  it("cenário 7: o 409 mostra que o e-mail já está em uso junto do campo", async () => {
    const usuario = userEvent.setup();
    servidor.use(
      http.post(URL_CADASTRO, () =>
        HttpResponse.json(
          erro("email_em_uso", "Este e-mail já está em uso.", [
            { campo: "email", mensagem: "Este e-mail já está em uso." },
          ]),
          { status: 409 },
        ),
      ),
    );
    render(<FormularioCadastro aoConcluir={vi.fn()} />);
    await preencher(usuario);
    await usuario.click(screen.getByRole("button", { name: "Criar conta" }));

    const campo = await screen.findByLabelText(/^E-mail/);
    await waitFor(() => expect(campo).toHaveAccessibleDescription("Este e-mail já está em uso."));
    expect(campo).toHaveFocus();
    expect(screen.getByLabelText(/^Nome/)).toHaveValue("Estudante Exemplo");
  });

  it("o 429 indica que é preciso tentar mais tarde", async () => {
    const usuario = userEvent.setup();
    servidor.use(
      http.post(URL_CADASTRO, () =>
        HttpResponse.json(
          erro("muitas_tentativas", "Muitas tentativas. Tente de novo em alguns minutos."),
          { status: 429, headers: { "Retry-After": "600" } },
        ),
      ),
    );
    render(<FormularioCadastro aoConcluir={vi.fn()} />);
    await preencher(usuario);
    await usuario.click(screen.getByRole("button", { name: "Criar conta" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(/tente de novo em alguns minutos/i);
    expect(screen.getByLabelText(/^E-mail/)).toHaveValue("estudante@exemplo.com");
  });

  it("falha do servidor mostra uma mensagem e permite tentar de novo", async () => {
    const usuario = userEvent.setup();
    servidor.use(http.post(URL_CADASTRO, () => new HttpResponse(null, { status: 503 })));
    render(<FormularioCadastro aoConcluir={vi.fn()} />);
    await preencher(usuario);
    await usuario.click(screen.getByRole("button", { name: "Criar conta" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(/não foi possível/i);
    expect(screen.getByRole("button", { name: "Criar conta" })).toBeEnabled();
  });

  it("impede o envio duplicado enquanto a requisição está em andamento", async () => {
    const usuario = userEvent.setup();
    let recebidas = 0;
    let liberar: () => void = () => undefined;
    const espera = new Promise<void>((resolver) => {
      liberar = resolver;
    });
    servidor.use(
      http.post(URL_CADASTRO, async () => {
        recebidas += 1;
        await espera;
        return HttpResponse.json(perfilFicticio(), { status: 201 });
      }),
    );
    const aoConcluir = vi.fn();
    render(<FormularioCadastro aoConcluir={aoConcluir} />);
    await preencher(usuario);
    const botao = screen.getByRole("button", { name: "Criar conta" });
    await usuario.click(botao);

    const ocupado = await screen.findByRole("button", { name: /aguarde/i });
    expect(ocupado).toBeDisabled();
    await usuario.click(ocupado);
    liberar();
    await waitFor(() => {
      expect(aoConcluir).toHaveBeenCalledTimes(1);
    });
    expect(recebidas).toBe(1);
  });

  it("RQ-004: não tem violações do axe, vazio nem com erros", async () => {
    const usuario = userEvent.setup();
    const { container } = render(<FormularioCadastro aoConcluir={vi.fn()} />);
    expect((await axe(container)).violations).toEqual([]);

    await usuario.click(screen.getByRole("button", { name: "Criar conta" }));
    await screen.findAllByText(/informe/i);
    expect((await axe(container)).violations).toEqual([]);
  });
});
