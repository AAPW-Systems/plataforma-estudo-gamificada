import type { Ref } from "react";
import {
  Group,
  Input,
  Label,
  NumberField,
  Text,
  type NumberFieldProps,
} from "react-aria-components";

export interface CampoNumeroProps extends Omit<NumberFieldProps, "children"> {
  rotulo: string;
  erro?: string | undefined;
  ajuda?: string;
  inputRef?: Ref<HTMLInputElement>;
}

export function CampoNumero({ rotulo, erro, ajuda, inputRef, ...props }: CampoNumeroProps) {
  return (
    <NumberField {...props} className="campo" validationBehavior="aria" isInvalid={Boolean(erro)}>
      <Label>{rotulo}</Label>
      <Group>
        <Input ref={inputRef} className="entrada" />
      </Group>
      {ajuda && <Text slot="description">{ajuda}</Text>}
      {erro && (
        <Text slot="errorMessage" className="erro-campo">
          {erro}
        </Text>
      )}
    </NumberField>
  );
}
