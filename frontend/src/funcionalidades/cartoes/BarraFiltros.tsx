import { useEffect, useState } from "react";
import { Input, Label, SearchField } from "react-aria-components";

import type { FiltrosCartoes } from "../../api/cartoes";
import { BUSCA_MAXIMA, ORIGENS_FILTRO, SITUACOES_FILTRO, combinarFiltros } from "./filtros";

/** Espera depois da última tecla antes de buscar (T038). */
export const ESPERA_BUSCA_MS = 300;

/**
 * Busca por texto e filtros de situação e origem (US4; RF-010). A busca só é aplicada depois de
 * `ESPERA_BUSCA_MS` sem digitar; os filtros, na hora. Tudo vai para a URL, pela rota.
 */
export function BarraFiltros({
  filtros,
  aoMudar,
}: {
  filtros: FiltrosCartoes;
  aoMudar: (filtros: FiltrosCartoes) => void;
}) {
  const [texto, definirTexto] = useState(filtros.busca ?? "");

  // A URL mudou por fora (Voltar, "Limpar"): o campo acompanha, ajustado na própria renderização.
  const [buscaVista, definirBuscaVista] = useState(filtros.busca);
  if (filtros.busca !== buscaVista) {
    definirBuscaVista(filtros.busca);
    definirTexto(filtros.busca ?? "");
  }

  useEffect(() => {
    const atual = filtros.busca ?? "";
    const novo = texto.trim() === "" ? "" : texto;
    if (novo === atual) return;
    const espera = setTimeout(() => {
      aoMudar(combinarFiltros(filtros, { busca: novo === "" ? undefined : novo }));
    }, ESPERA_BUSCA_MS);
    return () => {
      clearTimeout(espera);
    };
  }, [texto, filtros, aoMudar]);

  return (
    <div className="barra-filtros" role="search" aria-label="Busca e filtros dos cartões">
      <SearchField
        className="campo campo-busca"
        value={texto}
        onChange={definirTexto}
        onClear={() => {
          definirTexto("");
        }}
      >
        <Label>Buscar cartões</Label>
        <Input
          className="entrada"
          maxLength={BUSCA_MAXIMA}
          placeholder="Texto da frente ou do verso"
        />
      </SearchField>
      <div className="campo">
        <label htmlFor="filtro-situacao">Situação</label>
        <select
          id="filtro-situacao"
          className="entrada"
          value={filtros.situacao ?? ""}
          onChange={(evento) => {
            const valor = SITUACOES_FILTRO.find((s) => s.valor === evento.target.value)?.valor;
            aoMudar(combinarFiltros(filtros, { situacao: valor }));
          }}
        >
          <option value="">Todas</option>
          {SITUACOES_FILTRO.map((opcao) => (
            <option key={opcao.valor} value={opcao.valor}>
              {opcao.rotulo}
            </option>
          ))}
        </select>
      </div>
      <div className="campo">
        <label htmlFor="filtro-origem">Origem</label>
        <select
          id="filtro-origem"
          className="entrada"
          value={filtros.origem ?? ""}
          onChange={(evento) => {
            const valor = ORIGENS_FILTRO.find((o) => o.valor === evento.target.value)?.valor;
            aoMudar(combinarFiltros(filtros, { origem: valor }));
          }}
        >
          <option value="">Todas</option>
          {ORIGENS_FILTRO.map((opcao) => (
            <option key={opcao.valor} value={opcao.valor}>
              {opcao.rotulo}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
}
