import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { axe } from "vitest-axe";

import { Botao } from "./Botao";
import { DialogoConfirmacao } from "./DialogoConfirmacao";
import { GrupoOpcoes } from "./GrupoOpcoes";
import { SeloEstado } from "./SeloEstado";
import { ZonaArquivo } from "./ZonaArquivo";

afterEach(cleanup);

const OPCOES = [
  { valor: "manter", rotulo: "Manter os cartões", descricao: "Eles continuam nas lições." },
  { valor: "excluir", rotulo: "Excluir os cartões junto", descricao: "Eles serão apagados." },
];

function criarArquivo(nome = "citologia.pdf", conteudo = "x") {
  return new File([conteudo], nome, { type: "application/pdf" });
}

describe("SeloEstado (RQ-004)", () => {
  it.each([
    ["neutro", "Pendente"],
    ["andamento", "Processando"],
    ["sucesso", "Concluído"],
    ["erro", "Falhou"],
  ] as const)("tom %s mostra texto e ícone, sem depender só da cor", async (tom, texto) => {
    const { container } = render(<SeloEstado tom={tom}>{texto}</SeloEstado>);
    const selo = screen.getByText(texto).closest(".selo");
    expect(selo).not.toBeNull();
    // O ícone é decorativo (o texto já diz o estado) e existe em todo tom.
    const icone = selo?.querySelector("[aria-hidden='true']");
    expect(icone?.textContent.trim()).not.toBe("");
    expect((await axe(container)).violations).toEqual([]);
  });

  it("tons diferentes usam ícones diferentes", () => {
    const { container } = render(
      <>
        <SeloEstado tom="neutro">A</SeloEstado>
        <SeloEstado tom="andamento">B</SeloEstado>
        <SeloEstado tom="sucesso">C</SeloEstado>
        <SeloEstado tom="erro">D</SeloEstado>
      </>,
    );
    const icones = [...container.querySelectorAll(".selo [aria-hidden='true']")].map(
      (i) => i.textContent,
    );
    expect(new Set(icones).size).toBe(4);
  });
});

describe("ZonaArquivo (DTEC 016; US1-4)", () => {
  it("mostra formatos e limite visíveis e não tem violações axe", async () => {
    const { container } = render(
      <ZonaArquivo
        rotulo="Enviar fonte"
        descricao="PDF com texto, TXT ou Markdown, até 2 MB."
        aceitos={[".pdf", ".txt", ".md", ".markdown"]}
        aoSelecionar={vi.fn()}
      />,
    );
    expect(screen.getByText("PDF com texto, TXT ou Markdown, até 2 MB.")).toBeVisible();
    expect(screen.getByRole("button", { name: /escolher arquivo/i })).toBeInTheDocument();
    expect((await axe(container)).violations).toEqual([]);
  });

  it("o botão abre o seletor restrito aos formatos aceitos e entrega o arquivo escolhido", async () => {
    const aoSelecionar = vi.fn();
    const { container } = render(
      <ZonaArquivo
        rotulo="Enviar fonte"
        descricao="PDF"
        aceitos={[".pdf", ".txt"]}
        aoSelecionar={aoSelecionar}
      />,
    );
    const entrada = container.querySelector<HTMLInputElement>("input[type='file']");
    if (!entrada) throw new Error("o seletor de arquivos não foi renderizado");
    expect(entrada.accept).toBe(".pdf,.txt");
    expect(entrada.multiple).toBe(false);
    const arquivo = criarArquivo();
    await userEvent.upload(entrada, arquivo);
    expect(aoSelecionar).toHaveBeenCalledTimes(1);
    expect(aoSelecionar).toHaveBeenCalledWith(arquivo);
  });

  it("é operável por teclado: Tab chega ao botão de escolher arquivo", async () => {
    const usuario = userEvent.setup();
    render(
      <ZonaArquivo
        rotulo="Enviar fonte"
        descricao="PDF"
        aceitos={[".pdf"]}
        aoSelecionar={vi.fn()}
      />,
    );
    // O React Aria põe antes um botão oculto da própria zona (arrastar com leitor de tela).
    const botao = screen.getByRole("button", { name: /escolher arquivo/i });
    for (let i = 0; i < 3 && document.activeElement !== botao; i += 1) await usuario.tab();
    expect(botao).toHaveFocus();
  });

  it("solta de um arquivo entrega o arquivo; mais de um é recusado com explicação", async () => {
    const aoSelecionar = vi.fn();
    const aoRecusar = vi.fn();
    render(
      <ZonaArquivo
        rotulo="Enviar fonte"
        descricao="PDF"
        aceitos={[".pdf"]}
        aoSelecionar={aoSelecionar}
        aoRecusar={aoRecusar}
      />,
    );
    const zona = screen.getByTestId("zona-arquivo");
    const arquivo = criarArquivo();
    const item = (f: File) => ({ kind: "file", type: f.type, getAsFile: () => f });
    fireEvent.drop(zona, { dataTransfer: { items: [item(arquivo)], types: ["Files"] } });
    await waitFor(() => {
      expect(aoSelecionar).toHaveBeenCalledWith(arquivo);
    });

    fireEvent.drop(zona, {
      dataTransfer: { items: [item(arquivo), item(criarArquivo("b.pdf"))], types: ["Files"] },
    });
    await waitFor(() => {
      expect(aoRecusar).toHaveBeenCalledWith("Envie um arquivo por vez.");
    });
    expect(aoSelecionar).toHaveBeenCalledTimes(1);
  });

  it("ocupada, não aceita outro arquivo e anuncia o andamento", async () => {
    const aoSelecionar = vi.fn();
    const { container } = render(
      <ZonaArquivo
        rotulo="Enviar fonte"
        descricao="PDF"
        aceitos={[".pdf"]}
        aoSelecionar={aoSelecionar}
        ocupado
      />,
    );
    expect(screen.getByRole("button", { name: /enviando/i })).toBeDisabled();
    expect(screen.getByRole("status")).toHaveTextContent(/enviando/i);
    expect((await axe(container)).violations).toEqual([]);
  });

  it("mostra o erro do servidor junto da zona, ligado por descrição", async () => {
    const { container } = render(
      <ZonaArquivo
        rotulo="Enviar fonte"
        descricao="PDF"
        aceitos={[".pdf"]}
        aoSelecionar={vi.fn()}
        erro="O conteúdo deste arquivo não corresponde à extensão .pdf."
      />,
    );
    const grupo = screen.getByRole("group", { name: /enviar fonte/i });
    expect(grupo).toHaveAccessibleDescription(/não corresponde à extensão/);
    expect((await axe(container)).violations).toEqual([]);
  });
});

