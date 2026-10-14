import type { components } from "../api/esquema.gerado";

/** Perfil fictício completo, no formato do contrato (conta @exemplo.com, regra 10). */
export function perfilFicticio(
  alteracoes: Partial<components["schemas"]["Perfil"]> = {},
): components["schemas"]["Perfil"] {
  return {
    nome: "Estudante Exemplo",
    email: "estudante@exemplo.com",
    papel: "estudante",
    fuso: "America/Recife",
    metaDiaria: 20,
    tamanhoLicao: 10,
    limiteNovosDia: 20,
    retencaoDesejada: 0.9,
    criadoEm: "2026-10-13T12:00:00Z",
    ...alteracoes,
  };
}
