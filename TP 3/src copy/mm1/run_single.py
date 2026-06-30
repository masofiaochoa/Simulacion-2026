"""Ejecuta una simulacion M/M/1 con los parametros base del TP."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.mm1.simulator import (
    ParametrosMM1,
    escribir_metricas_csv,
    escribir_probabilidades_cola_csv,
    escribir_serie_temporal_csv,
    simular_mm1,
)
from src.mm1.theory import teoria_mm1_infinita, teoria_mm1k


def principal() -> None:
    parser = argparse.ArgumentParser(description="Ejecuta una simulacion M/M/1.")
    parser.add_argument(
        "--config",
        "--configuracion",
        dest="configuracion",
        default="config/default_parameters.json",
        help="Ruta al archivo JSON de configuracion.",
    )
    parser.add_argument(
        "--arrival-factor",
        "--factor-arribo",
        dest="factor_arribo",
        type=float,
        default=0.75,
        help="Tasa de arribo como factor de la tasa de servicio.",
    )
    parser.add_argument(
        "--service-rate",
        "--tasa-servicio",
        dest="tasa_servicio",
        type=float,
        default=None,
        help="Tasa de servicio. Por defecto usa el valor de configuracion.",
    )
    parser.add_argument(
        "--simulation-time",
        "--tiempo-simulacion",
        dest="tiempo_simulacion",
        type=float,
        default=None,
        help="Horizonte de simulacion. Por defecto usa el valor de configuracion.",
    )
    parser.add_argument(
        "--queue-capacity",
        "--capacidad-cola",
        dest="capacidad_cola",
        default="infinite",
        help="Capacidad de espera: entero, 'infinita', 'inf' o 'ninguna'.",
    )
    parser.add_argument(
        "--seed",
        "--semilla",
        dest="semilla",
        type=int,
        default=None,
        help="Semilla aleatoria. Por defecto usa la semilla base de configuracion.",
    )
    parser.add_argument(
        "--output-dir",
        "--directorio-salida",
        dest="directorio_salida",
        default="results/mm1",
        help="Directorio donde se escriben las salidas CSV.",
    )
    parser.add_argument(
        "--no-time-series",
        "--sin-serie-temporal",
        dest="sin_serie_temporal",
        action="store_true",
        help="Omite la serie temporal a nivel de eventos.",
    )
    argumentos = parser.parse_args()

    configuracion = _cargar_configuracion(Path(argumentos.configuracion))
    configuracion_mm1 = configuracion["mm1"]

    tasa_servicio = (
        argumentos.tasa_servicio
        if argumentos.tasa_servicio is not None
        else float(configuracion_mm1["service_rate"])
    )
    tiempo_simulacion = (
        argumentos.tiempo_simulacion
        if argumentos.tiempo_simulacion is not None
        else float(configuracion_mm1["simulation_time"])
    )
    semilla = (
        argumentos.semilla
        if argumentos.semilla is not None
        else int(configuracion_mm1["base_seed"])
    )
    capacidad_cola = _parsear_capacidad_cola(argumentos.capacidad_cola)
    tasa_arribo = tasa_servicio * argumentos.factor_arribo

    parametros = ParametrosMM1(
        tasa_arribo=tasa_arribo,
        tasa_servicio=tasa_servicio,
        tiempo_simulacion=tiempo_simulacion,
        capacidad_cola=capacidad_cola,
        semilla=semilla,
    )
    resultado = simular_mm1(
        parametros,
        registrar_serie_temporal=not argumentos.sin_serie_temporal,
    )

    directorio_salida = Path(argumentos.directorio_salida)
    escribir_metricas_csv([resultado], directorio_salida / "mm1_single_metrics.csv")
    escribir_probabilidades_cola_csv(
        [resultado],
        directorio_salida / "mm1_single_queue_probabilities.csv",
    )
    if not argumentos.sin_serie_temporal:
        escribir_serie_temporal_csv(resultado, directorio_salida / "mm1_single_timeseries.csv")

    teoria = (
        teoria_mm1_infinita(tasa_arribo, tasa_servicio)
        if capacidad_cola is None
        else teoria_mm1k(tasa_arribo, tasa_servicio, capacidad_cola)
    )
    _imprimir_resumen(resultado.fila_metricas(), teoria)


def _cargar_configuracion(ruta: Path) -> dict:
    with ruta.open("r", encoding="utf-8") as archivo_configuracion:
        return json.load(archivo_configuracion)


def _parsear_capacidad_cola(valor_crudo: str) -> int | None:
    normalizado = valor_crudo.strip().lower()
    if normalizado in {"infinite", "infinita", "inf", "none", "ninguna", "null", "nulo"}:
        return None
    valor = int(normalizado)
    if valor < 0:
        raise ValueError("la capacidad de cola debe ser cero o mayor")
    return valor


def _imprimir_resumen(metricas: dict, teoria: dict[str, object]) -> None:
    print("Corrida individual M/M/1")
    print(f"  lambda: {metricas['tasa_arribo']:.6g}")
    print(f"  mu: {metricas['tasa_servicio']:.6g}")
    print(f"  rho: {metricas['rho']:.6g}")
    print(f"  capacidad de cola: {metricas['capacidad_cola']}")
    print(f"  tiempo de simulacion: {metricas['tiempo_simulacion']:.6g}")
    print(f"  semilla: {metricas['semilla']}")
    print("")
    print("Metricas simuladas")
    print(f"  clientes promedio en sistema: {metricas['promedio_clientes_sistema']:.6g}")
    print(f"  clientes promedio en cola: {metricas['promedio_clientes_cola']:.6g}")
    print(f"  tiempo promedio en sistema: {metricas['tiempo_promedio_sistema']:.6g}")
    print(f"  tiempo promedio en cola: {metricas['tiempo_promedio_cola']:.6g}")
    print(f"  utilizacion del servidor: {metricas['utilizacion_servidor']:.6g}")
    print(f"  probabilidad de denegacion: {metricas['probabilidad_denegacion']:.6g}")
    print("")
    print("Referencia teorica")
    if not teoria.get("estable", True):
        print("  no hay referencia estacionaria porque rho >= 1")
        return
    print(f"  clientes promedio en sistema: {teoria['promedio_clientes_sistema']:.6g}")
    print(f"  clientes promedio en cola: {teoria['promedio_clientes_cola']:.6g}")
    print(f"  tiempo promedio en sistema: {teoria['tiempo_promedio_sistema']:.6g}")
    print(f"  tiempo promedio en cola: {teoria['tiempo_promedio_cola']:.6g}")
    print(f"  utilizacion del servidor: {teoria['utilizacion_servidor']:.6g}")
    print(f"  probabilidad de denegacion: {teoria['probabilidad_denegacion']:.6g}")


if __name__ == "__main__":
    principal()
