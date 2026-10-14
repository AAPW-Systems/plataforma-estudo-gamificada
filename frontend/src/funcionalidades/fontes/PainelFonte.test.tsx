import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { describe, expect, it, vi } from "vitest";
import { axe } from "vitest-axe";

import {
  BASE,
  ID_FONTE,
  configurarServidorDeTestes,
  corpoErro,
  fonteFicticia,
  renderizarComConsultas,
} from "../../testes/acervo";
import { servidor } from "../../testes/servidor";
import { PainelFonte } from "./PainelFonte";

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

function responder(fonte: ReturnType<typeof fonteFicticia>) {
  servidor.use(http.get(`${BASE}/fontes/${ID_FONTE}`, () => HttpResponse.json(fonte)));
}

function valorDe(rotulo: string) {
  const termo = screen.getByText(rotulo, { selector: "dt" });
  const descricao = termo.nextElementSibling;
  if (!descricao) throw new Error(`sem valor para ${rotulo}`);
  return descricao;
}

describe("PainelFonte (T029; US1 cenário 3, RF-009)", () => {
  it("mostra título, arquivo, tipo, tamanho, data, páginas e trechos", async () => {
    responder(fonteFicticia());
    const { container } = renderizarComConsultas(
      <PainelFonte fonteId={ID_FONTE} aoFechar={vi.fn()} />,
    );

    expect(await screen.findByRole("heading", { name: "Citologia" })).toBeVisible();
    expect(valorDe("Arquivo")).toHaveTextContent("biologia-citologia.pdf");
    expect(valorDe("Tipo")).toHaveTextContent("PDF");
    expect(valorDe("Tamanho")).toHaveTextContent("1,0 MB");
    expect(valorDe("Enviada em")).toHaveTextContent(/14\/10\/2026/);
    expect(valorDe("Páginas")).toHaveTextContent("12");
    expect(valorDe("Trechos")).toHaveTextContent("34");
    expect(valorDe("Estado")).toHaveTextContent("Concluído");
    expect((await axe(container)).violations).toEqual([]);
  });

  it("TXT e Markdown não têm páginas: o campo nem aparece", async () => {
    responder(
      fonteFicticia({
        nomeArquivo: "anotacoes.md",
        tipoMidia: "text/markdown",
        totalPaginas: null,
        totalTrechos: 1,
      }),
    );
    renderizarComConsultas(<PainelFonte fonteId={ID_FONTE} aoFechar={vi.fn()} />);
    await screen.findByRole("heading", { name: "Citologia" });
    expect(valorDe("Tipo")).toHaveTextContent("Markdown");
    expect(screen.queryByText("Páginas", { selector: "dt" })).toBeNull();
    expect(valorDe("Trechos")).toHaveTextContent("1");
  });

  it("enquanto processa, mostra o estado e deixa a contagem em aberto", async () => {
    responder(
      fonteFicticia({
        estado: "processando",
        totalPaginas: null,
        totalTrechos: null,
        processadaEm: null,
      }),
    );
    renderizarComConsultas(<PainelFonte fonteId={ID_FONTE} aoFechar={vi.fn()} />);
    await screen.findByRole("heading", { name: "Citologia" });
    expect(valorDe("Estado")).toHaveTextContent("Processando");
    expect(valorDe("Trechos")).toHaveTextContent("—");
  });

  it("falha explicada e sem nova tentativa quando o arquivo não tem texto", async () => {
    responder(
      fonteFicticia({
        estado: "falhou",
        codigoFalha: "sem_texto",
        mensagemFalha: "Este PDF não tem texto (parece digitalizado).",
        podeTentarNovamente: false,
        totalPaginas: null,
        totalTrechos: null,
      }),
    );
    renderizarComConsultas(<PainelFonte fonteId={ID_FONTE} aoFechar={vi.fn()} />);
    await screen.findByRole("heading", { name: "Citologia" });
    expect(valorDe("Estado")).toHaveTextContent("Falhou");
    expect(screen.getByText("Este PDF não tem texto (parece digitalizado).")).toBeVisible();
    expect(screen.queryByRole("button", { name: /tentar novamente/i })).toBeNull();
  });

  it("fonte inexistente (404) mostra aviso neutro, sem detalhes do servidor", async () => {
    servidor.use(
      http.get(`${BASE}/fontes/${ID_FONTE}`, () =>
        HttpResponse.json(corpoErro("recurso_nao_encontrado", "Recurso não encontrado."), {
          status: 404,
        }),
      ),
    );
    renderizarComConsultas(<PainelFonte fonteId={ID_FONTE} aoFechar={vi.fn()} />);
    expect(await screen.findByRole("alert")).toHaveTextContent("Não encontramos esta fonte.");
  });

  it("Fechar avisa quem chamou", async () => {
    responder(fonteFicticia());
    const aoFechar = vi.fn();
    const usuario = userEvent.setup();
    renderizarComConsultas(<PainelFonte fonteId={ID_FONTE} aoFechar={aoFechar} />);
    await screen.findByRole("heading", { name: "Citologia" });
    await usuario.click(screen.getByRole("button", { name: "Fechar" }));
    expect(aoFechar).toHaveBeenCalledTimes(1);
  });

  it("acompanha uma fonte em processamento até o estado final, e para de consultar", async () => {
    let consultas = 0;
    servidor.use(
      http.get(`${BASE}/fontes/${ID_FONTE}`, () => {
        consultas += 1;
        return HttpResponse.json(
          consultas < 3
            ? fonteFicticia({ estado: "processando", totalPaginas: null, totalTrechos: null })
            : fonteFicticia(),
        );
      }),
    );
    renderizarComConsultas(<PainelFonte fonteId={ID_FONTE} aoFechar={vi.fn()} />);
    await waitFor(() => {
      expect(within(document.body).getByText("Concluído")).toBeInTheDocument();
    });
    const aoTerminar = consultas;
    await new Promise((resolver) => setTimeout(resolver, 250));
    expect(consultas).toBe(aoTerminar);
  });
});
