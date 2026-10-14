import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { describe, expect, it, vi } from "vitest";
import { axe } from "vitest-axe";

import {
  BASE,
  ID_FONTE,
  ID_MATERIA,
  configurarServidorDeTestes,
  corpoErro,
  renderizarComConsultas,
} from "../../testes/acervo";
import { servidor } from "../../testes/servidor";
import { DialogoExclusaoFonte } from "./DialogoExclusaoFonte";

configurarServidorDeTestes();

const URL_IMPACTO = `${BASE}/fontes/${ID_FONTE}/impacto-exclusao`;
const URL_EXCLUSAO = `${BASE}/fontes/${ID_FONTE}/exclusao`;
const FONTE = { id: ID_FONTE, materiaId: ID_MATERIA, titulo: "Citologia" };

interface Contagens {
  cartoesGeradosAceitos: number;
  cartoesAguardandoRevisao: number;
  cartoesReferencia: number;
}
const COM_CARTOES: Contagens = {
  cartoesGeradosAceitos: 3,
  cartoesAguardandoRevisao: 2,
  cartoesReferencia: 1,
};

function simularImpacto(contagens: () => Contagens = () => COM_CARTOES) {
  servidor.use(
    http.get(URL_IMPACTO, () =>
      HttpResponse.json({ titulo: "Citologia", estado: "concluido", contagens: contagens() }),
    ),
  );
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
  await usuario.click(screen.getByRole("button", { name: "Excluir fonte: Citologia" }));
  return screen.findByRole("dialog");
}

function mostrar(aoExcluida = vi.fn()) {
  const resultado = renderizarComConsultas(
    <DialogoExclusaoFonte fonte={FONTE} aoExcluida={aoExcluida} />,
  );
  return { ...resultado, aoExcluida };
}

