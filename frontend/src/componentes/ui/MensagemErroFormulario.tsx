export function MensagemErroFormulario({ mensagem }: { mensagem?: string | undefined }) {
  return mensagem ? (
    <div className="erro-formulario" role="alert">
      {mensagem}
    </div>
  ) : null;
}
