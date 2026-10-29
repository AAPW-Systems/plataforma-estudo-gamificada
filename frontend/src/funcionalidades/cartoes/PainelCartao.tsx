import { zodResolver } from "@hookform/resolvers/zod";
import { useQueryClient } from "@tanstack/react-query";
import { useEffect, useMemo, useRef, useState } from "react";
import { Dialog, Heading, Modal, ModalOverlay } from "react-aria-components";
import { Controller, useForm } from "react-hook-form";

import { type Materia, chaves } from "../../api/acervo";
import {
  type Cartao,
  type EdicaoCartao,
  type LimitesCartao,
  chavesCartoes,
  criarCartao,
  editarCartao,
} from "../../api/cartoes";
import { Botao } from "../../componentes/ui/Botao";
import { CampoTextoLongo } from "../../componentes/ui/CampoTextoLongo";
import { MensagemErroFormulario } from "../../componentes/ui/MensagemErroFormulario";
import { aplicarErroDaApi } from "../identidade/erros";
import { substituirNaLista } from "./cache";
import { CARTAO_VAZIO, type DadosCartao, esquemaCartao } from "./esquemas";

const CAMPOS = ["frente", "verso", "explicacao", "fonteId"] as const;

export interface PainelCartaoProps {
  materiaId: string;
  limites: LimitesCartao;
  /** Fontes da matéria que podem ser citadas como referência (RF-002). */
  fontes: readonly { id: string; titulo: string }[];
  aberto: boolean;
  aoAlterarAberto: (aberto: boolean) => void;
  aoCriado?: (cartao: Cartao) => void;
  /** Cartão a editar (US2): o painel abre com os valores dele e só salva o que mudou. */
  cartao?: Cartao;
}

function valoresDe(cartao: Cartao | undefined): DadosCartao {
  if (!cartao) return CARTAO_VAZIO;
  return {
    frente: cartao.frente,
    verso: cartao.verso,
    explicacao: cartao.explicacao ?? "",
    fonteId: "",
  };
}

/** Só os campos alterados; explicação vazia vai como `null`, que a remove. */
function alteracoesDe(iniciais: DadosCartao, dados: DadosCartao): EdicaoCartao {
  const alteracoes: EdicaoCartao = {};
  if (dados.frente !== iniciais.frente) alteracoes.frente = dados.frente;
  if (dados.verso !== iniciais.verso) alteracoes.verso = dados.verso;
  if (dados.explicacao !== iniciais.explicacao) {
    alteracoes.explicacao = dados.explicacao.trim() === "" ? null : dados.explicacao;
  }
  return alteracoes;
}

/** Soma um cartão ativo à matéria na lista e na consulta, antes de a rede responder. */
function contarNovoCartao(queryClient: ReturnType<typeof useQueryClient>, materiaId: string) {
  const somar = (materia: Materia): Materia =>
    materia.id === materiaId ? { ...materia, cartoesAtivos: materia.cartoesAtivos + 1 } : materia;
  queryClient.setQueryData<Materia[]>(chaves.materias, (lista) => lista?.map(somar));
  queryClient.setQueryData<Materia>(chaves.materia(materiaId), (materia) =>
    materia ? somar(materia) : materia,
  );
}

/**
 * Painel lateral de criação (US1; CS-001) e de edição (US2) de cartão. Só com o teclado: `Tab` entre os campos,
 * `Enter` quebra a linha, `Ctrl/⌘+Enter` salva e abre outro em branco, `Esc` fecha (e pergunta
 * antes de descartar o que foi digitado). Os erros ficam junto do campo, com os valores mantidos.
 * Na edição, `Ctrl/⌘+Enter` salva e fecha, e a fonte de referência não muda.
 */
