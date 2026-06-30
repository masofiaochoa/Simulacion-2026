"""Ejecuta la matriz completa de experimentos de inventario."""

from __future__ import annotations

import argparse
from pathlib import Path

from src.inventory.experimentos import (
    cargar_configuracion_inventario,
    escribir_salidas_experimentos,
    ejecutar_experimentos,
)


def principal() -> None:
    parser = argparse.ArgumentParser(
        description="Ejecuta todos los experimentos de inventario."
    )
    parser.add_argument(
        "--config",
        "--configuracion",
        dest="configuracion",
        default="config/default_parameters.json",
        help="Ruta al archivo JSON de configuracion.",
    )
    parser.add_argument(
        "--output-dir",
        "--directorio-salida",
        dest="directorio_salida",
        default="results/inventory/experiments",
        help="Directorio donde se escriben los CSV de experimentos.",
    )
    argumentos = parser.parse_args()

    configuracion = cargar_configuracion_inventario(Path(argumentos.configuracion))
    resultados = ejecutar_experimentos(configuracion)
    escribir_salidas_experimentos(resultados, Path(argumentos.directorio_salida))

    cantidad_corridas = len(configuracion.politicas) * configuracion.replicas
    print("Experimentos de inventario completados")
    print(f"  politicas evaluadas: {len(configuracion.politicas)}")
    print(f"  replicas por politica: {configuracion.replicas}")
    print(f"  corridas experimentales: {cantidad_corridas}")
    print(f"  directorio de salida: {argumentos.directorio_salida}")
    print("  criterio de faltantes: ventas perdidas")


if __name__ == "__main__":
    principal()

