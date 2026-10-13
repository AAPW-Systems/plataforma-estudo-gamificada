import { mkdir, readFile, writeFile } from "node:fs/promises";

import openapiTS, { astToString } from "openapi-typescript";
import { format } from "prettier";

const documento = JSON.parse(
  await readFile(new URL("../../backend/openapi.json", import.meta.url), "utf8"),
);
const destino = new URL("../src/api/", import.meta.url);
await mkdir(destino, { recursive: true });
const tipos = astToString(await openapiTS(documento));
await writeFile(
  new URL("esquema.gerado.d.ts", destino),
  await format(tipos, { parser: "typescript" }),
);

const limites = {};
for (const [nome, esquema] of Object.entries(documento.components?.schemas ?? {})) {
  const campos = {};
  for (const [campo, propriedade] of Object.entries(esquema.properties ?? {})) {
    const restricoes = Object.fromEntries(
      Object.entries(propriedade).filter(([chave]) =>
        ["minimum", "maximum", "minLength", "maxLength", "multipleOf"].includes(chave),
      ),
    );
    if (Object.keys(restricoes).length) campos[campo] = restricoes;
  }
  if (Object.keys(campos).length) limites[nome] = campos;
}
await writeFile(
  new URL("limites.gerado.ts", destino),
  await format(
    `// Gerado de backend/openapi.json. Não editar.\nexport const limites = ${JSON.stringify(limites)} as const;\n`,
    { parser: "typescript" },
  ),
);
