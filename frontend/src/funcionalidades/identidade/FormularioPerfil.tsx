import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { Controller, useForm } from "react-hook-form";

import { cliente } from "../../api/cliente";
import type { components } from "../../api/esquema.gerado";
import { Aviso } from "../../componentes/ui/Aviso";
import { Botao } from "../../componentes/ui/Botao";
import { CampoFuso } from "../../componentes/ui/CampoFuso";
import { CampoNumero } from "../../componentes/ui/CampoNumero";
import { CampoTexto } from "../../componentes/ui/CampoTexto";
import { MensagemErroFormulario } from "../../componentes/ui/MensagemErroFormulario";
import { aplicarErroDaApi } from "./erros";
import { type DadosPerfil, esquemaPerfil, lerRetencao } from "./esquemas";

type Perfil = components["schemas"]["Perfil"];
type Alteracao = components["schemas"]["PerfilAlteracao"];

const CAMPOS = [
  "nome",
  "fuso",
  "metaDiaria",
  "tamanhoLicao",
  "limiteNovosDia",
  "retencaoDesejada",
] as const;

const EXPLICACAO_RETENCAO =
  "É a chance de lembrar de um cartão quando ele voltar a aparecer. Ao aumentar, os cartões voltam " +
  "mais cedo: você esquece menos, mas revisa mais. Ao reduzir, eles voltam mais tarde: você revisa " +
  "menos, mas esquece mais. A mudança vale a partir da próxima revisão; as revisões anteriores não são alteradas.";

function valoresDoPerfil(perfil: Perfil): DadosPerfil {
  return {
    nome: perfil.nome,
    fuso: perfil.fuso,
    metaDiaria: perfil.metaDiaria,
    tamanhoLicao: perfil.tamanhoLicao,
    limiteNovosDia: perfil.limiteNovosDia,
    retencaoDesejada: perfil.retencaoDesejada.toFixed(2).replace(".", ","),
  };
}

/** Só o que mudou: a API altera apenas os campos enviados. */
function diferencas(perfil: Perfil, dados: DadosPerfil): Alteracao {
  const alteracao: Alteracao = {};
  if (dados.nome !== perfil.nome) alteracao.nome = dados.nome;
  if (dados.fuso !== perfil.fuso) alteracao.fuso = dados.fuso;
  if (dados.metaDiaria !== perfil.metaDiaria) alteracao.metaDiaria = dados.metaDiaria;
  if (dados.tamanhoLicao !== perfil.tamanhoLicao) alteracao.tamanhoLicao = dados.tamanhoLicao;
  if (dados.limiteNovosDia !== perfil.limiteNovosDia)
    alteracao.limiteNovosDia = dados.limiteNovosDia;
  const retencao = lerRetencao(dados.retencaoDesejada);
  if (retencao !== undefined && retencao !== perfil.retencaoDesejada) {
    alteracao.retencaoDesejada = retencao;
  }
  return alteracao;
}

export function FormularioPerfil({
  perfil,
  aoSalvar,
}: {
  perfil: Perfil;
  aoSalvar: (perfil: Perfil) => void;
}) {
  const [mensagem, definirMensagem] = useState<string>();
  const [aviso, definirAviso] = useState<string>();
  const formulario = useForm<DadosPerfil>({
    resolver: zodResolver(esquemaPerfil),
    // Valida no envio (e revalida a cada alteração depois dele): um erro no *blur* empurraria o
    // botão e o clique do estudante se perderia.
    mode: "onSubmit",
    reValidateMode: "onChange",
    defaultValues: valoresDoPerfil(perfil),
  });
  const { control, handleSubmit, formState, reset } = formulario;

  async function enviar(dados: DadosPerfil) {
    definirMensagem(undefined);
    definirAviso(undefined);
    const alteracao = diferencas(perfil, dados);
    if (Object.keys(alteracao).length === 0) {
      definirAviso("Nada para salvar: nenhum valor foi alterado.");
      return;
    }
    try {
      const { data } = await cliente.PATCH("/api/v1/perfil", { body: alteracao });
      if (!data) throw new Error("A API respondeu sem o perfil.");
      reset(valoresDoPerfil(data));
      definirAviso("Alterações salvas.");
      aoSalvar(data);
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
      <p className="campo-leitura">
        <span>E-mail (não pode ser alterado)</span> <strong>{perfil.email}</strong>
      </p>
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
        name="fuso"
        render={({ field, fieldState }) => (
          <CampoFuso
            rotulo="Fuso horário"
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
      <Controller
        control={control}
        name="metaDiaria"
        render={({ field, fieldState }) => (
          <CampoNumero
            rotulo="Meta diária (cartões por dia)"
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
        name="tamanhoLicao"
        render={({ field, fieldState }) => (
          <CampoNumero
            rotulo="Cartões por lição"
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
        name="limiteNovosDia"
        render={({ field, fieldState }) => (
          <CampoNumero
            rotulo="Cartões novos por dia"
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
        name="retencaoDesejada"
        render={({ field, fieldState }) => (
          <CampoTexto
            rotulo="Retenção desejada (de 0,70 a 0,97)"
            inputMode="decimal"
            ajuda={EXPLICACAO_RETENCAO}
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
        Salvar alterações
      </Botao>
    </form>
  );
}
