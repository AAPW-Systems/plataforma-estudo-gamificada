import type { ReactNode } from "react";

/**
 * Moldura das telas de entrada e de cadastro (design, 9.1): dois painéis no desktop e coluna
 * única no celular. O nome do produto ainda não foi decidido (UI-01), por isso o texto é genérico.
 */
export function LayoutAutenticacao({ titulo, children }: { titulo: string; children: ReactNode }) {
  return (
    <div className="autenticacao">
      <section className="autenticacao-institucional" aria-label="Sobre a plataforma">
        <p className="autenticacao-marca">Plataforma de estudos</p>
        <p className="autenticacao-chamada">Estude com os seus próprios materiais.</p>
        <ul className="autenticacao-beneficios">
          <li>Guarde suas fontes por matéria.</li>
          <li>Revise cartões no ritmo certo para lembrar.</li>
          <li>Acompanhe a sua constância dia a dia.</li>
        </ul>
      </section>
      <main className="autenticacao-formulario">
        <h1>{titulo}</h1>
        {children}
      </main>
    </div>
  );
}
