import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { axe } from "vitest-axe";

import { SeloOrigem } from "./SeloOrigem";

afterEach(cleanup);

describe("T006 / RF-009, RQ-003: SeloOrigem", () => {
  it.each([
    ["gerado_verificado", "Gerado e verificado"],
    ["editado", "Editado por você"],
    ["criado", "Criado por você"],
  ] as const)("mostra o texto de %s", (origem, texto) => {
    render(<SeloOrigem origem={origem} />);
    expect(screen.getByText(texto)).toBeInTheDocument();
  });

  it("nunca depende só de cor: cada origem tem texto e um ícone próprio, oculto ao leitor", () => {
    const icones = new Set<string>();
    for (const origem of ["gerado_verificado", "editado", "criado"] as const) {
      const { container, unmount } = render(<SeloOrigem origem={origem} />);
      const icone = container.querySelector('[aria-hidden="true"]');
      expect(icone?.textContent).toBeTruthy();
      icones.add(icone?.textContent ?? "");
      unmount();
    }
    expect(icones.size).toBe(3);
  });

  it("só 'Gerado e verificado' leva o selo de verificado", () => {
    const { container, rerender } = render(<SeloOrigem origem="gerado_verificado" />);
    expect(container.querySelector(".selo-origem-verificado")).not.toBeNull();
    rerender(<SeloOrigem origem="editado" />);
    expect(container.querySelector(".selo-origem-verificado")).toBeNull();
    rerender(<SeloOrigem origem="criado" />);
    expect(container.querySelector(".selo-origem-verificado")).toBeNull();
  });

  it("acrescenta 'Fonte apagada' como complemento, sem trocar a origem", () => {
    render(<SeloOrigem origem="criado" fonteApagada />);
    expect(screen.getByText("Criado por você")).toBeInTheDocument();
    expect(screen.getByText("Fonte apagada")).toBeInTheDocument();
  });

  it("sem fonte apagada, o complemento não aparece", () => {
    render(<SeloOrigem origem="criado" />);
    expect(screen.queryByText("Fonte apagada")).not.toBeInTheDocument();
  });

  it.each([
    ["gerado_verificado", false],
    ["editado", false],
    ["criado", false],
    ["criado", true],
    ["editado", true],
  ] as const)("%s (fonte apagada: %s) não tem violações axe", async (origem, fonteApagada) => {
    const { container } = render(
      <ul>
        <li>
          <SeloOrigem origem={origem} fonteApagada={fonteApagada} />
        </li>
      </ul>,
    );
    expect((await axe(container)).violations).toEqual([]);
  });
});
