import type { ReactNode } from "react";
import { Dialog, DialogTrigger, Heading, Modal, ModalOverlay } from "react-aria-components";

import { Botao } from "./Botao";

export function Dialogo({
  titulo,
  acionador,
  children,
}: {
  titulo: string;
  acionador: string;
  children: ReactNode;
}) {
  return (
    <DialogTrigger>
      <Botao variante="secundario">{acionador}</Botao>
      <ModalOverlay className="sobreposicao" isDismissable>
        <Modal className="modal">
          <Dialog>
            {({ close }) => (
              <>
                <Heading slot="title">{titulo}</Heading>
                {children}
                <Botao variante="secundario" onPress={close}>
                  Fechar
                </Botao>
              </>
            )}
          </Dialog>
        </Modal>
      </ModalOverlay>
    </DialogTrigger>
  );
}
