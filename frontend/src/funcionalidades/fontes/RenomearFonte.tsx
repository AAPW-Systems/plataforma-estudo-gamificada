import { useQueryClient } from "@tanstack/react-query";

import { type Fonte, chaves } from "../../api/acervo";
import { cliente } from "../../api/cliente";
import { RenomearInline } from "../acervo/RenomearInline";
import { esquemaTituloFonte } from "./esquemas";

/**
 * Renomeação do título da fonte (US3, cenário 5; D-005). Só o título muda: o arquivo, os trechos
 * e a descrição da origem já copiada nos cartões permanecem.
 */
export function RenomearFonte({ fonte }: { fonte: Pick<Fonte, "id" | "materiaId" | "titulo"> }) {
  const queryClient = useQueryClient();

  async function salvar(titulo: string) {
    await cliente.PATCH("/api/v1/fontes/{fonteId}", {
      params: { path: { fonteId: fonte.id } },
      body: { titulo },
    });
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: chaves.fonte(fonte.id) }),
      queryClient.invalidateQueries({ queryKey: chaves.fontes(fonte.materiaId) }),
    ]);
  }

  return (
    <RenomearInline
      rotuloBotao="Renomear fonte"
      rotuloCampo="Título da fonte"
      rotuloSalvar="Salvar título"
      valorAtual={fonte.titulo}
      campoApi="titulo"
      validar={(digitado) => {
        const resultado = esquemaTituloFonte.safeParse({ titulo: digitado });
        return resultado.success
          ? { valor: resultado.data.titulo }
          : { erro: resultado.error.issues[0]?.message ?? "Informe o título da fonte." };
      }}
      salvar={salvar}
    />
  );
}
