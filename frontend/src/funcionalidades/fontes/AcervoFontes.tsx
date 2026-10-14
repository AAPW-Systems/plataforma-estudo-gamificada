import { useQuery } from "@tanstack/react-query";
import { Link, useNavigate, useParams } from "@tanstack/react-router";
import { useEffect, useRef, useState } from "react";

import { consultaFontes } from "../../api/acervo";
import { SeloEstado } from "../../componentes/ui/SeloEstado";
import { BotaoTentarNovamente } from "./BotaoTentarNovamente";
import { DialogoExclusaoFonte } from "./DialogoExclusaoFonte";
import { ESTADOS, formatarTamanho, rotuloDoTipo } from "./textos";

/**
 * Acervo da matéria (design 9.4; RN-03). A lista se atualiza sozinha enquanto houver fonte
 * pendente ou processando (DTEC 026), e cada mudança de estado é anunciada numa região viva,
 * sem anunciar a carga inicial.
 */
export function AcervoFontes({ materiaId }: { materiaId: string }) {
  const { data: fontes, isPending, isError } = useQuery(consultaFontes(materiaId));
  const [anuncio, definirAnuncio] = useState("");
  const navegar = useNavigate();
  // A fonte aberta no painel (rota filha), se houver: excluí-la fecha o painel.
  const { fonteId: fonteAberta } = useParams({ strict: false });
  const anteriores = useRef<Map<string, string> | undefined>(undefined);

  useEffect(() => {
    if (!fontes) return;
    const atuais = new Map(fontes.map((fonte) => [fonte.id, fonte.estado] as const));
    const antes = anteriores.current;
    anteriores.current = atuais;
    if (!antes) return;
    const mudancas = fontes
      .filter((fonte) => antes.has(fonte.id) && antes.get(fonte.id) !== fonte.estado)
      .map((fonte) => `${fonte.titulo}: ${ESTADOS[fonte.estado].rotulo}`);
    if (mudancas.length > 0) definirAnuncio(mudancas.join("; "));
  }, [fontes]);

  return (
    <section aria-labelledby="titulo-acervo" className="acervo">
      <h2 id="titulo-acervo">Fontes</h2>
      <div role="status" aria-live="polite" aria-label="Atualizações do acervo" className="sr-only">
        {anuncio}
      </div>
      {isPending && <p>Carregando as fontes…</p>}
      {isError && (
        <p role="alert" className="erro-formulario">
          Não foi possível carregar as fontes. Tente novamente.
        </p>
      )}
      {fontes?.length === 0 && (
        <p className="estado-vazio">
          <strong>Enviar a primeira fonte</strong> para começar: escolha ou solte um arquivo na área
          de envio.
        </p>
      )}
      {fontes && fontes.length > 0 && (
        <ul className="lista-cartoes">
          {fontes.map((fonte) => {
            const estado = ESTADOS[fonte.estado];
            return (
              <li key={fonte.id} className="item-fonte">
                <div className="item-fonte-principal">
                  <Link
                    to="/materias/$materiaId/fontes/$fonteId"
                    params={{ materiaId, fonteId: fonte.id }}
                  >
                    {fonte.titulo}
                  </Link>
                  <span className="item-detalhes">
                    {rotuloDoTipo(fonte.tipoMidia)} · {formatarTamanho(fonte.tamanhoBytes)}
                  </span>
                  <SeloEstado tom={estado.tom}>{estado.rotulo}</SeloEstado>
                </div>
                {fonte.estado === "falhou" && fonte.mensagemFalha && (
                  <p className="erro-campo">{fonte.mensagemFalha}</p>
                )}
                <div className="item-fonte-acoes">
                  {fonte.podeTentarNovamente && <BotaoTentarNovamente fonte={fonte} />}
                  <DialogoExclusaoFonte
                    fonte={fonte}
                    aoExcluida={() => {
                      if (fonteAberta === fonte.id) {
                        void navegar({ to: "/materias/$materiaId", params: { materiaId } });
                      }
                    }}
                  />
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}
