import { Blob as BlobNativo, File as ArquivoNativo } from "node:buffer";
import { afterAll, beforeAll, vi } from "vitest";

/**
 * O jsdom troca `FormData`, `File` e `Blob` por versões suas, e o `fetch` do Node 24 não consegue
 * ler o corpo de um `File` do jsdom ("Premature close"). No navegador os três são nativos, então
 * os testes que enviam arquivo usam os do Node, obtidos aqui sem dependência nova.
 */
async function formDataNativo(): Promise<typeof FormData> {
  const formulario = await new Response(new URLSearchParams()).formData();
  return formulario.constructor as typeof FormData;
}

const NativoDoNode = await formDataNativo();

let ultimo: FormData | undefined;

/** Guarda o último formulário montado, para os testes conferirem o que foi enviado. */
class FormDataGravador extends NativoDoNode {
  constructor() {
    super();
    guardar(this);
  }
}

function guardar(formulario: FormData): void {
  ultimo = formulario;
}

/**
 * `FormData`, `File` e `Blob` nativos durante os testes do arquivo que chamar esta função.
 *
 * O handler do MSW não deve ler o corpo multipart: com corpos em fluxo, o MSW e o `fetch` do
 * Node 24 se atrapalham ("fetch failed"). O teste confere o tipo no cabeçalho e os campos pelo
 * formulário que o componente montou (`ultimoFormData`).
 */
export function usarFormDataNativo() {
  beforeAll(() => {
    // O `FormData` nativo só reconhece como arquivo o `File` e o `Blob` globais: os três juntos.
    vi.stubGlobal("FormData", FormDataGravador);
    vi.stubGlobal("File", ArquivoNativo);
    vi.stubGlobal("Blob", BlobNativo);
  });
  afterAll(() => {
    vi.unstubAllGlobals();
  });
}

export function ultimoFormData(): FormData | undefined {
  return ultimo;
}

/** `File` nativo, que o `fetch` do Node sabe enviar. */
export function arquivoNativo(nome: string, conteudo: string, tipo: string): File {
  return new ArquivoNativo([conteudo], nome, { type: tipo }) as unknown as File;
}
