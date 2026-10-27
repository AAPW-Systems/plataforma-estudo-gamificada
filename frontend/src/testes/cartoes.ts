import type { components } from "../api/esquema.gerado";
import { ID_FONTE, ID_MATERIA } from "./acervo";

type Cartao = components["schemas"]["Cartao"];
type LimitesCartao = components["schemas"]["LimitesCartao"];

export const ID_CARTAO = "33333333-3333-4333-8333-333333333333";

/** Cartão fictício no formato do contrato (nada de dados reais, regra 10). */
export function cartaoFicticio(alteracoes: Partial<Cartao> = {}): Cartao {
  return {
    id: ID_CARTAO,
    materiaId: ID_MATERIA,
    frente: "Qual organela produz ATP?",
    verso: "A mitocôndria.",
    explicacao: null,
    origem: "criado",
    verificado: false,
    situacao: "ativo",
    referencia: null,
    criadoEm: "2026-10-20T12:00:00Z",
    atualizadoEm: "2026-10-20T12:00:00Z",
    ...alteracoes,
  };
}

export function referenciaFicticia(fonteApagada = false): NonNullable<Cartao["referencia"]> {
  return {
    fonteId: fonteApagada ? null : ID_FONTE,
    titulo: "Citologia",
    nomeArquivo: "biologia-citologia.pdf",
    enviadaEm: "2026-10-14T12:00:00Z",
    fonteApagada,
  };
}

export function limitesFicticios(alteracoes: Partial<LimitesCartao> = {}): LimitesCartao {
  return { frenteMax: 1000, versoMax: 2000, explicacaoMax: 1000, buscaMax: 100, ...alteracoes };
}

/** Um id de cartão distinto por número, para listas com vários itens. */
export function idCartao(numero: number): string {
  return `33333333-3333-4333-8333-${String(numero).padStart(12, "0")}`;
}
