import { fireEvent, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { describe, expect, it, vi } from "vitest";
import { axe } from "vitest-axe";

import {
  BASE,
  ID_MATERIA,
  configurarServidorDeTestes,
  corpoErro,
  fonteFicticia,
  renderizarComConsultas,
  usoFicticio,
} from "../../testes/acervo";
import { arquivoNativo, ultimoFormData, usarFormDataNativo } from "../../testes/arquivos";
import { servidor } from "../../testes/servidor";
import { EnvioFonte } from "./EnvioFonte";

configurarServidorDeTestes();
usarFormDataNativo();

const URL_ENVIO = `${BASE}/materias/${ID_MATERIA}/fontes`;

function pdf(nome = "biologia-citologia.pdf") {
  return arquivoNativo(nome, "%PDF-1.7 conteudo ficticio", "application/pdf");
}

interface Recebido {
  arquivo: { name: string; size: number } | null;
  titulo: string | null;
  tipoDoCorpo: string;
}

function capturar(resposta: () => Response | Promise<Response>) {
  const recebidos: Recebido[] = [];
  servidor.use(
    http.post(URL_ENVIO, async ({ request }) => {
      // O corpo não é lido aqui (ver `usarFormDataNativo`); os campos vêm do formulário montado.
      const formulario = ultimoFormData();
      const arquivo = formulario?.get("arquivo");
      const titulo = formulario?.get("titulo");
      recebidos.push({
        arquivo:
          arquivo !== null && arquivo !== undefined && typeof arquivo !== "string" ? arquivo : null,
        titulo: typeof titulo === "string" ? titulo : null,
        tipoDoCorpo: request.headers.get("content-type") ?? "",
      });
      return resposta();
    }),
  );
  return recebidos;
}

function entradaDeArquivo(container: HTMLElement) {
  const entrada = container.querySelector<HTMLInputElement>("input[type='file']");
  if (!entrada) throw new Error("o seletor de arquivos não foi renderizado");
  return entrada;
}

describe("EnvioFonte (T029; US1 cenários 2 e 4, RN-02)", () => {
  it("lê formatos e limites de /acervo/uso e os deixa visíveis", () => {
    const { container } = renderizarComConsultas(
      <EnvioFonte materiaId={ID_MATERIA} uso={usoFicticio()} aoEnviada={vi.fn()} />,
    );
    expect(screen.getByText(/PDF com texto, TXT ou Markdown/)).toBeVisible();
    expect(screen.getByText(/até 2 MB/)).toBeVisible();
    expect(screen.getByText(/até 200 páginas/)).toBeVisible();
    expect(entradaDeArquivo(container).accept).toBe(".pdf,.txt,.md,.markdown");
  });

  it("acompanha os limites do servidor, sem números fixos", () => {
    renderizarComConsultas(
      <EnvioFonte
        materiaId={ID_MATERIA}
        uso={usoFicticio({
          tamanhoMaximoBytes: 5 * 1024 * 1024,
          paginasMaximasPdf: 50,
          extensoesAceitas: [".pdf", ".txt"],
        })}
        aoEnviada={vi.fn()}
      />,
    );
    expect(screen.getByText(/até 5 MB/)).toBeVisible();
    expect(screen.getByText(/até 50 páginas/)).toBeVisible();
    expect(screen.queryByText(/Markdown/)).toBeNull();
  });

  it("envia o arquivo escolhido pelo botão em multipart, com o título digitado", async () => {
    const recebidos = capturar(() =>
      HttpResponse.json(fonteFicticia({ estado: "pendente" }), { status: 201 }),
    );
    const aoEnviada = vi.fn();
    const usuario = userEvent.setup();
    const { container } = renderizarComConsultas(
      <EnvioFonte materiaId={ID_MATERIA} uso={usoFicticio()} aoEnviada={aoEnviada} />,
    );

    await usuario.type(screen.getByLabelText(/^Título/), "Citologia");
    await usuario.upload(entradaDeArquivo(container), pdf());

    await waitFor(() => {
      expect(aoEnviada).toHaveBeenCalledWith(expect.objectContaining({ titulo: "Citologia" }));
    });
    expect(recebidos).toHaveLength(1);
    expect(recebidos[0]?.tipoDoCorpo).toMatch(/^multipart\/form-data; boundary=/);
    expect(recebidos[0]?.arquivo?.name).toBe("biologia-citologia.pdf");
    expect(recebidos[0]?.arquivo?.size).toBe(pdf().size);
    expect(recebidos[0]?.titulo).toBe("Citologia");
    // Depois de enviar, o título volta ao vazio para a próxima fonte.
    expect(screen.getByLabelText(/^Título/)).toHaveValue("");
  });

  it("sem título, não manda o campo (o servidor usa o nome do arquivo)", async () => {
    const recebidos = capturar(() => HttpResponse.json(fonteFicticia(), { status: 201 }));
    const usuario = userEvent.setup();
    const { container } = renderizarComConsultas(
      <EnvioFonte materiaId={ID_MATERIA} uso={usoFicticio()} aoEnviada={vi.fn()} />,
    );
    await usuario.upload(entradaDeArquivo(container), pdf());
    await waitFor(() => {
      expect(recebidos).toHaveLength(1);
    });
    expect(recebidos[0]?.titulo).toBeNull();
  });

  it("aceita o arquivo solto na zona (arrastar e soltar)", async () => {
    const recebidos = capturar(() => HttpResponse.json(fonteFicticia(), { status: 201 }));
    renderizarComConsultas(
      <EnvioFonte materiaId={ID_MATERIA} uso={usoFicticio()} aoEnviada={vi.fn()} />,
    );
    const arquivo = pdf("resumo.pdf");
    fireEvent.drop(screen.getByTestId("zona-arquivo"), {
      dataTransfer: {
        items: [{ kind: "file", type: arquivo.type, getAsFile: () => arquivo }],
        types: ["Files"],
      },
    });
    await waitFor(() => {
      expect(recebidos).toHaveLength(1);
    });
    expect(recebidos[0]?.arquivo?.name).toBe("resumo.pdf");
    expect(recebidos[0]?.arquivo?.size).toBe(arquivo.size);
  });

  it("não duplica o envio enquanto o anterior carrega", async () => {
    let liberar: () => void = () => undefined;
    const portao = new Promise<void>((resolver) => {
      liberar = resolver;
    });
    const recebidos = capturar(async () => {
      await portao;
      return HttpResponse.json(fonteFicticia(), { status: 201 });
    });
    const aoEnviada = vi.fn();
    const usuario = userEvent.setup();
    const { container } = renderizarComConsultas(
      <EnvioFonte materiaId={ID_MATERIA} uso={usoFicticio()} aoEnviada={aoEnviada} />,
    );

    await usuario.upload(entradaDeArquivo(container), pdf());
    expect(await screen.findByText("Enviando o arquivo…")).toBeVisible();
    await usuario.upload(entradaDeArquivo(container), pdf("outro.pdf"));
    fireEvent.drop(screen.getByTestId("zona-arquivo"), {
      dataTransfer: {
        items: [{ kind: "file", type: "", getAsFile: () => pdf("x.pdf") }],
        types: ["Files"],
      },
    });
    liberar();

    await waitFor(() => {
      expect(aoEnviada).toHaveBeenCalledTimes(1);
    });
    expect(recebidos).toHaveLength(1);
    expect(screen.queryByText("Enviando o arquivo…")).toBeNull();
  });

  it.each([
    [409, "fonte_duplicada", "Esta fonte já está nesta matéria: «Citologia»."],
    [422, "formato_nao_aceito", "Envie um PDF com texto, um TXT ou um Markdown."],
    [413, "arquivo_muito_grande", "O arquivo tem 3 MB e o limite é 2 MB."],
  ])(
    "recusa %i (%s) mostra a mensagem do servidor junto do campo",
    async (status, codigo, mensagem) => {
      capturar(() => HttpResponse.json(corpoErro(codigo, mensagem), { status }));
      const aoEnviada = vi.fn();
      const usuario = userEvent.setup();
      const { container } = renderizarComConsultas(
        <EnvioFonte materiaId={ID_MATERIA} uso={usoFicticio()} aoEnviada={aoEnviada} />,
      );

      await usuario.upload(entradaDeArquivo(container), pdf());

      const texto = await screen.findByText(mensagem);
      expect(texto).toBeVisible();
      // A mensagem descreve a zona de envio, e não um aviso solto na página.
      const grupo = screen.getByRole("group", { name: /Enviar fonte/ });
      expect(grupo).toContainElement(texto);
      expect(grupo.getAttribute("aria-describedby")).toContain(texto.id);
      expect(aoEnviada).not.toHaveBeenCalled();
    },
  );

  it("depois de uma recusa, um novo envio limpa a mensagem anterior e funciona", async () => {
    let tentativa = 0;
    capturar(() => {
      tentativa += 1;
      return tentativa === 1
        ? HttpResponse.json(corpoErro("formato_nao_aceito", "Formato não aceito."), { status: 422 })
        : HttpResponse.json(fonteFicticia(), { status: 201 });
    });
    const aoEnviada = vi.fn();
    const usuario = userEvent.setup();
    const { container } = renderizarComConsultas(
      <EnvioFonte materiaId={ID_MATERIA} uso={usoFicticio()} aoEnviada={aoEnviada} />,
    );
    await usuario.upload(entradaDeArquivo(container), pdf("ruim.pdf"));
    await screen.findByText("Formato não aceito.");
    await usuario.upload(entradaDeArquivo(container), pdf("bom.pdf"));
    await waitFor(() => {
      expect(aoEnviada).toHaveBeenCalledTimes(1);
    });
    expect(screen.queryByText("Formato não aceito.")).toBeNull();
  });

  it("não tem violações de acessibilidade, em repouso e com recusa", async () => {
    capturar(() =>
      HttpResponse.json(corpoErro("formato_nao_aceito", "Formato não aceito."), { status: 422 }),
    );
    const usuario = userEvent.setup();
    const { container } = renderizarComConsultas(
      <EnvioFonte materiaId={ID_MATERIA} uso={usoFicticio()} aoEnviada={vi.fn()} />,
    );
    expect((await axe(container)).violations).toEqual([]);
    await usuario.upload(entradaDeArquivo(container), pdf());
    await screen.findByText("Formato não aceito.");
    expect((await axe(container)).violations).toEqual([]);
  });
});
