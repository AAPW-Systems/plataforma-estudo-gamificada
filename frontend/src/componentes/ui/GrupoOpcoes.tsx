import { Label, RadioButton, RadioField, RadioGroup, Text } from "react-aria-components";

export interface Opcao {
  valor: string;
  rotulo: string;
  descricao?: string;
}

export interface GrupoOpcoesProps {
  rotulo: string;
  opcoes: readonly Opcao[];
  /** Sem valor (`undefined`), nenhuma opção está escolhida: a escolha é do estudante. */
  valor: string | undefined;
  aoMudar: (valor: string) => void;
  obrigatorio?: boolean;
  erro?: string | undefined;
  desabilitado?: boolean;
}

/** Escolha exclusiva entre opções com descrição, operável por teclado (setas). */
export function GrupoOpcoes({
  rotulo,
  opcoes,
  valor,
  aoMudar,
  obrigatorio = false,
  erro,
  desabilitado = false,
}: GrupoOpcoesProps) {
  return (
    <RadioGroup
      className="grupo-opcoes"
      value={valor ?? null}
      onChange={aoMudar}
      isRequired={obrigatorio}
      isDisabled={desabilitado}
      isInvalid={Boolean(erro)}
      validationBehavior="aria"
    >
      <Label>
        {rotulo}
        {obrigatorio ? " (obrigatório)" : ""}
      </Label>
      {opcoes.map((opcao) => (
        <RadioField key={opcao.valor} value={opcao.valor} className="opcao">
          <RadioButton className="opcao-radio">{opcao.rotulo}</RadioButton>
          {opcao.descricao && (
            <Text slot="description" className="opcao-descricao">
              {opcao.descricao}
            </Text>
          )}
        </RadioField>
      ))}
      {erro && (
        <Text slot="errorMessage" className="erro-campo">
          {erro}
        </Text>
      )}
    </RadioGroup>
  );
}
