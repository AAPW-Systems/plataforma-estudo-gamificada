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

/** Início da frente, para distinguir as ações de cada cartão no leitor de tela. */
export function resumoDaFrente(texto: string): string {
  const linha = texto.split("\n", 1)[0] ?? "";
  return linha.length > 60 ? `${linha.slice(0, 60)}…` : linha;
}
