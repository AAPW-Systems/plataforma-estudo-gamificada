import { useQuery } from "@tanstack/react-query";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";
import { axe } from "vitest-axe";

import { chaves, consultaMateria } from "../../api/acervo";
import {
  BASE,
  ID_MATERIA,
  configurarServidorDeTestes,
  corpoErro,
  materiaFicticia,
  renderizarComConsultas,
} from "../../testes/acervo";
import { servidor } from "../../testes/servidor";
import { RenomearMateria } from "./RenomearMateria";

configurarServidorDeTestes();

const URL_MATERIA = `${BASE}/materias/${ID_MATERIA}`;
const MATERIA = { id: ID_MATERIA, nome: "Biologia" };

function capturar(resposta: (corpo: { nome: string }) => Response | Promise<Response>) {
  const recebidos: { nome: string }[] = [];
  servidor.use(
    http.patch(URL_MATERIA, async ({ request }) => {
      const corpo = (await request.json()) as { nome: string };
      recebidos.push(corpo);
      return resposta(corpo);
    }),
  );
  return recebidos;
}

async function abrirFormulario(usuario: ReturnType<typeof userEvent.setup>) {
  await usuario.click(screen.getByRole("button", { name: "Renomear matéria" }));
  return screen.getByLabelText(/^Nome da matéria/);
}

