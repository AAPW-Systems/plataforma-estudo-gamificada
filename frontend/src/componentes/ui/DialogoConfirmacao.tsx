import type { ReactNode } from "react";
import { Dialog, DialogTrigger, Heading, Modal, ModalOverlay } from "react-aria-components";

import { Botao } from "./Botao";
import { MensagemErroFormulario } from "./MensagemErroFormulario";

export interface DialogoConfirmacaoProps {
  /** O botão que abre o diálogo; o foco volta a ele ao fechar. */
  acionador: ReactNode;
  titulo: string;
  aberto: boolean;
  aoAlterarAberto: (aberto: boolean) => void;
  textoConfirmar: string;
  aoConfirmar: () => void;
  /** Enquanto verdadeiro, o diálogo não fecha e a confirmação não pode ser repetida. */
  ocupado?: boolean;
  confirmarDesabilitado?: boolean;
  mensagemErro?: string | undefined;
  children: ReactNode;
}

/**
 * Diálogo de confirmação de ação definitiva (RQ-004): foco preso e devolvido ao acionador,
 * Escape e Cancelar fecham, e a ação destrutiva é distinta por texto ("Ação definitiva"),
 * ícone e botão, não só por cor. Os campos de confirmação entram como `children` e participam
 * do mesmo formulário (Enter confirma, se a confirmação estiver habilitada).
 */
export function DialogoConfirmacao({
  acionador,
  titulo,
  aberto,
  aoAlterarAberto,
  textoConfirmar,
  aoConfirmar,
  ocupado = false,
  confirmarDesabilitado = false,
  mensagemErro,
  children,
}: DialogoConfirmacaoProps) {
  return (
    <DialogTrigger
      isOpen={aberto}
      onOpenChange={(proximo) => {
        if (!ocupado) aoAlterarAberto(proximo);
      }}
    >
      {acionador}
      <ModalOverlay
        className="sobreposicao"
        isDismissable={!ocupado}
        isKeyboardDismissDisabled={ocupado}
      >
        <Modal className="modal">
          <Dialog>
            <form
              className="formulario"
              noValidate
              onSubmit={(evento) => {
                evento.preventDefault();
                if (!ocupado && !confirmarDesabilitado) aoConfirmar();
              }}
            >
              <Heading slot="title">{titulo}</Heading>
              <p className="aviso-definitivo">
                <span aria-hidden="true" className="aviso-definitivo-icone">
                  ⚠
                </span>
                <strong>Ação definitiva:</strong> não pode ser desfeita.
              </p>
              {children}
              <MensagemErroFormulario mensagem={mensagemErro} />
              <div className="acoes-dialogo">
                <Botao
                  variante="secundario"
                  isDisabled={ocupado}
                  onPress={() => {
                    aoAlterarAberto(false);
                  }}
                >
                  Cancelar
                </Botao>
                <Botao
                  type="submit"
                  variante="destrutivo"
                  carregando={ocupado}
                  isDisabled={confirmarDesabilitado}
                >
                  {textoConfirmar}
                </Botao>
              </div>
            </form>
          </Dialog>
        </Modal>
      </ModalOverlay>
    </DialogTrigger>
  );
}
