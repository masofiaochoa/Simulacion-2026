"""Simulador de eventos discretos para colas M/M/1."""

from __future__ import annotations

import csv
import math
import random
from collections import defaultdict, deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


@dataclass(frozen=True)
class ParametrosMM1:
    tasa_arribo: float
    tasa_servicio: float
    tiempo_simulacion: float
    capacidad_cola: int | None = None
    semilla: int | None = None


@dataclass
class ResultadoMM1:
    parametros: ParametrosMM1
    clientes_generados: int
    clientes_aceptados: int
    clientes_rechazados: int
    clientes_atendidos: int
    promedio_clientes_sistema: float
    promedio_clientes_cola: float
    tiempo_promedio_sistema: float | None
    tiempo_promedio_cola: float | None
    utilizacion_servidor: float
    probabilidad_denegacion: float
    probabilidades_tiempo_longitud_cola: dict[int, float]
    serie_temporal: list[dict[str, Any]]

    def fila_metricas(self) -> dict[str, Any]:
        parametros = self.parametros
        return {
            "semilla": parametros.semilla,
            "tasa_arribo": parametros.tasa_arribo,
            "tasa_servicio": parametros.tasa_servicio,
            "rho": parametros.tasa_arribo / parametros.tasa_servicio,
            "tiempo_simulacion": parametros.tiempo_simulacion,
            "capacidad_cola": (
                "infinita" if parametros.capacidad_cola is None else parametros.capacidad_cola
            ),
            "clientes_generados": self.clientes_generados,
            "clientes_aceptados": self.clientes_aceptados,
            "clientes_rechazados": self.clientes_rechazados,
            "clientes_atendidos": self.clientes_atendidos,
            "promedio_clientes_sistema": self.promedio_clientes_sistema,
            "promedio_clientes_cola": self.promedio_clientes_cola,
            "tiempo_promedio_sistema": self.tiempo_promedio_sistema,
            "tiempo_promedio_cola": self.tiempo_promedio_cola,
            "utilizacion_servidor": self.utilizacion_servidor,
            "probabilidad_denegacion": self.probabilidad_denegacion,
        }


def simular_mm1(
    parametros: ParametrosMM1,
    registrar_serie_temporal: bool = True,
) -> ResultadoMM1:
    """Simula una cola M/M/1 durante un horizonte fijo."""

    _validar_parametros(parametros)

    generador = random.Random(parametros.semilla)
    cola: deque[float] = deque()
    reloj = 0.0
    proxima_llegada = generador.expovariate(parametros.tasa_arribo)
    proxima_salida = math.inf

    servidor_ocupado = False
    llegada_cliente_actual: float | None = None
    inicio_servicio_actual: float | None = None

    clientes_generados = 0
    clientes_aceptados = 0
    clientes_rechazados = 0
    clientes_atendidos = 0

    area_clientes_sistema = 0.0
    area_clientes_cola = 0.0
    tiempo_ocupado = 0.0
    tiempo_cola_por_longitud: dict[int, float] = defaultdict(float)

    tiempo_total_sistema = 0.0
    tiempo_total_cola = 0.0
    serie_temporal: list[dict[str, Any]] = []

    def registrar_estado(evento: str) -> None:
        if not registrar_serie_temporal:
            return
        longitud_cola = len(cola)
        serie_temporal.append(
            {
                "tiempo": reloj,
                "evento": evento,
                "clientes_sistema": longitud_cola + int(servidor_ocupado),
                "clientes_cola": longitud_cola,
                "servidor_ocupado": int(servidor_ocupado),
                "clientes_generados": clientes_generados,
                "clientes_rechazados": clientes_rechazados,
                "clientes_atendidos": clientes_atendidos,
            }
        )

    def acumular_hasta(instante: float) -> None:
        nonlocal area_clientes_sistema
        nonlocal area_clientes_cola
        nonlocal tiempo_ocupado
        nonlocal reloj

        transcurrido = instante - reloj
        if transcurrido < -1e-12:
            raise RuntimeError("el reloj de simulacion retrocedio")
        if transcurrido <= 0.0:
            reloj = instante
            return

        longitud_cola = len(cola)
        longitud_sistema = longitud_cola + int(servidor_ocupado)

        area_clientes_sistema += longitud_sistema * transcurrido
        area_clientes_cola += longitud_cola * transcurrido
        tiempo_ocupado += int(servidor_ocupado) * transcurrido
        tiempo_cola_por_longitud[longitud_cola] += transcurrido
        reloj = instante

    registrar_estado("inicio")

    while True:
        instante_evento = min(proxima_llegada, proxima_salida)
        if instante_evento > parametros.tiempo_simulacion:
            acumular_hasta(parametros.tiempo_simulacion)
            break

        acumular_hasta(instante_evento)

        if proxima_salida <= proxima_llegada:
            if llegada_cliente_actual is None or inicio_servicio_actual is None:
                raise RuntimeError("salida agendada sin cliente en servicio")

            clientes_atendidos += 1
            tiempo_total_sistema += reloj - llegada_cliente_actual
            tiempo_total_cola += inicio_servicio_actual - llegada_cliente_actual

            if cola:
                llegada_cliente_actual = cola.popleft()
                inicio_servicio_actual = reloj
                proxima_salida = reloj + generador.expovariate(parametros.tasa_servicio)
                servidor_ocupado = True
            else:
                llegada_cliente_actual = None
                inicio_servicio_actual = None
                proxima_salida = math.inf
                servidor_ocupado = False

            registrar_estado("salida")
            continue

        clientes_generados += 1
        proxima_llegada = reloj + generador.expovariate(parametros.tasa_arribo)

        if not servidor_ocupado:
            clientes_aceptados += 1
            servidor_ocupado = True
            llegada_cliente_actual = reloj
            inicio_servicio_actual = reloj
            proxima_salida = reloj + generador.expovariate(parametros.tasa_servicio)
            registrar_estado("llegada_inicio_servicio")
            continue

        if (
            parametros.capacidad_cola is None
            or len(cola) < parametros.capacidad_cola
        ):
            clientes_aceptados += 1
            cola.append(reloj)
            registrar_estado("llegada_a_cola")
            continue

        clientes_rechazados += 1
        registrar_estado("llegada_rechazada")

    tiempo_promedio_sistema = (
        tiempo_total_sistema / clientes_atendidos
        if clientes_atendidos > 0
        else None
    )
    tiempo_promedio_cola = (
        tiempo_total_cola / clientes_atendidos
        if clientes_atendidos > 0
        else None
    )

    return ResultadoMM1(
        parametros=parametros,
        clientes_generados=clientes_generados,
        clientes_aceptados=clientes_aceptados,
        clientes_rechazados=clientes_rechazados,
        clientes_atendidos=clientes_atendidos,
        promedio_clientes_sistema=area_clientes_sistema
        / parametros.tiempo_simulacion,
        promedio_clientes_cola=area_clientes_cola
        / parametros.tiempo_simulacion,
        tiempo_promedio_sistema=tiempo_promedio_sistema,
        tiempo_promedio_cola=tiempo_promedio_cola,
        utilizacion_servidor=tiempo_ocupado / parametros.tiempo_simulacion,
        probabilidad_denegacion=(
            clientes_rechazados / clientes_generados if clientes_generados > 0 else 0.0
        ),
        probabilidades_tiempo_longitud_cola={
            longitud_cola: duracion / parametros.tiempo_simulacion
            for longitud_cola, duracion in sorted(tiempo_cola_por_longitud.items())
        },
        serie_temporal=serie_temporal,
    )


