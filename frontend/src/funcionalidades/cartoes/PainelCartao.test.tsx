import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { useState } from "react";
import { describe, expect, it, vi } from "vitest";
import { axe } from "vitest-axe";

import type { Cartao, CriacaoCartao } from "../../api/cartoes";
import {
  BASE,
  ID_FONTE,
  ID_MATERIA,
  configurarServidorDeTestes,
  corpoErro,
  renderizarComConsultas,
} from "../../testes/acervo";
import { cartaoFicticio, limitesFicticios } from "../../testes/cartoes";
import { servidor } from "../../testes/servidor";
import { PainelCartao } from "./PainelCartao";

configurarServidorDeTestes();

const URL_CRIAR = `${BASE}/materias/${ID_MATERIA}/cartoes`;
const FONTES = [
  { id: ID_FONTE, titulo: "Citologia" },
  { id: "44444444-4444-4444-8444-444444444444", titulo: "Genética" },
];

function capturar(resposta?: (corpo: CriacaoCartao) => Response | Promise<Response>) {
  const recebidos: CriacaoCartao[] = [];
  servidor.use(
    http.post(URL_CRIAR, async ({ request }) => {
      const corpo = (await request.json()) as CriacaoCartao;
      recebidos.push(corpo);
      if (resposta) return resposta(corpo);
      return HttpResponse.json(cartaoFicticio({ frente: corpo.frente, verso: corpo.verso }), {
        status: 201,
      });
    }),
  );
  return recebidos;
}

function Cenario({ aoCriado }: { aoCriado?: (cartao: Cartao) => void }) {
  const [aberto, definirAberto] = useState(false);
  return (
    <>
      <button
        type="button"
        onClick={() => {
          definirAberto(true);
        }}
      >
        Criar cartão
      </button>
      <PainelCartao
        materiaId={ID_MATERIA}
        limites={limitesFicticios()}
        fontes={FONTES}
        aberto={aberto}
        aoAlterarAberto={definirAberto}
        {...(aoCriado ? { aoCriado } : {})}
      />
    </>
  );
}

async function abrir(usuario: ReturnType<typeof userEvent.setup>) {
  renderizarComConsultas(<Cenario />);
  await usuario.click(screen.getByRole("button", { name: "Criar cartão" }));
  return screen.getByRole("dialog", { name: "Novo cartão" });
}

const frente = () => screen.getByRole("textbox", { name: /^Frente/ });
const verso = () => screen.getByRole("textbox", { name: /^Verso/ });
const explicacao = () => screen.getByRole("textbox", { name: /^Explicação/ });

