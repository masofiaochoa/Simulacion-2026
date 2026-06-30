"""Orquestacion y resumenes de experimentos para simulaciones M/M/1."""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.common.csv_utils import escribir_filas_csv
from src.common.statistics import (
    desvio_estandar_muestral,
    error_porcentual,
    media,
    semiancho_intervalo_confianza,
)
from src.mm1.simulator import ParametrosMM1, ResultadoMM1, simular_mm1
from src.mm1.theory import teoria_mm1_infinita, teoria_mm1k

METRICAS = {
    "promedio_clientes_sistema": "promedio_clientes_sistema",
    "promedio_clientes_cola": "promedio_clientes_cola",
    "tiempo_promedio_sistema": "tiempo_promedio_sistema",
    "tiempo_promedio_cola": "tiempo_promedio_cola",
    "utilizacion_servidor": "utilizacion_servidor",
    "probabilidad_denegacion": "probabilidad_denegacion",
}


@dataclass(frozen=True)
class ConfiguracionExperimentos:
    tasa_servicio: float
    factores_tasa_arribo: list[float]
    capacidades_cola: list[int | None]
    tiempo_simulacion: float
    replicas: int
    semilla_base: int
    max_longitud_probabilidad_cola: int


def cargar_configuracion_experimentos(ruta: str | Path) -> ConfiguracionExperimentos:
    with Path(ruta).open("r", encoding="utf-8") as archivo_configuracion:
        configuracion = json.load(archivo_configuracion)["mm1"]

    return ConfiguracionExperimentos(
        tasa_servicio=float(configuracion["service_rate"]),
        factores_tasa_arribo=[
            float(factor) for factor in configuracion["arrival_rate_factors"]
        ],
        capacidades_cola=configuracion["queue_capacities"],
        tiempo_simulacion=float(configuracion["simulation_time"]),
        replicas=int(configuracion["replications"]),
        semilla_base=int(configuracion["base_seed"]),
        max_longitud_probabilidad_cola=int(
            configuracion.get("max_queue_probability_length", 20)
        ),
    )


def ejecutar_experimentos(configuracion: ConfiguracionExperimentos) -> list[ResultadoMM1]:
    resultados: list[ResultadoMM1] = []
    for indice_capacidad, capacidad_cola in enumerate(configuracion.capacidades_cola):
        for indice_factor, factor_arribo in enumerate(configuracion.factores_tasa_arribo):
            tasa_arribo = configuracion.tasa_servicio * factor_arribo
            for replica in range(configuracion.replicas):
                semilla = _semilla_replica(
                    configuracion.semilla_base,
                    indice_capacidad,
                    indice_factor,
                    replica,
                )
                parametros = ParametrosMM1(
                    tasa_arribo=tasa_arribo,
                    tasa_servicio=configuracion.tasa_servicio,
                    tiempo_simulacion=configuracion.tiempo_simulacion,
                    capacidad_cola=capacidad_cola,
                    semilla=semilla,
                )
                resultados.append(
                    simular_mm1(parametros, registrar_serie_temporal=False)
                )
    return resultados


def construir_filas_corridas(resultados: list[ResultadoMM1]) -> list[dict[str, Any]]:
    filas: list[dict[str, Any]] = []
    replica_por_experimento: dict[tuple[float, str], int] = defaultdict(int)
    for resultado in resultados:
        fila = resultado.fila_metricas()
        clave = (
            fila["rho"],
            str(fila["capacidad_cola"]),
        )
        fila["factor_arribo"] = fila["rho"]
        fila["modelo_cola"] = _modelo_cola(resultado.parametros.capacidad_cola)
        fila["replica"] = replica_por_experimento[clave]
        fila["estado_teorico"] = _estado_teorico(resultado.parametros)
        replica_por_experimento[clave] += 1
        filas.append(fila)
    return filas


