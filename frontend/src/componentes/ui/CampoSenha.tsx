import { CampoTexto, type CampoTextoProps } from "./CampoTexto";

export function CampoSenha(props: Omit<CampoTextoProps, "type">) {
  return <CampoTexto {...props} type="password" />;
}
