import { useQuery } from "@tanstack/react-query";

import { consultaFonte } from "../../api/acervo";
import { ErroApi } from "../../api/erros";
import { Botao } from "../../componentes/ui/Botao";
import { SeloEstado } from "../../componentes/ui/SeloEstado";
import { BotaoTentarNovamente } from "./BotaoTentarNovamente";
import { ESTADOS, formatarDataHora, formatarTamanho, rotuloDoTipo } from "./textos";

const SEM_VALOR = "—";

/** Dados de uma fonte (RF-009; US1, cenário 3). Acompanha o processamento até o estado final. */
export function PainelFonte({ fonteId, aoFechar }: { fonteId: string; aoFechar: () => void }) {
  const { data: fonte, error, isPending } = useQuery(consultaFonte(fonteId));

  if (error) {
    // Fonte de outra pessoa e inexistente respondem igual (404): a tela não distingue.
    const naoEncontrada = error instanceof ErroApi && error.status === 404;
    return (
      <section aria-label="Fonte" className="painel-fonte">
        <p role="alert" className="erro-formulario">
          {naoEncontrada
            ? "Não encontramos esta fonte."
            : "Não foi possível carregar a fonte. Tente novamente."}
        </p>
        <Botao variante="secundario" onPress={aoFechar}>
          Fechar
        </Botao>
      </section>
    );
  }
  if (isPending) return <p className="painel-fonte">Carregando a fonte…</p>;

  const estado = ESTADOS[fonte.estado];
  const ehPdf = fonte.tipoMidia === "application/pdf";
  return (
    <section aria-labelledby="titulo-painel-fonte" className="painel-fonte">
      <div className="painel-fonte-topo">
        <h3 id="titulo-painel-fonte">{fonte.titulo}</h3>
        <Botao variante="secundario" onPress={aoFechar}>
          Fechar
        </Botao>
      </div>
      <dl className="dados-fonte">
        <dt>Estado</dt>
        <dd>
          <SeloEstado tom={estado.tom}>{estado.rotulo}</SeloEstado>
        </dd>
        <dt>Arquivo</dt>
        <dd>{fonte.nomeArquivo}</dd>
        <dt>Tipo</dt>
        <dd>{rotuloDoTipo(fonte.tipoMidia)}</dd>
        <dt>Tamanho</dt>
        <dd>{formatarTamanho(fonte.tamanhoBytes)}</dd>
        <dt>Enviada em</dt>
        <dd>{formatarDataHora(fonte.enviadaEm)}</dd>
        {ehPdf && (
          <>
            <dt>Páginas</dt>
            <dd>{fonte.totalPaginas ?? SEM_VALOR}</dd>
          </>
        )}
        <dt>Trechos</dt>
        <dd>{fonte.totalTrechos ?? SEM_VALOR}</dd>
      </dl>
      {fonte.estado === "falhou" && fonte.mensagemFalha && (
        <p className="erro-campo">{fonte.mensagemFalha}</p>
      )}
      {fonte.podeTentarNovamente && <BotaoTentarNovamente fonte={fonte} />}
    </section>
  );
}
