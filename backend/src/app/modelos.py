"""Registro de todas as entidades do ORM, para o Alembic e para os testes de catálogo.

Cada spec acrescenta aqui a importação dos modelos do seu domínio.
"""

from __future__ import annotations

from app.fontes.modelos import Fonte, Trecho
from app.identidade.modelos import Sessao, TentativaAcesso, Usuario
from app.materias.modelos import Materia
from app.nucleo.banco import Base
from app.revisao.modelos import ParametrosFsrs

__all__ = [
    "Base",
    "Fonte",
    "Materia",
    "ParametrosFsrs",
    "Sessao",
    "TentativaAcesso",
    "Trecho",
    "Usuario",
]
