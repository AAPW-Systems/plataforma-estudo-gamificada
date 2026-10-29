export interface CitacaoDestacadaProps {
  /** Texto do trecho, exibido sempre como texto puro. */
  texto: string;
  /** Intervalo da citação no trecho, em code points, como o servidor conta (DTEC 042). */
  inicio: number;
  fim: number;
}

// Array.from separa por code point: um emoji fora do BMP conta 1, como o `char_length` do banco.
export function CitacaoDestacada({ texto, inicio, fim }: CitacaoDestacadaProps) {
  const pontos = Array.from(texto);
  const valido = Number.isInteger(inicio) && Number.isInteger(fim);
  if (!valido || inicio < 0 || inicio >= fim || fim > pontos.length) {
    return <p className="citacao-trecho">{texto}</p>;
  }
  return (
    <p className="citacao-trecho">
      {pontos.slice(0, inicio).join("")}
      <mark>{pontos.slice(inicio, fim).join("")}</mark>
      {pontos.slice(fim).join("")}
    </p>
  );
}
