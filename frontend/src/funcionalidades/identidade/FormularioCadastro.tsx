import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { Controller, useForm } from "react-hook-form";

import { cliente } from "../../api/cliente";
import type { components } from "../../api/esquema.gerado";
import { Botao } from "../../componentes/ui/Botao";
import { CampoSenha } from "../../componentes/ui/CampoSenha";
import { CampoTexto } from "../../componentes/ui/CampoTexto";
import { MensagemErroFormulario } from "../../componentes/ui/MensagemErroFormulario";
import { aplicarErroDaApi } from "./erros";
import { type DadosCadastro, esquemaCadastro } from "./esquemas";

type Perfil = components["schemas"]["Perfil"];

const CAMPOS = ["nome", "email", "senha"] as const;

export function FormularioCadastro({ aoConcluir }: { aoConcluir: (perfil: Perfil) => void }) {
  const [mensagem, definirMensagem] = useState<string>();
  const formulario = useForm<DadosCadastro>({
    resolver: zodResolver(esquemaCadastro),
    // Valida no envio (e revalida a cada alteração depois dele): um erro no *blur* empurraria o
    // botão e o clique do estudante se perderia.
    mode: "onSubmit",
    reValidateMode: "onChange",
    defaultValues: { nome: "", email: "", senha: "" },
  });
  const { control, handleSubmit, formState } = formulario;

  async function enviar(dados: DadosCadastro) {
    definirMensagem(undefined);
    try {
      const { data } = await cliente.POST("/api/v1/auth/cadastro", {
        body: { ...dados, fuso: Intl.DateTimeFormat().resolvedOptions().timeZone },
      });
      if (!data) throw new Error("A API respondeu sem o perfil.");
      aoConcluir(data);
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
      <Controller
        control={control}
        name="nome"
        render={({ field, fieldState }) => (
          <CampoTexto
            rotulo="Nome"
            isRequired
            autoComplete="name"
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
      <div role="note" aria-labelledby="titulo-privacidade" className="aviso-privacidade">
        <p id="titulo-privacidade" className="titulo-aviso">
          Sua privacidade
        </p>
        <p>
          Guardamos seu nome, seu e-mail e tudo o que você cadastrar aqui: matérias, fontes, cartões
          e histórico de revisões. Quando você pedir cartões gerados pela IA, trechos das suas
          fontes são enviados a um provedor de IA externo. Você pode excluir a conta e todos os
          dados quando quiser.
        </p>
      </div>
      <Botao type="submit" carregando={formState.isSubmitting}>
        Criar conta
      </Botao>
    </form>
  );
}
