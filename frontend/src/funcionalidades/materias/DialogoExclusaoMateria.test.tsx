import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { describe, expect, it, vi } from "vitest";
import { axe } from "vitest-axe";

import {
  BASE,
  ID_MATERIA,
  configurarServidorDeTestes,
  corpoErro,
  renderizarComConsultas,
} from "../../testes/acervo";
import { servidor } from "../../testes/servidor";
import { DialogoExclusaoMateria } from "./DialogoExclusaoMateria";

configurarServidorDeTestes();

const URL_IMPACTO = `${BASE}/materias/${ID_MATERIA}/impacto-exclusao`;
const URL_EXCLUSAO = `${BASE}/materias/${ID_MATERIA}/exclusao`;
const MATERIA = { id: ID_MATERIA, nome: "Biologia" };

interface Contagens {
  fontes: number;
  cartoesAtivos: number;
  cartoesAguardandoRevisao: number;
}
const COM_DADOS: Contagens = { fontes: 2, cartoesAtivos: 7, cartoesAguardandoRevisao: 3 };

function simularImpacto(contagens: () => Contagens = () => COM_DADOS, nome = "Biologia") {
  servidor.use(http.get(URL_IMPACTO, () => HttpResponse.json({ nome, contagens: contagens() })));
}

function capturarExclusao(
  resposta: () => Response | Promise<Response> = () => new HttpResponse(null, { status: 204 }),
) {
  const recebidos: unknown[] = [];
  servidor.use(
    http.post(URL_EXCLUSAO, async ({ request }) => {
      recebidos.push(await request.json());
      return resposta();
    }),
  );
  return recebidos;
}

async function abrir(usuario: ReturnType<typeof userEvent.setup>) {
  await usuario.click(screen.getByRole("button", { name: "Excluir matéria: Biologia" }));
  const dialogo = await screen.findByRole("dialog");
  await within(dialogo).findAllByRole("listitem"); // o impacto carregou
  return dialogo;
}

function campoDoNome(dialogo: HTMLElement) {
  return within(dialogo).getByLabelText(/^Digite o nome da matéria para confirmar/);
}

function mostrar(aoExcluida = vi.fn()) {
  const resultado = renderizarComConsultas(
    <DialogoExclusaoMateria materia={MATERIA} aoExcluida={aoExcluida} />,
  );
  return { ...resultado, aoExcluida };
}