describe("GrupoOpcoes (RN-14)", () => {
  function Controlado({ aoMudar }: { aoMudar?: (v: string) => void }) {
    const [valor, definir] = useState<string | undefined>(undefined);
    return (
      <GrupoOpcoes
        rotulo="O que fazer com os cartões?"
        opcoes={OPCOES}
        valor={valor}
        aoMudar={(v) => {
          definir(v);
          aoMudar?.(v);
        }}
        obrigatorio
      />
    );
  }

  it("não tem violações axe e começa sem escolha (a escolha é obrigatória)", async () => {
    const { container } = render(<Controlado />);
    for (const radio of screen.getAllByRole("radio")) expect(radio).not.toBeChecked();
    expect(screen.getByRole("radiogroup", { name: /o que fazer/i })).toBeInTheDocument();
    expect((await axe(container)).violations).toEqual([]);
  });

  it("mostra a descrição de cada opção associada ao botão de rádio", () => {
    render(<Controlado />);
    expect(screen.getByRole("radio", { name: /manter os cartões/i })).toHaveAccessibleDescription(
      "Eles continuam nas lições.",
    );
  });

  it("escolhe por clique e por teclado (setas)", async () => {
    const usuario = userEvent.setup();
    const aoMudar = vi.fn();
    render(<Controlado aoMudar={aoMudar} />);
    await usuario.click(screen.getByRole("radio", { name: /manter os cartões/i }));
    expect(aoMudar).toHaveBeenLastCalledWith("manter");
    await usuario.keyboard("{ArrowDown}");
    expect(aoMudar).toHaveBeenLastCalledWith("excluir");
    expect(screen.getByRole("radio", { name: /excluir os cartões junto/i })).toBeChecked();
  });

  it("liga o erro ao grupo", () => {
    render(
      <GrupoOpcoes
        rotulo="Escolha"
        opcoes={OPCOES}
        valor={undefined}
        aoMudar={vi.fn()}
        erro="Escolha uma opção."
      />,
    );
    expect(screen.getByRole("radiogroup")).toHaveAccessibleDescription("Escolha uma opção.");
  });
});

