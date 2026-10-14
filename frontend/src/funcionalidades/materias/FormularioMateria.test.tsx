import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { describe, expect, it, vi } from "vitest";
import { axe } from "vitest-axe";

import {
  BASE,
  configurarServidorDeTestes,
  corpoErro,
  materiaFicticia,
  renderizarComConsultas,
} from "../../testes/acervo";
import { servidor } from "../../testes/servidor";
import { FormularioMateria } from "./FormularioMateria";

configurarServidorDeTestes();

function capturar(resposta: () => Response | Promise<Response>) {
  const recebidos: unknown[] = [];
  servidor.use(
    http.post(`${BASE}/materias`, async ({ request }) => {
      recebidos.push(await request.json());
      return resposta();
    }),
  );
  return recebidos;
}

describe("FormularioMateria (T029; US1 cenário 1, US3 cenário 2)", () => {
  it("cria a matéria, avisa quem chamou e limpa o campo", async () => {
    const recebidos = capturar(() =>
      HttpResponse.json(materiaFicticia({ nome: "Biologia" }), { status: 201 }),
    );
    const aoCriar = vi.fn();
    const usuario = userEvent.setup();
    renderizarComConsultas(<FormularioMateria aoCriar={aoCriar} />);

    await usuario.type(screen.getByLabelText(/^Nome da matéria/), "  Biologia ");
    await usuario.click(screen.getByRole("button", { name: "Criar matéria" }));

    await waitFor(() => {
      expect(aoCriar).toHaveBeenCalledWith(expect.objectContaining({ nome: "Biologia" }));
    });
    expect(recebidos).toEqual([{ nome: "Biologia" }]);
    expect(screen.getByLabelText(/^Nome da matéria/)).toHaveValue("");
  });

  it('sem matérias, a ação se chama "Criar primeira matéria"', () => {
    renderizarComConsultas(<FormularioMateria primeira aoCriar={vi.fn()} />);
    expect(screen.getByRole("button", { name: "Criar primeira matéria" })).toBeInTheDocument();
  });

  it("nome vazio é recusado junto do campo, sem chamar o servidor", async () => {
    const recebidos = capturar(() => HttpResponse.json(materiaFicticia(), { status: 201 }));
    const usuario = userEvent.setup();
    renderizarComConsultas(<FormularioMateria aoCriar={vi.fn()} />);

    await usuario.click(screen.getByRole("button", { name: "Criar matéria" }));

    const campo = screen.getByLabelText(/^Nome da matéria/);
    expect(await screen.findByText("Informe o nome da matéria.")).toBeVisible();
    expect(campo).toHaveAttribute("aria-invalid", "true");
    expect(recebidos).toEqual([]);
  });

  it("422 do servidor aparece junto do campo, com o valor preservado e o foco nele", async () => {
    capturar(() =>
      HttpResponse.json(
        corpoErro("validacao_falhou", "Dados inválidos.", [
          { campo: "nome", mensagem: "Use apenas letras, números e pontuação comum." },
        ]),
        { status: 422 },
      ),
    );
    const usuario = userEvent.setup();
    renderizarComConsultas(<FormularioMateria aoCriar={vi.fn()} />);

    const campo = screen.getByLabelText(/^Nome da matéria/);
    await usuario.type(campo, "Bio‮logia");
    await usuario.click(screen.getByRole("button", { name: "Criar matéria" }));

    expect(await screen.findByText("Use apenas letras, números e pontuação comum.")).toBeVisible();
    expect(campo).toHaveValue("Bio‮logia");
    expect(campo).toHaveFocus();
  });

  it("409 de nome em uso aparece junto do campo, com o valor digitado preservado", async () => {
    capturar(() =>
      HttpResponse.json(
        corpoErro("nome_em_uso", "Você já tem uma matéria com esse nome.", [
          { campo: "nome", mensagem: "Você já tem uma matéria com esse nome." },
        ]),
        { status: 409 },
      ),
    );
    const usuario = userEvent.setup();
    renderizarComConsultas(<FormularioMateria aoCriar={vi.fn()} />);

    const campo = screen.getByLabelText(/^Nome da matéria/);
    await usuario.type(campo, "biologia");
    await usuario.click(screen.getByRole("button", { name: "Criar matéria" }));

    expect(await screen.findByText("Você já tem uma matéria com esse nome.")).toBeVisible();
    expect(campo).toHaveValue("biologia");
    expect(campo).toHaveAttribute("aria-invalid", "true");
  });

  it("falha sem campo (cota, 403) vira mensagem do formulário", async () => {
    capturar(() =>
      HttpResponse.json(corpoErro("cota_materias_excedida", "Você atingiu o limite de matérias."), {
        status: 409,
      }),
    );
    const usuario = userEvent.setup();
    renderizarComConsultas(<FormularioMateria aoCriar={vi.fn()} />);

    await usuario.type(screen.getByLabelText(/^Nome da matéria/), "Química");
    await usuario.click(screen.getByRole("button", { name: "Criar matéria" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Você atingiu o limite de matérias.",
    );
  });

  it("não envia duas vezes enquanto a criação está em andamento", async () => {
    let liberar: () => void = () => undefined;
    const portao = new Promise<void>((resolver) => {
      liberar = resolver;
    });
    const recebidos = capturar(async () => {
      await portao;
      return HttpResponse.json(materiaFicticia(), { status: 201 });
    });
    const usuario = userEvent.setup();
    renderizarComConsultas(<FormularioMateria aoCriar={vi.fn()} />);

    await usuario.type(screen.getByLabelText(/^Nome da matéria/), "Biologia");
    const botao = screen.getByRole("button", { name: "Criar matéria" });
    await usuario.click(botao);
    await usuario.click(screen.getByRole("button", { name: /aguarde/i }));
    liberar();

    await waitFor(() => {
      expect(screen.getByLabelText(/^Nome da matéria/)).toHaveValue("");
    });
    expect(recebidos).toHaveLength(1);
  });

  it("não tem violações de acessibilidade, com e sem erro", async () => {
    capturar(() =>
      HttpResponse.json(
        corpoErro("nome_em_uso", "Você já tem uma matéria com esse nome.", [
          { campo: "nome", mensagem: "Você já tem uma matéria com esse nome." },
        ]),
        { status: 409 },
      ),
    );
    const usuario = userEvent.setup();
    const { container } = renderizarComConsultas(<FormularioMateria aoCriar={vi.fn()} />);
    expect((await axe(container)).violations).toEqual([]);

    await usuario.type(screen.getByLabelText(/^Nome da matéria/), "biologia");
    await usuario.click(screen.getByRole("button", { name: "Criar matéria" }));
    await screen.findByText("Você já tem uma matéria com esse nome.");
    expect((await axe(container)).violations).toEqual([]);
  });
});
