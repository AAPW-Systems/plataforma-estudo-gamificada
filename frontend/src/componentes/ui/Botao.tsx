import type { Ref } from "react";
import { Button, type ButtonProps } from "react-aria-components";

export interface BotaoProps extends ButtonProps {
  variante?: "primario" | "secundario" | "discreto" | "destrutivo";
  carregando?: boolean;
  ref?: Ref<HTMLButtonElement>;
}

export function Botao({
  variante = "primario",
  carregando = false,
  children,
  ...props
}: BotaoProps) {
  return (
    <Button
      {...props}
      className={`botao botao-${variante}`}
      isDisabled={(props.isDisabled ?? false) || carregando}
      aria-busy={carregando}
    >
      {carregando ? "Aguarde…" : children}
    </Button>
  );
}
