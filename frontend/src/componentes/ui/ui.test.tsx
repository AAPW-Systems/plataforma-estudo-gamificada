import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { axe } from "vitest-axe";

import { Aviso } from "./Aviso";
import { Botao } from "./Botao";
import { CampoFuso } from "./CampoFuso";
import { CampoNumero } from "./CampoNumero";
import { CampoSenha } from "./CampoSenha";
import { CampoTexto } from "./CampoTexto";
import { Dialogo } from "./Dialogo";
import { MensagemErroFormulario } from "./MensagemErroFormulario";

afterEach(cleanup);

describe("T024 / RQ-004: componentes acessíveis", () => {
  it.each([
    ["Botao", <Botao key="botao">Salvar</Botao>],
    ["CampoTexto", <CampoTexto key="texto" rotulo="Nome" />],
    ["CampoSenha", <CampoSenha key="senha" rotulo="Senha" />],
    ["CampoNumero", <CampoNumero key="numero" rotulo="Meta" minValue={1} maxValue={200} />],
    ["CampoFuso", <CampoFuso key="fuso" rotulo="Fuso" />],
    ["Aviso", <Aviso key="aviso">Alteração salva.</Aviso>],
    ["MensagemErroFormulario", <MensagemErroFormulario key="erro" mensagem="Tente novamente." />],
    [
      "Dialogo",
      <Dialogo key="dialogo" titulo="Confirmar" acionador="Abrir">
        <p>Confira os dados.</p>
      </Dialogo>,
    ],
  ])("%s não tem violações axe", async (_nome, componente) => {
    const { container } = render(componente);
    expect((await axe(container)).violations).toEqual([]);
  });

  it("associa rótulo, erro e preserva o texto", async () => {
    const usuario = userEvent.setup();
    render(<CampoTexto rotulo="Nome" erro="Confira o nome." defaultValue="Teste" />);
    const campo = screen.getByRole("textbox", { name: "Nome" });
    expect(campo).toHaveAccessibleDescription("Confira o nome.");
    await usuario.type(campo, " Exemplo");
    expect(campo).toHaveValue("Teste Exemplo");
  });

  it("botão ocupado impede reenvio", async () => {
    const acao = vi.fn();
    render(
      <Botao carregando onPress={acao}>
        Salvar
      </Botao>,
    );
    await userEvent.click(screen.getByRole("button"));
    expect(acao).not.toHaveBeenCalled();
  });

  it("diálogo abre por teclado, fecha e devolve o foco", async () => {
    const usuario = userEvent.setup();
    render(
      <Dialogo titulo="Confirmar exclusão" acionador="Excluir">
        <p>A ação é definitiva.</p>
      </Dialogo>,
    );
    await usuario.tab();
    await usuario.keyboard("{Enter}");
    const dialogo = screen.getByRole("dialog", { name: "Confirmar exclusão" });
    expect((await axe(dialogo)).violations).toEqual([]);
    await usuario.keyboard("{Escape}");
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    await waitFor(() => expect(screen.getByRole("button", { name: "Excluir" })).toHaveFocus());
  });
});
