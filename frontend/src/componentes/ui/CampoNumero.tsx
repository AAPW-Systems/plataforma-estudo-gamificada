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
  erro?: string;
}

export function CampoNumero({ rotulo, erro, ...props }: CampoNumeroProps) {
  return (
    <NumberField {...props} className="campo" validationBehavior="aria" isInvalid={Boolean(erro)}>
      <Label>{rotulo}</Label>
      <Group>
        <Input className="entrada" />
      </Group>
      {erro && (
        <Text slot="errorMessage" className="erro-campo">
          {erro}
        </Text>
      )}
    </NumberField>
  );
}
