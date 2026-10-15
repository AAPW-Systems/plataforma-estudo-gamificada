import { queryOptions } from "@tanstack/react-query";

import { intervaloDeAcompanhamento } from "./acompanhamento";
import { cliente } from "./cliente";
import type { components } from "./esquema.gerado";

export type Materia = components["schemas"]["Materia"];
export type Fonte = components["schemas"]["Fonte"];
export type UsoAcervo = components["schemas"]["UsoAcervo"];

/** Chaves das consultas do acervo; as mutações as invalidam por prefixo. */
export const chaves = {
  materias: ["materias"] as const,
  materia: (id: string) => ["materias", id] as const,
  fontes: (materiaId: string) => ["materias", materiaId, "fontes"] as const,
  fonte: (id: string) => ["fontes", id] as const,
  uso: ["acervo", "uso"] as const,
};

function exigir<T>(dados: T | undefined): T {
  if (dados === undefined) throw new Error("A API respondeu sem corpo.");
  return dados;
}

export const consultaMaterias = queryOptions({
  queryKey: chaves.materias,
  queryFn: async () => exigir((await cliente.GET("/api/v1/materias")).data).itens,
});

export const consultaMateria = (materiaId: string) =>
  queryOptions({
    queryKey: chaves.materia(materiaId),
    queryFn: async () =>
      exigir(
        (await cliente.GET("/api/v1/materias/{materiaId}", { params: { path: { materiaId } } }))
          .data,
      ),
  });

/** Limites e formatos vêm do servidor: a tela nunca fixa números (RN-02). */
export const consultaUsoAcervo = queryOptions({
  queryKey: chaves.uso,
  queryFn: async () => exigir((await cliente.GET("/api/v1/acervo/uso")).data),
});

/** Enquanto alguma fonte estiver pendente ou processando, a lista se repete (DTEC 026). */
export const consultaFontes = (materiaId: string) =>
  queryOptions({
    queryKey: chaves.fontes(materiaId),
    queryFn: async () =>
      exigir(
        (
          await cliente.GET("/api/v1/materias/{materiaId}/fontes", {
            params: { path: { materiaId } },
          })
        ).data,
      ).itens,
    refetchInterval: (consulta) => intervaloDeAcompanhamento(consulta.state.data),
  });

export const consultaFonte = (fonteId: string) =>
  queryOptions({
    queryKey: chaves.fonte(fonteId),
    queryFn: async () =>
      exigir(
        (await cliente.GET("/api/v1/fontes/{fonteId}", { params: { path: { fonteId } } })).data,
      ),
    retry: false,
    refetchInterval: (consulta) =>
      intervaloDeAcompanhamento(consulta.state.data ? [consulta.state.data] : undefined),
  });

/**
 * O que a exclusão da fonte afeta (US2). Sempre consultado de novo ao abrir o diálogo: o
 * estudante decide sobre números atuais, e o servidor confere o que ele viu (DTEC 031).
 */
export const consultaImpactoExclusaoFonte = (fonteId: string, habilitada: boolean) =>
  queryOptions({
    queryKey: [...chaves.fonte(fonteId), "impacto-exclusao"] as const,
    queryFn: async () =>
      exigir(
        (
          await cliente.GET("/api/v1/fontes/{fonteId}/impacto-exclusao", {
            params: { path: { fonteId } },
          })
        ).data,
      ),
    enabled: habilitada,
    retry: false,
    staleTime: 0,
    gcTime: 0,
  });

/**
 * O que a exclusão da matéria afeta (US3). Sempre consultado de novo ao abrir o diálogo: o
 * estudante decide sobre números atuais, e o servidor confere o que ele viu (DTEC 031).
 */
export const consultaImpactoExclusaoMateria = (materiaId: string, habilitada: boolean) =>
  queryOptions({
    queryKey: [...chaves.materia(materiaId), "impacto-exclusao"] as const,
    queryFn: async () =>
      exigir(
        (
          await cliente.GET("/api/v1/materias/{materiaId}/impacto-exclusao", {
            params: { path: { materiaId } },
          })
        ).data,
      ),
    enabled: habilitada,
    retry: false,
    staleTime: 0,
    gcTime: 0,
  });
