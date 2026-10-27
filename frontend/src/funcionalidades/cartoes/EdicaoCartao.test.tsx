import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";
import { axe } from "vitest-axe";

import type { Cartao } from "../../api/cartoes";
import {
  BASE,
  ID_MATERIA,
  configurarServidorDeTestes,
  corpoErro,
  fonteFicticia,
  renderizarComConsultas,
} from "../../testes/acervo";
import { ID_CARTAO, cartaoFicticio, limitesFicticios } from "../../testes/cartoes";
import { servidor } from "../../testes/servidor";
import { AbaCartoes } from "./AbaCartoes";

configurarServidorDeTestes();

const URL_CARTAO = `${BASE}/cartoes/${ID_CARTAO}`;

type Edicao = Partial<Pick<Cartao, "frente" | "verso" | "explicacao">>;

/** Serve a lista com um cartão e aplica as edições recebidas a ele, como a API faria. */
function servir(inicial: Cartao, resposta?: (corpo: Edicao) => Response | undefined) {
  let atual = inicial;
  const recebidos: Edicao[] = [];
  servidor.use(
    http.get(`${BASE}/cartoes/limites`, () => HttpResponse.json(limitesFicticios())),
    http.get(`${BASE}/materias/${ID_MATERIA}/fontes`, () =>
      HttpResponse.json({ itens: [fonteFicticia()] }),
    ),
    http.get(`${BASE}/materias/${ID_MATERIA}/cartoes`, () =>
      HttpResponse.json({ itens: [atual], proximoCursor: null, total: 1 }),
    ),
    http.patch(URL_CARTAO, async ({ request }) => {
      const corpo = (await request.json()) as Edicao;
      recebidos.push(corpo);
      const especial = resposta?.(corpo);
      if (especial) return especial;
      const mudou = Object.entries(corpo).some(
        ([campo, valor]) => (atual as Record<string, unknown>)[campo] !== valor,
      );
      atual = {
        ...atual,
        ...corpo,
        origem: mudou && atual.origem === "gerado_verificado" ? "editado" : atual.origem,
        verificado: mudou ? false : atual.verificado,
      };
      return HttpResponse.json(atual);
    }),
  );
  return recebidos;
}

async function abrirEdicao(usuario: ReturnType<typeof userEvent.setup>) {
  const lista = await screen.findByRole("list", { name: "Cartões da matéria" });
  await usuario.click(within(lista).getByRole("button", { name: /^Editar/ }));
  return screen.findByRole("dialog", { name: "Editar cartão" });
}

const campo = (nome: string) => screen.getByRole("textbox", { name: new RegExp(`^${nome}`) });

