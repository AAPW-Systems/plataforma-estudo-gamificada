import { z } from "zod";

const corpoErro = z.object({
  codigo: z.string(),
  mensagem: z.string(),
  campos: z.array(z.object({ campo: z.string(), mensagem: z.string() })).optional(),
  idRequisicao: z.string().optional(),
});

export class ErroApi extends Error {
  readonly codigo: string;
  readonly campos: { campo: string; mensagem: string }[];
  readonly idRequisicao: string | undefined;

  constructor(
    readonly status: number,
    corpo: unknown,
  ) {
    const validado = corpoErro.safeParse(corpo);
    const dados = validado.success ? validado.data : undefined;
    super(dados?.mensagem ?? "Não foi possível concluir a requisição. Tente novamente.");
    this.name = "ErroApi";
    this.codigo = dados?.codigo ?? "erro_interno";
    this.campos = dados?.campos ?? [];
    this.idRequisicao = dados?.idRequisicao;
  }
}

export async function lerErro(resposta: Response): Promise<ErroApi> {
  let corpo: unknown;
  try {
    corpo = await resposta.clone().json();
  } catch {
    corpo = undefined;
  }
  return new ErroApi(resposta.status, corpo);
}
