import { useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { type Fonte, chaves } from "../../api/acervo";
import { cliente } from "../../api/cliente";
import { ErroApi } from "../../api/erros";
import { Botao } from "../../componentes/ui/Botao";
import { MensagemErroFormulario } from "../../componentes/ui/MensagemErroFormulario";
import { MENSAGEM_FALHA_GENERICA } from "../identidade/erros";

/**
 * Nova tentativa de uma fonte que falhou por motivo técnico (US1, cenário 5). O servidor decide
 * se ela é possível (`podeTentarNovamente`), e a tela só mostra o botão nesse caso. Se outra aba
 * já pediu (409 `reprocessamento_indisponivel`), nada é dito: a lista é atualizada e mostra o
 * estado verdadeiro.
 */
export function BotaoTentarNovamente({
  fonte,
}: {
  fonte: Pick<Fonte, "id" | "materiaId" | "titulo">;
}) {
  const queryClient = useQueryClient();
  const [ocupado, definirOcupado] = useState(false);
  const [mensagem, definirMensagem] = useState<string>();

  async function tentarNovamente() {
    definirOcupado(true);
    definirMensagem(undefined);
    try {
      await cliente.POST("/api/v1/fontes/{fonteId}/reprocessamento", {
        params: { path: { fonteId: fonte.id } },
      });
    } catch (erro) {
      const jaEmAndamento =
        erro instanceof ErroApi && erro.codigo === "reprocessamento_indisponivel";
      if (!jaEmAndamento) {
        definirMensagem(erro instanceof ErroApi ? erro.message : MENSAGEM_FALHA_GENERICA);
      }
    } finally {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: chaves.fontes(fonte.materiaId) }),
        queryClient.invalidateQueries({ queryKey: chaves.fonte(fonte.id) }),
      ]);
      definirOcupado(false);
    }
  }

  return (
    <>
      <Botao
        variante="secundario"
        carregando={ocupado}
        aria-label={`Tentar novamente: ${fonte.titulo}`}
        onPress={() => void tentarNovamente()}
      >
        Tentar novamente
      </Botao>
      <MensagemErroFormulario mensagem={mensagem} />
    </>
  );
}
