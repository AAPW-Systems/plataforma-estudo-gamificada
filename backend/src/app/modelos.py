"""Registro de todas as entidades do ORM, para o Alembic e para os testes de catálogo.

Cada spec acrescenta aqui a importação dos modelos do seu domínio.
"""

from __future__ import annotations

from app.identidade.modelos import Sessao, TentativaAcesso, Usuario
from app.nucleo.banco import Base
from app.revisao.modelos import ParametrosFsrs

__all__ = ["Base", "Usuario", "Sessao", "TentativaAcesso", "ParametrosFsrs"]
