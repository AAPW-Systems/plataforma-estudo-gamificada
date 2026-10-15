import { screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { axe } from "vitest-axe";

import {
  configurarServidorDeTestes,
  materiaFicticia,
  renderizarComConsultas,
} from "../../testes/acervo";
import { CabecalhoMateria } from "./CabecalhoMateria";

configurarServidorDeTestes();

describe("CabecalhoMateria (T044; US3)", () => {
  it("mostra o nome como título da página, com renomear e excluir a um toque", () => {
    renderizarComConsultas(
      <CabecalhoMateria materia={materiaFicticia({ nome: "Genética" })} aoExcluida={vi.fn()} />,
    );

    expect(screen.getByRole("heading", { level: 1, name: "Genética" })).toBeVisible();
    expect(screen.getByRole("button", { name: "Renomear matéria" })).toBeVisible();
    expect(screen.getByRole("button", { name: "Excluir matéria: Genética" })).toBeVisible();
  });

  it("não tem violações de acessibilidade", async () => {
    const { container } = renderizarComConsultas(
      <CabecalhoMateria materia={materiaFicticia()} aoExcluida={vi.fn()} />,
    );
    expect((await axe(container)).violations).toEqual([]);
  });
});
