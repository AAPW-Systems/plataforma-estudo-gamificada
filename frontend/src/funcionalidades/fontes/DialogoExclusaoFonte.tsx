import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { type Fonte, chaves, consultaImpactoExclusaoFonte } from "../../api/acervo";
import { cliente } from "../../api/cliente";
import { ErroApi } from "../../api/erros";
import type { components } from "../../api/esquema.gerado";
import { Botao } from "../../componentes/ui/Botao";
import { DialogoConfirmacao } from "../../componentes/ui/DialogoConfirmacao";
import { GrupoOpcoes } from "../../componentes/ui/GrupoOpcoes";
import { MENSAGEM_FALHA_GENERICA } from "../identidade/erros";

type Contagens = components["schemas"]["ContagensExclusaoFonte"];
type Modo = components["schemas"]["ExclusaoFonteEntrada"]["modoCartoes"];

const OPCOES = [
  {
    valor: "manter",
    rotulo: "Manter os cartões",
    descricao:
      "Os cartões aceitos continuam nas suas lições, com «Fonte apagada» e sem o selo de verificado.",
  },
  {
    valor: "excluir",
    rotulo: "Excluir os cartões junto",
    descricao:
      "Os cartões aceitos desta fonte são apagados. As revisões, o XP e a sequência já registrados permanecem.",
  },
] as const;

function plural(n: number, singular: string, pluralizado: string): string {
  return `${String(n)} ${n === 1 ? singular : pluralizado}`;
}

function Impacto({ contagens }: { contagens: Contagens }) {
  const { cartoesGeradosAceitos: aceitos, cartoesAguardandoRevisao: aguardando } = contagens;
  const referencia = contagens.cartoesReferencia;
  if (aceitos + aguardando + referencia === 0) {
    return <p>Esta fonte não tem cartões ligados a ela.</p>;
  }
  return (
    <ul className="impacto-exclusao">
      <li>
        <strong>{plural(aceitos, "cartão gerado e aceito", "cartões gerados e aceitos")}</strong>{" "}
        desta fonte: seguem a sua escolha abaixo.
      </li>
      <li>
        <strong>
          {plural(aguardando, "cartão aguardando revisão", "cartões aguardando revisão")}
        </strong>
        : sempre apagados, qualquer que seja a escolha.
      </li>
      <li>
        <strong>{plural(referencia, "cartão criado por você", "cartões criados por você")}</strong>{" "}
        {referencia === 1 ? "que cita" : "que citam"} esta fonte:{" "}
        {referencia === 1 ? "mantido" : "mantidos"}, com «Fonte apagada».
      </li>
    </ul>
  );
}

/**
 * Exclusão definitiva de uma fonte, com o impacto à vista e a escolha sobre os cartões (US2,
 * RN-14, D-009). A escolha é sempre obrigatória e nunca pré-marcada, mesmo sem cartões (Princípio
 * III e quickstart). A confirmação devolve ao servidor os números que o estudante viu; se eles
 * mudaram (`409 impacto_alterado`), o diálogo recarrega o impacto, avisa e pede nova confirmação,
 * mantendo a escolha já feita. Vale para fonte em qualquer estado, inclusive `falhou` (RF-012).
 */
export function DialogoExclusaoFonte({
  fonte,
  aoExcluida,
}: {
  fonte: Pick<Fonte, "id" | "materiaId" | "titulo">;
  aoExcluida?: () => void;
}) {
  const queryClient = useQueryClient();
  const [aberto, definirAberto] = useState(false);
  const [escolha, definirEscolha] = useState<Modo>();
  const [ocupado, definirOcupado] = useState(false);
  const [mensagem, definirMensagem] = useState<string>();
  const impacto = useQuery(consultaImpactoExclusaoFonte(fonte.id, aberto));
  const contagens = impacto.data?.contagens;

  function alterarAberto(proximo: boolean) {
    definirAberto(proximo);
    if (!proximo) {
      definirEscolha(undefined);
      definirMensagem(undefined);
    }
  }

  async function concluir() {
    definirAberto(false);
    definirEscolha(undefined);
    definirMensagem(undefined);
    queryClient.removeQueries({ queryKey: chaves.fonte(fonte.id) });
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: chaves.fontes(fonte.materiaId) }),
      queryClient.invalidateQueries({ queryKey: chaves.materia(fonte.materiaId) }),
      queryClient.invalidateQueries({ queryKey: chaves.materias }),
      queryClient.invalidateQueries({ queryKey: chaves.uso }),
    ]);
    aoExcluida?.();
  }

  async function confirmar() {
    if (!contagens || ocupado) return;
    if (escolha === undefined) return;
    definirOcupado(true);
    definirMensagem(undefined);
    try {
      await cliente.POST("/api/v1/fontes/{fonteId}/exclusao", {
        params: { path: { fonteId: fonte.id } },
        body: { modoCartoes: escolha, impactoConfirmado: contagens },
      });
      await concluir();
    } catch (erro) {
      if (erro instanceof ErroApi && erro.status === 404) {
        await concluir(); // já foi excluída (outra aba): a tela só precisa convergir
      } else if (erro instanceof ErroApi && erro.codigo === "impacto_alterado") {
        definirMensagem(erro.message);
        await impacto.refetch();
      } else {
        definirMensagem(erro instanceof ErroApi ? erro.message : MENSAGEM_FALHA_GENERICA);
      }
    } finally {
      definirOcupado(false);
    }
  }

  return (
    <DialogoConfirmacao
      acionador={
        <Botao variante="secundario" aria-label={`Excluir fonte: ${fonte.titulo}`}>
          Excluir
        </Botao>
      }
      titulo={`Excluir a fonte «${fonte.titulo}»?`}
      aberto={aberto}
      aoAlterarAberto={alterarAberto}
      textoConfirmar="Excluir fonte"
      aoConfirmar={() => void confirmar()}
      ocupado={ocupado}
      confirmarDesabilitado={!contagens || impacto.isFetching || escolha === undefined}
      mensagemErro={
        mensagem ??
        (impacto.isError
          ? "Não foi possível carregar o que será afetado. Tente novamente."
          : undefined)
      }
    >
      <p>
        O arquivo e o texto extraído são apagados. Confira o que acontece com os cartões desta
        fonte:
      </p>
      {impacto.isPending && impacto.fetchStatus !== "idle" && (
        <p role="status">Calculando o que será afetado…</p>
      )}
      {contagens && <Impacto contagens={contagens} />}
      {contagens && (
        <GrupoOpcoes
          rotulo="O que fazer com os cartões gerados e aceitos"
          opcoes={OPCOES}
          valor={escolha}
          aoMudar={(valor) => {
            definirEscolha(valor as Modo);
          }}
          obrigatorio
          desabilitado={ocupado}
        />
      )}
    </DialogoConfirmacao>
  );
}
