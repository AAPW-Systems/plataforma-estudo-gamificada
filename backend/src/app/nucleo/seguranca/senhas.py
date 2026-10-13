"""Hash de senha com Argon2id, perfil de pouca memória da RFC 9106 (DTEC 023).

Parâmetros: t=3, m=64 MiB, p=4. O cálculo roda em *thread* e passa por um semáforo
(`ARGON2_CONCORRENCIA`), para que uma rajada de entradas não esgote a memória da VPS
(pico de concorrência × 64 MiB). A senha não é normalizada (`padroes-implementacao.md`).
"""

from __future__ import annotations

import asyncio
import secrets

import structlog
from argon2 import PasswordHasher, profiles
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

logger = structlog.get_logger(__name__)


def criar_hasher() -> PasswordHasher:
    return PasswordHasher.from_parameters(profiles.RFC_9106_LOW_MEMORY)


class ServicoSenhas:
    def __init__(self, concorrencia: int, hasher: PasswordHasher | None = None) -> None:
        self._hasher = hasher or criar_hasher()
        self._semaforo = asyncio.Semaphore(concorrencia)
        self._trava_ficticio = asyncio.Lock()
        self._ficticio: str | None = None

    async def gerar_hash(self, senha: str) -> str:
        async with self._semaforo:
            return await asyncio.to_thread(self._hasher.hash, senha)

    async def verificar(self, hash_armazenado: str, senha: str) -> bool:
        async with self._semaforo:
            return await asyncio.to_thread(self._verificar_sincrono, hash_armazenado, senha)

    def _verificar_sincrono(self, hash_armazenado: str, senha: str) -> bool:
        try:
            return self._hasher.verify(hash_armazenado, senha)
        except VerifyMismatchError:
            return False
        except (InvalidHashError, VerificationError):
            # Hash corrompido no banco: nunca autentica, mas não pode passar em silêncio.
            logger.warning("hash_senha_invalido")
            return False

    def precisa_novo_hash(self, hash_armazenado: str) -> bool:
        """Verdadeiro quando os parâmetros do hash ficaram abaixo do perfil vigente."""
        try:
            return self._hasher.check_needs_rehash(hash_armazenado)
        except InvalidHashError:
            return True

    async def preparar(self) -> None:
        """Calcula o hash fictício na subida, para que a primeira entrada não pague o custo."""
        await self._obter_ficticio()

    async def _obter_ficticio(self) -> str:
        async with self._trava_ficticio:
            if self._ficticio is None:
                self._ficticio = await self.gerar_hash(secrets.token_urlsafe(32))
            return self._ficticio

    async def verificar_ficticia(self, senha: str) -> bool:
        """Gasta o mesmo custo de uma verificação real e sempre recusa (CS-003).

        Usada quando o e-mail não tem conta, para que o tempo da resposta não revele isso.
        """
        await self.verificar(await self._obter_ficticio(), senha)
        return False
