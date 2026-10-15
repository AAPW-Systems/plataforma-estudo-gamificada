import { useEffect, useRef, useState } from "react";

import { ErroApi } from "../../api/erros";
import { Botao } from "../../componentes/ui/Botao";
import { CampoTexto } from "../../componentes/ui/CampoTexto";
import { MensagemErroFormulario } from "../../componentes/ui/MensagemErroFormulario";
import { MENSAGEM_FALHA_GENERICA } from "../identidade/erros";

export type ResultadoValidacao = { valor: string } | { erro: string };

export interface RenomearInlineProps {
  /** O botão que abre o formulário, por exemplo "Renomear matéria". */
  rotuloBotao: string;
  rotuloCampo: string;
  rotuloSalvar: string;
  valorAtual: string;
  /** Normaliza e valida no envio (não a cada tecla), com a mensagem junto do campo. */
  validar: (digitado: string) => ResultadoValidacao;
  /** Nome do campo no corpo de erro do servidor (`campos[].campo`). */
  campoApi: string;
  /** Grava o novo valor; erros da API (`ErroApi`) voltam para o campo ou para o formulário. */
  salvar: (valor: string) => Promise<void>;
}

/**
 * Renomeação no próprio lugar (US3): um botão que vira um campo com Salvar e Cancelar.
 * Erros do servidor ficam junto do campo, com o valor digitado preservado e o foco nele; o
 * foco vai ao campo ao abrir e volta ao botão ao fechar (por Salvar, Cancelar ou Escape).
 */
export function RenomearInline({
  rotuloBotao,
  rotuloCampo,
  rotuloSalvar,
  valorAtual,
  validar,
  campoApi,
  salvar,
}: RenomearInlineProps) {
  const [editando, definirEditando] = useState(false);
  const [rascunho, definirRascunho] = useState(valorAtual);
  const [erroCampo, definirErroCampo] = useState<string>();
  const [mensagem, definirMensagem] = useState<string>();
  const [salvando, definirSalvando] = useState(false);
  const raiz = useRef<HTMLDivElement>(null);
  const campo = useRef<HTMLInputElement>(null);
  const devolverFoco = useRef(false);

  useEffect(() => {
    if (editando) {
      campo.current?.focus();
    } else if (devolverFoco.current) {
      devolverFoco.current = false;
      raiz.current?.querySelector("button")?.focus();
    }
  }, [editando]);

  function abrir() {
    definirRascunho(valorAtual);
    definirErroCampo(undefined);
    definirMensagem(undefined);
    definirEditando(true);
  }

  function fechar() {
    devolverFoco.current = true;
    definirEditando(false);
  }

  async function enviar() {
    if (salvando) return;
    definirMensagem(undefined);
    const resultado = validar(rascunho);
    if ("erro" in resultado) {
      definirErroCampo(resultado.erro);
      campo.current?.focus();
      return;
    }
    definirErroCampo(undefined);
    if (resultado.valor === valorAtual) {
      fechar(); // nada a salvar: não vale uma ida ao servidor
      return;
    }
    definirSalvando(true);
    try {
      await salvar(resultado.valor);
      fechar();
    } catch (erro) {
      const doCampo = erro instanceof ErroApi && erro.campos.find((c) => c.campo === campoApi);
      if (doCampo) {
        definirErroCampo(doCampo.mensagem);
        campo.current?.focus();
      } else {
        definirMensagem(erro instanceof ErroApi ? erro.message : MENSAGEM_FALHA_GENERICA);
      }
    } finally {
      definirSalvando(false);
    }
  }

  return (
    <div ref={raiz} className="renomear-inline">
      {editando ? (
        <form
          className="formulario formulario-linha"
          aria-label={rotuloBotao}
          noValidate
          onSubmit={(evento) => {
            evento.preventDefault();
            void enviar();
          }}
        >
          <MensagemErroFormulario mensagem={mensagem} />
          <CampoTexto
            rotulo={rotuloCampo}
            isRequired
            value={rascunho}
            onChange={(valor) => {
              definirRascunho(valor);
              definirErroCampo(undefined);
            }}
            inputRef={campo}
            onKeyDown={(evento) => {
              if (evento.key === "Escape" && !salvando) {
                evento.preventDefault();
                fechar();
              }
            }}
            erro={erroCampo}
          />
          <div className="acoes-dialogo">
            <Botao variante="secundario" isDisabled={salvando} onPress={fechar}>
              Cancelar
            </Botao>
            <Botao type="submit" carregando={salvando}>
              {rotuloSalvar}
            </Botao>
          </div>
        </form>
      ) : (
        <Botao variante="secundario" onPress={abrir}>
          {rotuloBotao}
        </Botao>
      )}
    </div>
  );
}