describe("PainelCartao: criação (T017; US1 cenários 1 a 3, CS-001, RQ-003)", () => {
  it("abre com o foco na frente, os contadores dos limites do servidor e sem violações axe", async () => {
    const usuario = userEvent.setup();
    const painel = await abrir(usuario);

    await waitFor(() => {
      expect(frente()).toHaveFocus();
    });
    expect(frente()).toHaveAccessibleDescription("0 de 1.000");
    expect(verso()).toHaveAccessibleDescription("0 de 2.000");
    expect(explicacao()).toHaveAccessibleDescription("0 de 1.000");
    expect(frente()).toBeRequired();
    expect(explicacao()).not.toBeRequired();
    expect((await axe(painel)).violations).toEqual([]);
  });

  it("Ctrl+Enter salva e cria outro: o painel fica aberto, vazio e com o foco na frente", async () => {
    const recebidos = capturar();
    const usuario = userEvent.setup();
    const aoCriado = vi.fn();
    renderizarComConsultas(<Cenario aoCriado={aoCriado} />);
    await usuario.click(screen.getByRole("button", { name: "Criar cartão" }));

    await usuario.type(frente(), "Qual organela produz ATP?");
    await usuario.type(verso(), "A mitocôndria.");
    await usuario.type(explicacao(), "Linha 1{Enter}Linha 2");
    await usuario.keyboard("{Control>}{Enter}{/Control}");

    await waitFor(() => {
      expect(recebidos).toHaveLength(1);
    });
    expect(recebidos[0]).toEqual({
      frente: "Qual organela produz ATP?",
      verso: "A mitocôndria.",
      explicacao: "Linha 1\nLinha 2",
      fonteId: null,
    });
    await waitFor(() => {
      expect(frente()).toHaveValue("");
    });
    expect(verso()).toHaveValue("");
    expect(explicacao()).toHaveValue("");
    expect(screen.getByRole("dialog", { name: "Novo cartão" })).toBeInTheDocument();
    await waitFor(() => {
      expect(frente()).toHaveFocus();
    });
    expect(screen.getByRole("status")).toHaveTextContent("Cartão criado.");
    expect(aoCriado).toHaveBeenCalledTimes(1);
  });

  it("⌘+Enter (macOS) também salva e cria outro", async () => {
    const recebidos = capturar();
    const usuario = userEvent.setup();
    await abrir(usuario);
    await usuario.type(frente(), "f");
    await usuario.type(verso(), "v");
    await usuario.keyboard("{Meta>}{Enter}{/Meta}");
    await waitFor(() => {
      expect(recebidos).toHaveLength(1);
    });
    expect(screen.getByRole("dialog", { name: "Novo cartão" })).toBeInTheDocument();
  });

  it("'Salvar' cria e fecha o painel, e o foco volta ao acionador", async () => {
    const recebidos = capturar();
    const usuario = userEvent.setup();
    await abrir(usuario);
    await usuario.type(frente(), "f");
    await usuario.type(verso(), "v");
    await usuario.click(screen.getByRole("button", { name: "Salvar" }));

    await waitFor(() => {
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    });
    expect(recebidos).toHaveLength(1);
    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Criar cartão" })).toHaveFocus();
    });
  });

  it("Enter quebra a linha nos campos, sem enviar", async () => {
    const recebidos = capturar();
    const usuario = userEvent.setup();
    await abrir(usuario);
    await usuario.type(frente(), "um{Enter}dois");
    await usuario.type(verso(), "três{Enter}");
    expect(frente()).toHaveValue("um\ndois");
    expect(recebidos).toHaveLength(0);
    expect(screen.getByRole("dialog", { name: "Novo cartão" })).toBeInTheDocument();
  });

  it("Esc sem texto digitado fecha sem perguntar", async () => {
    const usuario = userEvent.setup();
    await abrir(usuario);
    await usuario.keyboard("{Escape}");
    await waitFor(() => {
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    });
  });

  it("Esc com texto digitado pede confirmação; continuar mantém o texto e descartar fecha", async () => {
    const usuario = userEvent.setup();
    await abrir(usuario);
    await usuario.type(frente(), "Rascunho");
    await usuario.keyboard("{Escape}");

    const pergunta = await screen.findByRole("alertdialog", { name: /Descartar/ });
    expect(screen.getByRole("dialog", { name: "Novo cartão" })).toBeInTheDocument();
    expect((await axe(pergunta)).violations).toEqual([]);
    await usuario.click(within(pergunta).getByRole("button", { name: "Continuar editando" }));
    expect(screen.queryByRole("alertdialog")).not.toBeInTheDocument();
    expect(frente()).toHaveValue("Rascunho");

    await usuario.click(screen.getByRole("button", { name: "Cancelar" }));
    await usuario.click(
      within(await screen.findByRole("alertdialog")).getByRole("button", { name: "Descartar" }),
    );
    await waitFor(() => {
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    });
  });

  it("valida no envio, com o erro junto do campo e o foco no primeiro inválido", async () => {
    const recebidos = capturar();
    const usuario = userEvent.setup();
    await abrir(usuario);
    expect(screen.queryByText(/Use de 1 a/)).not.toBeInTheDocument();
    await usuario.type(verso(), "   ");
    await usuario.click(screen.getByRole("button", { name: "Salvar" }));

    await waitFor(() => {
      expect(frente()).toHaveAccessibleDescription(
        expect.stringContaining("Use de 1 a 1.000 caracteres."),
      );
    });
    expect(verso()).toHaveAccessibleDescription(
      expect.stringContaining("Use de 1 a 2.000 caracteres."),
    );
    expect(frente()).toHaveFocus();
    expect(recebidos).toHaveLength(0);
  });

  it("conta em code points: 1.000 emoji cabem e 1.001 não", async () => {
    const recebidos = capturar();
    const usuario = userEvent.setup();
    await abrir(usuario);
    await usuario.click(frente());
    await usuario.paste("🧬".repeat(1001));
    await usuario.click(verso());
    await usuario.paste("v");
    await usuario.click(screen.getByRole("button", { name: "Salvar" }));
    await waitFor(() => {
      expect(frente()).toBeInvalid();
    });
    expect(recebidos).toHaveLength(0);

    await usuario.clear(frente());
    await usuario.click(frente());
    await usuario.paste("🧬".repeat(1000));
    expect(frente()).toHaveAccessibleDescription(expect.stringContaining("1.000 de 1.000"));
    await usuario.click(screen.getByRole("button", { name: "Salvar" }));
    await waitFor(() => {
      expect(recebidos).toHaveLength(1);
    });
  });

  it("422 do servidor fica junto do campo, com os valores preservados e o foco nele", async () => {
    capturar(() =>
      HttpResponse.json(
        corpoErro("dados_invalidos", "Alguns campos precisam de correção.", [
          { campo: "verso", mensagem: "Use de 1 a 5 caracteres." },
        ]),
        { status: 422 },
      ),
    );
    const usuario = userEvent.setup();
    const painel = await abrir(usuario);
    await usuario.type(frente(), "Frente");
    await usuario.type(verso(), "Verso comprido");
    await usuario.click(screen.getByRole("button", { name: "Salvar" }));

    await waitFor(() => {
      expect(verso()).toHaveAccessibleDescription(
        expect.stringContaining("Use de 1 a 5 caracteres."),
      );
    });
    expect(verso()).toHaveFocus();
    expect(frente()).toHaveValue("Frente");
    expect(verso()).toHaveValue("Verso comprido");
    expect(screen.getByRole("dialog", { name: "Novo cartão" })).toBeInTheDocument();
    expect((await axe(painel)).violations).toEqual([]);
  });

  it("fonte inválida (422 em fonteId) aparece junto da escolha da fonte", async () => {
    capturar(() =>
      HttpResponse.json(
        corpoErro("dados_invalidos", "Alguns campos precisam de correção.", [
          { campo: "fonteId", mensagem: "Escolha uma fonte desta matéria." },
        ]),
        { status: 422 },
      ),
    );
    const usuario = userEvent.setup();
    await abrir(usuario);
    await usuario.type(frente(), "f");
    await usuario.type(verso(), "v");
    await usuario.selectOptions(screen.getByRole("combobox", { name: /Fonte de referência/ }), [
      "Citologia",
    ]);
    await usuario.click(screen.getByRole("button", { name: "Salvar" }));
    const escolha = screen.getByRole("combobox", { name: /Fonte de referência/ });
    await waitFor(() => {
      expect(escolha).toHaveAccessibleDescription(
        expect.stringContaining("Escolha uma fonte desta matéria."),
      );
    });
    expect(escolha).toHaveFocus();
  });

  it("um único envio enquanto salva, mesmo com cliques e atalhos repetidos", async () => {
    let liberar: () => void = () => undefined;
    const pronto = new Promise<void>((resolver) => {
      liberar = resolver;
    });
    const recebidos = capturar(async (corpo) => {
      await pronto;
      return HttpResponse.json(cartaoFicticio({ frente: corpo.frente }), { status: 201 });
    });
    const usuario = userEvent.setup();
    await abrir(usuario);
    await usuario.type(frente(), "f");
    await usuario.type(verso(), "v");
    await usuario.click(screen.getByRole("button", { name: "Salvar e criar outro" }));
    await usuario.keyboard("{Control>}{Enter}{/Control}");
    for (const botao of screen.getAllByRole("button", { name: /Salvar|Aguarde/ })) {
      await usuario.click(botao);
    }
    liberar();
    await waitFor(() => {
      expect(frente()).toHaveValue("");
    });
    expect(recebidos).toHaveLength(1);
  });

  it("a fonte de referência é opcional e lista as fontes da matéria", async () => {
    const recebidos = capturar();
    const usuario = userEvent.setup();
    await abrir(usuario);
    const escolha = screen.getByRole("combobox", { name: /Fonte de referência/ });
    expect(
      within(escolha)
        .getAllByRole("option")
        .map((o) => o.textContent),
    ).toEqual(["Nenhuma", "Citologia", "Genética"]);
    await usuario.type(frente(), "f");
    await usuario.type(verso(), "v");
    await usuario.selectOptions(escolha, ["Genética"]);
    await usuario.keyboard("{Control>}{Enter}{/Control}");
    await waitFor(() => {
      expect(recebidos).toHaveLength(1);
    });
    expect(recebidos[0]?.fonteId).toBe(FONTES[1]?.id);
  });

  it("erro de rede mantém o rascunho no painel, avisa e deixa tentar de novo", async () => {
    let falhar = true;
    const recebidos = capturar(() =>
      falhar ? HttpResponse.error() : HttpResponse.json(cartaoFicticio(), { status: 201 }),
    );
    const usuario = userEvent.setup();
    await abrir(usuario);
    await usuario.type(frente(), "Rascunho");
    await usuario.type(verso(), "Verso");
    await usuario.click(screen.getByRole("button", { name: "Salvar" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(/Não foi possível/);
    expect(frente()).toHaveValue("Rascunho");
    expect(verso()).toHaveValue("Verso");
    falhar = false;
    await usuario.click(screen.getByRole("button", { name: "Salvar" }));
    await waitFor(() => {
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    });
    expect(recebidos).toHaveLength(2);
  });
});
