"""Ejecuta la matriz completa de experimentos M/M/1."""

from __future__ import annotations

import argparse
from pathlib import Path

from src.mm1.experiments import (
    cargar_configuracion_experimentos,
    escribir_salidas_experimentos,
    ejecutar_experimentos,
)


def principal() -> None:
    parser = argparse.ArgumentParser(description="Ejecuta todos los experimentos M/M/1.")
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
        default="results/mm1/experiments",
        help="Directorio donde se escriben los CSV de experimentos.",
    )
    argumentos = parser.parse_args()

    configuracion = cargar_configuracion_experimentos(Path(argumentos.configuracion))
    resultados = ejecutar_experimentos(configuracion)
    escribir_salidas_experimentos(
        resultados,
        Path(argumentos.directorio_salida),
        configuracion.max_longitud_probabilidad_cola,
    )

    cantidad_corridas = (
        len(configuracion.factores_tasa_arribo)
        * len(configuracion.capacidades_cola)
        * configuracion.replicas
    )
    print("Experimentos M/M/1 completados")
    print(f"  corridas experimentales: {cantidad_corridas}")
    print(f"  directorio de salida: {argumentos.directorio_salida}")
    print("  nota: los casos de cola infinita con rho >= 1 se marcan sin regimen estacionario")


if __name__ == "__main__":
    principal()
