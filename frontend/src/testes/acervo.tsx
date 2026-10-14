import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, render } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import type { ReactElement } from "react";
import { afterAll, afterEach, beforeAll, beforeEach } from "vitest";

import type { components } from "../api/esquema.gerado";
import { perfilFicticio } from "./perfil";
import { servidor } from "./servidor";

type Materia = components["schemas"]["Materia"];
type Fonte = components["schemas"]["Fonte"];
type UsoAcervo = components["schemas"]["UsoAcervo"];

export const BASE = "https://teste/api/v1";
export const ID_MATERIA = "11111111-1111-4111-8111-111111111111";
export const ID_FONTE = "22222222-2222-4222-8222-222222222222";

/** Matéria fictícia no formato do contrato (nada de dados reais, regra 10). */
export function materiaFicticia(alteracoes: Partial<Materia> = {}): Materia {
  return {
    id: ID_MATERIA,
    nome: "Biologia",
    totalFontes: 0,
    cartoesAtivos: 0,
    cartoesAguardandoRevisao: 0,
    criadoEm: "2026-10-14T12:00:00Z",
    atualizadoEm: "2026-10-14T12:00:00Z",
    ...alteracoes,
  };
}

export function fonteFicticia(alteracoes: Partial<Fonte> = {}): Fonte {
  return {
    id: ID_FONTE,
    materiaId: ID_MATERIA,
    titulo: "Citologia",
    nomeArquivo: "biologia-citologia.pdf",
    tipoMidia: "application/pdf",
    tamanhoBytes: 1_048_576,
    estado: "concluido",
    codigoFalha: null,
    mensagemFalha: null,
    podeTentarNovamente: false,
    totalPaginas: 12,
    totalTrechos: 34,
    enviadaEm: "2026-10-14T12:00:00Z",
    processadaEm: "2026-10-14T12:00:08Z",
    ...alteracoes,
  };
}

export function usoFicticio(alteracoes: Partial<UsoAcervo> = {}): UsoAcervo {
  return {
    tamanhoMaximoBytes: 2_097_152,
    extensoesAceitas: [".pdf", ".txt", ".md", ".markdown"],
    paginasMaximasPdf: 200,
    cotaMaterias: 20,
    totalMaterias: 1,
    cotaFontesPorMateria: 30,
    usoArmazenamentoBytes: 0,
    cotaArmazenamentoBytes: 104_857_600,
    ...alteracoes,
  };
}

export function corpoErro(
  codigo: string,
  mensagem: string,
  campos?: { campo: string; mensagem: string }[],
) {
  return {
    codigo,
    mensagem,
    ...(campos ? { campos } : {}),
    idRequisicao: "00000000-0000-4000-8000-000000000001",
  };
}

/** Ciclo do servidor simulado, com o cookie de CSRF que as escritas exigem. */
export function configurarServidorDeTestes() {
  beforeAll(() => {
    servidor.listen({ onUnhandledFrame: "error" });
  });
  beforeEach(() => {
    document.cookie = "__Host-csrf=token-de-teste; Path=/; Secure";
  });
  afterEach(() => {
    cleanup();
    servidor.resetHandlers();
    document.cookie = "__Host-csrf=; Max-Age=0; Path=/; Secure";
  });
  afterAll(() => {
    servidor.close();
  });
}

/** Sessão aberta, para as telas dentro da área do estudante. */
export function simularSessaoAberta() {
  servidor.use(http.get(`${BASE}/perfil`, () => HttpResponse.json(perfilFicticio())));
}

/** Para componentes que só precisam das consultas (sem roteador). */
export function renderizarComConsultas(elemento: ReactElement) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={queryClient}>{elemento}</QueryClientProvider>);
}
