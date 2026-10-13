"""Fábricas de dados fictícios (regra 10: nenhum dado pessoal real).

Toda conta usa o domínio reservado `exemplo.com`. As fábricas de cada spec ficam em
arquivos próprios (`fabricas_cartoes.py`...), conforme a divisão da implementação do MVP.
"""

from __future__ import annotations

import itertools
import uuid
from dataclasses import dataclass

_sequencia = itertools.count(1)


@dataclass(frozen=True, slots=True)
class DadosConta:
    nome: str
    email: str
    senha: str
    fuso: str = "America/Recife"

    def cadastro(self) -> dict[str, str]:
        return {"nome": self.nome, "email": self.email, "senha": self.senha, "fuso": self.fuso}

    def entrada(self) -> dict[str, str]:
        return {"email": self.email, "senha": self.senha}


def dados_conta(**alteracoes: str) -> DadosConta:
    """Conta fictícia única por chamada."""
    numero = next(_sequencia)
    sufixo = uuid.uuid4().hex[:8]
    base = {
        "nome": f"Estudante Teste {numero}",
        "email": f"estudante.{numero}.{sufixo}@exemplo.com",
        "senha": f"uma frase longa e incomum {sufixo}",
    }
    base.update(alteracoes)
    return DadosConta(**base)
