import { useState } from "react";

import { type Cartao, excluirCartao } from "../../api/cartoes";
import { ErroApi } from "../../api/erros";
import { Botao } from "../../componentes/ui/Botao";
import { DialogoConfirmacao } from "../../componentes/ui/DialogoConfirmacao";
import { MENSAGEM_FALHA_GENERICA } from "../identidade/erros";
import { resumoDaFrente } from "./textos";

/**
 * Exclusão definitiva de um cartão (US3-3; RF-008, RQ-004), sobre o diálogo destrutivo da 002:
 * aviso de ação definitiva, foco preso e devolvido ao acionador ao cancelar. Um `404` (já
 * excluído em outra aba) conta como excluído: a tela só precisa convergir.
 */
export function DialogoExclusaoCartao({
  cartao,
  aoExcluido,
}: {
  cartao: Pick<Cartao, "id" | "frente">;
  aoExcluido: () => void;
}) {
  const [aberto, definirAberto] = useState(false);
  const [ocupado, definirOcupado] = useState(false);
  const [mensagem, definirMensagem] = useState<string>();
  const resumo = resumoDaFrente(cartao.frente);

  async function confirmar() {
    definirOcupado(true);
    definirMensagem(undefined);
    try {
      await excluirCartao(cartao.id);
      definirAberto(false);
      aoExcluido();
    } catch (erro) {
      if (erro instanceof ErroApi && erro.status === 404) {
        definirAberto(false);
        aoExcluido();
      } else {
        definirMensagem(MENSAGEM_FALHA_GENERICA);
      }
    } finally {
      definirOcupado(false);
    }
  }

  return (
    <DialogoConfirmacao
      acionador={
        <Botao variante="discreto" aria-label={`Excluir o cartão: ${resumo}`}>
          Excluir
        </Botao>
      }
      titulo="Excluir este cartão?"
      aberto={aberto}
      aoAlterarAberto={(proximo) => {
        definirAberto(proximo);
        if (!proximo) definirMensagem(undefined);
      }}
      textoConfirmar="Excluir cartão"
      aoConfirmar={() => {
        void confirmar();
      }}
      ocupado={ocupado}
      mensagemErro={mensagem}
    >
      <p className="texto-cartao">
        <strong>{resumo}</strong>
      </p>
      <p>O cartão sai da matéria e das lições. As revisões e o XP já registrados permanecem.</p>
    </DialogoConfirmacao>
  );
}
