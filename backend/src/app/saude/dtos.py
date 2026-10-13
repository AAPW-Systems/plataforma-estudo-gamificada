from typing import Literal

from app.nucleo.dtos import ModeloDTO


class Saude(ModeloDTO):
    estado: Literal["ok", "indisponivel"]
    verificacoes: dict[str, Literal["ok", "falhou"]] | None = None