describe("Edição do cartão (T025; US2, RF-005, RF-006, RF-009)", () => {
  it("o painel abre com os valores atuais, sem 'Salvar e criar outro' nem fonte, sem violações axe", async () => {
    servir(cartaoFicticio({ explicacao: "Respiração celular." }));
    const usuario = userEvent.setup();
    renderizarComConsultas(<AbaCartoes materiaId={ID_MATERIA} />);
    const painel = await abrirEdicao(usuario);

    expect(campo("Frente")).toHaveValue("Qual organela produz ATP?");
    expect(campo("Verso")).toHaveValue("A mitocôndria.");
    expect(campo("Explicação")).toHaveValue("Respiração celular.");
    expect(campo("Frente")).toHaveFocus();
    expect(
      within(painel).queryByRole("button", { name: "Salvar e criar outro" }),
    ).not.toBeInTheDocument();
    expect(within(painel).queryByRole("combobox")).not.toBeInTheDocument();
    expect((await axe(painel)).violations).toEqual([]);
  });

  it("Ctrl+Enter salva só o que mudou e fecha o painel; a lista mostra o texto novo", async () => {
    const recebidos = servir(cartaoFicticio({ explicacao: "Antiga." }));
    const usuario = userEvent.setup();
    renderizarComConsultas(<AbaCartoes materiaId={ID_MATERIA} />);
    await abrirEdicao(usuario);

    await usuario.clear(campo("Verso"));
    await usuario.type(campo("Verso"), "As mitocôndrias.");
    await usuario.clear(campo("Explicação"));
    await usuario.keyboard("{Control>}{Enter}{/Control}");

    await waitFor(() => {
      expect(screen.queryByRole("dialog", { name: "Editar cartão" })).not.toBeInTheDocument();
    });
    expect(recebidos).toEqual([{ verso: "As mitocôndrias.", explicacao: null }]);
    const lista = screen.getByRole("list", { name: "Cartões da matéria" });
    expect(await within(lista).findByText("As mitocôndrias.")).toBeInTheDocument();
  });

  it("editar um cartão gerado troca o selo para 'Editado por você'", async () => {
    servir(cartaoFicticio({ origem: "gerado_verificado", verificado: true }));
    const usuario = userEvent.setup();
    renderizarComConsultas(<AbaCartoes materiaId={ID_MATERIA} />);
    const lista = await screen.findByRole("list", { name: "Cartões da matéria" });
    expect(within(lista).getByText("Gerado e verificado")).toBeInTheDocument();
    await abrirEdicao(usuario);

    await usuario.type(campo("Frente"), " (revisada)");
    await usuario.click(screen.getByRole("button", { name: "Salvar" }));

    expect(await within(lista).findByText("Editado por você")).toBeInTheDocument();
    expect(within(lista).queryByText("Gerado e verificado")).not.toBeInTheDocument();
  });

  it("salvar sem mudar nada não chama a API e fecha o painel", async () => {
    const recebidos = servir(cartaoFicticio());
    const usuario = userEvent.setup();
    renderizarComConsultas(<AbaCartoes materiaId={ID_MATERIA} />);
    await abrirEdicao(usuario);

    await usuario.click(screen.getByRole("button", { name: "Salvar" }));

    await waitFor(() => {
      expect(screen.queryByRole("dialog", { name: "Editar cartão" })).not.toBeInTheDocument();
    });
    expect(recebidos).toEqual([]);
  });

  it("422 do servidor fica junto do campo, com os valores mantidos e o painel aberto", async () => {
    servir(cartaoFicticio(), () =>
      HttpResponse.json(
        corpoErro("dados_invalidos", "Alguns campos precisam de correção.", [
          { campo: "frente", mensagem: "Use de 1 a 10 caracteres." },
        ]),
        { status: 422 },
      ),
    );
    const usuario = userEvent.setup();
    renderizarComConsultas(<AbaCartoes materiaId={ID_MATERIA} />);
    const painel = await abrirEdicao(usuario);

    await usuario.type(campo("Frente"), " e mais texto");
    await usuario.click(screen.getByRole("button", { name: "Salvar" }));

    await waitFor(() => {
      expect(campo("Frente")).toHaveAccessibleDescription(
        expect.stringContaining("Use de 1 a 10 caracteres."),
      );
    });
    expect(campo("Frente")).toHaveFocus();
    expect(campo("Frente")).toHaveValue("Qual organela produz ATP? e mais texto");
    expect(screen.getByRole("dialog", { name: "Editar cartão" })).toBeInTheDocument();
    expect((await axe(painel)).violations).toEqual([]);
  });

  it("Esc sem mudança fecha direto; com mudança pergunta antes de descartar", async () => {
    servir(cartaoFicticio());
    const usuario = userEvent.setup();
    renderizarComConsultas(<AbaCartoes materiaId={ID_MATERIA} />);

    await abrirEdicao(usuario);
    await usuario.keyboard("{Escape}");
    await waitFor(() => {
      expect(screen.queryByRole("dialog", { name: "Editar cartão" })).not.toBeInTheDocument();
    });

    await abrirEdicao(usuario);
    await usuario.type(campo("Verso"), "!");
    await usuario.keyboard("{Escape}");
    expect(
      await screen.findByRole("alertdialog", { name: "Descartar as alterações?" }),
    ).toBeInTheDocument();
  });
});
