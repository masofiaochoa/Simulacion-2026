"""Ayudantes CSV compartidos por los scripts."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Iterable


def escribir_filas_csv(filas: Iterable[dict[str, Any]], ruta: str | Path) -> None:
    lista_filas = list(filas)
    if not lista_filas:
        return

    ruta_salida = Path(ruta)
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    with ruta_salida.open("w", newline="", encoding="utf-8") as archivo_csv:
        escritor = csv.DictWriter(
            archivo_csv,
            fieldnames=list(lista_filas[0].keys()),
            lineterminator="\n",
        )
        escritor.writeheader()
        escritor.writerows(lista_filas)


def leer_filas_csv(ruta: str | Path) -> list[dict[str, str]]:
    with Path(ruta).open("r", newline="", encoding="utf-8") as archivo_csv:
        return list(csv.DictReader(archivo_csv))