describe("RenomearMateria (T044; US3 cenários 1 e 2, RF-001)", () => {
  it("começa só com o botão e abre o formulário com o nome atual, já com o foco nele", async () => {
    const usuario = userEvent.setup();
    renderizarComConsultas(<RenomearMateria materia={MATERIA} />);
    expect(screen.queryByLabelText(/^Nome da matéria/)).toBeNull();

    const campo = await abrirFormulario(usuario);

    expect(campo).toHaveValue("Biologia");
    await waitFor(() => {
      expect(campo).toHaveFocus();
    });
    expect(screen.getByRole("button", { name: "Salvar nome" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Cancelar" })).toBeInTheDocument();
  });

  it("salva o novo nome normalizado pelo servidor, fecha o formulário e devolve o foco", async () => {
    let nomeAtual = "Biologia";
    servidor.use(
      http.get(URL_MATERIA, () => HttpResponse.json(materiaFicticia({ nome: nomeAtual }))),
    );
    const recebidos = capturar(({ nome }) => {
      nomeAtual = nome;
      return HttpResponse.json(materiaFicticia({ nome }));
    });
    function NomeNaTela() {
      const { data } = useQuery(consultaMateria(ID_MATERIA));
      return <p data-testid="nome-na-tela">{data?.nome}</p>;
    }
    const usuario = userEvent.setup();
    renderizarComConsultas(
      <>
        <NomeNaTela />
        <RenomearMateria materia={MATERIA} />
      </>,
    );
    await waitFor(() => {
      expect(screen.getByTestId("nome-na-tela")).toHaveTextContent("Biologia");
    });

    const campo = await abrirFormulario(usuario);
    await usuario.clear(campo);
    await usuario.type(campo, "Genética");
    await usuario.click(screen.getByRole("button", { name: "Salvar nome" }));

    await waitFor(() => {
      expect(screen.queryByLabelText(/^Nome da matéria/)).toBeNull();
    });
    expect(recebidos).toEqual([{ nome: "Genética" }]);
    // A consulta da matéria foi invalidada: o novo nome aparece sem recarregar a página.
    await waitFor(() => {
      expect(screen.getByTestId("nome-na-tela")).toHaveTextContent("Genética");
    });
    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Renomear matéria" })).toHaveFocus();
    });
  });

  it("atualiza o nome na lista em cache na hora, para a lista não mostrar o nome velho ao voltar", async () => {
    capturar(({ nome }) => HttpResponse.json(materiaFicticia({ nome })));
    const outra = materiaFicticia({ id: "33333333-3333-4333-8333-333333333333", nome: "Química" });
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    queryClient.setQueryData(chaves.materias, [materiaFicticia(), outra]);
    const usuario = userEvent.setup();
    render(
      <QueryClientProvider client={queryClient}>
        <RenomearMateria materia={MATERIA} />
      </QueryClientProvider>,
    );
    const campo = await abrirFormulario(usuario);
    await usuario.clear(campo);
    await usuario.type(campo, "Genética");
    await usuario.click(screen.getByRole("button", { name: "Salvar nome" }));

    await waitFor(() => {
      expect(screen.queryByLabelText(/^Nome da matéria/)).toBeNull();
    });
    const lista = queryClient.getQueryData<{ id: string; nome: string }[]>(chaves.materias);
    expect(lista?.map((m) => m.nome)).toEqual(["Genética", "Química"]);
    expect(queryClient.getQueryData<{ nome: string }>(chaves.materia(ID_MATERIA))?.nome).toBe(
      "Genética",
    );
  });

  it("nome em uso (409) fica junto do campo, com o valor preservado, o foco nele e o formulário aberto", async () => {
    capturar(() =>
      HttpResponse.json(
        corpoErro("materia_nome_em_uso", "Você já tem uma matéria com esse nome.", [
          { campo: "nome", mensagem: "Você já tem uma matéria com esse nome." },
        ]),
        { status: 409 },
      ),
    );
    const usuario = userEvent.setup();
    renderizarComConsultas(<RenomearMateria materia={MATERIA} />);
    const campo = await abrirFormulario(usuario);
    await usuario.clear(campo);
    await usuario.type(campo, "química");
    await usuario.click(screen.getByRole("button", { name: "Salvar nome" }));

    expect(await screen.findByText("Você já tem uma matéria com esse nome.")).toBeVisible();
    expect(campo).toHaveValue("química");
    expect(campo).toHaveAttribute("aria-invalid", "true");
    await waitFor(() => {
      expect(campo).toHaveFocus();
    });
    expect(screen.getByRole("button", { name: "Salvar nome" })).toBeEnabled();
  });

  it("422 do servidor também aparece junto do campo", async () => {
    capturar(() =>
      HttpResponse.json(
        corpoErro("dados_invalidos", "Alguns campos precisam de correção.", [
          { campo: "nome", mensagem: "O nome tem caracteres que não podem ser usados." },
        ]),
        { status: 422 },
      ),
    );
    const usuario = userEvent.setup();
    renderizarComConsultas(<RenomearMateria materia={MATERIA} />);
    const campo = await abrirFormulario(usuario);
    await usuario.type(campo, "x");
    await usuario.click(screen.getByRole("button", { name: "Salvar nome" }));

    expect(await screen.findByText(/caracteres que não podem ser usados/)).toBeVisible();
    expect(campo).toHaveAttribute("aria-invalid", "true");
  });

  it.each([
    ["vazio", "", "Informe o nome da matéria."],
    ["só espaços", "   ", "Informe o nome da matéria."],
    ["61 caracteres", "x".repeat(61), "Use no máximo 60 caracteres."],
  ])("nome %s é recusado no envio, sem chamar o servidor", async (_caso, digitado, mensagem) => {
    const recebidos = capturar(() => HttpResponse.json(materiaFicticia()));
    const usuario = userEvent.setup();
    renderizarComConsultas(<RenomearMateria materia={MATERIA} />);
    const campo = await abrirFormulario(usuario);
    await usuario.clear(campo);
    if (digitado) await usuario.type(campo, digitado);
    await usuario.click(screen.getByRole("button", { name: "Salvar nome" }));

    expect(await screen.findByText(mensagem)).toBeVisible();
    expect(campo).toHaveAttribute("aria-invalid", "true");
    expect(recebidos).toEqual([]);
  });

  it("60 caracteres é aceito", async () => {
    const recebidos = capturar(({ nome }) => HttpResponse.json(materiaFicticia({ nome })));
    const usuario = userEvent.setup();
    renderizarComConsultas(<RenomearMateria materia={MATERIA} />);
    const campo = await abrirFormulario(usuario);
    await usuario.clear(campo);
    await usuario.type(campo, "y".repeat(60));
    await usuario.click(screen.getByRole("button", { name: "Salvar nome" }));

    await waitFor(() => {
      expect(recebidos).toEqual([{ nome: "y".repeat(60) }]);
    });
  });

  it("salvar o mesmo nome só fecha o formulário, sem chamar o servidor", async () => {
    const recebidos = capturar(() => HttpResponse.json(materiaFicticia()));
    const usuario = userEvent.setup();
    renderizarComConsultas(<RenomearMateria materia={MATERIA} />);
    await abrirFormulario(usuario);

    await usuario.click(screen.getByRole("button", { name: "Salvar nome" }));

    await waitFor(() => {
      expect(screen.queryByLabelText(/^Nome da matéria/)).toBeNull();
    });
    expect(recebidos).toEqual([]);
  });

  it("Cancelar e Escape fecham sem salvar, descartam o que foi digitado e devolvem o foco", async () => {
    const recebidos = capturar(() => HttpResponse.json(materiaFicticia()));
    const usuario = userEvent.setup();
    renderizarComConsultas(<RenomearMateria materia={MATERIA} />);

    let campo = await abrirFormulario(usuario);
    await usuario.type(campo, " rascunho");
    await usuario.click(screen.getByRole("button", { name: "Cancelar" }));
    await waitFor(() => {
      expect(screen.queryByLabelText(/^Nome da matéria/)).toBeNull();
    });
    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Renomear matéria" })).toHaveFocus();
    });

    campo = await abrirFormulario(usuario);
    expect(campo).toHaveValue("Biologia"); // o rascunho anterior não voltou
    await usuario.keyboard("{Escape}");
    await waitFor(() => {
      expect(screen.queryByLabelText(/^Nome da matéria/)).toBeNull();
    });
    expect(recebidos).toEqual([]);
  });

  it("não envia duas vezes enquanto salva", async () => {
    let liberar: () => void = () => undefined;
    const portao = new Promise<void>((resolver) => {
      liberar = resolver;
    });
    const recebidos = capturar(async ({ nome }) => {
      await portao;
      return HttpResponse.json(materiaFicticia({ nome }));
    });
    const usuario = userEvent.setup();
    renderizarComConsultas(<RenomearMateria materia={MATERIA} />);
    const campo = await abrirFormulario(usuario);
    await usuario.clear(campo);
    await usuario.type(campo, "Genética");

    await usuario.click(screen.getByRole("button", { name: "Salvar nome" }));
    await usuario.click(await screen.findByRole("button", { name: /aguarde/i }));
    liberar();

    await waitFor(() => {
      expect(screen.queryByLabelText(/^Nome da matéria/)).toBeNull();
    });
    expect(recebidos).toHaveLength(1);
  });

  it("falha inesperada mostra a mensagem no formulário e permite tentar de novo", async () => {
    capturar(() =>
      HttpResponse.json(corpoErro("erro_interno", "Algo deu errado."), { status: 500 }),
    );
    const usuario = userEvent.setup();
    renderizarComConsultas(<RenomearMateria materia={MATERIA} />);
    const campo = await abrirFormulario(usuario);
    await usuario.type(campo, "x");
    await usuario.click(screen.getByRole("button", { name: "Salvar nome" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Algo deu errado");
    expect(screen.getByRole("button", { name: "Salvar nome" })).toBeEnabled();
  });

  it("não tem violações de acessibilidade, fechado, aberto e com erro", async () => {
    capturar(() =>
      HttpResponse.json(
        corpoErro("materia_nome_em_uso", "Você já tem uma matéria com esse nome.", [
          { campo: "nome", mensagem: "Você já tem uma matéria com esse nome." },
        ]),
        { status: 409 },
      ),
    );
    const usuario = userEvent.setup();
    const { container } = renderizarComConsultas(<RenomearMateria materia={MATERIA} />);
    expect((await axe(container)).violations).toEqual([]);

    const campo = await abrirFormulario(usuario);
    expect((await axe(container)).violations).toEqual([]);

    await usuario.type(campo, "x");
    await usuario.click(screen.getByRole("button", { name: "Salvar nome" }));
    await screen.findByText("Você já tem uma matéria com esse nome.");
    expect((await axe(container)).violations).toEqual([]);
  });
});
