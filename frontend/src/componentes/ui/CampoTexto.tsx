import { Input, Label, Text, TextField, type TextFieldProps } from "react-aria-components";
import type { Ref } from "react";

export interface CampoTextoProps extends Omit<TextFieldProps, "children"> {
  rotulo: string;
  erro?: string | undefined;
  ajuda?: string;
  inputRef?: Ref<HTMLInputElement>;
}

export function CampoTexto({ rotulo, erro, ajuda, inputRef, ...props }: CampoTextoProps) {
  return (
    <TextField {...props} className="campo" isInvalid={Boolean(erro)}>
      <Label>
        {rotulo}
        {props.isRequired ? " (obrigatório)" : ""}
      </Label>
      <Input ref={inputRef} className="entrada" />
      {ajuda && <Text slot="description">{ajuda}</Text>}
      {erro && (
        <Text slot="description" className="erro-campo">
          {erro}
        </Text>
      )}
    </TextField>
  );
}
