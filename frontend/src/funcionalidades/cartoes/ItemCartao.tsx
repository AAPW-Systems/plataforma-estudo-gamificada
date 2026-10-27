import type { Cartao } from "../../api/cartoes";
import { Botao } from "../../componentes/ui/Botao";
import { SeloEstado } from "../../componentes/ui/SeloEstado";
import { SeloOrigem } from "../../componentes/ui/SeloOrigem";
import { SITUACOES } from "./textos";

/**
 * Um cartão na lista (RF-004, RF-009). O texto do estudante é sempre texto, com as quebras de
 * linha mantidas por `pre-wrap`; nada é interpretado como marcação (RQ-001).
 */
/** Início da frente, para distinguir os botões "Editar" de cada cartão no leitor de tela. */
function resumo(texto: string): string {
  const linha = texto.split("\n", 1)[0] ?? "";
  return linha.length > 60 ? `${linha.slice(0, 60)}…` : linha;
}

export function ItemCartao({ cartao, aoEditar }: { cartao: Cartao; aoEditar: () => void }) {
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
      <div className="item-cartao-acoes">
        <Botao
          variante="secundario"
          aria-label={`Editar o cartão: ${resumo(cartao.frente)}`}
          onPress={aoEditar}
        >
          Editar
        </Botao>
      </div>
    </li>
  );
}
