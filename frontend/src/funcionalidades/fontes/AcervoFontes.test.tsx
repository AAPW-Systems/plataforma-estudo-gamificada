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
  fonteFicticia,
  materiaFicticia,
  simularSessaoAberta,
  usoFicticio,
} from "../../testes/acervo";
import { renderizarComRoteador } from "../../testes/renderizar";
import { servidor } from "../../testes/servidor";

// O intervalo real é de 2 s (DTEC 026); o teste só encurta o relógio, mantendo a regra de parar.
vi.mock("../../api/acompanhamento", async (importarOriginal) => {
  const original = await importarOriginal<typeof import("../../api/acompanhamento")>();
  return {
    ...original,
    intervaloDeAcompanhamento: (itens: Parameters<typeof original.intervaloDeAcompanhamento>[0]) =>
      original.intervaloDeAcompanhamento(itens) === false ? false : 40,
  };
});

configurarServidorDeTestes();

type Fonte = ReturnType<typeof fonteFicticia>;

/** Serve a matéria, o uso e a lista de fontes; `lista` pode mudar a cada consulta. */
function simularMateria(lista: () => Fonte[]) {
  const contagem = { listas: 0 };
  simularSessaoAberta();
  servidor.use(
    http.get(`${BASE}/materias/${ID_MATERIA}`, () => HttpResponse.json(materiaFicticia())),
    http.get(`${BASE}/acervo/uso`, () => HttpResponse.json(usoFicticio())),
    http.get(`${BASE}/materias/${ID_MATERIA}/fontes`, () => {
      contagem.listas += 1;
      return HttpResponse.json({ itens: lista() });
    }),
  );
  return contagem;
}

async function abrirMateria() {
  const resultado = renderizarComRoteador(`/materias/${ID_MATERIA}`);
  await screen.findByRole("heading", { name: "Biologia" });
  return resultado;
}

function acervo() {
  return screen.getByRole("region", { name: "Fontes" });
}

const falha = (alteracoes: Partial<Fonte> = {}) =>
  fonteFicticia({
    estado: "falhou",
    codigoFalha: "falha_tecnica",
    mensagemFalha: "Não foi possível processar o arquivo agora.",
    podeTentarNovamente: true,
    totalPaginas: null,
    totalTrechos: null,
    ...alteracoes,
  });

