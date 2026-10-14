import type { ReactNode } from "react";

export type TomSelo = "neutro" | "andamento" | "sucesso" | "erro";

// O ícone acompanha o texto para que o estado não dependa só da cor (WCAG 2.2, 1.4.1).
const ICONES: Record<TomSelo, string> = {
  neutro: "○",
  andamento: "◐",
  sucesso: "✓",
  erro: "✕",
};

export function SeloEstado({ tom, children }: { tom: TomSelo; children: ReactNode }) {
  return (
    <span className={`selo selo-${tom}`}>
      <span aria-hidden="true" className="selo-icone">
        {ICONES[tom]}
      </span>
      <span>{children}</span>
    </span>
  );
}
