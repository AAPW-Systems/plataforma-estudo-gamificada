import type { components } from "../../api/esquema.gerado";
import type { TomSelo } from "../../componentes/ui/SeloEstado";

type EstadoFonte = components["schemas"]["EstadoFonte"];

/** Estado de processamento em palavras e em tom do selo (RN-03; texto e ícone, nunca só cor). */
export const ESTADOS: Record<EstadoFonte, { rotulo: string; tom: TomSelo }> = {
  pendente: { rotulo: "Pendente", tom: "neutro" },
  processando: { rotulo: "Processando", tom: "andamento" },
  concluido: { rotulo: "Concluído", tom: "sucesso" },
  falhou: { rotulo: "Falhou", tom: "erro" },
};

const TIPOS: Record<string, string> = {
  "application/pdf": "PDF",
  "text/plain": "TXT",
  "text/markdown": "Markdown",
};

export function rotuloDoTipo(tipoMidia: string): string {
  return TIPOS[tipoMidia] ?? tipoMidia;
}

const NUMERO = new Intl.NumberFormat("pt-BR", {
  maximumFractionDigits: 1,
  minimumFractionDigits: 1,
});
const INTEIRO = new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 0 });

/** Tamanho em unidades legíveis: "1,0 MB", "340 KB", "812 bytes". */
export function formatarTamanho(bytes: number): string {
  if (bytes >= 1024 * 1024) return `${NUMERO.format(bytes / (1024 * 1024))} MB`;
  if (bytes >= 1024) return `${INTEIRO.format(bytes / 1024)} KB`;
  return `${INTEIRO.format(bytes)} bytes`;
}

/** Limite em MB inteiros quando possível ("2 MB"), para a descrição do envio. */
export function formatarLimite(bytes: number): string {
  const megabytes = bytes / (1024 * 1024);
  return `${Number.isInteger(megabytes) ? INTEIRO.format(megabytes) : NUMERO.format(megabytes)} MB`;
}

const DATA_HORA = new Intl.DateTimeFormat("pt-BR", { dateStyle: "short", timeStyle: "short" });

export function formatarDataHora(iso: string): string {
  return DATA_HORA.format(new Date(iso));
}

/** Formatos aceitos em palavras, a partir das extensões que o servidor informa. */
export function descreverFormatos(extensoes: readonly string[]): string {
  const nomes: string[] = [];
  if (extensoes.includes(".pdf")) nomes.push("PDF com texto");
  if (extensoes.includes(".txt")) nomes.push("TXT");
  if (extensoes.some((e) => e === ".md" || e === ".markdown")) nomes.push("Markdown");
  if (nomes.length <= 1) return nomes.join("");
  return `${nomes.slice(0, -1).join(", ")} ou ${nomes[nomes.length - 1] ?? ""}`;
}
