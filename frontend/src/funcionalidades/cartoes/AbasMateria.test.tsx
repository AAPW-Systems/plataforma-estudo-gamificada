import { screen, waitFor } from "@testing-library/react";
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
  usoFicticio,
} from "../../testes/acervo";
import { cartaoFicticio, limitesFicticios } from "../../testes/cartoes";
import { renderizarComRoteador } from "../../testes/renderizar";
import { servidor } from "../../testes/servidor";

configurarServidorDeTestes();

function servirMateria() {
  simularSessaoAberta();
  servidor.use(
    http.get(`${BASE}/materias/${ID_MATERIA}`, () => HttpResponse.json(materiaFicticia())),
    http.get(`${BASE}/acervo/uso`, () => HttpResponse.json(usoFicticio())),
    http.get(`${BASE}/materias/${ID_MATERIA}/fontes`, () => HttpResponse.json({ itens: [] })),
    http.get(`${BASE}/cartoes/limites`, () => HttpResponse.json(limitesFicticios())),
    http.get(`${BASE}/materias/${ID_MATERIA}/cartoes`, () =>
      HttpResponse.json({ itens: [cartaoFicticio()], proximoCursor: null, total: 1 }),
    ),
  );
}

describe("Áreas da matéria: Fontes e Cartões (T018; design 9.4)", () => {
  it("a aba Cartões tem endereço próprio e é a página atual na navegação", async () => {
    servirMateria();
    const { container, roteador } = renderizarComRoteador(`/materias/${ID_MATERIA}/cartoes`);

    expect(await screen.findByText("Qual organela produz ATP?")).toBeInTheDocument();
    const navegacao = screen.getByRole("navigation", { name: "Áreas da matéria" });
    expect(screen.getByRole("link", { name: "Cartões" })).toHaveAttribute("aria-current", "page");
    expect(screen.getByRole("link", { name: "Fontes" })).not.toHaveAttribute("aria-current");
    expect(screen.queryByRole("heading", { name: "Fontes" })).not.toBeInTheDocument();
    expect(roteador.state.location.pathname).toBe(`/materias/${ID_MATERIA}/cartoes`);
    expect((await axe(navegacao)).violations).toEqual([]);
    expect((await axe(container)).violations).toEqual([]);
  });

  it("os links trocam de área, e o Voltar do navegador volta à anterior", async () => {
    servirMateria();
    const usuario = userEvent.setup();
    const { roteador } = renderizarComRoteador(`/materias/${ID_MATERIA}`);

    expect(await screen.findByRole("heading", { name: "Fontes" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Fontes" })).toHaveAttribute("aria-current", "page");

    await usuario.click(screen.getByRole("link", { name: "Cartões" }));
    expect(await screen.findByText("Qual organela produz ATP?")).toBeInTheDocument();

    roteador.history.back();
    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Fontes" })).toBeInTheDocument();
    });
    expect(roteador.state.location.pathname).toBe(`/materias/${ID_MATERIA}`);
  });
});
