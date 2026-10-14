import { describe, expect, it } from "vitest";

import {
  INTERVALO_ACOMPANHAMENTO_MS,
  ESTADOS_NAO_FINAIS,
  intervaloDeAcompanhamento,
} from "./acompanhamento";

describe("DTEC 026: acompanhamento por polling condicional", () => {
  it("consulta a cada 2 s", () => {
    expect(INTERVALO_ACOMPANHAMENTO_MS).toBe(2000);
  });

  it("os estados não finais são pendente e processando", () => {
    expect([...ESTADOS_NAO_FINAIS]).toEqual(["pendente", "processando"]);
  });

  it.each(["pendente", "processando"])("continua consultando enquanto houver item %s", (estado) => {
    expect(intervaloDeAcompanhamento([{ estado: "concluido" }, { estado }])).toBe(2000);
  });

  it("para quando todos os itens chegam a um estado final", () => {
    expect(intervaloDeAcompanhamento([{ estado: "concluido" }, { estado: "falhou" }])).toBe(false);
  });

  it("não consulta sem dados ou com lista vazia", () => {
    expect(intervaloDeAcompanhamento(undefined)).toBe(false);
    expect(intervaloDeAcompanhamento([])).toBe(false);
  });
});