describe("DialogoExclusaoMateria (T044; US3 cenários 3 e 4, RF-011)", () => {
  it("mostra título, caráter definitivo e as três contagens em linhas separadas", async () => {
    simularImpacto();
    const usuario = userEvent.setup();
    mostrar();
    const dialogo = await abrir(usuario);

    expect(
      within(dialogo).getByRole("heading", { name: /Excluir a matéria «Biologia»/ }),
    ).toBeVisible();
    expect(within(dialogo).getByText(/Ação definitiva/)).toBeVisible();
    const linhas = within(dialogo).getAllByRole("listitem");
    expect(linhas).toHaveLength(3);
    expect(linhas[0]).toHaveTextContent("2 fontes");
    expect(linhas[1]).toHaveTextContent("7 cartões ativos ou suspensos");
    expect(linhas[2]).toHaveTextContent("3 cartões aguardando revisão");
    expect(
      within(dialogo).getByText(/revisões, o XP e a sequência já registrados permanecem/i),
    ).toBeVisible();
  });

  it("usa o singular com uma fonte e um cartão", async () => {
    simularImpacto(() => ({ fontes: 1, cartoesAtivos: 1, cartoesAguardandoRevisao: 1 }));
    const usuario = userEvent.setup();
    mostrar();
    const dialogo = await abrir(usuario);

    const linhas = within(dialogo).getAllByRole("listitem");
    expect(linhas[0]).toHaveTextContent(/^1 fonte\b/);
    expect(linhas[1]).toHaveTextContent("1 cartão ativo ou suspenso");
    expect(linhas[2]).toHaveTextContent("1 cartão aguardando revisão");
  });

  it("matéria vazia avisa que só ela será apagada, e ainda exige o nome", async () => {
    simularImpacto(() => ({ fontes: 0, cartoesAtivos: 0, cartoesAguardandoRevisao: 0 }));
    const usuario = userEvent.setup();
    mostrar();
    await usuario.click(screen.getByRole("button", { name: "Excluir matéria: Biologia" }));
    const dialogo = await screen.findByRole("dialog");

    expect(await within(dialogo).findByText(/não tem fontes nem cartões/i)).toBeVisible();
    expect(within(dialogo).getByRole("button", { name: "Excluir matéria" })).toBeDisabled();
  });

  it("só habilita a exclusão com o nome exato (a caixa conta; espaços nas pontas não)", async () => {
    simularImpacto();
    const usuario = userEvent.setup();
    mostrar();
    const dialogo = await abrir(usuario);
    const confirmar = within(dialogo).getByRole("button", { name: "Excluir matéria" });
    const campo = campoDoNome(dialogo);
    expect(confirmar).toBeDisabled();

    await usuario.type(campo, "biologia");
    expect(confirmar).toBeDisabled();
    await usuario.clear(campo);
    await usuario.type(campo, "Biolog");
    expect(confirmar).toBeDisabled();
    await usuario.clear(campo);
    await usuario.type(campo, "Biologia");
    expect(confirmar).toBeEnabled();
    await usuario.clear(campo);
    await usuario.type(campo, "  Biologia ");
    expect(confirmar).toBeEnabled();
    await usuario.type(campo, "!");
    expect(confirmar).toBeDisabled();
  });

  it("aceita o nome com acento digitado na forma decomposta", async () => {
    simularImpacto(() => COM_DADOS, "Física");
    const usuario = userEvent.setup();
    renderizarComConsultas(
      <DialogoExclusaoMateria materia={{ id: ID_MATERIA, nome: "Física" }} aoExcluida={vi.fn()} />,
    );
    await usuario.click(screen.getByRole("button", { name: "Excluir matéria: Física" }));
    const dialogo = await screen.findByRole("dialog");
    await within(dialogo).findAllByRole("listitem");

    await usuario.type(campoDoNome(dialogo), "Fi\u0301sica"); // "í" decomposto (NFD)

    expect(within(dialogo).getByRole("button", { name: "Excluir matéria" })).toBeEnabled();
  });

  it("confirmar envia o nome digitado e as contagens que o estudante viu, e avisa quem chamou", async () => {
    simularImpacto();
    const recebidos = capturarExclusao();
    const usuario = userEvent.setup();
    const { aoExcluida } = mostrar();
    const dialogo = await abrir(usuario);

    await usuario.type(campoDoNome(dialogo), "Biologia");
    await usuario.click(within(dialogo).getByRole("button", { name: "Excluir matéria" }));

    await waitFor(() => {
      expect(aoExcluida).toHaveBeenCalledTimes(1);
    });
    expect(recebidos).toEqual([{ nomeConfirmacao: "Biologia", impactoConfirmado: COM_DADOS }]);
    await waitFor(() => {
      expect(screen.queryByRole("dialog")).toBeNull();
    });
  });

  it("Enter no campo do nome confirma, mas só se o nome confere", async () => {
    simularImpacto();
    const recebidos = capturarExclusao();
    const usuario = userEvent.setup();
    const { aoExcluida } = mostrar();
    const dialogo = await abrir(usuario);

    await usuario.type(campoDoNome(dialogo), "errado{Enter}");
    expect(recebidos).toEqual([]);

    await usuario.clear(campoDoNome(dialogo));
    await usuario.type(campoDoNome(dialogo), "Biologia{Enter}");
    await waitFor(() => {
      expect(aoExcluida).toHaveBeenCalledTimes(1);
    });
    expect(recebidos).toHaveLength(1);
  });

  it("cancelar não muda nada, descarta o nome digitado e devolve o foco ao botão", async () => {
    simularImpacto();
    const recebidos = capturarExclusao();
    const usuario = userEvent.setup();
    const { aoExcluida } = mostrar();
    const acionador = screen.getByRole("button", { name: "Excluir matéria: Biologia" });
    let dialogo = await abrir(usuario);
    await usuario.type(campoDoNome(dialogo), "Biologia");

    await usuario.click(within(dialogo).getByRole("button", { name: "Cancelar" }));

    await waitFor(() => {
      expect(screen.queryByRole("dialog")).toBeNull();
    });
    expect(recebidos).toEqual([]);
    expect(aoExcluida).not.toHaveBeenCalled();
    await waitFor(() => {
      expect(acionador).toHaveFocus();
    });
    dialogo = await abrir(usuario);
    expect(campoDoNome(dialogo)).toHaveValue("");
    expect(within(dialogo).getByRole("button", { name: "Excluir matéria" })).toBeDisabled();
  });

  it("Escape também cancela, e o foco fica preso no diálogo enquanto ele está aberto", async () => {
    simularImpacto();
    const usuario = userEvent.setup();
    mostrar();
    const acionador = screen.getByRole("button", { name: "Excluir matéria: Biologia" });
    const dialogo = await abrir(usuario);

    for (let i = 0; i < 6; i += 1) {
      await usuario.tab();
      expect(dialogo).toContainElement(document.activeElement as HTMLElement);
    }

    await usuario.keyboard("{Escape}");
    await waitFor(() => {
      expect(screen.queryByRole("dialog")).toBeNull();
    });
    await waitFor(() => {
      expect(acionador).toHaveFocus();
    });
  });

  it("a ação destrutiva se distingue por texto e ícone, e não só pela cor", async () => {
    simularImpacto();
    const usuario = userEvent.setup();
    mostrar();
    const dialogo = await abrir(usuario);

    const aviso = within(dialogo)
      .getByText(/Ação definitiva/)
      .closest("p");
    expect(aviso?.querySelector("[aria-hidden='true']")?.textContent.trim()).not.toBe("");
    expect(within(dialogo).getByRole("button", { name: "Excluir matéria" })).toHaveClass(
      "botao-destrutivo",
    );
  });

  it("409 impacto_alterado recarrega o impacto, avisa, mantém o nome digitado e exige nova confirmação", async () => {
    let consulta = 0;
    simularImpacto(() => {
      consulta += 1;
      return consulta === 1 ? COM_DADOS : { ...COM_DADOS, cartoesAtivos: 9 };
    });
    let tentativas = 0;
    const recebidos = capturarExclusao(() => {
      tentativas += 1;
      return tentativas === 1
        ? HttpResponse.json(
            corpoErro(
              "impacto_alterado",
              "O conteúdo mudou desde que você abriu esta confirmação. Confira os números atualizados.",
            ),
            { status: 409 },
          )
        : new HttpResponse(null, { status: 204 });
    });
    const usuario = userEvent.setup();
    const { aoExcluida } = mostrar();
    const dialogo = await abrir(usuario);

    await usuario.type(campoDoNome(dialogo), "Biologia");
    await usuario.click(within(dialogo).getByRole("button", { name: "Excluir matéria" }));

    expect(await within(dialogo).findByRole("alert")).toHaveTextContent(
      /mudou desde que você abriu/,
    );
    await waitFor(() => {
      expect(within(dialogo).getAllByRole("listitem")[1]).toHaveTextContent(
        "9 cartões ativos ou suspensos",
      );
    });
    expect(aoExcluida).not.toHaveBeenCalled();
    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(campoDoNome(dialogo)).toHaveValue("Biologia");

    await usuario.click(within(dialogo).getByRole("button", { name: "Excluir matéria" }));
    await waitFor(() => {
      expect(aoExcluida).toHaveBeenCalledTimes(1);
    });
    expect(recebidos[1]).toEqual({
      nomeConfirmacao: "Biologia",
      impactoConfirmado: { ...COM_DADOS, cartoesAtivos: 9 },
    });
  });

  it("422 confirmacao_invalida aparece junto do campo do nome, com o valor preservado", async () => {
    simularImpacto();
    capturarExclusao(() =>
      HttpResponse.json(
        corpoErro("confirmacao_invalida", "O nome digitado não confere com o nome da matéria.", [
          { campo: "nomeConfirmacao", mensagem: "Digite o nome exatamente como aparece." },
        ]),
        { status: 422 },
      ),
    );
    const usuario = userEvent.setup();
    const { aoExcluida } = mostrar();
    const dialogo = await abrir(usuario);
    await usuario.type(campoDoNome(dialogo), "Biologia");
    await usuario.click(within(dialogo).getByRole("button", { name: "Excluir matéria" }));

    expect(
      await within(dialogo).findByText("Digite o nome exatamente como aparece."),
    ).toBeVisible();
    expect(campoDoNome(dialogo)).toHaveValue("Biologia");
    expect(campoDoNome(dialogo)).toHaveAttribute("aria-invalid", "true");
    expect(aoExcluida).not.toHaveBeenCalled();
  });

  it("não envia duas vezes enquanto a exclusão está em andamento", async () => {
    simularImpacto();
    let liberar: () => void = () => undefined;
    const portao = new Promise<void>((resolver) => {
      liberar = resolver;
    });
    const recebidos = capturarExclusao(async () => {
      await portao;
      return new HttpResponse(null, { status: 204 });
    });
    const usuario = userEvent.setup();
    const { aoExcluida } = mostrar();
    const dialogo = await abrir(usuario);
    await usuario.type(campoDoNome(dialogo), "Biologia");

    await usuario.click(within(dialogo).getByRole("button", { name: "Excluir matéria" }));
    await usuario.click(within(dialogo).getByRole("button", { name: /aguarde/i }));
    await usuario.keyboard("{Escape}");
    expect(screen.getByRole("dialog")).toBeInTheDocument(); // ocupado: não fecha
    liberar();

    await waitFor(() => {
      expect(aoExcluida).toHaveBeenCalledTimes(1);
    });
    expect(recebidos).toHaveLength(1);
  });

  it("matéria que já não existe (404) fecha o diálogo e deixa a tela se atualizar", async () => {
    simularImpacto();
    capturarExclusao(() =>
      HttpResponse.json(corpoErro("recurso_nao_encontrado", "Recurso não encontrado."), {
        status: 404,
      }),
    );
    const usuario = userEvent.setup();
    const { aoExcluida } = mostrar();
    const dialogo = await abrir(usuario);
    await usuario.type(campoDoNome(dialogo), "Biologia");
    await usuario.click(within(dialogo).getByRole("button", { name: "Excluir matéria" }));

    await waitFor(() => {
      expect(aoExcluida).toHaveBeenCalledTimes(1);
    });
  });

  it("falha inesperada mostra a mensagem no diálogo e permite tentar de novo", async () => {
    simularImpacto();
    capturarExclusao(() =>
      HttpResponse.json(corpoErro("erro_interno", "Algo deu errado. Tente novamente."), {
        status: 500,
      }),
    );
    const usuario = userEvent.setup();
    const { aoExcluida } = mostrar();
    const dialogo = await abrir(usuario);
    await usuario.type(campoDoNome(dialogo), "Biologia");
    await usuario.click(within(dialogo).getByRole("button", { name: "Excluir matéria" }));

    expect(await within(dialogo).findByRole("alert")).toHaveTextContent("Algo deu errado");
    expect(aoExcluida).not.toHaveBeenCalled();
    expect(within(dialogo).getByRole("button", { name: "Excluir matéria" })).toBeEnabled();
  });

  it("falha ao carregar o impacto impede a confirmação e explica", async () => {
    servidor.use(
      http.get(URL_IMPACTO, () =>
        HttpResponse.json(corpoErro("erro_interno", "Algo deu errado."), { status: 500 }),
      ),
    );
    const usuario = userEvent.setup();
    mostrar();
    await usuario.click(screen.getByRole("button", { name: "Excluir matéria: Biologia" }));
    const dialogo = await screen.findByRole("dialog");

    expect(await within(dialogo).findByRole("alert")).toHaveTextContent(
      /não foi possível carregar/i,
    );
    await usuario.type(campoDoNome(dialogo), "Biologia");
    expect(within(dialogo).getByRole("button", { name: "Excluir matéria" })).toBeDisabled();
  });

  it("não tem violações de acessibilidade, fechado, aberto e com erro de campo", async () => {
    simularImpacto();
    capturarExclusao(() =>
      HttpResponse.json(
        corpoErro("confirmacao_invalida", "O nome digitado não confere com o nome da matéria.", [
          { campo: "nomeConfirmacao", mensagem: "Digite o nome exatamente como aparece." },
        ]),
        { status: 422 },
      ),
    );
    const usuario = userEvent.setup();
    const { container } = mostrar();
    expect((await axe(container)).violations).toEqual([]);
    const dialogo = await abrir(usuario);
    expect((await axe(dialogo)).violations).toEqual([]);

    await usuario.type(campoDoNome(dialogo), "Biologia");
    await usuario.click(within(dialogo).getByRole("button", { name: "Excluir matéria" }));
    await within(dialogo).findByText("Digite o nome exatamente como aparece.");
    expect((await axe(dialogo)).violations).toEqual([]);
  });
});
