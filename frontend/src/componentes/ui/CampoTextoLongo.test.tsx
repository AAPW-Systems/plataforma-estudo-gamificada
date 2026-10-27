import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState, type SyntheticEvent } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { axe } from "vitest-axe";

import { CampoTextoLongo, contarCaracteres } from "./CampoTextoLongo";

afterEach(cleanup);

describe("T006 / DTEC 036: contarCaracteres", () => {
  it.each([
    ["", 0],
    ["abc", 3],
    ["🧬", 1], // emoji fora do plano básico: 2 unidades UTF-16, 1 code point
    ["a🧬b", 3],
    ["é", 1], // "e" + acento combinante vira "é" depois do NFC
    ["çãõ", 3],
    ["linha 1\nlinha 2", 15], // a quebra de linha conta
  ])("conta %j como %i", (texto, esperado) => {
    expect(contarCaracteres(texto)).toBe(esperado);
  });
});

describe("T006 / RQ-003: CampoTextoLongo", () => {
  it("não tem violações axe, com contador e com erro", async () => {
    const { container, rerender } = render(<CampoTextoLongo rotulo="Frente" limite={1000} />);
    expect((await axe(container)).violations).toEqual([]);
    rerender(<CampoTextoLongo rotulo="Frente" limite={1000} erro="Use de 1 a 1.000 caracteres." />);
    expect((await axe(container)).violations).toEqual([]);
  });

  it("associa rótulo, contador e erro ao campo por aria-describedby", () => {
    render(
      <CampoTextoLongo
        rotulo="Verso"
        limite={2000}
        defaultValue="Mitocôndria"
        erro="Use de 1 a 2.000 caracteres."
      />,
    );
    const campo = screen.getByRole("textbox", { name: "Verso" });
    expect(campo).toHaveAccessibleDescription(
      expect.stringContaining("Use de 1 a 2.000 caracteres."),
    );
    expect(campo).toHaveAccessibleDescription(expect.stringContaining("11 de 2.000"));
    expect(campo).toBeInvalid();
  });

  it("marca o rótulo como obrigatório por texto, sem depender de símbolo", () => {
    render(<CampoTextoLongo rotulo="Frente" limite={1000} isRequired />);
    expect(screen.getByRole("textbox", { name: "Frente (obrigatório)" })).toBeRequired();
  });

  it("o contador acompanha o texto em code points e atualiza ao digitar", async () => {
    const usuario = userEvent.setup();
    render(<CampoTextoLongo rotulo="Frente" limite={10} />);
    const campo = screen.getByRole("textbox", { name: "Frente" });
    expect(campo).toHaveAccessibleDescription("0 de 10");
    await usuario.type(campo, "ab🧬");
    expect(campo).toHaveAccessibleDescription("3 de 10");
  });

  it("acima do limite o contador avisa por texto e o campo continua editável", async () => {
    const usuario = userEvent.setup();
    render(<CampoTextoLongo rotulo="Frente" limite={3} defaultValue="abc" />);
    const campo = screen.getByRole("textbox", { name: "Frente" });
    expect(screen.queryByText(/acima do limite/i)).not.toBeInTheDocument();
    await usuario.type(campo, "de");
    expect(campo).toHaveValue("abcde");
    expect(campo).toHaveAccessibleDescription(expect.stringContaining("5 de 3"));
    expect(campo).toHaveAccessibleDescription(expect.stringContaining("2 acima do limite"));
  });

  it("aceita valor controlado e avisa as mudanças", async () => {
    const usuario = userEvent.setup();
    const aoMudar = vi.fn();
    function Controlado() {
      const [valor, definir] = useState("x");
      return (
        <CampoTextoLongo
          rotulo="Explicação"
          limite={50}
          value={valor}
          onChange={(novo) => {
            aoMudar(novo);
            definir(novo.toUpperCase());
          }}
        />
      );
    }
    render(<Controlado />);
    const campo = screen.getByRole("textbox", { name: "Explicação" });
    await usuario.type(campo, "y");
    expect(aoMudar).toHaveBeenLastCalledWith("xy");
    expect(campo).toHaveValue("XY");
    expect(campo).toHaveAccessibleDescription("2 de 50");
  });

  it("Enter quebra a linha dentro do campo, sem enviar formulário", async () => {
    const usuario = userEvent.setup();
    const aoEnviar = vi.fn((e: SyntheticEvent) => {
      e.preventDefault();
    });
    render(
      <form onSubmit={aoEnviar}>
        <CampoTextoLongo rotulo="Verso" limite={100} />
      </form>,
    );
    const campo = screen.getByRole("textbox", { name: "Verso" });
    await usuario.type(campo, "um{Enter}dois");
    expect(campo).toHaveValue("um\ndois");
    expect(aoEnviar).not.toHaveBeenCalled();
    expect(screen.getByText(/7 de 100/)).toBeInTheDocument();
  });

  it("repassa a referência ao textarea para o foco", () => {
    const referencia = { current: null as HTMLTextAreaElement | null };
    render(<CampoTextoLongo rotulo="Frente" limite={10} inputRef={referencia} />);
    expect(referencia.current).toBe(screen.getByRole("textbox", { name: "Frente" }));
  });

  it("mostra o texto do estudante como texto, sem interpretar marcação", () => {
    render(
      <CampoTextoLongo rotulo="Frente" limite={100} defaultValue="<img src=x onerror=alert(1)>" />,
    );
    expect(screen.getByRole("textbox", { name: "Frente" })).toHaveValue(
      "<img src=x onerror=alert(1)>",
    );
    expect(document.querySelector("img")).toBeNull();
  });
});
