import { type Materia } from "../../api/acervo";
import { DialogoExclusaoMateria } from "./DialogoExclusaoMateria";
import { RenomearMateria } from "./RenomearMateria";

/** Título da página da matéria, com renomear e excluir (US3). Excluir leva de volta à lista. */
export function CabecalhoMateria({
  materia,
  aoExcluida,
}: {
  materia: Pick<Materia, "id" | "nome">;
  aoExcluida: () => void;
}) {
  return (
    <header className="cabecalho-materia">
      <h1>{materia.nome}</h1>
      <div className="cabecalho-materia-acoes">
        <RenomearMateria materia={materia} />
        <DialogoExclusaoMateria materia={materia} aoExcluida={aoExcluida} />
      </div>
    </header>
  );
}