describe("DialogoConfirmacao (RQ-004)", () => {
  function Exemplo({
    aoConfirmar = vi.fn(),
    ocupado = false,
    confirmarDesabilitado = false,
    mensagemErro,
  }: {
    aoConfirmar?: () => void;
    ocupado?: boolean;
    confirmarDesabilitado?: boolean;
    mensagemErro?: string;
  }) {
    const [aberto, definir] = useState(false);
    return (
      <DialogoConfirmacao
        acionador={<Botao variante="destrutivo">Excluir fonte</Botao>}
        titulo="Excluir a fonte «Citologia»?"
        aberto={aberto}
        aoAlterarAberto={definir}
        textoConfirmar="Excluir definitivamente"
        aoConfirmar={aoConfirmar}
        ocupado={ocupado}
        confirmarDesabilitado={confirmarDesabilitado}
        mensagemErro={mensagemErro}
      >
        <p>Os trechos serão apagados.</p>
      </DialogoConfirmacao>
    );
  }

  async function abrir(usuario: ReturnType<typeof userEvent.setup>) {
    await usuario.click(screen.getByRole("button", { name: "Excluir fonte" }));
    return screen.findByRole("dialog");
  }

  it("o diálogo destrutivo tem título, aviso de ação definitiva com ícone e axe limpo", async () => {
    const usuario = userEvent.setup();
    render(<Exemplo />);
    const dialogo = await abrir(usuario);
    expect(dialogo).toHaveAccessibleName("Excluir a fonte «Citologia»?");
    // A distinção destrutiva não depende só de cor: há texto e ícone.
    expect(within(dialogo).getByText(/ação definitiva/i)).toBeVisible();
    expect(dialogo.querySelector("[aria-hidden='true']")).not.toBeNull();
    expect(
      within(dialogo).getByRole("button", { name: "Excluir definitivamente" }),
    ).toBeInTheDocument();
    expect((await axe(dialogo)).violations).toEqual([]);
  });

  it("prende o foco, fecha com Escape e devolve o foco ao acionador", async () => {
    const usuario = userEvent.setup();
    render(<Exemplo />);
    const dialogo = await abrir(usuario);
    for (let i = 0; i < 8; i += 1) {
      await usuario.tab();
      expect(dialogo).toContainElement(document.activeElement as HTMLElement);
    }
    await usuario.keyboard("{Escape}");
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    await waitFor(() =>
      expect(screen.getByRole("button", { name: "Excluir fonte" })).toHaveFocus(),
    );
  });

  it("cancelar fecha sem confirmar", async () => {
    const usuario = userEvent.setup();
    const aoConfirmar = vi.fn();
    render(<Exemplo aoConfirmar={aoConfirmar} />);
    const dialogo = await abrir(usuario);
    await usuario.click(within(dialogo).getByRole("button", { name: "Cancelar" }));
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    expect(aoConfirmar).not.toHaveBeenCalled();
  });

  it("confirmar chama a ação uma vez", async () => {
    const usuario = userEvent.setup();
    const aoConfirmar = vi.fn();
    render(<Exemplo aoConfirmar={aoConfirmar} />);
    const dialogo = await abrir(usuario);
    await usuario.click(within(dialogo).getByRole("button", { name: "Excluir definitivamente" }));
    expect(aoConfirmar).toHaveBeenCalledTimes(1);
  });

  it("com a confirmação desabilitada, não chama a ação nem por Enter no formulário", async () => {
    const usuario = userEvent.setup();
    const aoConfirmar = vi.fn();
    render(<Exemplo aoConfirmar={aoConfirmar} confirmarDesabilitado />);
    const dialogo = await abrir(usuario);
    const confirmar = within(dialogo).getByRole("button", { name: "Excluir definitivamente" });
    expect(confirmar).toBeDisabled();
    await usuario.click(confirmar);
    expect(aoConfirmar).not.toHaveBeenCalled();
  });

  it("ocupado, não fecha por Escape nem permite nova confirmação", async () => {
    const usuario = userEvent.setup();
    const aoConfirmar = vi.fn();
    const { rerender } = render(<Exemplo aoConfirmar={aoConfirmar} />);
    const dialogo = await abrir(usuario);
    rerender(<Exemplo aoConfirmar={aoConfirmar} ocupado />);
    await usuario.keyboard("{Escape}");
    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(within(dialogo).getByRole("button", { name: /aguarde/i })).toBeDisabled();
    expect(within(dialogo).getByRole("button", { name: "Cancelar" })).toBeDisabled();
    await usuario.click(within(dialogo).getByRole("button", { name: /aguarde/i }));
    expect(aoConfirmar).not.toHaveBeenCalled();
  });

  it("mostra a mensagem de erro dentro do diálogo", async () => {
    const usuario = userEvent.setup();
    render(<Exemplo mensagemErro="Algo mudou. Confira os números." />);
    const dialogo = await abrir(usuario);
    expect(within(dialogo).getByText("Algo mudou. Confira os números.")).toBeVisible();
  });
});
