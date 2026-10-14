import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { Controller, useForm } from "react-hook-form";

import { cliente } from "../../api/cliente";
import { Aviso } from "../../componentes/ui/Aviso";
import { Botao } from "../../componentes/ui/Botao";
import { CampoSenha } from "../../componentes/ui/CampoSenha";
import { MensagemErroFormulario } from "../../componentes/ui/MensagemErroFormulario";
import { aplicarErroDaApi } from "./erros";
import { type DadosSenha, esquemaSenha } from "./esquemas";

const CAMPOS = ["senhaAtual", "novaSenha"] as const;

/** Troca a senha com a sessão aberta; as outras sessões da conta terminam (RF-014, D-004). */
export function FormularioSenha({ aoTrocar }: { aoTrocar: () => void }) {
  const [mensagem, definirMensagem] = useState<string>();
  const [aviso, definirAviso] = useState<string>();
  const formulario = useForm<DadosSenha>({
    resolver: zodResolver(esquemaSenha),
    mode: "onSubmit",
    reValidateMode: "onChange",
    defaultValues: { senhaAtual: "", novaSenha: "" },
  });
  const { control, handleSubmit, formState, reset } = formulario;

  async function enviar(dados: DadosSenha) {
    definirMensagem(undefined);
    definirAviso(undefined);
    try {
      await cliente.POST("/api/v1/perfil/senha", { body: dados });
      reset({ senhaAtual: "", novaSenha: "" });
      definirAviso("Senha trocada. As outras sessões foram encerradas.");
      aoTrocar();
    } catch (erro) {
      definirMensagem(aplicarErroDaApi(erro, formulario, CAMPOS));
    }
  }

  return (
    <form
      className="formulario"
      onSubmit={(evento) => void handleSubmit(enviar)(evento)}
      noValidate
    >
      <MensagemErroFormulario mensagem={mensagem} />
      {aviso && <Aviso>{aviso}</Aviso>}
      <Controller
        control={control}
        name="senhaAtual"
        render={({ field, fieldState }) => (
          <CampoSenha
            rotulo="Senha atual"
            isRequired
            autoComplete="current-password"
            name={field.name}
            value={field.value}
            onChange={field.onChange}
            onBlur={field.onBlur}
            inputRef={field.ref}
            erro={fieldState.error?.message}
          />
        )}
      />
      <Controller
        control={control}
        name="novaSenha"
        render={({ field, fieldState }) => (
          <CampoSenha
            rotulo="Nova senha"
            isRequired
            autoComplete="new-password"
            ajuda="De 8 a 128 caracteres. Uma frase longa é melhor do que uma senha curta e complicada."
            name={field.name}
            value={field.value}
            onChange={field.onChange}
            onBlur={field.onBlur}
            inputRef={field.ref}
            erro={fieldState.error?.message}
          />
        )}
      />
      <Botao type="submit" carregando={formState.isSubmitting}>
        Trocar senha
      </Botao>
    </form>
  );
}
