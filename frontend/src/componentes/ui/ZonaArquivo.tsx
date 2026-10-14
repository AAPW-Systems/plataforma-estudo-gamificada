import { useId } from "react";
import { DropZone, FileTrigger, type DropItem, Text, isFileDropItem } from "react-aria-components";

import { Botao } from "./Botao";

export interface ZonaArquivoProps {
  rotulo: string;
  /** Formatos aceitos e limite, sempre visíveis (ex.: "PDF com texto, TXT ou Markdown, até 2 MB"). */
  descricao: string;
  /** Extensões do seletor de arquivos (ex.: ".pdf"). */
  aceitos: readonly string[];
  aoSelecionar: (arquivo: File) => void;
  /** Chamado quando a solta não pode virar um envio (vários arquivos, algo que não é arquivo). */
  aoRecusar?: (mensagem: string) => void;
  ocupado?: boolean;
  erro?: string | undefined;
}

/**
 * Seleção de um arquivo por botão ou por arrastar e soltar (DTEC 016). Aceita um arquivo por
 * vez (RN-02); a validação de tipo e tamanho é do servidor, e esta zona só mostra os limites.
 */
export function ZonaArquivo({
  rotulo,
  descricao,
  aceitos,
  aoSelecionar,
  aoRecusar,
  ocupado = false,
  erro,
}: ZonaArquivoProps) {
  const id = useId();
  const idRotulo = `${id}-rotulo`;
  const idDescricao = `${id}-descricao`;
  const idErro = `${id}-erro`;

  async function aoSoltar(itens: DropItem[]) {
    const arquivos = itens.filter(isFileDropItem);
    if (itens.length > 1) {
      aoRecusar?.("Envie um arquivo por vez.");
      return;
    }
    const [item] = arquivos;
    if (!item) {
      aoRecusar?.("Solte um arquivo do seu dispositivo.");
      return;
    }
    aoSelecionar(await item.getFile());
  }

  return (
    <div
      role="group"
      className="zona-arquivo-bloco"
      aria-labelledby={idRotulo}
      aria-describedby={erro ? `${idDescricao} ${idErro}` : idDescricao}
    >
      <span id={idRotulo} className="rotulo">
        {rotulo}
      </span>
      <DropZone
        data-testid="zona-arquivo"
        className="zona-arquivo"
        isDisabled={ocupado}
        onDrop={(evento) => void aoSoltar(evento.items)}
      >
        <Text slot="label" className="zona-arquivo-chamada">
          Arraste um arquivo para cá ou
        </Text>
        <FileTrigger
          acceptedFileTypes={[...aceitos]}
          allowsMultiple={false}
          onSelect={(arquivos) => {
            const arquivo = arquivos?.item(0);
            if (arquivo) aoSelecionar(arquivo);
          }}
        >
          <Botao variante="secundario" isDisabled={ocupado}>
            {ocupado ? "Enviando…" : "Escolher arquivo"}
          </Botao>
        </FileTrigger>
      </DropZone>
      <p id={idDescricao} className="zona-arquivo-descricao">
        {descricao}
      </p>
      {erro && (
        <p id={idErro} className="erro-campo">
          {erro}
        </p>
      )}
      {ocupado && (
        <p role="status" className="zona-arquivo-descricao">
          Enviando o arquivo…
        </p>
      )}
    </div>
  );
}
