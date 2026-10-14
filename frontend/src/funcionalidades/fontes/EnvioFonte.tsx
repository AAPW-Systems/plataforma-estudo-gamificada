import { useQueryClient } from "@tanstack/react-query";
import { useRef, useState } from "react";

import { type Fonte, type UsoAcervo, chaves } from "../../api/acervo";
import { cliente } from "../../api/cliente";
import { ErroApi } from "../../api/erros";
import { CampoTexto } from "../../componentes/ui/CampoTexto";
import { ZonaArquivo } from "../../componentes/ui/ZonaArquivo";
import { MENSAGEM_FALHA_GENERICA } from "../identidade/erros";
import { descreverFormatos, formatarLimite } from "./textos";

export interface EnvioFonteProps {
  materiaId: string;
  /** Formatos e limites do servidor (`GET /acervo/uso`): a tela não fixa números (RN-02). */
  uso: UsoAcervo;
  aoEnviada: (fonte: Fonte) => void;
}

function descricaoDosLimites(uso: UsoAcervo): string {
  return (
    `${descreverFormatos(uso.extensoesAceitas)}, até ${formatarLimite(uso.tamanhoMaximoBytes)}` +
    ` (PDF com até ${String(uso.paginasMaximasPdf)} páginas).`
  );
}

/**
 * Envio de uma fonte por botão ou por arrastar e soltar (US1, cenários 2 e 4). Um arquivo por
 * vez: enquanto um envio está em andamento, outro é ignorado. A validação é do servidor, e a
 * mensagem dele fica junto do campo a que se refere.
 */
export function EnvioFonte({ materiaId, uso, aoEnviada }: EnvioFonteProps) {
  const queryClient = useQueryClient();
  const [titulo, definirTitulo] = useState("");
  const [ocupado, definirOcupado] = useState(false);
  const [erroArquivo, definirErroArquivo] = useState<string>();
  const [erroTitulo, definirErroTitulo] = useState<string>();
  // O estado só atualiza na próxima renderização; o ref fecha a janela entre dois eventos.
  const emAndamento = useRef(false);

  async function enviar(arquivo: File) {
    if (emAndamento.current) return;
    emAndamento.current = true;
    definirOcupado(true);
    definirErroArquivo(undefined);
    definirErroTitulo(undefined);
    const tituloDigitado = titulo.trim();
    try {
      const { data } = await cliente.POST("/api/v1/materias/{materiaId}/fontes", {
        params: { path: { materiaId } },
        // O corpo é multipart: o serializador monta o formulário com o arquivo de verdade.
        body: { arquivo: arquivo.name },
        bodySerializer: () => {
          const formulario = new FormData();
          formulario.append("arquivo", arquivo, arquivo.name);
          if (tituloDigitado) formulario.append("titulo", tituloDigitado);
          return formulario;
        },
      });
      if (!data) throw new Error("A API respondeu sem a fonte.");
      definirTitulo("");
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: chaves.fontes(materiaId) }),
        queryClient.invalidateQueries({ queryKey: chaves.materias }),
        queryClient.invalidateQueries({ queryKey: chaves.uso }),
      ]);
      aoEnviada(data);
    } catch (erro) {
      if (erro instanceof ErroApi) {
        const doTitulo = erro.campos.find((item) => item.campo === "titulo");
        if (doTitulo) definirErroTitulo(doTitulo.mensagem);
        else definirErroArquivo(erro.message);
      } else {
        definirErroArquivo(MENSAGEM_FALHA_GENERICA);
      }
    } finally {
      emAndamento.current = false;
      definirOcupado(false);
    }
  }

  return (
    <div className="envio-fonte">
      <CampoTexto
        rotulo="Título (opcional)"
        ajuda="Se ficar em branco, usamos o nome do arquivo."
        value={titulo}
        onChange={definirTitulo}
        isDisabled={ocupado}
        erro={erroTitulo}
      />
      <ZonaArquivo
        rotulo="Enviar fonte"
        descricao={descricaoDosLimites(uso)}
        aceitos={uso.extensoesAceitas}
        aoSelecionar={(arquivo) => void enviar(arquivo)}
        aoRecusar={definirErroArquivo}
        ocupado={ocupado}
        erro={erroArquivo}
      />
    </div>
  );
}