export function PainelCartao({
  materiaId,
  limites,
  fontes,
  aberto,
  aoAlterarAberto,
  aoCriado,
  cartao,
}: PainelCartaoProps) {
  const editando = cartao !== undefined;
  const queryClient = useQueryClient();
  const esquema = useMemo(() => esquemaCartao(limites), [limites]);
  const iniciais = useMemo(() => valoresDe(cartao), [cartao]);
  const formulario = useForm<DadosCartao>({
    resolver: zodResolver(esquema),
    mode: "onSubmit",
    reValidateMode: "onChange",
    defaultValues: iniciais,
  });
  const { control, handleSubmit, register, reset, setFocus, getValues, formState } = formulario;
  const [mensagem, definirMensagem] = useState<string>();
  const [anuncio, definirAnuncio] = useState("");
  const [confirmandoDescarte, definirConfirmandoDescarte] = useState(false);
  const enviando = useRef(false);
  const continuar = useRef<HTMLButtonElement>(null);

  // Pedido de foco na frente: ao abrir e depois de "Salvar e criar outro", já com o formulário
  // limpo e renderizado de novo.
  const [focoNaFrente, definirFocoNaFrente] = useState(0);
  useEffect(() => {
    if (aberto) setFocus("frente");
  }, [aberto, focoNaFrente, setFocus]);

  useEffect(() => {
    if (confirmandoDescarte) continuar.current?.focus();
  }, [confirmandoDescarte]);

  function fechar() {
    reset(iniciais);
    definirMensagem(undefined);
    definirAnuncio("");
    definirConfirmandoDescarte(false);
    aoAlterarAberto(false);
  }

  function tentarFechar() {
    if (enviando.current) return;
    const atuais = getValues();
    const digitado = editando
      ? Object.keys(alteracoesDe(iniciais, atuais)).length > 0
      : Object.values(atuais).some((valor) => valor.trim() !== "");
    if (digitado) definirConfirmandoDescarte(true);
    else fechar();
  }

  function salvar(criarOutro: boolean) {
    if (enviando.current) return;
    void handleSubmit(async (dados) => {
      enviando.current = true;
      definirMensagem(undefined);
      definirAnuncio("");
      try {
        if (cartao) {
          const alteracoes = alteracoesDe(iniciais, dados);
          if (Object.keys(alteracoes).length > 0) {
            substituirNaLista(queryClient, materiaId, await editarCartao(cartao.id, alteracoes));
            void queryClient.invalidateQueries({ queryKey: chavesCartoes.lista(materiaId) });
          }
          fechar();
          return;
        }
        const criado = await criarCartao(materiaId, {
          frente: dados.frente,
          verso: dados.verso,
          explicacao: dados.explicacao.trim() === "" ? null : dados.explicacao,
          fonteId: dados.fonteId === "" ? null : dados.fonteId,
        });
        contarNovoCartao(queryClient, materiaId);
        void queryClient.invalidateQueries({ queryKey: chavesCartoes.lista(materiaId) });
        void queryClient.invalidateQueries({ queryKey: chaves.materias });
        aoCriado?.(criado);
        if (criarOutro) {
          reset(CARTAO_VAZIO);
          definirAnuncio("Cartão criado.");
          definirFocoNaFrente((pedido) => pedido + 1);
        } else {
          fechar();
        }
      } catch (erro) {
        definirMensagem(aplicarErroDaApi(erro, formulario, CAMPOS));
      } finally {
        enviando.current = false;
      }
    })();
  }

  /** `Ctrl/⌘+Enter` em qualquer campo: salvar e criar outro (na edição, salvar e fechar). */
  function aoTeclar(evento: {
    key: string;
    ctrlKey: boolean;
    metaKey: boolean;
    preventDefault: () => void;
    /** Só nos campos do React Aria, que por padrão não deixam o evento subir. */
    continuePropagation?: () => void;
  }) {
    if (evento.key === "Enter" && (evento.ctrlKey || evento.metaKey)) {
      evento.preventDefault();
      salvar(!editando);
      return;
    }
    // Esc e as demais teclas seguem para o painel (que fecha com Esc).
    evento.continuePropagation?.();
  }

  const ocupado = formState.isSubmitting;
  const erroFonte = formState.errors.fonteId?.message;

  return (
    <ModalOverlay
      className="sobreposicao"
      isOpen={aberto}
      onOpenChange={(proximo) => {
        if (!proximo) tentarFechar();
      }}
      isDismissable
    >
      <Modal className="modal modal-painel">
        <Dialog>
          <form
            className="formulario"
            noValidate
            onSubmit={(evento) => {
              evento.preventDefault();
              salvar(false);
            }}
          >
            <Heading slot="title">{editando ? "Editar cartão" : "Novo cartão"}</Heading>
            <p className="dica-teclado">
              <kbd>Ctrl</kbd>+<kbd>Enter</kbd> (<kbd>⌘</kbd>+<kbd>Enter</kbd> no macOS){" "}
              {editando ? "salva as alterações." : "salva e abre outro cartão."}
            </p>
            <div role="status" aria-live="polite" className="sr-only">
              {anuncio}
            </div>
            <MensagemErroFormulario mensagem={mensagem} />
            {(["frente", "verso", "explicacao"] as const).map((campo) => (
              <Controller
                key={campo}
                control={control}
                name={campo}
                render={({ field, fieldState }) => (
                  <CampoTextoLongo
                    rotulo={{ frente: "Frente", verso: "Verso", explicacao: "Explicação" }[campo]}
                    limite={
                      {
                        frente: limites.frenteMax,
                        verso: limites.versoMax,
                        explicacao: limites.explicacaoMax,
                      }[campo]
                    }
                    isRequired={campo !== "explicacao"}
                    linhas={campo === "frente" ? 3 : 4}
                    name={field.name}
                    value={field.value}
                    onChange={field.onChange}
                    onBlur={field.onBlur}
                    inputRef={field.ref}
                    onKeyDown={aoTeclar}
                    erro={fieldState.error?.message}
                  />
                )}
              />
            ))}
            {!editando && (
              <div className="campo">
                <label htmlFor="fonte-referencia">Fonte de referência (opcional)</label>
                <select
                  id="fonte-referencia"
                  className="entrada"
                  aria-invalid={erroFonte ? true : undefined}
                  aria-describedby={`fonte-referencia-ajuda${erroFonte ? " fonte-referencia-erro" : ""}`}
                  {...register("fonteId")}
                  onKeyDown={aoTeclar}
                >
                  <option value="">Nenhuma</option>
                  {fontes.map((fonte) => (
                    <option key={fonte.id} value={fonte.id}>
                      {fonte.titulo}
                    </option>
                  ))}
                </select>
                <span id="fonte-referencia-ajuda" className="contador">
                  Só para consulta: citar uma fonte não dá o selo de verificado.
                </span>
                {erroFonte && (
                  <span id="fonte-referencia-erro" className="erro-campo">
                    {erroFonte}
                  </span>
                )}
              </div>
            )}
            {confirmandoDescarte ? (
              <div
                role="alertdialog"
                aria-labelledby="titulo-descarte"
                aria-describedby="texto-descarte"
                className="confirmacao-descarte"
              >
                <p id="titulo-descarte">
                  <strong>
                    {editando ? "Descartar as alterações?" : "Descartar o que você digitou?"}
                  </strong>
                </p>
                <p id="texto-descarte">
                  {editando
                    ? "As alterações ainda não foram salvas."
                    : "O cartão ainda não foi salvo."}
                </p>
                <div className="acoes-dialogo">
                  <Botao
                    ref={continuar}
                    variante="secundario"
                    onPress={() => {
                      definirConfirmandoDescarte(false);
                      setFocus("frente");
                    }}
                  >
                    Continuar editando
                  </Botao>
                  <Botao variante="destrutivo" onPress={fechar}>
                    Descartar
                  </Botao>
                </div>
              </div>
            ) : (
              <div className="acoes-dialogo">
                <Botao variante="discreto" isDisabled={ocupado} onPress={tentarFechar}>
                  Cancelar
                </Botao>
                {!editando && (
                  <Botao
                    variante="secundario"
                    carregando={ocupado}
                    onPress={() => {
                      salvar(true);
                    }}
                  >
                    Salvar e criar outro
                  </Botao>
                )}
                <Botao type="submit" carregando={ocupado}>
                  Salvar
                </Botao>
              </div>
            )}
          </form>
        </Dialog>
      </Modal>
    </ModalOverlay>
  );
}
