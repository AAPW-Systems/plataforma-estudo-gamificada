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
    <NumberField {...props} className="campo" isInvalid={Boolean(erro)}>
      <Label>{rotulo}</Label>
      <Group>
        <Input className="entrada" />
      </Group>
      {erro && (
        <Text slot="description" className="erro-campo">
          {erro}
        </Text>
      )}
    </NumberField>
  );
}
