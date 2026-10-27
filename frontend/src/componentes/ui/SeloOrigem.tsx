export type Origem = "gerado_verificado" | "editado" | "criado";

interface Apresentacao {
  rotulo: string;
  icone: string;
  classe: string;
}

// Cada origem tem texto e um ícone próprio: a origem nunca depende só da cor (RF-009, RQ-003).
// Só "Gerado e verificado" leva o selo de verificado (Princípio I, D-002).
const ORIGENS: Record<Origem, Apresentacao> = {
  gerado_verificado: {
    rotulo: "Gerado e verificado",
    icone: "✓",
    classe: "selo-origem-verificado",
  },
  editado: { rotulo: "Editado por você", icone: "✎", classe: "selo-origem-editado" },
  criado: { rotulo: "Criado por você", icone: "✚", classe: "selo-origem-criado" },
};

export interface SeloOrigemProps {
  origem: Origem;
  /** A fonte de referência foi excluída: o complemento "Fonte apagada" aparece junto (D-006). */
  fonteApagada?: boolean;
}

export function SeloOrigem({ origem, fonteApagada = false }: SeloOrigemProps) {
  const { rotulo, icone, classe } = ORIGENS[origem];
  return (
    <span className="selos-origem">
      <span className={`selo ${classe}`}>
        <span aria-hidden="true" className="selo-icone">
          {icone}
        </span>
        <span>{rotulo}</span>
      </span>
      {fonteApagada && (
        <span className="selo selo-neutro">
          <span aria-hidden="true" className="selo-icone">
            ⊘
          </span>
          <span>Fonte apagada</span>
        </span>
      )}
    </span>
  );
}
