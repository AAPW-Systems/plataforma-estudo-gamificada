import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { Controller, useForm } from "react-hook-form";

import { cliente } from "../../api/cliente";
import { ErroApi } from "../../api/erros";
import type { components } from "../../api/esquema.gerado";
import { Botao } from "../../componentes/ui/Botao";
import { CampoSenha } from "../../componentes/ui/CampoSenha";
import { CampoTexto } from "../../componentes/ui/CampoTexto";
import { MensagemErroFormulario } from "../../componentes/ui/MensagemErroFormulario";
import { aplicarErroDaApi } from "./erros";
import { type DadosEntrada, esquemaEntrada } from "./esquemas";

type Perfil = components["schemas"]["Perfil"];

const CAMPOS = ["email", "senha"] as const;

export function FormularioEntrada({ aoConcluir }: { aoConcluir: (perfil: Perfil) => void }) {
  const [mensagem, definirMensagem] = useState<string>();
  const formulario = useForm<DadosEntrada>({
    resolver: zodResolver(esquemaEntrada),
    mode: "onTouched",
    defaultValues: { email: "", senha: "" },
  });
  const { control, handleSubmit, formState, resetField, setFocus } = formulario;

  async function enviar(dados: DadosEntrada) {
    definirMensagem(undefined);
    try {
      const { data } = await cliente.POST("/api/v1/auth/entrada", { body: dados });
      if (!data) throw new Error("A API respondeu sem o perfil.");
      aoConcluir(data);
    } catch (erro) {
      definirMensagem(aplicarErroDaApi(erro, formulario, CAMPOS));
      if (erro instanceof ErroApi && erro.status === 401) {
        // Mensagem neutra (RF-004): mantém o e-mail, limpa a senha e volta o foco a ela.
        resetField("senha", { defaultValue: "" });
        setFocus("senha");
      }
    }
  }

  return (
    <form
      className="formulario"
      onSubmit={(evento) => void handleSubmit(enviar)(evento)}
      noValidate
    >
      <MensagemErroFormulario mensagem={mensagem} />
      <Controller
        control={control}
        name="email"
        render={({ field, fieldState }) => (
          <CampoTexto
            rotulo="E-mail"
            isRequired
            type="email"
            autoComplete="email"
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
        name="senha"
        render={({ field, fieldState }) => (
          <CampoSenha
            rotulo="Senha"
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
      <Botao type="submit" carregando={formState.isSubmitting}>
        Entrar
      </Botao>
    </form>
  );
}
