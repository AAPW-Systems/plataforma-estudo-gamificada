import { cleanup, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { afterAll, afterEach, beforeAll, beforeEach, describe, expect, it, vi } from "vitest";
import { axe } from "vitest-axe";

import { servidor } from "../../testes/servidor";
import { DialogoExclusao } from "./DialogoExclusao";

const URL_EXCLUSAO = "https://teste/api/v1/perfil/exclusao";

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

async function abrir(usuario: ReturnType<typeof userEvent.setup>) {
  await usuario.click(screen.getByRole("button", { name: "Excluir conta" }));
  return screen.findByRole("dialog");
}

describe("DialogoExclusao (T057; US4)", () => {
  it("cenário 3: explica que a exclusão é definitiva e o que é apagado", async () => {
    const usuario = userEvent.setup();
    render(<DialogoExclusao aoExcluir={vi.fn()} />);
    const dialogo = await abrir(usuario);

    expect(dialogo).toHaveAccessibleName(/excluir a conta/i);
    expect(dialogo).toHaveTextContent(/definitiva/i);
    for (const item of ["matérias", "fontes", "cartões", "revisões", "XP", "sequência"]) {
      expect(dialogo).toHaveTextContent(item);
    }
    expect(dialogo).toHaveTextContent(/senha atual/i);
    expect(
      within(dialogo).getByRole("button", { name: "Excluir definitivamente" }),
    ).toBeInTheDocument();
    expect(within(dialogo).getByRole("button", { name: "Cancelar" })).toBeInTheDocument();
  });

  it("exige a senha: sem ela, não chama a API e mostra o erro junto do campo", async () => {
    const usuario = userEvent.setup();
    const chamadas = vi.fn();
    servidor.use(
      http.post(URL_EXCLUSAO, () => {
        chamadas();
        return new HttpResponse(null, { status: 204 });
      }),
    );
    render(<DialogoExclusao aoExcluir={vi.fn()} />);
    const dialogo = await abrir(usuario);
    await usuario.click(within(dialogo).getByRole("button", { name: "Excluir definitivamente" }));

    expect(await within(dialogo).findByText("Informe a senha atual.")).toBeInTheDocument();
    expect(within(dialogo).getByLabelText(/^Senha atual/)).toHaveFocus();
    expect(chamadas).not.toHaveBeenCalled();
  });

  it("prende o foco dentro do diálogo e o devolve ao acionador ao cancelar", async () => {
    const usuario = userEvent.setup();
    render(<DialogoExclusao aoExcluir={vi.fn()} />);
    const acionador = screen.getByRole("button", { name: "Excluir conta" });
    const dialogo = await abrir(usuario);
    expect(dialogo).toContainElement(document.activeElement as HTMLElement);

    for (let i = 0; i < 8; i += 1) {
      await usuario.tab();
      expect(dialogo).toContainElement(document.activeElement as HTMLElement);
    }
    await usuario.click(within(dialogo).getByRole("button", { name: "Cancelar" }));
    await waitFor(() => {
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    });
    await waitFor(() => {
      expect(acionador).toHaveFocus();
    });
  });

  it("Escape fecha o diálogo sem excluir nada", async () => {
    const usuario = userEvent.setup();
    const aoExcluir = vi.fn();
    render(<DialogoExclusao aoExcluir={aoExcluir} />);
    await abrir(usuario);
    await usuario.keyboard("{Escape}");
    await waitFor(() => {
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    });
    expect(aoExcluir).not.toHaveBeenCalled();
  });

  it("cenário 3: senha incorreta aparece no diálogo, que continua aberto, sem excluir", async () => {
    const usuario = userEvent.setup();
    servidor.use(
      http.post(URL_EXCLUSAO, () =>
        HttpResponse.json(
          erro("senha_atual_incorreta", "A senha atual está incorreta.", [
            { campo: "senhaAtual", mensagem: "A senha atual está incorreta." },
          ]),
          { status: 422 },
        ),
      ),
    );
    const aoExcluir = vi.fn();
    render(<DialogoExclusao aoExcluir={aoExcluir} />);
    const dialogo = await abrir(usuario);
    await usuario.type(within(dialogo).getByLabelText(/^Senha atual/), "errada-errada-1");
    await usuario.click(within(dialogo).getByRole("button", { name: "Excluir definitivamente" }));

    const campo = await within(dialogo).findByLabelText(/^Senha atual/);
    await waitFor(() => expect(campo).toHaveAccessibleDescription(/está incorreta/i));
    await waitFor(() => expect(campo).toHaveFocus());
    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(aoExcluir).not.toHaveBeenCalled();
  });

  it("cenário 4: com a senha certa, envia a senha, exclui e avisa a tela", async () => {
    const usuario = userEvent.setup();
    let corpo: unknown;
    servidor.use(
      http.post(URL_EXCLUSAO, async ({ request }) => {
        corpo = await request.json();
        return new HttpResponse(null, { status: 204 });
      }),
    );
    const aoExcluir = vi.fn();
    render(<DialogoExclusao aoExcluir={aoExcluir} />);
    const dialogo = await abrir(usuario);
    await usuario.type(within(dialogo).getByLabelText(/^Senha atual/), "senha atual do estudante");
    await usuario.click(within(dialogo).getByRole("button", { name: "Excluir definitivamente" }));

    await waitFor(() => {
      expect(aoExcluir).toHaveBeenCalledTimes(1);
    });
    expect(corpo).toEqual({ senhaAtual: "senha atual do estudante" });
  });

  it("o 429 mostra que é preciso tentar mais tarde, sem fechar o diálogo", async () => {
    const usuario = userEvent.setup();
    servidor.use(
      http.post(URL_EXCLUSAO, () =>
        HttpResponse.json(
          erro("muitas_tentativas", "Muitas tentativas. Tente de novo em alguns minutos."),
          { status: 429, headers: { "Retry-After": "600" } },
        ),
      ),
    );
    render(<DialogoExclusao aoExcluir={vi.fn()} />);
    const dialogo = await abrir(usuario);
    await usuario.type(within(dialogo).getByLabelText(/^Senha atual/), "qualquer senha");
    await usuario.click(within(dialogo).getByRole("button", { name: "Excluir definitivamente" }));
    expect(await within(dialogo).findByRole("alert")).toHaveTextContent(/alguns minutos/i);
  });

  it("impede o envio duplicado enquanto a exclusão está em andamento", async () => {
    const usuario = userEvent.setup();
    let recebidas = 0;
    let liberar: () => void = () => undefined;
    const espera = new Promise<void>((resolver) => {
      liberar = resolver;
    });
    servidor.use(
      http.post(URL_EXCLUSAO, async () => {
        recebidas += 1;
        await espera;
        return new HttpResponse(null, { status: 204 });
      }),
    );
    const aoExcluir = vi.fn();
    render(<DialogoExclusao aoExcluir={aoExcluir} />);
    const dialogo = await abrir(usuario);
    await usuario.type(within(dialogo).getByLabelText(/^Senha atual/), "senha atual do estudante");
    await usuario.click(within(dialogo).getByRole("button", { name: "Excluir definitivamente" }));

    const ocupado = await within(dialogo).findByRole("button", { name: /aguarde/i });
    expect(ocupado).toBeDisabled();
    await usuario.keyboard("{Escape}");
    expect(screen.getByRole("dialog")).toBeInTheDocument();
    liberar();
    await waitFor(() => {
      expect(aoExcluir).toHaveBeenCalledTimes(1);
    });
    expect(recebidas).toBe(1);
  });

  it("RQ-004: não tem violações do axe, fechado nem aberto nem com erro", async () => {
    const usuario = userEvent.setup();
    const { container } = render(<DialogoExclusao aoExcluir={vi.fn()} />);
    expect((await axe(container)).violations).toEqual([]);
    const dialogo = await abrir(usuario);
    expect((await axe(document.body)).violations).toEqual([]);
    await usuario.click(within(dialogo).getByRole("button", { name: "Excluir definitivamente" }));
    await within(dialogo).findByText("Informe a senha atual.");
    expect((await axe(document.body)).violations).toEqual([]);
  });
});
