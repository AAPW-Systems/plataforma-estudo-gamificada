import { CampoTexto, type CampoTextoProps } from "./CampoTexto";

export function CampoFuso(props: CampoTextoProps) {
  return <CampoTexto ajuda="Use um fuso IANA, como America/Sao_Paulo." {...props} />;
}
