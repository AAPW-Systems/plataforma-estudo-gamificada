import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";
import { axe } from "vitest-axe";

import {
  BASE,
  ID_MATERIA,
  configurarServidorDeTestes,
  materiaFicticia,
  simularSessaoAberta,
} from "../../testes/acervo";
import { renderizarComRoteador } from "../../testes/renderizar";
import { servidor } from "../../testes/servidor";

configurarServidorDeTestes();

function simularLista(itens: ReturnType<typeof materiaFicticia>[]) {
  simularSessaoAberta();
  servidor.use(http.get(`${BASE}/materias`, () => HttpResponse.json({ itens })));
}

describe("Lista de matérias (T029; US1 cenário 1, design 9.3)", () => {
  it('sem matérias, mostra o estado vazio com a ação "Criar primeira matéria"', async () => {
    simularLista([]);
    renderizarComRoteador("/materias");
    expect(await screen.findByRole("heading", { name: "Matérias" })).toBeVisible();
    expect(await screen.findByText(/Você ainda não tem matérias/)).toBeVisible();
    expect(screen.getByRole("button", { name: "Criar primeira matéria" })).toBeVisible();
    expect(screen.queryByRole("list")).toBeNull();
  });

  it("mostra nome, fontes, cartões ativos e aguardando revisão de cada matéria", async () => {
    simularLista([
      materiaFicticia({ totalFontes: 3, cartoesAtivos: 12, cartoesAguardandoRevisao: 4 }),
      materiaFicticia({
        id: "55555555-5555-4555-8555-555555555555",
        nome: "Química",
        totalFontes: 1,
        cartoesAtivos: 0,
        cartoesAguardandoRevisao: 0,
      }),
    ]);
    renderizarComRoteador("/materias");
    const itens = await screen.findAllByRole("listitem");
    expect(itens).toHaveLength(2);
    expect(screen.getByRole("link", { name: "Biologia" })).toBeVisible();
    expect(itens[0]).toHaveTextContent("3 fontes");
    expect(itens[0]).toHaveTextContent("12 cartões ativos");
    expect(itens[0]).toHaveTextContent("4 aguardando revisão");
    expect(itens[1]).toHaveTextContent("1 fonte");
    expect(itens[1]).toHaveTextContent("0 cartões ativos");
    expect(screen.getByRole("button", { name: "Criar matéria" })).toBeVisible();
  });

  it("criar uma matéria a coloca na lista e leva à página dela", async () => {
    let criadas: ReturnType<typeof materiaFicticia>[] = [];
    simularSessaoAberta();
    servidor.use(
      http.get(`${BASE}/materias`, () => HttpResponse.json({ itens: criadas })),
      http.post(`${BASE}/materias`, () => {
        criadas = [materiaFicticia()];
        return HttpResponse.json(criadas[0], { status: 201 });
      }),
      http.get(`${BASE}/materias/${ID_MATERIA}`, () => HttpResponse.json(materiaFicticia())),
      http.get(`${BASE}/acervo/uso`, () =>
        HttpResponse.json({
          tamanhoMaximoBytes: 2_097_152,
          extensoesAceitas: [".pdf", ".txt", ".md", ".markdown"],
          paginasMaximasPdf: 200,
          cotaMaterias: 20,
          totalMaterias: 1,
          cotaFontesPorMateria: 30,
          usoArmazenamentoBytes: 0,
          cotaArmazenamentoBytes: 104_857_600,
        }),
      ),
      http.get(`${BASE}/materias/${ID_MATERIA}/fontes`, () => HttpResponse.json({ itens: [] })),
    );
    const usuario = userEvent.setup();
    const { roteador } = renderizarComRoteador("/materias");
    await usuario.type(await screen.findByLabelText(/^Nome da matéria/), "Biologia");
    await usuario.click(screen.getByRole("button", { name: "Criar primeira matéria" }));
    await waitFor(() => {
      expect(roteador.state.location.pathname).toBe(`/materias/${ID_MATERIA}`);
    });
    expect(await screen.findByRole("heading", { name: "Biologia" })).toBeVisible();
    expect(await screen.findByText("Enviar a primeira fonte")).toBeVisible();
  });

  it("a navegação principal tem o item Matérias", async () => {
    simularLista([]);
    renderizarComRoteador("/materias");
    const navegacao = await screen.findByRole("navigation", { name: "Principal" });
    expect(within(navegacao).getByRole("link", { name: "Matérias" })).toHaveAttribute(
      "href",
      "/materias",
    );
  });

  it("não tem violações de acessibilidade, vazia e com matérias", async () => {
    simularLista([]);
    const { container, unmount } = renderizarComRoteador("/materias");
    await screen.findByText(/Você ainda não tem matérias/);
    expect((await axe(container)).violations).toEqual([]);
    unmount();

    simularLista([materiaFicticia({ totalFontes: 2 })]);
    const segunda = renderizarComRoteador("/materias");
    await screen.findByRole("link", { name: "Biologia" });
    expect((await axe(segunda.container)).violations).toEqual([]);
  });
});