def construir_filas_resumen(
    resultados: list[ResultadoMM1],
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    grupos = _agrupar_resultados(resultados)
    filas_anchas: list[dict[str, Any]] = []
    filas_largas: list[dict[str, Any]] = []

    for clave, resultados_grupo in sorted(grupos.items(), key=_clave_orden_grupo):
        factor_arribo, etiqueta_capacidad_cola = clave
        parametros = resultados_grupo[0].parametros
        teoria = referencia_teorica(parametros)
        estado_teorico = _estado_teorico(parametros)

        fila_base: dict[str, Any] = {
            "factor_arribo": factor_arribo,
            "tasa_arribo": parametros.tasa_arribo,
            "tasa_servicio": parametros.tasa_servicio,
            "rho": parametros.tasa_arribo / parametros.tasa_servicio,
            "capacidad_cola": etiqueta_capacidad_cola,
            "modelo_cola": _modelo_cola(parametros.capacidad_cola),
            "tiempo_simulacion": parametros.tiempo_simulacion,
            "replicas": len(resultados_grupo),
            "estado_teorico": estado_teorico,
        }
        fila_ancha = dict(fila_base)

        for atributo_metrica, columna_metrica in METRICAS.items():
            valores = [
                getattr(resultado, atributo_metrica)
                for resultado in resultados_grupo
                if getattr(resultado, atributo_metrica) is not None
            ]
            media_metrica = media(valores)
            desvio_metrica = desvio_estandar_muestral(valores)
            ic_metrica = semiancho_intervalo_confianza(valores)
            valor_teorico = teoria.get(columna_metrica)
            error_metrica = error_porcentual(
                media_metrica,
                valor_teorico if isinstance(valor_teorico, float) else None,
            )

            fila_ancha[f"{columna_metrica}_media"] = media_metrica
            fila_ancha[f"{columna_metrica}_desvio_estandar"] = desvio_metrica
            fila_ancha[f"{columna_metrica}_semiancho_ic95"] = ic_metrica
            fila_ancha[f"{columna_metrica}_teoria"] = valor_teorico
            fila_ancha[f"{columna_metrica}_error_porcentual"] = error_metrica

            fila_larga = dict(fila_base)
            fila_larga.update(
                {
                    "metrica": columna_metrica,
                    "media": media_metrica,
                    "desvio_estandar": desvio_metrica,
                    "semiancho_ic95": ic_metrica,
                    "teoria": valor_teorico,
                    "error_porcentual": error_metrica,
                }
            )
            filas_largas.append(fila_larga)

        filas_anchas.append(fila_ancha)

    return filas_anchas, filas_largas


def construir_filas_probabilidades_cola(
    resultados: list[ResultadoMM1],
    max_longitud_cola: int,
) -> list[dict[str, Any]]:
    grupos = _agrupar_resultados(resultados)
    filas: list[dict[str, Any]] = []

    for clave, resultados_grupo in sorted(grupos.items(), key=_clave_orden_grupo):
        factor_arribo, etiqueta_capacidad_cola = clave
        parametros = resultados_grupo[0].parametros
        teoria = referencia_teorica(parametros)
        probabilidades_teoricas = teoria.get("probabilidades_longitud_cola") or {}

        longitudes_cola = range(0, max_longitud_cola + 1)
        for longitud_cola in longitudes_cola:
            valores = [
                resultado.probabilidades_tiempo_longitud_cola.get(longitud_cola, 0.0)
                for resultado in resultados_grupo
            ]
            probabilidad_media = media(valores)
            valor_teorico = (
                probabilidades_teoricas.get(longitud_cola)
                if isinstance(probabilidades_teoricas, dict)
                else None
            )
            filas.append(
                {
                    "factor_arribo": factor_arribo,
                    "tasa_arribo": parametros.tasa_arribo,
                    "tasa_servicio": parametros.tasa_servicio,
                    "rho": parametros.tasa_arribo / parametros.tasa_servicio,
                    "capacidad_cola": etiqueta_capacidad_cola,
                    "modelo_cola": _modelo_cola(parametros.capacidad_cola),
                    "longitud_cola": longitud_cola,
                    "probabilidad_media": probabilidad_media,
                    "desvio_estandar": desvio_estandar_muestral(valores),
                    "semiancho_ic95": semiancho_intervalo_confianza(valores),
                    "teoria": valor_teorico,
                    "error_porcentual": error_porcentual(
                        probabilidad_media,
                        valor_teorico
                        if isinstance(valor_teorico, float)
                        else None,
                    ),
                    "estado_teorico": _estado_teorico(parametros),
                }
            )

        valores_cola = [
            sum(
                probabilidad
                for longitud, probabilidad
                in resultado.probabilidades_tiempo_longitud_cola.items()
                if longitud > max_longitud_cola
            )
            for resultado in resultados_grupo
        ]
        filas.append(
            {
                "factor_arribo": factor_arribo,
                "tasa_arribo": parametros.tasa_arribo,
                "tasa_servicio": parametros.tasa_servicio,
                "rho": parametros.tasa_arribo / parametros.tasa_servicio,
                "capacidad_cola": etiqueta_capacidad_cola,
                "modelo_cola": _modelo_cola(parametros.capacidad_cola),
                "longitud_cola": f">{max_longitud_cola}",
                "probabilidad_media": media(valores_cola),
                "desvio_estandar": desvio_estandar_muestral(valores_cola),
                "semiancho_ic95": semiancho_intervalo_confianza(valores_cola),
                "teoria": None,
                "error_porcentual": None,
                "estado_teorico": _estado_teorico(parametros),
            }
        )

    return filas


def referencia_teorica(parametros: ParametrosMM1) -> dict[str, Any]:
    if parametros.capacidad_cola is None:
        return teoria_mm1_infinita(
            parametros.tasa_arribo,
            parametros.tasa_servicio,
        )
    return teoria_mm1k(
        parametros.tasa_arribo,
        parametros.tasa_servicio,
        parametros.capacidad_cola,
    )


def escribir_salidas_experimentos(
    resultados: list[ResultadoMM1],
    directorio_salida: str | Path,
    max_longitud_probabilidad_cola: int,
) -> None:
    ruta_salida = Path(directorio_salida)
    filas_anchas, filas_largas = construir_filas_resumen(resultados)
    escribir_filas_csv(construir_filas_corridas(resultados), ruta_salida / "mm1_runs.csv")
    escribir_filas_csv(filas_anchas, ruta_salida / "mm1_summary.csv")
    escribir_filas_csv(filas_largas, ruta_salida / "mm1_summary_long.csv")
    escribir_filas_csv(
        construir_filas_probabilidades_cola(
            resultados,
            max_longitud_probabilidad_cola,
        ),
        ruta_salida / "mm1_queue_probabilities.csv",
    )


def _agrupar_resultados(
    resultados: list[ResultadoMM1],
) -> dict[tuple[float, str], list[ResultadoMM1]]:
    grupos: dict[tuple[float, str], list[ResultadoMM1]] = defaultdict(list)
    for resultado in resultados:
        parametros = resultado.parametros
        clave = (
            parametros.tasa_arribo / parametros.tasa_servicio,
            _etiqueta_capacidad_cola(parametros.capacidad_cola),
        )
        grupos[clave].append(resultado)
    return grupos


def _clave_orden_grupo(
    item: tuple[tuple[float, str], list[ResultadoMM1]],
) -> tuple[float, int]:
    (factor_arribo, etiqueta_capacidad_cola), _ = item
    if etiqueta_capacidad_cola == "infinita":
        return factor_arribo, -1
    return factor_arribo, int(etiqueta_capacidad_cola)


def _etiqueta_capacidad_cola(capacidad_cola: int | None) -> str:
    return "infinita" if capacidad_cola is None else str(capacidad_cola)


def _modelo_cola(capacidad_cola: int | None) -> str:
    return "M/M/1" if capacidad_cola is None else "M/M/1/K"


def _estado_teorico(parametros: ParametrosMM1) -> str:
    if parametros.capacidad_cola is not None:
        return "capacidad_finita_regimen_estacionario"
    if parametros.tasa_arribo < parametros.tasa_servicio:
        return "capacidad_infinita_regimen_estacionario"
    return "capacidad_infinita_sin_regimen_estacionario"


def _semilla_replica(
    semilla_base: int,
    indice_capacidad: int,
    indice_factor: int,
    replica: int,
) -> int:
    return semilla_base + indice_capacidad * 10000 + indice_factor * 100 + replica
