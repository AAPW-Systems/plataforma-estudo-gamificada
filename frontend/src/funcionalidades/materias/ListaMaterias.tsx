import { Link } from "@tanstack/react-router";

import type { Materia } from "../../api/acervo";

function plural(quantidade: number, singular: string, pluralizado: string): string {
  return `${String(quantidade)} ${quantidade === 1 ? singular : pluralizado}`;
}

/** Matérias com o que o estudante precisa ver de relance: fontes, cartões ativos e a revisar. */
export function ListaMaterias({ materias }: { materias: readonly Materia[] }) {
  if (materias.length === 0) {
    return (
      <p className="estado-vazio">
        Você ainda não tem matérias. Crie a primeira para guardar as suas fontes e gerar cartões.
      </p>
    );
  }
  return (
    <ul className="lista-cartoes">
      {materias.map((materia) => (
        <li key={materia.id} className="item-materia">
          <h2 className="item-titulo">
            <Link to="/materias/$materiaId" params={{ materiaId: materia.id }}>
              {materia.nome}
            </Link>
          </h2>
          <p className="item-detalhes">
            {plural(materia.totalFontes, "fonte", "fontes")} ·{" "}
            {plural(materia.cartoesAtivos, "cartão ativo", "cartões ativos")} ·{" "}
            {String(materia.cartoesAguardandoRevisao)} aguardando revisão
          </p>
        </li>
      ))}
    </ul>
  );
}