describe("DialogoExclusaoFonte (T037; US2, RQ-004)", () => {
  it("mostra título, caráter definitivo e as três contagens em linhas separadas", async () => {
    simularImpacto();
    const usuario = userEvent.setup();
    mostrar();
    const dialogo = await abrir(usuario);

    expect(
      within(dialogo).getByRole("heading", { name: /Excluir a fonte «Citologia»/ }),
    ).toBeVisible();
    expect(within(dialogo).getByText(/Ação definitiva/)).toBeVisible();
    const linhas = await within(dialogo).findAllByRole("listitem");
    expect(linhas).toHaveLength(3);
    expect(linhas[0]).toHaveTextContent("3 cartões gerados e aceitos");
    expect(linhas[1]).toHaveTextContent("2 cartões aguardando revisão");
    expect(linhas[1]).toHaveTextContent(/sempre apagados/i);
    expect(linhas[2]).toHaveTextContent("1 cartão criado por você");
    expect(linhas[2]).toHaveTextContent(/mantido/i);
    expect(linhas[2]).toHaveTextContent("Fonte apagada");
  });

  it("exige uma escolha entre manter e excluir os cartões, sem nenhuma pré-marcada", async () => {
    simularImpacto();
    const recebidos = capturarExclusao();
    const usuario = userEvent.setup();
    mostrar();
    const dialogo = await abrir(usuario);

    const manter = await within(dialogo).findByRole("radio", { name: "Manter os cartões" });
    const excluir = within(dialogo).getByRole("radio", { name: "Excluir os cartões junto" });
    expect(manter).not.toBeChecked();
    expect(excluir).not.toBeChecked();
    const confirmar = within(dialogo).getByRole("button", { name: "Excluir fonte" });
    expect(confirmar).toBeDisabled();
    await usuario.click(confirmar);
    expect(recebidos).toEqual([]);

    await usuario.click(manter);
    expect(confirmar).toBeEnabled();
  });

  it.each([
    ["Manter os cartões", "manter"],
    ["Excluir os cartões junto", "excluir"],
  ])("confirmar com «%s» envia o modo e as contagens que o estudante viu", async (opcao, modo) => {
    simularImpacto();
    const recebidos = capturarExclusao();
    const usuario = userEvent.setup();
    const { aoExcluida } = mostrar();
    const dialogo = await abrir(usuario);

    await usuario.click(await within(dialogo).findByRole("radio", { name: opcao }));
    await usuario.click(within(dialogo).getByRole("button", { name: "Excluir fonte" }));

    await waitFor(() => {
      expect(aoExcluida).toHaveBeenCalledTimes(1);
    });
    expect(recebidos).toEqual([{ modoCartoes: modo, impactoConfirmado: COM_CARTOES }]);
    await waitFor(() => {
      expect(screen.queryByRole("dialog")).toBeNull();
    });
  });

  it("sem cartões o diálogo avisa, mas a escolha segue obrigatória e vai como foi feita", async () => {
    const zeros = { cartoesGeradosAceitos: 0, cartoesAguardandoRevisao: 0, cartoesReferencia: 0 };
    simularImpacto(() => zeros);
    const recebidos = capturarExclusao();
    const usuario = userEvent.setup();
    const { aoExcluida } = mostrar();
    const dialogo = await abrir(usuario);

    expect(await within(dialogo).findByText(/não tem cartões ligados a ela/i)).toBeVisible();
    const confirmar = within(dialogo).getByRole("button", { name: "Excluir fonte" });
    expect(confirmar).toBeDisabled();
    await usuario.click(within(dialogo).getByRole("radio", { name: "Excluir os cartões junto" }));
    await usuario.click(confirmar);

    await waitFor(() => {
      expect(aoExcluida).toHaveBeenCalled();
    });
    expect(recebidos).toEqual([{ modoCartoes: "excluir", impactoConfirmado: zeros }]);
  });

  it("cancelar não muda nada e devolve o foco ao botão que abriu o diálogo", async () => {
    simularImpacto();
    const recebidos = capturarExclusao();
    const usuario = userEvent.setup();
    const { aoExcluida } = mostrar();
    const acionador = screen.getByRole("button", { name: "Excluir fonte: Citologia" });
    const dialogo = await abrir(usuario);
    await within(dialogo).findByRole("radio", { name: "Manter os cartões" });

    await usuario.click(within(dialogo).getByRole("button", { name: "Cancelar" }));

    await waitFor(() => {
      expect(screen.queryByRole("dialog")).toBeNull();
    });
    expect(recebidos).toEqual([]);
    expect(aoExcluida).not.toHaveBeenCalled();
    await waitFor(() => {
      expect(acionador).toHaveFocus();
    });
  });

  it("Escape também cancela, e o foco fica preso no diálogo enquanto ele está aberto", async () => {
    simularImpacto();
    const usuario = userEvent.setup();
    mostrar();
    const acionador = screen.getByRole("button", { name: "Excluir fonte: Citologia" });
    const dialogo = await abrir(usuario);
    await within(dialogo).findByRole("radio", { name: "Manter os cartões" });

    for (let i = 0; i < 8; i += 1) {
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
    await within(dialogo).findByRole("radio", { name: "Manter os cartões" });

    const aviso = within(dialogo)
      .getByText(/Ação definitiva/)
      .closest("p");
    expect(aviso?.querySelector("[aria-hidden='true']")?.textContent.trim()).not.toBe("");
    expect(within(dialogo).getByRole("button", { name: "Excluir fonte" })).toHaveClass(
      "botao-destrutivo",
    );
  });

  it("409 impacto_alterado recarrega o impacto, avisa e exige nova confirmação", async () => {
    let consulta = 0;
    simularImpacto(() => {
      consulta += 1;
      return consulta === 1 ? COM_CARTOES : { ...COM_CARTOES, cartoesGeradosAceitos: 4 };
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

    await usuario.click(
      await within(dialogo).findByRole("radio", { name: "Excluir os cartões junto" }),
    );
    await usuario.click(within(dialogo).getByRole("button", { name: "Excluir fonte" }));

    // O alerta aparece e os números novos entram; nada foi excluído ainda.
    expect(await within(dialogo).findByRole("alert")).toHaveTextContent(
      /mudou desde que você abriu/,
    );
    await waitFor(() => {
      expect(within(dialogo).getAllByRole("listitem")[0]).toHaveTextContent(
        "4 cartões gerados e aceitos",
      );
    });
    expect(aoExcluida).not.toHaveBeenCalled();
    expect(screen.getByRole("dialog")).toBeInTheDocument();

    // A escolha do estudante foi mantida; ele confirma de novo, agora com os números novos.
    expect(within(dialogo).getByRole("radio", { name: "Excluir os cartões junto" })).toBeChecked();
    await usuario.click(within(dialogo).getByRole("button", { name: "Excluir fonte" }));
    await waitFor(() => {
      expect(aoExcluida).toHaveBeenCalledTimes(1);
    });
    expect(recebidos[1]).toEqual({
      modoCartoes: "excluir",
      impactoConfirmado: { ...COM_CARTOES, cartoesGeradosAceitos: 4 },
    });
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
    await usuario.click(await within(dialogo).findByRole("radio", { name: "Manter os cartões" }));

    await usuario.click(within(dialogo).getByRole("button", { name: "Excluir fonte" }));
    await usuario.click(within(dialogo).getByRole("button", { name: /aguarde/i }));
    await usuario.keyboard("{Escape}");
    expect(screen.getByRole("dialog")).toBeInTheDocument(); // ocupado: não fecha
    liberar();

    await waitFor(() => {
      expect(aoExcluida).toHaveBeenCalledTimes(1);
    });
    expect(recebidos).toHaveLength(1);
  });

  it("fonte que já não existe (404) fecha o diálogo e deixa a tela se atualizar", async () => {
    simularImpacto();
    capturarExclusao(() =>
      HttpResponse.json(corpoErro("recurso_nao_encontrado", "Recurso não encontrado."), {
        status: 404,
      }),
    );
    const usuario = userEvent.setup();
    const { aoExcluida } = mostrar();
    const dialogo = await abrir(usuario);
    await usuario.click(await within(dialogo).findByRole("radio", { name: "Manter os cartões" }));
    await usuario.click(within(dialogo).getByRole("button", { name: "Excluir fonte" }));

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
    await usuario.click(await within(dialogo).findByRole("radio", { name: "Manter os cartões" }));
    await usuario.click(within(dialogo).getByRole("button", { name: "Excluir fonte" }));

    expect(await within(dialogo).findByRole("alert")).toHaveTextContent("Algo deu errado");
    expect(aoExcluida).not.toHaveBeenCalled();
    expect(within(dialogo).getByRole("button", { name: "Excluir fonte" })).toBeEnabled();
  });

  it("falha ao carregar o impacto impede a confirmação e explica", async () => {
    servidor.use(
      http.get(URL_IMPACTO, () =>
        HttpResponse.json(corpoErro("erro_interno", "Algo deu errado."), { status: 500 }),
      ),
    );
    const usuario = userEvent.setup();
    mostrar();
    const dialogo = await abrir(usuario);
    expect(await within(dialogo).findByRole("alert")).toHaveTextContent(
      /não foi possível carregar/i,
    );
    expect(within(dialogo).getByRole("button", { name: "Excluir fonte" })).toBeDisabled();
  });

  it("não tem violações de acessibilidade, fechado e aberto", async () => {
    simularImpacto();
    const usuario = userEvent.setup();
    const { container } = mostrar();
    expect((await axe(container)).violations).toEqual([]);
    const dialogo = await abrir(usuario);
    await within(dialogo).findByRole("radio", { name: "Manter os cartões" });
    expect((await axe(dialogo)).violations).toEqual([]);
  });
});
