import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { afterAll, afterEach, beforeAll, beforeEach, describe, expect, it, vi } from "vitest";
import { axe } from "vitest-axe";

import { perfilFicticio } from "../../testes/perfil";
import { servidor } from "../../testes/servidor";
import { FormularioPerfil } from "./FormularioPerfil";

const URL_PERFIL = "https://teste/api/v1/perfil";

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

function capturar(resposta: () => Response | Promise<Response>) {
  const recebidos: unknown[] = [];
  servidor.use(
    http.patch(URL_PERFIL, async ({ request }) => {
      recebidos.push(await request.json());
      return resposta();
    }),
  );
  return recebidos;
}

async function digitar(usuario: ReturnType<typeof userEvent.setup>, rotulo: RegExp, valor: string) {
  const campo = screen.getByLabelText(rotulo);
  await usuario.clear(campo);
  await usuario.type(campo, valor);
}

describe("FormularioPerfil (T050; US3)", () => {
  it("cenário 1: mostra os valores atuais e explica a retenção em linguagem simples", () => {
    render(<FormularioPerfil perfil={perfilFicticio()} aoSalvar={vi.fn()} />);
    expect(screen.getByLabelText(/^Nome/)).toHaveValue("Estudante Exemplo");
    expect(screen.getByLabelText(/^Fuso/)).toHaveValue("America/Recife");
    expect(screen.getByLabelText(/^Meta diária/)).toHaveValue("20");
    expect(screen.getByLabelText(/^Cartões por lição/)).toHaveValue("10");
    expect(screen.getByLabelText(/^Cartões novos por dia/)).toHaveValue("20");
    const retencao = screen.getByLabelText(/^Retenção desejada/);
    expect(retencao).toHaveValue("0,90");
    expect(screen.getByText("estudante@exemplo.com")).toBeInTheDocument();

    const explicacao = retencao.getAttribute("aria-describedby");
    expect(explicacao).toBeTruthy();
    const texto = retencao.ownerDocument.getElementById(
      explicacao?.split(" ")[0] ?? "",
    )?.textContent;
    expect(texto).toMatch(/chance de lembrar/i);
    expect(texto).toMatch(/aumentar/i);
    expect(texto).toMatch(/mais cedo/i);
    expect(texto).toMatch(/reduzir/i);
    expect(texto).toMatch(/próxima revisão/i);
  });

  it("envia só os campos alterados e entrega o perfil devolvido", async () => {
    const usuario = userEvent.setup();
    const salvo = perfilFicticio({ metaDiaria: 30 });
    const recebidos = capturar(() => HttpResponse.json(salvo));
    const aoSalvar = vi.fn();
    render(<FormularioPerfil perfil={perfilFicticio()} aoSalvar={aoSalvar} />);

    await digitar(usuario, /^Meta diária/, "30");
    await usuario.click(screen.getByRole("button", { name: "Salvar alterações" }));

    await waitFor(() => {
      expect(aoSalvar).toHaveBeenCalledWith(salvo);
    });
    expect(recebidos).toEqual([{ metaDiaria: 30 }]);
    expect(await screen.findByRole("status")).toHaveTextContent("Alterações salvas.");
  });

  it("aceita a retenção com vírgula ou ponto e a envia como número", async () => {
    const usuario = userEvent.setup();
    const recebidos = capturar(() => HttpResponse.json(perfilFicticio({ retencaoDesejada: 0.85 })));
    render(<FormularioPerfil perfil={perfilFicticio()} aoSalvar={vi.fn()} />);

    await digitar(usuario, /^Retenção desejada/, "0,85");
    await usuario.click(screen.getByRole("button", { name: "Salvar alterações" }));
    await waitFor(() => {
      expect(recebidos).toEqual([{ retencaoDesejada: 0.85 }]);
    });
  });

  it("sem alteração não chama a API e avisa", async () => {
    const usuario = userEvent.setup();
    const recebidos = capturar(() => HttpResponse.json(perfilFicticio()));
    render(<FormularioPerfil perfil={perfilFicticio()} aoSalvar={vi.fn()} />);

    await usuario.click(screen.getByRole("button", { name: "Salvar alterações" }));
    expect(await screen.findByRole("status")).toHaveTextContent(/nada para salvar/i);
    expect(recebidos).toEqual([]);
  });

  it("cenário 2: valores fora dos limites do contrato são recusados na interface, junto do campo", async () => {
    const usuario = userEvent.setup();
    const recebidos = capturar(() => HttpResponse.json(perfilFicticio()));
    render(<FormularioPerfil perfil={perfilFicticio()} aoSalvar={vi.fn()} />);

    await digitar(usuario, /^Meta diária/, "0");
    await digitar(usuario, /^Cartões por lição/, "51");
    await digitar(usuario, /^Retenção desejada/, "0,99");
    await usuario.click(screen.getByRole("button", { name: "Salvar alterações" }));

    expect(await screen.findByText("Use um valor de 1 a 200.")).toBeInTheDocument();
    expect(screen.getByText("Use um valor de 5 a 50.")).toBeInTheDocument();
    expect(screen.getByText(/com no máximo duas casas decimais/)).toBeInTheDocument();
    expect(screen.getByLabelText(/^Meta diária/)).toBeInvalid();
    expect(screen.getByLabelText(/^Meta diária/)).toHaveFocus();
    expect(recebidos).toEqual([]);
  });

  it("cenário 2: o 422 do servidor aparece por campo, com foco no primeiro e valores preservados", async () => {
    const usuario = userEvent.setup();
    capturar(() =>
      HttpResponse.json(
        erro("dados_invalidos", "Alguns campos precisam de correção.", [
          { campo: "fuso", mensagem: "Fuso desconhecido." },
          { campo: "nome", mensagem: "Informe o nome." },
        ]),
        { status: 422 },
      ),
    );
    render(<FormularioPerfil perfil={perfilFicticio()} aoSalvar={vi.fn()} />);

    await digitar(usuario, /^Fuso/, "Marte/Phobos");
    await digitar(usuario, /^Meta diária/, "33");
    await usuario.click(screen.getByRole("button", { name: "Salvar alterações" }));

    const fuso = await screen.findByLabelText(/^Fuso/);
    await waitFor(() => expect(fuso).toHaveAccessibleDescription(/Fuso desconhecido\./));
    expect(screen.getByLabelText(/^Nome/)).toHaveAccessibleDescription(/Informe o nome\./);
    await waitFor(() => expect(screen.getByLabelText(/^Nome/)).toHaveFocus());
    expect(fuso).toHaveValue("Marte/Phobos");
    expect(screen.getByLabelText(/^Meta diária/)).toHaveValue("33");
  });

  it("falha do servidor mostra uma mensagem e mantém os valores digitados", async () => {
    const usuario = userEvent.setup();
    capturar(() => new HttpResponse(null, { status: 503 }));
    render(<FormularioPerfil perfil={perfilFicticio()} aoSalvar={vi.fn()} />);

    await digitar(usuario, /^Meta diária/, "45");
    await usuario.click(screen.getByRole("button", { name: "Salvar alterações" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(/não foi possível/i);
    expect(screen.getByLabelText(/^Meta diária/)).toHaveValue("45");
    expect(screen.getByRole("button", { name: "Salvar alterações" })).toBeEnabled();
  });

  it("RQ-004: não tem violações do axe, em repouso nem com erros", async () => {
    const usuario = userEvent.setup();
    const { container } = render(<FormularioPerfil perfil={perfilFicticio()} aoSalvar={vi.fn()} />);
    expect((await axe(container)).violations).toEqual([]);

    await digitar(usuario, /^Meta diária/, "0");
    await usuario.click(screen.getByRole("button", { name: "Salvar alterações" }));
    await screen.findByText("Use um valor de 1 a 200.");
    expect((await axe(container)).violations).toEqual([]);
  });
});
