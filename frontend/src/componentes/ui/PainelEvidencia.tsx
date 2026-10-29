import { Button, Disclosure, DisclosurePanel, Heading } from "react-aria-components";

import { CitacaoDestacada } from "./CitacaoDestacada";

/** Uma evidência do cartão gerado (contrato da 004, esquema `Evidencia`). */
export interface EvidenciaExibida {
  fonteTitulo: string;
  fonteNomeArquivo: string;
  fonteEnviadaEm: string;
  pagina: number | null;
  /** Nulo depois da exclusão da fonte: "Fonte apagada", sem o trecho. */
  trecho: { texto: string; citacaoInicio: number; citacaoFim: number } | null;
}

const DATA = new Intl.DateTimeFormat("pt-BR", { dateStyle: "short" });

// Design 9.8: recolhido por padrão e expansível, sem esconder a explicação, que fica fora dele.
export function PainelEvidencia({ evidencia }: { evidencia: EvidenciaExibida }) {
  const { trecho, pagina } = evidencia;
  return (
    <Disclosure className="painel-evidencia">
      <Heading level={4} className="painel-evidencia-titulo">
        <Button slot="trigger" className="botao botao-discreto">
          {trecho ? "Ver trecho" : "Ver origem"}
        </Button>
      </Heading>
      <DisclosurePanel className="painel-evidencia-conteudo">
        {trecho ? (
          <>
            <p className="painel-evidencia-fonte">{evidencia.fonteTitulo}</p>
            <CitacaoDestacada
              texto={trecho.texto}
              inicio={trecho.citacaoInicio}
              fim={trecho.citacaoFim}
            />
            {pagina !== null && <p className="painel-evidencia-pagina">Página {pagina}</p>}
          </>
        ) : (
          <>
            <p className="selo selo-neutro">
              <span aria-hidden="true" className="selo-icone">
                ⊘
              </span>
              <span>Fonte apagada</span>
            </p>
            <dl className="painel-evidencia-origem">
              <dt>Título</dt>
              <dd>{evidencia.fonteTitulo}</dd>
              <dt>Arquivo</dt>
              <dd>{evidencia.fonteNomeArquivo}</dd>
              {pagina !== null && (
                <>
                  <dt>Página</dt>
                  <dd>Página {pagina}</dd>
                </>
              )}
              <dt>Enviada em</dt>
              <dd>{DATA.format(new Date(evidencia.fonteEnviadaEm))}</dd>
            </dl>
          </>
        )}
      </DisclosurePanel>
    </Disclosure>
  );
}
