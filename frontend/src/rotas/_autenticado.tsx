import { Link, Outlet, createFileRoute, redirect, useNavigate } from "@tanstack/react-router";
import { useState } from "react";

import { cliente } from "../api/cliente";
import { ErroApi } from "../api/erros";
import { consultaPerfil } from "../api/perfil";
import { Botao } from "../componentes/ui/Botao";
import { MensagemErroFormulario } from "../componentes/ui/MensagemErroFormulario";

export const Route = createFileRoute("/_autenticado")({
  beforeLoad: async ({ context }) => {
    try {
      await context.queryClient.query(consultaPerfil);
    } catch (erro) {
      if (erro instanceof ErroApi && erro.status === 401) return redirect({ to: "/entrar" });
      throw erro;
    }
    return undefined;
  },
  component: AreaDoEstudante,
  errorComponent: ({ reset }) => (
    <main role="alert">
      <p>Não foi possível carregar seus estudos.</p>
      <button onClick={reset}>Tentar novamente</button>
    </main>
  ),
});

function AreaDoEstudante() {
  const { queryClient } = Route.useRouteContext();
  const navegar = useNavigate();
  const [mensagem, definirMensagem] = useState<string>();
  const [saindo, definirSaindo] = useState(false);

  async function sair() {
    definirMensagem(undefined);
    definirSaindo(true);
    try {
      await cliente.POST("/api/v1/auth/saida");
    } catch (erro) {
      // Um 401 significa que a sessão já terminou; qualquer outra falha mantém o estudante aqui.
      if (!(erro instanceof ErroApi && erro.status === 401)) {
        definirMensagem("Não foi possível sair agora. Tente novamente.");
        definirSaindo(false);
        return;
      }
    }
    queryClient.clear();
    await navegar({ to: "/entrar" });
  }

  return (
    <>
      <header className="cabecalho">
        <span className="cabecalho-marca">Plataforma de estudos</span>
        <nav aria-label="Principal" className="cabecalho-navegacao">
          <Link to="/">Estudos</Link>
          <Link to="/perfil">Perfil</Link>
        </nav>
        <Botao variante="secundario" carregando={saindo} onPress={() => void sair()}>
          Sair
        </Botao>
      </header>
      <MensagemErroFormulario mensagem={mensagem} />
      <Outlet />
    </>
  );
}
