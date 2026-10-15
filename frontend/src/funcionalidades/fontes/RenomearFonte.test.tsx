import { useQuery } from "@tanstack/react-query";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";
import { axe } from "vitest-axe";

import { consultaFonte } from "../../api/acervo";
import {
  BASE,
  ID_FONTE,
  ID_MATERIA,
  configurarServidorDeTestes,
  corpoErro,
  fonteFicticia,
  renderizarComConsultas,
} from "../../testes/acervo";
import { servidor } from "../../testes/servidor";
import { RenomearFonte } from "./RenomearFonte";

configurarServidorDeTestes();

const URL_FONTE = `${BASE}/fontes/${ID_FONTE}`;
const FONTE = { id: ID_FONTE, materiaId: ID_MATERIA, titulo: "Citologia" };

function capturar(resposta: (corpo: { titulo: string }) => Response | Promise<Response>) {
  const recebidos: { titulo: string }[] = [];
  servidor.use(
    http.patch(URL_FONTE, async ({ request }) => {
      const corpo = (await request.json()) as { titulo: string };
      recebidos.push(corpo);
      return resposta(corpo);
    }),
  );
  return recebidos;
}

async function abrirFormulario(usuario: ReturnType<typeof userEvent.setup>) {
  await usuario.click(screen.getByRole("button", { name: "Renomear fonte" }));
  return screen.getByLabelText(/^Título da fonte/);
}

