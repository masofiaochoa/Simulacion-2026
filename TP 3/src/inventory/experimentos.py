"""Orquestacion y resumenes de experimentos de inventario."""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.common.csv_utils import escribir_filas_csv
from src.common.statistics import (
    desvio_estandar_muestral,
    media,
    semiancho_intervalo_confianza,
)
from src.inventory.simulador import (
    ParametrosInventario,
    PoliticaInventario,
    ResultadoInventario,
    simular_inventario,
)


METRICAS_RESUMEN = [
    "demanda_total",
    "demanda_satisfecha",
    "unidades_faltantes",
    "ordenes_emitidas",
    "inventario_promedio",
    "costo_orden",
    "costo_mantenimiento",
    "costo_faltante",
    "costo_total",
    "nivel_servicio",
]


@dataclass(frozen=True)
class ConfiguracionInventario:
    unidad_tiempo: str
    politica_revision: str
    horizonte_dias: int
    replicas: int
    semilla_base: int
    distribucion_demanda: str
    demanda_media_diaria: float
    tiempo_entrega_dias: int
    inventario_inicial: int
    costo_fijo_orden: float
    costo_mantenimiento_unidad_dia: float
    costo_faltante_unidad: float
    politicas: list[PoliticaInventario]


def cargar_configuracion_inventario(ruta: str | Path) -> ConfiguracionInventario:
    with Path(ruta).open("r", encoding="utf-8") as archivo_configuracion:
        configuracion = json.load(archivo_configuracion)["inventory"]

    politicas = [
        PoliticaInventario(
            nombre=str(politica["name"]),
            Q=int(politica["order_quantity"]),
            r=int(politica["reorder_point"]),
        )
        for politica in configuracion["policies"]
    ]
    return ConfiguracionInventario(
        unidad_tiempo=str(configuracion["time_unit"]),
        politica_revision=str(configuracion["policy"]),
        horizonte_dias=int(configuracion["horizon_days"]),
        replicas=int(configuracion["replications"]),
        semilla_base=int(configuracion["base_seed"]),
        distribucion_demanda=str(configuracion["demand_distribution"]),
        demanda_media_diaria=float(configuracion["mean_daily_demand"]),
        tiempo_entrega_dias=int(configuracion["lead_time_days"]),
        inventario_inicial=int(configuracion["initial_inventory"]),
        costo_fijo_orden=float(configuracion["order_cost"]),
        costo_mantenimiento_unidad_dia=float(
            configuracion["holding_cost_per_unit_day"]
        ),
        costo_faltante_unidad=float(configuracion["shortage_cost_per_unit"]),
        politicas=politicas,
    )


def ejecutar_experimentos(
    configuracion: ConfiguracionInventario,
) -> list[ResultadoInventario]:
    resultados: list[ResultadoInventario] = []
    for indice_politica, politica in enumerate(configuracion.politicas):
        for replica in range(configuracion.replicas):
            semilla = _semilla_replica(
                configuracion.semilla_base,
                indice_politica,
                replica,
            )
            parametros = ParametrosInventario(
                horizonte_dias=configuracion.horizonte_dias,
                demanda_media_diaria=configuracion.demanda_media_diaria,
                inventario_inicial=configuracion.inventario_inicial,
                tiempo_entrega_dias=configuracion.tiempo_entrega_dias,
                costo_fijo_orden=configuracion.costo_fijo_orden,
                costo_mantenimiento_unidad_dia=(
                    configuracion.costo_mantenimiento_unidad_dia
                ),
                costo_faltante_unidad=configuracion.costo_faltante_unidad,
                politica=politica,
                semilla=semilla,
            )
            resultados.append(simular_inventario(parametros))
    return resultados


def construir_filas_corridas(
    resultados: list[ResultadoInventario],
) -> list[dict[str, Any]]:
    filas: list[dict[str, Any]] = []
    replica_por_politica: dict[str, int] = defaultdict(int)

    for resultado in resultados:
        politica = resultado.parametros.politica.nombre
        replica = replica_por_politica[politica]
        fila = resultado.fila_metricas()
        fila = {
            "politica": fila.pop("politica"),
            "replica": replica,
            **fila,
        }
        filas.append(fila)
        replica_por_politica[politica] += 1

    return filas


def construir_filas_resumen(
    resultados: list[ResultadoInventario],
) -> list[dict[str, Any]]:
    grupos = _agrupar_por_politica(resultados)
    filas: list[dict[str, Any]] = []

    for politica, resultados_politica in grupos.items():
        parametros = resultados_politica[0].parametros
        fila: dict[str, Any] = {
            "politica": politica,
            "Q": parametros.politica.Q,
            "r": parametros.politica.r,
            "horizonte_dias": parametros.horizonte_dias,
            "replicas": len(resultados_politica),
            "demanda_media_diaria": parametros.demanda_media_diaria,
            "inventario_inicial": parametros.inventario_inicial,
            "tiempo_entrega_dias": parametros.tiempo_entrega_dias,
            "costo_fijo_orden": parametros.costo_fijo_orden,
            "costo_mantenimiento_unidad_dia": (
                parametros.costo_mantenimiento_unidad_dia
            ),
            "costo_faltante_unidad": parametros.costo_faltante_unidad,
        }

        for metrica in METRICAS_RESUMEN:
            valores = [float(getattr(resultado, metrica)) for resultado in resultados_politica]
            fila[f"{metrica}_media"] = media(valores)
            fila[f"{metrica}_desvio_estandar"] = desvio_estandar_muestral(valores)
            fila[f"{metrica}_semiancho_ic95"] = semiancho_intervalo_confianza(valores)

        filas.append(fila)

    return filas


def construir_filas_series(
    resultados: list[ResultadoInventario],
) -> list[dict[str, Any]]:
    filas: list[dict[str, Any]] = []
    replica_por_politica: dict[str, int] = defaultdict(int)

    for resultado in resultados:
        parametros = resultado.parametros
        politica = parametros.politica.nombre
        replica = replica_por_politica[politica]
        for fila_serie in resultado.serie_temporal:
            filas.append(
                {
                    "politica": politica,
                    "replica": replica,
                    "semilla": parametros.semilla,
                    "Q": parametros.politica.Q,
                    "r": parametros.politica.r,
                    **fila_serie,
                }
            )
        replica_por_politica[politica] += 1

    return filas


def escribir_salidas_experimentos(
    resultados: list[ResultadoInventario],
    directorio_salida: str | Path,
) -> None:
    ruta_salida = Path(directorio_salida)
    escribir_filas_csv(
        construir_filas_corridas(resultados),
        ruta_salida / "inventario_corridas.csv",
    )
    escribir_filas_csv(
        construir_filas_resumen(resultados),
        ruta_salida / "inventario_resumen.csv",
    )
    escribir_filas_csv(
        construir_filas_series(resultados),
        ruta_salida / "inventario_series.csv",
    )


def _agrupar_por_politica(
    resultados: list[ResultadoInventario],
) -> dict[str, list[ResultadoInventario]]:
    grupos: dict[str, list[ResultadoInventario]] = defaultdict(list)
    for resultado in resultados:
        grupos[resultado.parametros.politica.nombre].append(resultado)
    return grupos


def _semilla_replica(
    semilla_base: int,
    indice_politica: int,
    replica: int,
) -> int:
    return semilla_base + indice_politica * 1000 + replica

