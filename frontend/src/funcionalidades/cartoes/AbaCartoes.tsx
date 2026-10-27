import { useInfiniteQuery, useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { consultaFontes } from "../../api/acervo";
import { type Cartao, consultaCartoes, consultaLimitesCartao } from "../../api/cartoes";
import { Botao } from "../../componentes/ui/Botao";
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

  const paginas = cartoes.data?.pages ?? [];
  const itens = paginas.flatMap((pagina) => pagina.itens);
  const total = paginas.at(-1)?.total;
  const abrir = () => {
    definirAberto(true);
  };

  return (
    <section aria-labelledby="titulo-cartoes" className="aba-cartoes">
      <div className="cabecalho-secao">
        <h2 id="titulo-cartoes">Cartões</h2>
        {total !== undefined && total > 0 && (
          <p className="item-detalhes">{totalDeCartoes(total)}</p>
        )}
        {total !== undefined && total > 0 && (
          <Botao isDisabled={!limites} onPress={abrir}>
            Criar cartão
          </Botao>
        )}
      </div>
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
