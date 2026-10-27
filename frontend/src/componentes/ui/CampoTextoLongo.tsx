import { useState, type Ref } from "react";
import { Label, Text, TextArea, TextField, type TextFieldProps } from "react-aria-components";

/**
 * Conta como o servidor: em code points depois do NFC (DTEC 036). Um emoji vale 1, e "e" mais o
 * acento combinante vale 1, ao contrário de `texto.length`, que conta unidades UTF-16.
 */
export function contarCaracteres(texto: string): number {
  // `Array.from` percorre por code points (como o `len` do servidor), não por grafemas.
  return Array.from(texto.normalize("NFC")).length;
}

const formatador = new Intl.NumberFormat("pt-BR");

export interface CampoTextoLongoProps extends Omit<TextFieldProps, "children"> {
  rotulo: string;
  /** Limite vigente, vindo do servidor (`GET /cartoes/limites`); o campo não corta o texto. */
  limite: number;
  erro?: string | undefined;
  ajuda?: string;
  linhas?: number;
  inputRef?: Ref<HTMLTextAreaElement>;
}

/**
 * Texto de várias linhas com rótulo, contador em code points e erro associados ao campo.
 * `Enter` quebra a linha. Funciona controlado (`value`) ou não (`defaultValue`).
 */
export function CampoTextoLongo({
  rotulo,
  limite,
  erro,
  ajuda,
  linhas = 4,
  inputRef,
  value,
  defaultValue,
  onChange,
  ...props
}: CampoTextoLongoProps) {
  const [interno, definirInterno] = useState(defaultValue ?? "");
  const atual = value ?? interno;
  const total = contarCaracteres(atual);
  const excesso = Math.max(0, total - limite);

  function aoMudar(novo: string) {
    if (value === undefined) definirInterno(novo);
    onChange?.(novo);
  }

  return (
    <TextField
      {...props}
      value={atual}
      onChange={aoMudar}
      className="campo"
      validationBehavior="aria"
      isInvalid={Boolean(erro)}
    >
      <Label>
        {rotulo}
        {props.isRequired ? " (obrigatório)" : ""}
      </Label>
      <TextArea ref={inputRef} rows={linhas} className="entrada entrada-longa" />
      <Text slot="description" className="contador" data-excedido={excesso > 0}>
        {ajuda ? `${ajuda} ` : ""}
        {formatador.format(total)} de {formatador.format(limite)}
        {excesso > 0 ? ` (${formatador.format(excesso)} acima do limite)` : ""}
      </Text>
      {erro && (
        <Text slot="errorMessage" className="erro-campo">
          {erro}
        </Text>
      )}
    </TextField>
  );
}