describe("Acervo da matéria (T029; US1 cenário 2, RN-03)", () => {
  it("sem fontes, convida a enviar a primeira", async () => {
    simularMateria(() => []);
    await abrirMateria();
    expect(await within(acervo()).findByText("Enviar a primeira fonte")).toBeVisible();
    expect(within(acervo()).queryByRole("list")).toBeNull();
  });

  it("lista as fontes com título, tipo e estado em texto e ícone", async () => {
    simularMateria(() => [
      fonteFicticia(),
      fonteFicticia({
        id: "33333333-3333-4333-8333-333333333333",
        titulo: "Anotações",
        nomeArquivo: "anotacoes.md",
        tipoMidia: "text/markdown",
        estado: "pendente",
        totalPaginas: null,
        totalTrechos: null,
        processadaEm: null,
      }),
    ]);
    await abrirMateria();
    const itens = await within(acervo()).findAllByRole("listitem");
    expect(itens).toHaveLength(2);
    expect(itens[0]).toHaveTextContent("Citologia");
    expect(itens[0]).toHaveTextContent("PDF");
    expect(itens[0]).toHaveTextContent("Concluído");
    expect(itens[1]).toHaveTextContent("Markdown");
    expect(itens[1]).toHaveTextContent("Pendente");
    // O estado nunca depende só da cor: cada selo traz um ícone decorativo ao lado do texto.
    expect(itens[1]?.querySelector(".selo [aria-hidden='true']")).not.toBeNull();
  });

  it("cada fonte abre o seu painel", async () => {
    simularMateria(() => [fonteFicticia()]);
    servidor.use(http.get(`${BASE}/fontes/${ID_FONTE}`, () => HttpResponse.json(fonteFicticia())));
    const usuario = userEvent.setup();
    const { roteador } = await abrirMateria();
    await usuario.click(await within(acervo()).findByRole("link", { name: /Citologia/ }));
    expect(roteador.state.location.pathname).toBe(`/materias/${ID_MATERIA}/fontes/${ID_FONTE}`);
    expect(await screen.findByRole("heading", { name: "Citologia", level: 3 })).toBeVisible();
  });

  it("acompanha do pendente ao concluído sozinho e para de consultar no estado final", async () => {
    let consulta = 0;
    const contagem = simularMateria(() => {
      consulta += 1;
      const estado = consulta === 1 ? "pendente" : consulta === 2 ? "processando" : "concluido";
      return [fonteFicticia({ estado })];
    });
    await abrirMateria();
    await within(acervo()).findByText("Pendente");
    await within(acervo()).findByText("Processando");
    await within(acervo()).findByText("Concluído");

    const aoTerminar = contagem.listas;
    await new Promise((resolver) => setTimeout(resolver, 300));
    expect(contagem.listas).toBe(aoTerminar);
  });

  it("anuncia a mudança de estado numa região viva, sem anunciar a carga inicial", async () => {
    let concluida = false;
    simularMateria(() => [fonteFicticia({ estado: concluida ? "concluido" : "processando" })]);
    await abrirMateria();
    const anuncios = await screen.findByRole("status", { name: "Atualizações do acervo" });
    expect(anuncios).toHaveAttribute("aria-live", "polite");
    await within(acervo()).findByText("Processando");
    // A carga inicial não é anunciada: a região só fala quando algo muda.
    expect(anuncios).toBeEmptyDOMElement();

    concluida = true;
    await waitFor(() => {
      expect(anuncios).toHaveTextContent("Citologia: Concluído");
    });
  });

  it("falha técnica explica o motivo e oferece Tentar novamente, que reprocessa", async () => {
    let reprocessada = false;
    simularMateria(() => [reprocessada ? fonteFicticia({ estado: "processando" }) : falha()]);
    servidor.use(
      http.post(`${BASE}/fontes/${ID_FONTE}/reprocessamento`, () => {
        reprocessada = true;
        return HttpResponse.json(fonteFicticia({ estado: "processando" }), { status: 202 });
      }),
    );
    const usuario = userEvent.setup();
    await abrirMateria();
    expect(
      await within(acervo()).findByText("Não foi possível processar o arquivo agora."),
    ).toBeVisible();
    await usuario.click(within(acervo()).getByRole("button", { name: /Tentar novamente/ }));
    await within(acervo()).findByText("Processando");
    expect(within(acervo()).queryByRole("button", { name: /Tentar novamente/ })).toBeNull();
  });

  it("PDF sem texto falha sem o botão Tentar novamente", async () => {
    simularMateria(() => [
      falha({
        codigoFalha: "sem_texto",
        mensagemFalha: "Este PDF não tem texto (parece digitalizado).",
        podeTentarNovamente: false,
      }),
    ]);
    await abrirMateria();
    expect(
      await within(acervo()).findByText("Este PDF não tem texto (parece digitalizado)."),
    ).toBeVisible();
    expect(within(acervo()).getByText("Falhou")).toBeVisible();
    expect(within(acervo()).queryByRole("button", { name: /Tentar novamente/ })).toBeNull();
  });

  it("409 de reprocessamento indisponível atualiza a lista em silêncio", async () => {
    let jaAndando = false;
    simularMateria(() => [jaAndando ? fonteFicticia({ estado: "processando" }) : falha()]);
    servidor.use(
      http.post(`${BASE}/fontes/${ID_FONTE}/reprocessamento`, () => {
        jaAndando = true; // outra aba já pediu a nova tentativa
        return HttpResponse.json(
          corpoErro("reprocessamento_indisponivel", "Esta fonte não pode ser reprocessada agora."),
          { status: 409 },
        );
      }),
    );
    const usuario = userEvent.setup();
    await abrirMateria();
    await usuario.click(await within(acervo()).findByRole("button", { name: /Tentar novamente/ }));
    await within(acervo()).findByText("Processando");
    expect(screen.queryByRole("alert")).toBeNull();
  });

  it("enviar na página confirma o envio e a fonte entra no acervo como Pendente", async () => {
    let enviada = false;
    simularMateria(() => (enviada ? [fonteFicticia({ estado: "pendente" })] : []));
    servidor.use(
      http.post(`${BASE}/materias/${ID_MATERIA}/fontes`, () => {
        enviada = true;
        return HttpResponse.json(fonteFicticia({ estado: "pendente" }), { status: 201 });
      }),
    );
    const usuario = userEvent.setup();
    const { container } = await abrirMateria();
    await within(acervo()).findByText("Enviar a primeira fonte");

    const entrada = await waitFor(() => {
      const achada = container.querySelector<HTMLInputElement>("input[type='file']");
      if (!achada) throw new Error("sem seletor de arquivos");
      return achada;
    });
    await usuario.upload(
      entrada,
      new File(["%PDF-1.7 x"], "citologia.pdf", { type: "application/pdf" }),
    );

    expect(await screen.findByText("Fonte «Citologia» enviada.")).toBeVisible();
    expect(await within(acervo()).findByText("Pendente")).toBeVisible();
  });

  it("não tem violações de acessibilidade com fontes em vários estados", async () => {
    simularMateria(() => [
      fonteFicticia(),
      falha({ id: "44444444-4444-4444-8444-444444444444", titulo: "Escaneado" }),
    ]);
    const { container } = await abrirMateria();
    await within(acervo()).findByText("Escaneado");
    expect((await axe(container)).violations).toEqual([]);
  });
});
