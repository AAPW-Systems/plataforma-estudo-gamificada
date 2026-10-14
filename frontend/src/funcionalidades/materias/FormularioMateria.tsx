import { zodResolver } from "@hookform/resolvers/zod";
import { useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Controller, useForm } from "react-hook-form";

import { type Materia, chaves } from "../../api/acervo";
import { cliente } from "../../api/cliente";
import { Botao } from "../../componentes/ui/Botao";
import { CampoTexto } from "../../componentes/ui/CampoTexto";
import { MensagemErroFormulario } from "../../componentes/ui/MensagemErroFormulario";
import { aplicarErroDaApi } from "../identidade/erros";
import { type DadosMateria, esquemaMateria } from "./esquemas";

/**
 * Criação de matéria (US1, cenário 1). Erros de campo do servidor (422, 409 de nome em uso)
 * ficam junto do campo, com o valor digitado preservado e o foco nele.
 */
export function FormularioMateria({
  aoCriar,
  primeira = false,
}: {
  aoCriar: (materia: Materia) => void;
  /** Sem nenhuma matéria ainda, a ação se chama "Criar primeira matéria". */
  primeira?: boolean;
}) {
  const queryClient = useQueryClient();
  const [mensagem, definirMensagem] = useState<string>();
  const formulario = useForm<DadosMateria>({
    resolver: zodResolver(esquemaMateria),
    mode: "onSubmit",
    reValidateMode: "onChange",
    defaultValues: { nome: "" },
  });
  const { control, handleSubmit, formState, reset } = formulario;

  async function enviar(dados: DadosMateria) {
    definirMensagem(undefined);
    try {
      const { data } = await cliente.POST("/api/v1/materias", { body: { nome: dados.nome } });
      if (!data) throw new Error("A API respondeu sem a matéria.");
      reset({ nome: "" });
      await queryClient.invalidateQueries({ queryKey: chaves.materias });
      void queryClient.invalidateQueries({ queryKey: chaves.uso });
      aoCriar(data);
    } catch (erro) {
      definirMensagem(aplicarErroDaApi(erro, formulario, ["nome"]));
    }
  }

  return (
    <form
      className="formulario formulario-linha"
      onSubmit={(evento) => void handleSubmit(enviar)(evento)}
      noValidate
    >
      <MensagemErroFormulario mensagem={mensagem} />
      <Controller
        control={control}
        name="nome"
        render={({ field, fieldState }) => (
          <CampoTexto
            rotulo="Nome da matéria"
            isRequired
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
        {primeira ? "Criar primeira matéria" : "Criar matéria"}
      </Botao>
    </form>
  );
}
