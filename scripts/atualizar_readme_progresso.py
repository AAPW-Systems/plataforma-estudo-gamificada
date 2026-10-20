#!/usr/bin/env python3
"""Gera a tabela "Progresso do desenvolvimento" do README.md a partir dos tasks.md.

Uso:
    python scripts/atualizar_readme_progresso.py           # reescreve o README.md
    python scripts/atualizar_readme_progresso.py --check   # falha se o README estiver desatualizado

Só usa a biblioteca padrão, para rodar igual em qualquer máquina e com qualquer agente.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SPECS = RAIZ / "docs" / "specs"
README = RAIZ / "README.md"
INICIO = "<!-- progresso:inicio (gerado por scripts/atualizar_readme_progresso.py; não edite à mão) -->"
FIM = "<!-- progresso:fim -->"
ESTAGIO_MVP = range(1, 8)  # specs 001 a 007

FEITA = re.compile(r"^\s*- \[[xX]\]\s+(T\d+)")
ABERTA = re.compile(r"^\s*- \[ \]\s+(T\d+)")
TITULO = re.compile(r"^#\s+\d{3}-[a-z0-9-]+:\s*(.+)$")
STATUS = re.compile(r"^\|\s*Status\s*\|\s*(.+?)\s*\|\s*$")


def ler(caminho: Path) -> list[str]:
    return caminho.read_text(encoding="utf-8").splitlines()


def linha_da_spec(pasta: Path) -> str:
    numero = pasta.name[:3]
    feitas: list[str] = []
    abertas: list[str] = []
    for linha in ler(pasta / "tasks.md"):
        if m := FEITA.match(linha):
            feitas.append(m.group(1))
        elif m := ABERTA.match(linha):
            abertas.append(m.group(1))
    titulo = status = ""
    for linha in ler(pasta / "README.md"):
        if not titulo and (m := TITULO.match(linha)):
            titulo = m.group(1)
        if not status and (m := STATUS.match(linha)):
            status = m.group(1)
    titulo = titulo[:1].upper() + titulo[1:]
    total = len(feitas) + len(abertas)
    situacao = status
    if feitas and abertas and len(abertas) <= 3:
        situacao += f" ({'falta' if len(abertas) == 1 else 'faltam'} {', '.join(abertas)})"
    return (
        f"| [{numero}: {titulo}](docs/specs/{pasta.name}/spec.md) "
        f"| {len(feitas)} de {total} ([tarefas](docs/specs/{pasta.name}/tasks.md)) "
        f"| {situacao} |"
    )


def tabela() -> str:
    pastas = sorted(p for p in SPECS.iterdir() if p.is_dir() and int(p.name[:3]) in ESTAGIO_MVP)
    linhas = ["| Spec | Tarefas concluídas | Situação |", "|---|---|---|"]
    linhas += [linha_da_spec(p) for p in pastas]
    return "\n".join(linhas)


def gerar(texto: str) -> str:
    i, f = texto.find(INICIO.split(" (")[0]), texto.find(FIM)
    if i < 0 or f < 0:
        sys.exit("Marcadores de progresso não encontrados no README.md.")
    corpo = (
        f"{INICIO}\n{tabela()}\n\n"
        "As specs 008 a 016 pertencem ao final acadêmico e seguem em especificação; "
        "o índice completo está em [`docs/specs/`](docs/specs/README.md).\n"
    )
    return texto[:i] + corpo + texto[f:]


def main() -> int:
    atual = README.read_text(encoding="utf-8")
    novo = gerar(atual)
    if "--check" in sys.argv:
        if novo != atual:
            print("README.md desatualizado: rode `python scripts/atualizar_readme_progresso.py`.")
            return 1
        return 0
    if novo != atual:
        README.write_text(novo, encoding="utf-8", newline="")
        print("README.md atualizado.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
