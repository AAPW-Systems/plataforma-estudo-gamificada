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
  materiaFicticia,
  simularSessaoAberta,
  usoFicticio,
} from "../../testes/acervo";
import { cartaoFicticio, idCartao, limitesFicticios } from "../../testes/cartoes";
import { renderizarComRoteador } from "../../testes/renderizar";
import { servidor } from "../../testes/servidor";

configurarServidorDeTestes();

const CARTOES: Cartao[] = [
  cartaoFicticio({ id: idCartao(1), frente: "O que é a Célula?" }),
  cartaoFicticio({ id: idCartao(2), frente: "CÉLULA eucarionte", situacao: "suspenso" }),
  cartaoFicticio({ id: idCartao(3), frente: "Mitose", origem: "editado" }),
];

interface Pedido {
  busca: string | null;
  situacao: string | null;
  origem: string | null;
  em: number;
}

/** Filtra como a API (sem acentos e sem caixa) e guarda cada pedido da lista. */
function servir(cartoes: Cartao[] = CARTOES) {
  simularSessaoAberta();
  const pedidos: Pedido[] = [];
  const simples = (t: string) => t.normalize("NFD").replace(/\p{M}/gu, "").toLowerCase();
  servidor.use(
    http.get(`${BASE}/materias/${ID_MATERIA}`, () => HttpResponse.json(materiaFicticia())),
    http.get(`${BASE}/acervo/uso`, () => HttpResponse.json(usoFicticio())),
    http.get(`${BASE}/materias/${ID_MATERIA}/fontes`, () => HttpResponse.json({ itens: [] })),
    http.get(`${BASE}/cartoes/limites`, () => HttpResponse.json(limitesFicticios())),
    http.get(`${BASE}/materias/${ID_MATERIA}/cartoes`, ({ request }) => {
      const url = new URL(request.url);
      const busca = url.searchParams.get("busca");
      const situacao = url.searchParams.get("situacao");
      const origem = url.searchParams.get("origem");
      pedidos.push({ busca, situacao, origem, em: performance.now() });
      const itens = cartoes.filter(
        (c) =>
          (!busca || simples(c.frente + c.verso).includes(simples(busca))) &&
          (!situacao || c.situacao === situacao) &&
          (!origem || c.origem === origem),
      );
      return HttpResponse.json({ itens, proximoCursor: null, total: itens.length });
    }),
  );
  return pedidos;
}

const caminho = (consulta = "") => `/materias/${ID_MATERIA}/cartoes${consulta}`;

async function lista() {
  return screen.findByRole("list", { name: "Cartões da matéria" });
}

describe("Busca e filtros da lista de cartões (T038; US4, RF-010)", () => {
  it("a busca espera 300 ms sem digitar antes de pedir, e um pedido só para o termo inteiro", async () => {
    const pedidos = servir();
    const usuario = userEvent.setup();
    renderizarComRoteador(caminho());
    await lista();

    const campo = screen.getByRole("searchbox", { name: "Buscar cartões" });
    await usuario.type(campo, "celula");
    const fimDaDigitacao = performance.now();

    await waitFor(() => {
      expect(pedidos.some((p) => p.busca === "celula")).toBe(true);
    });
    const comBusca = pedidos.filter((p) => p.busca !== null);
    expect(comBusca.map((p) => p.busca)).toEqual(["celula"]);
    expect((comBusca[0]?.em ?? 0) - fimDaDigitacao).toBeGreaterThanOrEqual(290);
    const itens = within(await lista()).getAllByRole("listitem");
    expect(itens.map((li) => within(li).getAllByRole("paragraph")[0]?.textContent)).toEqual([
      "O que é a Célula?",
      "CÉLULA eucarionte",
    ]);
  });

  it("situação e origem se combinam com a busca e vão para a URL", async () => {
    const pedidos = servir();
    const usuario = userEvent.setup();
    const { roteador } = renderizarComRoteador(caminho("?busca=celula"));
    await lista();

    await usuario.selectOptions(screen.getByRole("combobox", { name: "Situação" }), "suspenso");
    await waitFor(() => {
      expect(pedidos.at(-1)).toMatchObject({ busca: "celula", situacao: "suspenso" });
    });
    await usuario.selectOptions(screen.getByRole("combobox", { name: "Origem" }), "criado");
    await waitFor(() => {
      expect(pedidos.at(-1)).toMatchObject({
        busca: "celula",
        situacao: "suspenso",
        origem: "criado",
      });
    });
    expect(roteador.state.location.search).toEqual({
      busca: "celula",
      situacao: "suspenso",
      origem: "criado",
    });
    expect(await screen.findByText("CÉLULA eucarionte")).toBeInTheDocument();
    expect(screen.queryByText("O que é a Célula?")).not.toBeInTheDocument();
  });

  it("busca e filtros da URL são aplicados ao abrir (recarregar), e valores inválidos são ignorados", async () => {
    const pedidos = servir();
    renderizarComRoteador(caminho("?busca=celula&situacao=suspenso&origem=xpto"));
    await lista();

    expect(screen.getByRole("searchbox", { name: "Buscar cartões" })).toHaveValue("celula");
    expect(screen.getByRole("combobox", { name: "Situação" })).toHaveValue("suspenso");
    expect(screen.getByRole("combobox", { name: "Origem" })).toHaveValue("");
    expect(pedidos[0]).toMatchObject({ busca: "celula", situacao: "suspenso", origem: null });
    expect(screen.getByText("CÉLULA eucarionte")).toBeInTheDocument();
  });

  it("um termo acima de 100 caracteres na URL é cortado no teto, sem pedido inválido", async () => {
    const pedidos = servir();
    renderizarComRoteador(caminho(`?busca=${"a".repeat(150)}`));
    await screen.findByText(/Nenhum cartão corresponde/);
    expect(pedidos[0]?.busca).toHaveLength(100);
  });

  it("sem resultado mostra 'Nenhum cartão corresponde à busca', diferente da matéria vazia, e limpar volta à lista", async () => {
    servir();
    const usuario = userEvent.setup();
    const { container, roteador } = renderizarComRoteador(caminho("?busca=xyzw"));

    expect(await screen.findByText("Nenhum cartão corresponde à busca.")).toBeInTheDocument();
    expect(screen.queryByText(/ainda não tem cartões/)).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Criar o primeiro cartão" }),
    ).not.toBeInTheDocument();
    expect((await axe(container)).violations).toEqual([]);

    await usuario.click(screen.getByRole("button", { name: "Limpar busca e filtros" }));

    expect(await lista()).toBeInTheDocument();
    expect(screen.getByRole("searchbox", { name: "Buscar cartões" })).toHaveValue("");
    expect(roteador.state.location.search).toEqual({});
  });

  it("a matéria vazia mantém o próprio estado, sem a barra de busca", async () => {
    servir([]);
    renderizarComRoteador(caminho());
    expect(await screen.findByText(/ainda não tem cartões/)).toBeInTheDocument();
    expect(screen.queryByRole("searchbox", { name: "Buscar cartões" })).not.toBeInTheDocument();
  });

  it("o total acompanha os filtros e a página fica sem violações axe", async () => {
    servir();
    const usuario = userEvent.setup();
    const { container } = renderizarComRoteador(caminho());
    await lista();
    expect(screen.getByText("3 cartões")).toBeInTheDocument();

    await usuario.selectOptions(screen.getByRole("combobox", { name: "Origem" }), "editado");

    expect(await screen.findByText("1 cartão")).toBeInTheDocument();
    expect((await axe(container)).violations).toEqual([]);
  });
});
