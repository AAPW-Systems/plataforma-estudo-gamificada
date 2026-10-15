import { useQueryClient } from "@tanstack/react-query";

import { type Materia, chaves } from "../../api/acervo";
import { cliente } from "../../api/cliente";
import { RenomearInline } from "../acervo/RenomearInline";
import { esquemaMateria } from "./esquemas";

/**
 * Renomeação da matéria (US3, cenários 1 e 2). O servidor normaliza o nome e recusa o que outra
 * matéria do estudante já usa, sem diferenciar maiúsculas e minúsculas (`409`, junto do campo).
 */
export function RenomearMateria({ materia }: { materia: Pick<Materia, "id" | "nome"> }) {
  const queryClient = useQueryClient();

  async function salvar(nome: string) {
    const { data } = await cliente.PATCH("/api/v1/materias/{materiaId}", {
      params: { path: { materiaId: materia.id } },
      body: { nome },
    });
    if (data) {
      // A lista não está montada nesta página: sem isto, ela mostraria o nome velho ao voltar.
      queryClient.setQueryData(chaves.materia(materia.id), data);
      queryClient.setQueryData<Materia[]>(chaves.materias, (lista) =>
        lista?.map((item) => (item.id === materia.id ? data : item)),
      );
    }
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: chaves.materia(materia.id) }),
      queryClient.invalidateQueries({ queryKey: chaves.materias }),
    ]);
  }

  return (
    <RenomearInline
      rotuloBotao="Renomear matéria"
      rotuloCampo="Nome da matéria"
      rotuloSalvar="Salvar nome"
      valorAtual={materia.nome}
      campoApi="nome"
      validar={(digitado) => {
        const resultado = esquemaMateria.safeParse({ nome: digitado });
        return resultado.success
          ? { valor: resultado.data.nome }
          : { erro: resultado.error.issues[0]?.message ?? "Informe o nome da matéria." };
      }}
      salvar={salvar}
    />
  );
}
