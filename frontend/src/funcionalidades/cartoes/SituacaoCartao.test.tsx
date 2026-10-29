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
  fonteFicticia,
  renderizarComConsultas,
} from "../../testes/acervo";
import {
  cartaoFicticio,
  idCartao,
  limitesFicticios,
  referenciaFicticia,
} from "../../testes/cartoes";
import { servidor } from "../../testes/servidor";
import { AbaCartoes } from "./AbaCartoes";

configurarServidorDeTestes();

/** Lista servida a partir de um estado que as ações alteram, como a API faria. */
function servir(iniciais: Cartao[]) {
  let cartoes = [...iniciais];
  const pedidos: string[] = [];
  const trocar = (id: string, situacao: Cartao["situacao"]) => {
    cartoes = cartoes.map((c) => (c.id === id ? { ...c, situacao } : c));
    return cartoes.find((c) => c.id === id);
  };
  servidor.use(
    http.get(`${BASE}/cartoes/limites`, () => HttpResponse.json(limitesFicticios())),
    http.get(`${BASE}/materias/${ID_MATERIA}/fontes`, () =>
      HttpResponse.json({ itens: [fonteFicticia()] }),
    ),
    http.get(`${BASE}/materias/${ID_MATERIA}/cartoes`, () =>
      HttpResponse.json({ itens: cartoes, proximoCursor: null, total: cartoes.length }),
    ),
    http.post(`${BASE}/cartoes/:id/suspensao`, ({ params }) => {
      pedidos.push(`suspender ${String(params.id)}`);
      return HttpResponse.json(trocar(String(params.id), "suspenso"));
    }),
    http.post(`${BASE}/cartoes/:id/reativacao`, ({ params }) => {
      pedidos.push(`reativar ${String(params.id)}`);
      return HttpResponse.json(trocar(String(params.id), "ativo"));
    }),
    http.delete(`${BASE}/cartoes/:id`, ({ params }) => {
      pedidos.push(`excluir ${String(params.id)}`);
      cartoes = cartoes.filter((c) => c.id !== params.id);
      return new HttpResponse(null, { status: 204 });
    }),
  );
  return pedidos;
}

async function lista() {
  return screen.findByRole("list", { name: "Cartões da matéria" });
}

function item(frente: string): HTMLElement {
  const encontrado = screen
    .getAllByRole("listitem")
    .find((li) => within(li).queryByText(frente) !== null);
  if (!encontrado) throw new Error(`cartão ${frente} ausente`);
  return encontrado;
}

