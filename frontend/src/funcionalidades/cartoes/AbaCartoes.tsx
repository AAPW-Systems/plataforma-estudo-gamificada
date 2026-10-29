import { useInfiniteQuery, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRef, useState } from "react";

import { consultaFontes } from "../../api/acervo";
import {
  type Cartao,
  consultaCartoes,
  consultaLimitesCartao,
  reativarCartao,
  suspenderCartao,
} from "../../api/cartoes";
import { ErroApi } from "../../api/erros";
import { Botao } from "../../componentes/ui/Botao";
import { invalidarCartoesEMaterias, removerDaLista, substituirNaLista } from "./cache";
import { ItemCartao } from "./ItemCartao";
import { PainelCartao } from "./PainelCartao";
import { totalDeCartoes } from "./textos";

/** Cartões ativos e suspensos da matéria, com a criação no painel lateral (design 9.4; US1). */
export function AbaCartoes({ materiaId }: { materiaId: string }) {
  const { data: limites } = useQuery(consultaLimitesCartao);
  const { data: fontes } = useQuery(consultaFontes(materiaId));
  const cartoes = useInfiniteQuery(consultaCartoes(materiaId));
  const [aberto, definirAberto] = useState(false);
  const [emEdicao, definirEmEdicao] = useState<Cartao>();
  const [anuncio, definirAnuncio] = useState("");
  const [erroAcao, definirErroAcao] = useState<string>();
  const [alternando, definirAlternando] = useState<string>();
  const titulo = useRef<HTMLHeadingElement>(null);
  const queryClient = useQueryClient();

  async function alternarSituacao(cartao: Cartao) {
    const suspender = cartao.situacao === "ativo";
    definirAlternando(cartao.id);
    definirErroAcao(undefined);
    definirAnuncio("");
    try {
      const novo = await (suspender ? suspenderCartao(cartao.id) : reativarCartao(cartao.id));
      substituirNaLista(queryClient, materiaId, novo);
      definirAnuncio(suspender ? "Cartão suspenso." : "Cartão reativado.");
      void invalidarCartoesEMaterias(queryClient, materiaId);
    } catch (erro) {
      if (erro instanceof ErroApi && erro.status === 404) {
        removerDaLista(queryClient, materiaId, cartao.id); // excluído em outra aba
        void invalidarCartoesEMaterias(queryClient, materiaId);
      }
      definirErroAcao("Não foi possível mudar a situação do cartão. Tente novamente.");
    } finally {
      definirAlternando(undefined);
    }
  }

  function aoExcluido(cartao: Cartao) {
    removerDaLista(queryClient, materiaId, cartao.id);
    definirAnuncio("Cartão excluído.");
    void invalidarCartoesEMaterias(queryClient, materiaId);
    // O acionador sumiu com o cartão: o foco vai para o título da seção.
    titulo.current?.focus();
  }

  const paginas = cartoes.data?.pages ?? [];
  const itens = paginas.flatMap((pagina) => pagina.itens);
  const total = paginas.at(-1)?.total;
  const abrir = () => {
    definirAberto(true);
  };

  return (
    <section aria-labelledby="titulo-cartoes" className="aba-cartoes">
      <div className="cabecalho-secao">
        <h2 id="titulo-cartoes" ref={titulo} tabIndex={-1}>
          Cartões
        </h2>
        {total !== undefined && total > 0 && (
          <p className="item-detalhes">{totalDeCartoes(total)}</p>
        )}
        {total !== undefined && total > 0 && (
          <Botao isDisabled={!limites} onPress={abrir}>
            Criar cartão
          </Botao>
        )}
      </div>
      <div role="status" aria-live="polite" className="sr-only">
        {anuncio}
      </div>
      {erroAcao && (
        <p role="alert" className="erro-formulario">
          {erroAcao}
        </p>
      )}
      {cartoes.isPending && <p>Carregando os cartões…</p>}
      {cartoes.isError && (
        <p role="alert" className="erro-formulario">
          Não foi possível carregar os cartões. Tente novamente.
        </p>
      )}
      {total === 0 && (
        <div className="estado-vazio">
          <p>Esta matéria ainda não tem cartões.</p>
          <Botao isDisabled={!limites} onPress={abrir}>
            Criar o primeiro cartão
          </Botao>
        </div>
      )}
      {itens.length > 0 && (
        <ul aria-label="Cartões da matéria" className="lista-cartoes">
          {itens.map((cartao) => (
            <ItemCartao
              key={cartao.id}
              cartao={cartao}
              aoEditar={() => {
                definirEmEdicao(cartao);
              }}
              aoAlternarSituacao={() => {
                void alternarSituacao(cartao);
              }}
              alternando={alternando === cartao.id}
              aoExcluido={() => {
                aoExcluido(cartao);
              }}
            />
          ))}
        </ul>
      )}
      {cartoes.hasNextPage && (
        <Botao
          variante="secundario"
          carregando={cartoes.isFetchingNextPage}
          onPress={() => {
            void cartoes.fetchNextPage();
          }}
        >
          Carregar mais
        </Botao>
      )}
      {limites && (
        <PainelCartao
          materiaId={materiaId}
          limites={limites}
          fontes={fontes ?? []}
          aberto={aberto}
          aoAlterarAberto={definirAberto}
        />
      )}
      {limites && emEdicao && (
        <PainelCartao
          key={emEdicao.id}
          materiaId={materiaId}
          limites={limites}
          fontes={[]}
          cartao={emEdicao}
          aberto
          aoAlterarAberto={(proximo) => {
            if (!proximo) definirEmEdicao(undefined);
          }}
        />
      )}
    </section>
  );
}
