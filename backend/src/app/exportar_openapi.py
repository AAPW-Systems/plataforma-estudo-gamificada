"""Exporta o contrato sem abrir conexões: uv run python -m app.exportar_openapi."""

import json
from pathlib import Path

from app.principal import criar_aplicacao


def exportar(destino: Path = Path("openapi.json")) -> None:
    destino.write_text(
        json.dumps(criar_aplicacao().openapi(), ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    exportar()
