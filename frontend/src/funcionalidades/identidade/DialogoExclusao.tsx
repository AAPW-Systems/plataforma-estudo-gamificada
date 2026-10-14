import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { Controller, useForm } from "react-hook-form";
import { Dialog, DialogTrigger, Heading, Modal, ModalOverlay } from "react-aria-components";

import { cliente } from "../../api/cliente";
import { Botao } from "../../componentes/ui/Botao";
import { CampoSenha } from "../../componentes/ui/CampoSenha";
import { MensagemErroFormulario } from "../../componentes/ui/MensagemErroFormulario";
import { aplicarErroDaApi } from "./erros";
import { type DadosExclusao, esquemaExclusao } from "./esquemas";

const CAMPOS = ["senhaAtual"] as const;

/**
 * Exclusão definitiva da conta (RF-015, D-003): o diálogo explica o que é apagado, prende o
 * foco, exige a senha atual e só fecha por Cancelar, Escape ou pela exclusão concluída. Durante
 * o envio ele não fecha, e o botão não pode ser acionado de novo.
 */
export function DialogoExclusao({ aoExcluir }: { aoExcluir: () => void }) {
  const [aberto, definirAberto] = useState(false);
  const [mensagem, definirMensagem] = useState<string>();
  const formulario = useForm<DadosExclusao>({
    resolver: zodResolver(esquemaExclusao),
    mode: "onSubmit",
    reValidateMode: "onChange",
    defaultValues: { senhaAtual: "" },
  });
  const { control, handleSubmit, formState, reset } = formulario;
  const enviando = formState.isSubmitting;

  function alternar(abrir: boolean) {
    if (enviando) return;
    definirAberto(abrir);
    if (!abrir) {
      definirMensagem(undefined);
      reset({ senhaAtual: "" });
    }
  }

  async function excluir(dados: DadosExclusao) {
    definirMensagem(undefined);
    try {
      await cliente.POST("/api/v1/perfil/exclusao", { body: dados });
      definirAberto(false);
      aoExcluir();
    } catch (erro) {
      definirMensagem(aplicarErroDaApi(erro, formulario, CAMPOS));
    }
  }

  return (
    <DialogTrigger isOpen={aberto} onOpenChange={alternar}>
      <Botao variante="destrutivo">Excluir conta</Botao>
      <ModalOverlay
        className="sobreposicao"
        isDismissable={!enviando}
        isKeyboardDismissDisabled={enviando}
      >
        <Modal className="modal">
          <Dialog>
            <form
              className="formulario"
              onSubmit={(evento) => void handleSubmit(excluir)(evento)}
              noValidate
            >
              <Heading slot="title">Excluir a conta definitivamente?</Heading>
              <p>
                A exclusão é definitiva e não pode ser desfeita. Serão apagados: matérias, fontes,
                cartões, revisões, XP e sequência, além dos arquivos enviados. Todas as sessões
                serão encerradas, e o e-mail poderá ser usado em um novo cadastro.
              </p>
              <MensagemErroFormulario mensagem={mensagem} />
              <Controller
                control={control}
                name="senhaAtual"
                render={({ field, fieldState }) => (
                  <CampoSenha
                    rotulo="Senha atual"
                    isRequired
                    autoComplete="current-password"
                    ajuda="Digite a sua senha para confirmar."
                    name={field.name}
                    value={field.value}
                    onChange={field.onChange}
                    onBlur={field.onBlur}
                    inputRef={field.ref}
                    erro={fieldState.error?.message}
                  />
                )}
              />
              <div className="acoes-dialogo">
                <Botao
                  variante="secundario"
                  isDisabled={enviando}
                  onPress={() => {
                    alternar(false);
                  }}
                >
                  Cancelar
                </Botao>
                <Botao type="submit" variante="destrutivo" carregando={enviando}>
                  Excluir definitivamente
                </Botao>
              </div>
            </form>
          </Dialog>
        </Modal>
      </ModalOverlay>
    </DialogTrigger>
  );
}