describe("Suspender, reativar e excluir (T031; US3, RF-007, RF-008, RF-009)", () => {
  it("'Suspender' muda a situação na lista e anuncia pela região viva; 'Reativar' desfaz", async () => {
    const pedidos = servir([cartaoFicticio({ id: idCartao(1), frente: "Mitose" })]);
    const usuario = userEvent.setup();
    renderizarComConsultas(<AbaCartoes materiaId={ID_MATERIA} />);
    await lista();

    await usuario.click(within(item("Mitose")).getByRole("button", { name: /^Suspender/ }));

    expect(await within(item("Mitose")).findByText("Suspenso")).toBeInTheDocument();
    expect(screen.getByRole("status")).toHaveTextContent("Cartão suspenso.");
    const reativar = within(item("Mitose")).getByRole("button", { name: /^Reativar/ });
    expect(reativar).toHaveAccessibleName("Reativar o cartão: Mitose");

    await usuario.click(reativar);

    expect(await within(item("Mitose")).findByText("Ativo")).toBeInTheDocument();
    expect(screen.getByRole("status")).toHaveTextContent("Cartão reativado.");
    expect(within(item("Mitose")).getByRole("button", { name: /^Suspender/ })).toHaveFocus();
    expect(pedidos).toEqual([`suspender ${idCartao(1)}`, `reativar ${idCartao(1)}`]);
  });

  it("durante o pedido o botão segue habilitado e com o foco, e cliques repetidos não repetem o pedido", async () => {
    // Desabilitar o botão tiraria o foco dele no navegador real (achado da T033).
    const pedidos = servir([cartaoFicticio({ id: idCartao(1), frente: "Mitose" })]);
    let liberar: () => void = () => undefined;
    const pendente = new Promise<void>((resolver) => {
      liberar = resolver;
    });
    servidor.use(
      http.post(`${BASE}/cartoes/:id/suspensao`, async () => {
        pedidos.push("suspender lento");
        await pendente;
        return HttpResponse.json(
          cartaoFicticio({ id: idCartao(1), frente: "Mitose", situacao: "suspenso" }),
        );
      }),
    );
    const usuario = userEvent.setup();
    renderizarComConsultas(<AbaCartoes materiaId={ID_MATERIA} />);
    await lista();
    const botao = within(item("Mitose")).getByRole("button", { name: /^Suspender/ });

    await usuario.click(botao);
    await usuario.click(botao);
    await usuario.keyboard("{Enter}");

    expect(botao).toBeEnabled();
    expect(botao).toHaveFocus();
    liberar();
    expect(await within(item("Mitose")).findByText("Suspenso")).toBeInTheDocument();
    expect(pedidos).toEqual(["suspender lento"]);
  });

  it("o diálogo de exclusão avisa que é definitiva, prende o foco e devolve-o ao cancelar, sem violações axe", async () => {
    const pedidos = servir([cartaoFicticio({ frente: "Mitose" })]);
    const usuario = userEvent.setup();
    renderizarComConsultas(<AbaCartoes materiaId={ID_MATERIA} />);
    await lista();
    const acionador = within(item("Mitose")).getByRole("button", { name: /^Excluir/ });
    expect(acionador).toHaveAccessibleName("Excluir o cartão: Mitose");

    await usuario.click(acionador);
    const dialogo = await screen.findByRole("dialog", { name: "Excluir este cartão?" });

    expect(within(dialogo).getByText(/Ação definitiva/)).toBeVisible();
    expect(within(dialogo).getByText("Mitose")).toBeVisible();
    expect(within(dialogo).getByText(/revisões e o XP já registrados permanecem/)).toBeVisible();
    const confirmar = within(dialogo).getByRole("button", { name: "Excluir cartão" });
    expect(confirmar).toHaveClass("botao-destrutivo");
    expect((await axe(dialogo)).violations).toEqual([]);
    // Foco preso: o Tab percorre só o diálogo.
    for (let i = 0; i < 4; i++) {
      await usuario.tab();
      expect(dialogo).toContainElement(document.activeElement as HTMLElement);
    }

    await usuario.click(within(dialogo).getByRole("button", { name: "Cancelar" }));

    await waitFor(() => {
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    });
    await waitFor(() => {
      expect(acionador).toHaveFocus();
    });
    expect(pedidos).toEqual([]);
    expect(item("Mitose")).toBeInTheDocument();
  });

  it("confirmar a exclusão tira o cartão da lista, anuncia e leva o foco ao título da seção", async () => {
    const pedidos = servir([
      cartaoFicticio({ id: idCartao(1), frente: "Mitose" }),
      cartaoFicticio({ id: idCartao(2), frente: "Meiose" }),
    ]);
    const usuario = userEvent.setup();
    renderizarComConsultas(<AbaCartoes materiaId={ID_MATERIA} />);
    await lista();

    await usuario.click(within(item("Mitose")).getByRole("button", { name: /^Excluir/ }));
    const dialogo = await screen.findByRole("dialog", { name: "Excluir este cartão?" });
    await usuario.click(within(dialogo).getByRole("button", { name: "Excluir cartão" }));

    await waitFor(() => {
      expect(screen.queryByText("Mitose")).not.toBeInTheDocument();
    });
    expect(screen.getByText("Meiose")).toBeInTheDocument();
    expect(screen.getByRole("status")).toHaveTextContent("Cartão excluído.");
    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Cartões" })).toHaveFocus();
    });
    expect(pedidos).toEqual([`excluir ${idCartao(1)}`]);
  });

  it("'Fonte apagada' aparece junto da descrição da origem, com a lista sem violações axe", async () => {
    servir([
      cartaoFicticio({ id: idCartao(1), frente: "Com fonte", referencia: referenciaFicticia() }),
      cartaoFicticio({
        id: idCartao(2),
        frente: "Fonte excluída",
        situacao: "suspenso",
        referencia: referenciaFicticia(true),
      }),
    ]);
    const { container } = renderizarComConsultas(<AbaCartoes materiaId={ID_MATERIA} />);
    await lista();

    const apagada = item("Fonte excluída");
    const origem = within(apagada).getByText("Criado por você").closest(".selos-origem");
    expect(origem).not.toBeNull();
    expect(within(origem as HTMLElement).getByText("Fonte apagada")).toBeInTheDocument();
    expect(within(item("Com fonte")).queryByText("Fonte apagada")).not.toBeInTheDocument();
    expect(within(apagada).getByRole("button", { name: /^Reativar/ })).toBeInTheDocument();
    expect((await axe(container)).violations).toEqual([]);
  });
});
