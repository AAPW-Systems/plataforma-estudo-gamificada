import type { components } from "../../api/esquema.gerado";
import type { TomSelo } from "../../componentes/ui/SeloEstado";

type SituacaoCartao = components["schemas"]["SituacaoCartao"];

/** Situação em palavras e no tom do selo (texto e ícone, nunca só cor; RQ-003). */
export const SITUACOES: Record<SituacaoCartao, { rotulo: string; tom: TomSelo }> = {
  ativo: { rotulo: "Ativo", tom: "sucesso" },
  suspenso: { rotulo: "Suspenso", tom: "neutro" },
};

const NUMERO = new Intl.NumberFormat("pt-BR");

export function formatarNumero(numero: number): string {
  return NUMERO.format(numero);
}

export function totalDeCartoes(total: number): string {
  return `${formatarNumero(total)} ${total === 1 ? "cartão" : "cartões"}`;
}
