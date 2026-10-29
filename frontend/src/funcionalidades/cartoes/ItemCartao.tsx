import type { Cartao } from "../../api/cartoes";
import { Botao } from "../../componentes/ui/Botao";
import { SeloEstado } from "../../componentes/ui/SeloEstado";
import { SeloOrigem } from "../../componentes/ui/SeloOrigem";
import { DialogoExclusaoCartao } from "./DialogoExclusaoCartao";
import { SITUACOES, resumoDaFrente } from "./textos";

export interface ItemCartaoProps {
  cartao: Cartao;
  aoEditar: () => void;
  /** Suspende o ativo ou reativa o suspenso (US3-1, 2). */
  /** Pedidos repetidos enquanto o primeiro corre são ignorados por quem chama. */
  aoAlternarSituacao: () => void;
  aoExcluido: () => void;
}

/**
 * Um cartão na lista (RF-004, RF-009). O texto do estudante é sempre texto, com as quebras de
 * linha mantidas por `pre-wrap`; nada é interpretado como marcação (RQ-001).
 */
export function ItemCartao({ cartao, aoEditar, aoAlternarSituacao, aoExcluido }: ItemCartaoProps) {
  const situacao = SITUACOES[cartao.situacao];
  const referencia = cartao.referencia;
  const resumo = resumoDaFrente(cartao.frente);
  const acaoSituacao = cartao.situacao === "ativo" ? "Suspender" : "Reativar";
  return (
    <li className="item-cartao">
      <p className="texto-cartao item-cartao-frente">{cartao.frente}</p>
      <p className="texto-cartao item-cartao-verso">{cartao.verso}</p>
      <div className="item-cartao-detalhes">
        <SeloOrigem origem={cartao.origem} fonteApagada={referencia?.fonteApagada ?? false} />
        <SeloEstado tom={situacao.tom}>{situacao.rotulo}</SeloEstado>
        {referencia && (
          <span className="item-detalhes">
            Fonte: {referencia.titulo} ({referencia.nomeArquivo})
          </span>
        )}
      </div>
      <div className="item-cartao-acoes">
        <Botao variante="secundario" aria-label={`Editar o cartão: ${resumo}`} onPress={aoEditar}>
          Editar
        </Botao>
        <Botao
          variante="secundario"
          aria-label={`${acaoSituacao} o cartão: ${resumo}`}
          onPress={aoAlternarSituacao}
        >
          {acaoSituacao}
        </Botao>
        <DialogoExclusaoCartao cartao={cartao} aoExcluido={aoExcluido} />
      </div>
    </li>
  );
}
