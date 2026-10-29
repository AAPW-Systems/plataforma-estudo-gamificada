import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it } from "vitest";
import { axe } from "vitest-axe";

import { CitacaoDestacada } from "./CitacaoDestacada";
import { PainelEvidencia, type EvidenciaExibida } from "./PainelEvidencia";

afterEach(cleanup);

const TEXTO = "A mitocôndria produz ATP por respiração celular.";

describe("T010 (004): CitacaoDestacada", () => {
  it("destaca o intervalo da citação em <mark> e mantém o resto do trecho", () => {
    const { container } = render(<CitacaoDestacada texto={TEXTO} inicio={2} fim={13} />);
    const marca = container.querySelector("mark");
    expect(marca?.textContent).toBe("mitocôndria");
    expect(container.textContent).toBe(TEXTO);
  });

  it("conta em code points, como o servidor: emoji e caracteres fora do BMP valem 1", () => {
    // "🧬" ocupa 2 unidades UTF-16 e 1 code point
    const texto = "🧬 O DNA guarda a informação genética.";
    const { container } = render(<CitacaoDestacada texto={texto} inicio={2} fim={7} />);
    expect(container.querySelector("mark")?.textContent).toBe("O DNA");
  });

  it("citação no início e no fim do trecho", () => {
    const { container, rerender } = render(<CitacaoDestacada texto={TEXTO} inicio={0} fim={1} />);
    expect(container.querySelector("mark")?.textContent).toBe("A");
    rerender(<CitacaoDestacada texto={TEXTO} inicio={TEXTO.length - 8} fim={TEXTO.length} />);
    expect(container.querySelector("mark")?.textContent).toBe("celular.");
  });

  it.each([
    [5, 5],
    [6, 2],
    [-1, 3],
    [0, 999],
  ])("intervalo inválido (%i, %i) mostra o trecho sem destaque", (inicio, fim) => {
    const { container } = render(<CitacaoDestacada texto={TEXTO} inicio={inicio} fim={fim} />);
    expect(container.querySelector("mark")).toBeNull();
    expect(container.textContent).toBe(TEXTO);
  });

  it("marcação e script no trecho são texto puro, nunca HTML", () => {
    const texto = '<script>alert("x")</script> <b>negrito</b>';
    const { container } = render(<CitacaoDestacada texto={texto} inicio={0} fim={8} />);
    expect(container.querySelector("script")).toBeNull();
    expect(container.querySelector("b")).toBeNull();
    expect(container.querySelector("mark")?.textContent).toBe("<script>");
    expect(container.textContent).toBe(texto);
  });

  it("preserva as quebras de linha do trecho", () => {
    const { container } = render(
      <CitacaoDestacada texto={"linha 1\nlinha 2"} inicio={0} fim={5} />,
    );
    // a classe aplica `white-space: pre-wrap` (global.css)
    expect(container.firstElementChild?.className).toContain("citacao-trecho");
    expect(container.textContent).toBe("linha 1\nlinha 2");
  });
});

const COM_FONTE: EvidenciaExibida = {
  fonteTitulo: "Citologia",
  fonteNomeArquivo: "citologia.pdf",
  fonteEnviadaEm: "2026-10-01T12:30:00Z",
  pagina: 3,
  trecho: { texto: TEXTO, citacaoInicio: 2, citacaoFim: 13 },
};

const APAGADA: EvidenciaExibida = { ...COM_FONTE, trecho: null };

describe("T010 (004), design 9.8: PainelEvidencia", () => {
  it("vem recolhido: o trecho só aparece depois de expandir", async () => {
    const usuario = userEvent.setup();
    render(<PainelEvidencia evidencia={COM_FONTE} />);
    const botao = screen.getByRole("button", { name: "Ver trecho" });
    expect(botao).toHaveAttribute("aria-expanded", "false");
    // recolhido, o painel fica no DOM mas escondido (`hidden`), fora da árvore de acessibilidade
    expect(screen.getByText("mitocôndria")).not.toBeVisible();

    await usuario.click(botao);

    expect(botao).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByText("mitocôndria")).toBeVisible();
    expect(screen.getByText("mitocôndria").tagName).toBe("MARK");
    expect(screen.getByText("Citologia")).toBeInTheDocument();
    expect(screen.getByText("Página 3")).toBeInTheDocument();
  });

  it("abre e fecha só pelo teclado", async () => {
    const usuario = userEvent.setup();
    render(<PainelEvidencia evidencia={COM_FONTE} />);
    await usuario.tab();
    expect(screen.getByRole("button", { name: "Ver trecho" })).toHaveFocus();
    await usuario.keyboard("{Enter}");
    expect(screen.getByText("mitocôndria")).toBeVisible();
    await usuario.keyboard(" ");
    expect(screen.getByText("mitocôndria")).not.toBeVisible();
  });

  it("sem página conhecida, nenhuma página é mostrada (RN-05)", async () => {
    const usuario = userEvent.setup();
    render(<PainelEvidencia evidencia={{ ...COM_FONTE, pagina: null }} />);
    await usuario.click(screen.getByRole("button", { name: "Ver trecho" }));
    expect(screen.queryByText(/Página/)).not.toBeInTheDocument();
  });

  it("fonte apagada: 'Fonte apagada' com título, arquivo, página e data, sem o trecho", async () => {
    const usuario = userEvent.setup();
    render(<PainelEvidencia evidencia={APAGADA} />);
    await usuario.click(screen.getByRole("button", { name: "Ver origem" }));
    expect(screen.getByText("Fonte apagada")).toBeInTheDocument();
    expect(screen.getByText("Citologia")).toBeInTheDocument();
    expect(screen.getByText("citologia.pdf")).toBeInTheDocument();
    expect(screen.getByText("Página 3")).toBeInTheDocument();
    expect(screen.getByText(/01\/10\/2026/)).toBeInTheDocument();
    expect(screen.queryByText("mitocôndria")).not.toBeInTheDocument();
    expect(document.querySelector("mark")).toBeNull();
  });

  it("fonte apagada sem página não inventa página", async () => {
    const usuario = userEvent.setup();
    render(<PainelEvidencia evidencia={{ ...APAGADA, pagina: null }} />);
    await usuario.click(screen.getByRole("button", { name: "Ver origem" }));
    expect(screen.queryByText(/Página/)).not.toBeInTheDocument();
  });

  it.each([
    ["com fonte", COM_FONTE],
    ["fonte apagada", APAGADA],
  ] as const)("%s, recolhido e expandido, não tem violações axe", async (_, evidencia) => {
    const usuario = userEvent.setup();
    const { container } = render(<PainelEvidencia evidencia={evidencia} />);
    expect((await axe(container)).violations).toEqual([]);
    await usuario.click(screen.getByRole("button"));
    expect((await axe(container)).violations).toEqual([]);
  });
});
