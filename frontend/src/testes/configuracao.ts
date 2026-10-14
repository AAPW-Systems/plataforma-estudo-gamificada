import "@testing-library/jest-dom/vitest";

import { configure } from "@testing-library/react";

// O limite padrão de 1 s dos `findBy*` e `waitFor` estoura quando a máquina está carregada
// (CI, suíte do backend rodando ao lado). 4 s mantém a falha real visível sem oscilar.
configure({ asyncUtilTimeout: 4000 });
