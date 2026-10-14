"""O worker carrega as tarefas de todos os domínios ao iniciar (T056)."""

from __future__ import annotations

import json
import subprocess
import sys

import pytest

pytestmark = pytest.mark.integration

SCRIPT = """
import json
from app.worker import carregar_tarefas
from app.nucleo.fila import app_fila
carregar_tarefas()
print(json.dumps(sorted(app_fila.tasks)))
"""


def test_o_worker_registra_as_tarefas_da_identidade_num_processo_novo() -> None:
    """Num processo limpo, só `carregar_tarefas` pode registrá-las (sem importar `servicos`)."""
    resultado = subprocess.run(  # noqa: S603
        [sys.executable, "-c", SCRIPT], capture_output=True, text=True, check=True, timeout=60
    )
    tarefas = json.loads(resultado.stdout.strip().splitlines()[-1])
    assert "identidade.apagar_objetos_usuario" in tarefas
    assert "identidade.limpar_registros_expirados" in tarefas
