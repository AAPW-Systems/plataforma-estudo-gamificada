import type { Cartao } from "../../api/cartoes";
import { SeloEstado } from "../../componentes/ui/SeloEstado";
import { SeloOrigem } from "../../componentes/ui/SeloOrigem";
import { SITUACOES } from "./textos";

/**
 * Um cartão na lista (RF-004, RF-009). O texto do estudante é sempre texto, com as quebras de
 * linha mantidas por `pre-wrap`; nada é interpretado como marcação (RQ-001).
 */
export function ItemCartao({ cartao }: { cartao: Cartao }) {
  const situacao = SITUACOES[cartao.situacao];
  const referencia = cartao.referencia;
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
    </li>
  );
}