describe("RenomearFonte (T044; US3 cenário 5, RF-015, D-005)", () => {
  it("abre o formulário com o título atual e o foco nele", async () => {
    const usuario = userEvent.setup();
    renderizarComConsultas(<RenomearFonte fonte={FONTE} />);

    const campo = await abrirFormulario(usuario);

    expect(campo).toHaveValue("Citologia");
    await waitFor(() => {
      expect(campo).toHaveFocus();
    });
  });

  it("salva o novo título, atualiza a tela e devolve o foco ao botão", async () => {
    let tituloAtual = "Citologia";
    servidor.use(
      http.get(URL_FONTE, () => HttpResponse.json(fonteFicticia({ titulo: tituloAtual }))),
    );
    const recebidos = capturar(({ titulo }) => {
      tituloAtual = titulo;
      return HttpResponse.json(fonteFicticia({ titulo }));
    });
    function TituloNaTela() {
      const { data } = useQuery(consultaFonte(ID_FONTE));
      return <p data-testid="titulo-na-tela">{data?.titulo}</p>;
    }
    const usuario = userEvent.setup();
    renderizarComConsultas(
      <>
        <TituloNaTela />
        <RenomearFonte fonte={FONTE} />
      </>,
    );
    await waitFor(() => {
      expect(screen.getByTestId("titulo-na-tela")).toHaveTextContent("Citologia");
    });

    const campo = await abrirFormulario(usuario);
    await usuario.clear(campo);
    await usuario.type(campo, "Aula 3: organelas");
    await usuario.click(screen.getByRole("button", { name: "Salvar título" }));

    await waitFor(() => {
      expect(screen.queryByLabelText(/^Título da fonte/)).toBeNull();
    });
    expect(recebidos).toEqual([{ titulo: "Aula 3: organelas" }]);
    await waitFor(() => {
      expect(screen.getByTestId("titulo-na-tela")).toHaveTextContent("Aula 3: organelas");
    });
    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Renomear fonte" })).toHaveFocus();
    });
  });

  it.each([
    ["vazio", "", "Informe o título da fonte."],
    ["só espaços", "   ", "Informe o título da fonte."],
    ["121 caracteres", "t".repeat(121), "Use no máximo 120 caracteres."],
  ])("título %s é recusado no envio, sem chamar o servidor", async (_caso, digitado, mensagem) => {
    const recebidos = capturar(() => HttpResponse.json(fonteFicticia()));
    const usuario = userEvent.setup();
    renderizarComConsultas(<RenomearFonte fonte={FONTE} />);
    const campo = await abrirFormulario(usuario);
    await usuario.clear(campo);
    if (digitado) await usuario.type(campo, digitado);
    await usuario.click(screen.getByRole("button", { name: "Salvar título" }));

    expect(await screen.findByText(mensagem)).toBeVisible();
    expect(campo).toHaveAttribute("aria-invalid", "true");
    expect(recebidos).toEqual([]);
  });

  it.each([1, 120])("título de %i caractere(s) é aceito", async (tamanho) => {
    const recebidos = capturar(({ titulo }) => HttpResponse.json(fonteFicticia({ titulo })));
    const usuario = userEvent.setup();
    renderizarComConsultas(<RenomearFonte fonte={FONTE} />);
    const campo = await abrirFormulario(usuario);
    await usuario.clear(campo);
    await usuario.type(campo, "t".repeat(tamanho));
    await usuario.click(screen.getByRole("button", { name: "Salvar título" }));

    await waitFor(() => {
      expect(recebidos).toEqual([{ titulo: "t".repeat(tamanho) }]);
    });
  });

  it("422 do servidor fica junto do campo, com o valor preservado", async () => {
    capturar(() =>
      HttpResponse.json(
        corpoErro("dados_invalidos", "Alguns campos precisam de correção.", [
          { campo: "titulo", mensagem: "O título tem caracteres que não podem ser usados." },
        ]),
        { status: 422 },
      ),
    );
    const usuario = userEvent.setup();
    renderizarComConsultas(<RenomearFonte fonte={FONTE} />);
    const campo = await abrirFormulario(usuario);
    await usuario.type(campo, "!");
    await usuario.click(screen.getByRole("button", { name: "Salvar título" }));

    expect(await screen.findByText(/caracteres que não podem ser usados/)).toBeVisible();
    expect(campo).toHaveValue("Citologia!");
    expect(campo).toHaveAttribute("aria-invalid", "true");
    await waitFor(() => {
      expect(campo).toHaveFocus();
    });
  });

  it("salvar o mesmo título só fecha, e Cancelar e Escape descartam o rascunho", async () => {
    const recebidos = capturar(() => HttpResponse.json(fonteFicticia()));
    const usuario = userEvent.setup();
    renderizarComConsultas(<RenomearFonte fonte={FONTE} />);

    await abrirFormulario(usuario);
    await usuario.click(screen.getByRole("button", { name: "Salvar título" }));
    await waitFor(() => {
      expect(screen.queryByLabelText(/^Título da fonte/)).toBeNull();
    });

    let campo = await abrirFormulario(usuario);
    await usuario.type(campo, " rascunho");
    await usuario.click(screen.getByRole("button", { name: "Cancelar" }));
    await waitFor(() => {
      expect(screen.queryByLabelText(/^Título da fonte/)).toBeNull();
    });

    campo = await abrirFormulario(usuario);
    expect(campo).toHaveValue("Citologia");
    await usuario.keyboard("{Escape}");
    await waitFor(() => {
      expect(screen.queryByLabelText(/^Título da fonte/)).toBeNull();
    });
    expect(recebidos).toEqual([]);
  });

  it("fonte que já não existe (404) avisa no formulário", async () => {
    capturar(() =>
      HttpResponse.json(
        corpoErro("recurso_nao_encontrado", "Não encontramos o que você procurou."),
        {
          status: 404,
        },
      ),
    );
    const usuario = userEvent.setup();
    renderizarComConsultas(<RenomearFonte fonte={FONTE} />);
    const campo = await abrirFormulario(usuario);
    await usuario.type(campo, "x");
    await usuario.click(screen.getByRole("button", { name: "Salvar título" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(/não encontramos/i);
  });

  it("não tem violações de acessibilidade, fechado e aberto", async () => {
    const usuario = userEvent.setup();
    const { container } = renderizarComConsultas(<RenomearFonte fonte={FONTE} />);
    expect((await axe(container)).violations).toEqual([]);
    await abrirFormulario(usuario);
    expect((await axe(container)).violations).toEqual([]);
  });
});
