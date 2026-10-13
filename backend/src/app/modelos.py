"""Registro de todas as entidades do ORM, para o Alembic e para os testes de catálogo.

Cada spec acrescenta aqui a importação dos modelos do seu domínio.
"""

from __future__ import annotations

from app.nucleo.banco import Base

__all__ = ["Base"]
