import { useQuery } from "@tanstack/react-query";
import { Link, Outlet, createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState } from "react";

import { consultaMateria, consultaUsoAcervo } from "../../../api/acervo";
import { ErroApi } from "../../../api/erros";
import { Aviso } from "../../../componentes/ui/Aviso";
import { AcervoFontes } from "../../../funcionalidades/fontes/AcervoFontes";
import { EnvioFonte } from "../../../funcionalidades/fontes/EnvioFonte";
import { CabecalhoMateria } from "../../../funcionalidades/materias/CabecalhoMateria";

export const Route = createFileRoute("/_autenticado/materias/$materiaId")({
  component: PaginaMateria,
});

/**
 * Página da matéria (design 9.4 e 9.5): o acervo com o envio e, ao lado, o painel da fonte
 * aberta (rota filha). A área de cartões fica vazia até a spec 003.
 */
function PaginaMateria() {
  const { materiaId } = Route.useParams();
  const { data: materia, error } = useQuery(consultaMateria(materiaId));
  const { data: uso } = useQuery(consultaUsoAcervo);
  const [confirmacao, definirConfirmacao] = useState<string>();
  const navegar = useNavigate();

  if (error) {
    const naoEncontrada = error instanceof ErroApi && error.status === 404;
    return (
      <main className="pagina">
        <h1>Matéria</h1>
        <p role="alert" className="erro-formulario">
          {naoEncontrada
            ? "Não encontramos esta matéria."
            : "Não foi possível carregar a matéria. Tente novamente."}
        </p>
        <Link to="/materias">Voltar às matérias</Link>
      </main>
    );
  }

  return (
    <main className="pagina">
      <p>
        <Link to="/materias">← Matérias</Link>
      </p>
      {materia ? (
        <CabecalhoMateria
          materia={materia}
          aoExcluida={() => {
            void navegar({ to: "/materias" });
          }}
        />
      ) : (
        <h1>Carregando a matéria…</h1>
      )}
      <div className="pagina-materia">
        <div className="pagina-materia-fontes">
          {uso && (
            <EnvioFonte
              materiaId={materiaId}
              uso={uso}
              aoEnviada={(fonte) => {
                definirConfirmacao(`Fonte «${fonte.titulo}» enviada.`);
              }}
            />
          )}
          {confirmacao && <Aviso>{confirmacao}</Aviso>}
          <AcervoFontes materiaId={materiaId} />
        </div>
        <Outlet />
      </div>
      <section aria-labelledby="titulo-cartoes" className="secao-perfil">
        <h2 id="titulo-cartoes">Cartões</h2>
        <p className="estado-vazio">
          Os cartões desta matéria aparecem aqui quando você criar ou gerar o primeiro.
        </p>
      </section>
    </main>
  );
}
