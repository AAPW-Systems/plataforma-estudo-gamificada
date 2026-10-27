import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";
import { axe } from "vitest-axe";

import { chaves, type Materia } from "../../api/acervo";
import type { Cartao, CriacaoCartao } from "../../api/cartoes";
import {
  BASE,
  ID_MATERIA,
  configurarServidorDeTestes,
  fonteFicticia,
  materiaFicticia,
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

function item(itens: HTMLElement[], indice: number): HTMLElement {
  const encontrado = itens[indice];
  if (!encontrado) throw new Error(`item ${String(indice)} ausente`);
  return encontrado;
}

const URL_LISTA = `${BASE}/materias/${ID_MATERIA}/cartoes`;

function servir(paginas: { itens: Cartao[]; proximoCursor: string | null; total: number }[]) {
  const cursores: (string | null)[] = [];
  servidor.use(
    http.get(`${BASE}/cartoes/limites`, () => HttpResponse.json(limitesFicticios())),
    http.get(`${BASE}/materias/${ID_MATERIA}/fontes`, () =>
      HttpResponse.json({ itens: [fonteFicticia()] }),
    ),
    http.get(URL_LISTA, ({ request }) => {
      const cursor = new URL(request.url).searchParams.get("cursor");
      cursores.push(cursor);
      const indice = cursor === null ? 0 : Number(cursor.replace("pagina-", ""));
      return HttpResponse.json(paginas[indice]);
    }),
  );
  return cursores;
}

describe("AbaCartoes: lista e criação (T017; US1, RF-004, RF-009, RQ-001, RQ-003)", () => {
  it("matéria sem cartões mostra o estado vazio com 'Criar o primeiro cartão', sem violações axe", async () => {
    servir([{ itens: [], proximoCursor: null, total: 0 }]);
    const { container } = renderizarComConsultas(<AbaCartoes materiaId={ID_MATERIA} />);

    expect(
      await screen.findByRole("button", { name: "Criar o primeiro cartão" }),
    ).toBeInTheDocument();
    expect(screen.getByText(/ainda não tem cartões/)).toBeInTheDocument();
    expect(screen.queryByRole("list", { name: "Cartões da matéria" })).not.toBeInTheDocument();
    expect((await axe(container)).violations).toEqual([]);
  });

  it("cada cartão mostra frente, verso, origem com texto e ícone e situação", async () => {
    servir([
      {
        itens: [
          cartaoFicticio({ id: idCartao(1), frente: "Pergunta ativa" }),
          cartaoFicticio({
            id: idCartao(2),
            frente: "Pergunta suspensa",
            situacao: "suspenso",
            origem: "editado",
          }),
          cartaoFicticio({
            id: idCartao(3),
            frente: "Pergunta gerada",
            origem: "gerado_verificado",
            verificado: true,
          }),
        ],
        proximoCursor: null,
        total: 3,
      },
    ]);
    const { container } = renderizarComConsultas(<AbaCartoes materiaId={ID_MATERIA} />);

    const lista = await screen.findByRole("list", { name: "Cartões da matéria" });
    const itens = within(lista).getAllByRole("listitem");
    expect(itens).toHaveLength(3);
    expect(screen.getByText("3 cartões")).toBeInTheDocument();
    expect(within(item(itens, 0)).getByText("Pergunta ativa")).toBeInTheDocument();
    expect(within(item(itens, 0)).getByText("A mitocôndria.")).toBeInTheDocument();
    expect(within(item(itens, 0)).getByText("Criado por você")).toBeInTheDocument();
    expect(within(item(itens, 0)).getByText("Ativo")).toBeInTheDocument();
    expect(within(item(itens, 1)).getByText("Editado por você")).toBeInTheDocument();
    expect(within(item(itens, 1)).getByText("Suspenso")).toBeInTheDocument();
    expect(within(item(itens, 2)).getByText("Gerado e verificado")).toBeInTheDocument();
    expect((await axe(container)).violations).toEqual([]);
  });

  it("texto com quebras de linha é preservado e marcação é exibida literalmente (RQ-001)", async () => {
    servir([
      {
        itens: [
          cartaoFicticio({
            frente: "<img src=x onerror=alert(1)>",
            verso: "<script>alert(1)</script>\nsegunda linha",
          }),
        ],
        proximoCursor: null,
        total: 1,
      },
    ]);
    renderizarComConsultas(<AbaCartoes materiaId={ID_MATERIA} />);

    const frente = await screen.findByText("<img src=x onerror=alert(1)>");
    expect(frente).toHaveClass("texto-cartao");
    const verso = screen.getByText(
      (_, elemento) => elemento?.textContent === "<script>alert(1)</script>\nsegunda linha",
    );
    expect(verso).toHaveClass("texto-cartao");
    expect(document.querySelector("img")).toBeNull();
    expect(document.querySelector("script")).toBeNull();
  });

  it("a referência mostra a fonte e, apagada, o complemento 'Fonte apagada'", async () => {
    servir([
      {
        itens: [
          cartaoFicticio({
            id: idCartao(1),
            frente: "Com fonte",
            referencia: referenciaFicticia(),
          }),
          cartaoFicticio({
            id: idCartao(2),
            frente: "Fonte excluída",
            referencia: referenciaFicticia(true),
          }),
        ],
        proximoCursor: null,
        total: 2,
      },
    ]);
    renderizarComConsultas(<AbaCartoes materiaId={ID_MATERIA} />);
    const itens = within(
      await screen.findByRole("list", { name: "Cartões da matéria" }),
    ).getAllByRole("listitem");
    expect(within(item(itens, 0)).getByText(/Citologia/)).toBeInTheDocument();
    expect(within(item(itens, 0)).queryByText("Fonte apagada")).not.toBeInTheDocument();
    expect(within(item(itens, 1)).getByText(/Citologia/)).toBeInTheDocument();
    expect(within(item(itens, 1)).getByText("Fonte apagada")).toBeInTheDocument();
    expect(within(item(itens, 1)).queryByText(/Gerado e verificado/)).toBeNull();
  });

  it("'Carregar mais' pede a próxima página pelo cursor e some na última", async () => {
    const cursores = servir([
      {
        itens: [cartaoFicticio({ id: idCartao(1), frente: "Primeiro" })],
        proximoCursor: "pagina-1",
        total: 2,
      },
      {
        itens: [cartaoFicticio({ id: idCartao(2), frente: "Segundo" })],
        proximoCursor: null,
        total: 2,
      },
    ]);
    const usuario = userEvent.setup();
    renderizarComConsultas(<AbaCartoes materiaId={ID_MATERIA} />);

    await screen.findByText("Primeiro");
    await usuario.click(screen.getByRole("button", { name: "Carregar mais" }));

    expect(await screen.findByText("Segundo")).toBeInTheDocument();
    expect(screen.getByText("Primeiro")).toBeInTheDocument();
    expect(cursores).toEqual([null, "pagina-1"]);
    expect(screen.queryByRole("button", { name: "Carregar mais" })).not.toBeInTheDocument();
    expect(screen.getByText("2 cartões")).toBeInTheDocument();
  });

  it("falha ao carregar avisa com um alerta", async () => {
    servir([]);
    servidor.use(http.get(URL_LISTA, () => HttpResponse.json({}, { status: 500 })));
    renderizarComConsultas(<AbaCartoes materiaId={ID_MATERIA} />);
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Não foi possível carregar os cartões.",
    );
  });

  it("criar atualiza a lista e grava a contagem na lista de matérias, sem esperar a rede", async () => {
    let itens: Cartao[] = [];
    servir([]);
    servidor.use(
      http.get(URL_LISTA, () =>
        HttpResponse.json({ itens, proximoCursor: null, total: itens.length }),
      ),
      http.post(URL_LISTA, async ({ request }) => {
        const corpo = (await request.json()) as CriacaoCartao;
        const novo = cartaoFicticio({ frente: corpo.frente, verso: corpo.verso });
        itens = [novo, ...itens];
        return HttpResponse.json(novo, { status: 201 });
      }),
      // A lista de matérias responde devagar: o cache precisa estar certo antes dela.
      http.get(`${BASE}/materias`, async () => {
        await new Promise((resolver) => setTimeout(resolver, 5000));
        return HttpResponse.json({ itens: [materiaFicticia({ cartoesAtivos: 1 })] });
      }),
    );
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    queryClient.setQueryData<Materia[]>(chaves.materias, [materiaFicticia({ cartoesAtivos: 0 })]);
    queryClient.setQueryData<Materia>(chaves.materia(ID_MATERIA), materiaFicticia());
    const usuario = userEvent.setup();
    render(
      <QueryClientProvider client={queryClient}>
        <AbaCartoes materiaId={ID_MATERIA} />
      </QueryClientProvider>,
    );

    await usuario.click(await screen.findByRole("button", { name: "Criar o primeiro cartão" }));
    await usuario.type(screen.getByRole("textbox", { name: /^Frente/ }), "Nova pergunta");
    await usuario.type(screen.getByRole("textbox", { name: /^Verso/ }), "Nova resposta");
    await usuario.click(screen.getByRole("button", { name: "Salvar" }));

    expect(await screen.findByText("Nova pergunta")).toBeInTheDocument();
    expect(screen.getByText("1 cartão")).toBeInTheDocument();
    expect(queryClient.getQueryData<Materia[]>(chaves.materias)?.[0]?.cartoesAtivos).toBe(1);
    expect(queryClient.getQueryData<Materia>(chaves.materia(ID_MATERIA))?.cartoesAtivos).toBe(1);
  });
});
