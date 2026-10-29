import type { FiltrosCartoes, OrigemCartao, SituacaoCartao } from "../../api/cartoes";
import { limites } from "../../api/limites.gerado";

export const SITUACOES_FILTRO: readonly { valor: SituacaoCartao; rotulo: string }[] = [
  { valor: "ativo", rotulo: "Ativos" },
  { valor: "suspenso", rotulo: "Suspensos" },
];

export const ORIGENS_FILTRO: readonly { valor: OrigemCartao; rotulo: string }[] = [
  { valor: "criado", rotulo: "Criado por você" },
  { valor: "editado", rotulo: "Editado por você" },
  { valor: "gerado_verificado", rotulo: "Gerado e verificado" },
];

/** O teto da busca vem do contrato (DTEC 033, estático): a URL nunca gera um pedido recusado. */
export const BUSCA_MAXIMA = limites.LimitesCartao.buscaMax.maximum;

function de<T extends string>(opcoes: readonly { valor: T }[], valor: unknown): T | undefined {
  return opcoes.find((opcao) => opcao.valor === valor)?.valor;
}

/**
 * Parâmetros da URL da aba Cartões, validados: valor desconhecido é ignorado, a busca é cortada
 * no teto, e busca vazia ou só com espaços some (equivale a sem busca, como na API).
 */
export function validarFiltros(parametros: Record<string, unknown>): FiltrosCartoes {
  const filtros: FiltrosCartoes = {};
  const { busca } = parametros;
  if (typeof busca === "string" && busca.trim() !== "") {
    filtros.busca = Array.from(busca).slice(0, BUSCA_MAXIMA).join("");
  }
  const situacao = de(SITUACOES_FILTRO, parametros.situacao);
  if (situacao) filtros.situacao = situacao;
  const origem = de(ORIGENS_FILTRO, parametros.origem);
  if (origem) filtros.origem = origem;
  return filtros;
}

export function haFiltros(filtros: FiltrosCartoes): boolean {
  return Boolean(filtros.busca ?? filtros.situacao ?? filtros.origem);
}

/** Uma mudança de filtro; `undefined` tira o filtro. */
export type MudancaFiltros = { [K in keyof FiltrosCartoes]?: FiltrosCartoes[K] | undefined };

/** Aplica a mudança e devolve só os filtros presentes (a URL e o cache não guardam vazios). */
export function combinarFiltros(filtros: FiltrosCartoes, mudanca: MudancaFiltros): FiltrosCartoes {
  return validarFiltros({ ...filtros, ...mudanca });
}