def escribir_metricas_csv(
    resultados: Iterable[ResultadoMM1],
    ruta: str | Path,
) -> None:
    filas = [resultado.fila_metricas() for resultado in resultados]
    if not filas:
        return

    ruta_salida = Path(ruta)
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    with ruta_salida.open("w", newline="", encoding="utf-8") as archivo_csv:
        escritor = csv.DictWriter(
            archivo_csv,
            fieldnames=list(filas[0].keys()),
            lineterminator="\n",
        )
        escritor.writeheader()
        escritor.writerows(filas)


def escribir_probabilidades_cola_csv(
    resultados: Iterable[ResultadoMM1],
    ruta: str | Path,
) -> None:
    filas: list[dict[str, Any]] = []
    for resultado in resultados:
        parametros = resultado.parametros
        for longitud_cola, probabilidad in resultado.probabilidades_tiempo_longitud_cola.items():
            filas.append(
                {
                    "semilla": parametros.semilla,
                    "tasa_arribo": parametros.tasa_arribo,
                    "tasa_servicio": parametros.tasa_servicio,
                    "capacidad_cola": (
                        "infinita"
                        if parametros.capacidad_cola is None
                        else parametros.capacidad_cola
                    ),
                    "longitud_cola": longitud_cola,
                    "probabilidad": probabilidad,
                }
            )

    if not filas:
        return

    ruta_salida = Path(ruta)
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    with ruta_salida.open("w", newline="", encoding="utf-8") as archivo_csv:
        escritor = csv.DictWriter(
            archivo_csv,
            fieldnames=list(filas[0].keys()),
            lineterminator="\n",
        )
        escritor.writeheader()
        escritor.writerows(filas)


def escribir_serie_temporal_csv(resultado: ResultadoMM1, ruta: str | Path) -> None:
    if not resultado.serie_temporal:
        return

    ruta_salida = Path(ruta)
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    with ruta_salida.open("w", newline="", encoding="utf-8") as archivo_csv:
        escritor = csv.DictWriter(
            archivo_csv,
            fieldnames=list(resultado.serie_temporal[0].keys()),
            lineterminator="\n",
        )
        escritor.writeheader()
        escritor.writerows(resultado.serie_temporal)


def _validar_parametros(parametros: ParametrosMM1) -> None:
    if parametros.tasa_arribo <= 0:
        raise ValueError("tasa_arribo debe ser mayor que cero")
    if parametros.tasa_servicio <= 0:
        raise ValueError("tasa_servicio debe ser mayor que cero")
    if parametros.tiempo_simulacion <= 0:
        raise ValueError("tiempo_simulacion debe ser mayor que cero")
    if parametros.capacidad_cola is not None and parametros.capacidad_cola < 0:
        raise ValueError("capacidad_cola debe ser cero o mayor")
