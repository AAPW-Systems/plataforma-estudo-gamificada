import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { type Materia, chaves, consultaImpactoExclusaoMateria } from "../../api/acervo";
import { cliente } from "../../api/cliente";
import { ErroApi } from "../../api/erros";
import type { components } from "../../api/esquema.gerado";
import { Botao } from "../../componentes/ui/Botao";
import { CampoTexto } from "../../componentes/ui/CampoTexto";
import { DialogoConfirmacao } from "../../componentes/ui/DialogoConfirmacao";
import { MENSAGEM_FALHA_GENERICA } from "../identidade/erros";

type Contagens = components["schemas"]["ContagensExclusaoMateria"];

function plural(n: number, singular: string, pluralizado: string): string {
  return `${String(n)} ${n === 1 ? singular : pluralizado}`;
}

/** O servidor compara depois de NFC e sem espaços nas extremidades, diferenciando a caixa. */
function nomeConfere(digitado: string, nome: string): boolean {
  const normalizado = digitado.normalize("NFC").trim();
  return normalizado !== "" && normalizado === nome.normalize("NFC").trim();
}

function Impacto({ contagens }: { contagens: Contagens }) {
  const { fontes, cartoesAtivos: ativos, cartoesAguardandoRevisao: aguardando } = contagens;
  if (fontes + ativos + aguardando === 0) {
    return <p>Esta matéria não tem fontes nem cartões: só ela será apagada.</p>;
  }
  return (
    <>
      <ul className="impacto-exclusao">
        <li>
          <strong>{plural(fontes, "fonte", "fontes")}</strong>, com {fontes === 1 ? "o" : "os"}{" "}
          {fontes === 1 ? "arquivo e o texto extraído" : "arquivos e os textos extraídos"}.
        </li>
        <li>
          <strong>
            {plural(ativos, "cartão ativo ou suspenso", "cartões ativos ou suspensos")}
          </strong>
          .
        </li>
        <li>
          <strong>
            {plural(aguardando, "cartão aguardando revisão", "cartões aguardando revisão")}
          </strong>
          .
        </li>
      </ul>
      <p>As revisões, o XP e a sequência já registrados permanecem.</p>
    </>
  );
}

/**
 * Exclusão definitiva de uma matéria em cascata, com o impacto à vista e a confirmação pelo nome
 * digitado (US3, cenários 3 e 4; RF-011). A confirmação devolve ao servidor os números que o
 * estudante viu; se mudaram (`409 impacto_alterado`), o diálogo recarrega o impacto, avisa e
 * mantém o nome digitado. O servidor é a autoridade na comparação do nome (`422`).
 */
export function DialogoExclusaoMateria({
  materia,
  aoExcluida,
}: {
  materia: Pick<Materia, "id" | "nome">;
  aoExcluida?: () => void;
}) {
  const queryClient = useQueryClient();
  const [aberto, definirAberto] = useState(false);
  const [digitado, definirDigitado] = useState("");
  const [erroNome, definirErroNome] = useState<string>();
  const [ocupado, definirOcupado] = useState(false);
  const [mensagem, definirMensagem] = useState<string>();
  const impacto = useQuery(consultaImpactoExclusaoMateria(materia.id, aberto));
  const contagens = impacto.data?.contagens;
  const nome = impacto.data?.nome ?? materia.nome;

  function limpar() {
    definirDigitado("");
    definirErroNome(undefined);
    definirMensagem(undefined);
  }

  function alterarAberto(proximo: boolean) {
    definirAberto(proximo);
    if (!proximo) limpar();
  }

  async function concluir() {
    definirAberto(false);
    limpar();
    queryClient.removeQueries({ queryKey: chaves.materia(materia.id) });
    // A lista não está montada nesta página: só invalidada, ela mostraria a matéria por um
    // instante ao voltar. Tirá-la do cache evita o piscar; a invalidação confere com o servidor.
    queryClient.setQueryData<Materia[]>(chaves.materias, (lista) =>
      lista?.filter((item) => item.id !== materia.id),
    );
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: chaves.materias }),
      queryClient.invalidateQueries({ queryKey: chaves.uso }),
    ]);
    aoExcluida?.();
  }

  async function confirmar() {
    if (!contagens || ocupado || !nomeConfere(digitado, nome)) return;
    definirOcupado(true);
    definirMensagem(undefined);
    definirErroNome(undefined);
    try {
      await cliente.POST("/api/v1/materias/{materiaId}/exclusao", {
        params: { path: { materiaId: materia.id } },
        body: { nomeConfirmacao: digitado, impactoConfirmado: contagens },
      });
      await concluir();
    } catch (erro) {
      if (erro instanceof ErroApi && erro.status === 404) {
        await concluir(); // já foi excluída (outra aba): a tela só precisa convergir
      } else if (erro instanceof ErroApi && erro.codigo === "impacto_alterado") {
        definirMensagem(erro.message);
        await impacto.refetch();
      } else if (erro instanceof ErroApi && erro.codigo === "confirmacao_invalida") {
        definirErroNome(
          erro.campos.find((c) => c.campo === "nomeConfirmacao")?.mensagem ?? erro.message,
        );
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
        <Botao variante="secundario" aria-label={`Excluir matéria: ${materia.nome}`}>
          Excluir matéria
        </Botao>
      }
      titulo={`Excluir a matéria «${materia.nome}»?`}
      aberto={aberto}
      aoAlterarAberto={alterarAberto}
      textoConfirmar="Excluir matéria"
      aoConfirmar={() => void confirmar()}
      ocupado={ocupado}
      confirmarDesabilitado={!contagens || impacto.isFetching || !nomeConfere(digitado, nome)}
      mensagemErro={
        mensagem ??
        (impacto.isError
          ? "Não foi possível carregar o que será afetado. Tente novamente."
          : undefined)
      }
    >
      <p>
        A matéria e tudo o que está nela serão apagados. Confira o que será afetado, inclusive os
        arquivos das fontes:
      </p>
      {impacto.isPending && impacto.fetchStatus !== "idle" && (
        <p role="status">Calculando o que será afetado…</p>
      )}
      {contagens && <Impacto contagens={contagens} />}
      <CampoTexto
        rotulo="Digite o nome da matéria para confirmar"
        ajuda={`O nome é «${nome}». Maiúsculas e minúsculas contam.`}
        value={digitado}
        onChange={(valor) => {
          definirDigitado(valor);
          definirErroNome(undefined);
        }}
        isDisabled={ocupado}
        erro={erroNome}
        autoComplete="off"
      />
    </DialogoConfirmacao>
  );
}
