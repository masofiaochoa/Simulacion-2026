"""Medidas teoricas para colas M/M/1 y M/M/1/K con capacidad finita."""

from __future__ import annotations

from math import isclose


def _validar_tasas(tasa_arribo: float, tasa_servicio: float) -> None:
    if tasa_arribo <= 0:
        raise ValueError("tasa_arribo debe ser mayor que cero")
    if tasa_servicio <= 0:
        raise ValueError("tasa_servicio debe ser mayor que cero")


def teoria_mm1_infinita(
    tasa_arribo: float,
    tasa_servicio: float,
    max_longitud_cola: int = 10,
) -> dict[str, object]:
    """Devuelve metricas estacionarias para una cola M/M/1 infinita.

    Las metricas solo son finitas cuando rho < 1. Para rho >= 1, el
    diccionario marca que no hay regimen estacionario y deja esas metricas en
    None. Eso permite tratar los casos lambda = mu y lambda > mu pedidos por el
    TP sin compararlos contra teoria estacionaria.
    """

    _validar_tasas(tasa_arribo, tasa_servicio)
    rho = tasa_arribo / tasa_servicio
    estable = rho < 1.0

    resultado: dict[str, object] = {
        "modelo": "M/M/1",
        "tasa_arribo": tasa_arribo,
        "tasa_servicio": tasa_servicio,
        "rho": rho,
        "estable": estable,
        "capacidad_cola": None,
    }

    if not estable:
        resultado.update(
            {
                "promedio_clientes_sistema": None,
                "promedio_clientes_cola": None,
                "tiempo_promedio_sistema": None,
                "tiempo_promedio_cola": None,
                "utilizacion_servidor": None,
                "probabilidad_denegacion": 0.0,
                "probabilidades_longitud_cola": {},
            }
        )
        return resultado

    p0 = 1.0 - rho
    probabilidades_longitud_cola = {
        0: p0 + p0 * rho,
    }
    for longitud_cola in range(1, max_longitud_cola + 1):
        probabilidades_longitud_cola[longitud_cola] = p0 * rho ** (longitud_cola + 1)

    resultado.update(
        {
            "promedio_clientes_sistema": rho / (1.0 - rho),
            "promedio_clientes_cola": rho**2 / (1.0 - rho),
            "tiempo_promedio_sistema": 1.0 / (tasa_servicio - tasa_arribo),
            "tiempo_promedio_cola": tasa_arribo
            / (tasa_servicio * (tasa_servicio - tasa_arribo)),
            "utilizacion_servidor": rho,
            "probabilidad_denegacion": 0.0,
            "probabilidades_longitud_cola": probabilidades_longitud_cola,
        }
    )
    return resultado


def teoria_mm1k(
    tasa_arribo: float,
    tasa_servicio: float,
    capacidad_cola: int,
) -> dict[str, object]:
    """Devuelve metricas estacionarias para M/M/1/K con sala de espera finita."""

    _validar_tasas(tasa_arribo, tasa_servicio)
    if capacidad_cola < 0:
        raise ValueError("capacidad_cola debe ser cero o mayor")

    capacidad_total = capacidad_cola + 1
    rho = tasa_arribo / tasa_servicio

    if isclose(rho, 1.0):
        probabilidades_estado = [
            1.0 / (capacidad_total + 1) for _ in range(capacidad_total + 1)
        ]
    else:
        p0 = (1.0 - rho) / (1.0 - rho ** (capacidad_total + 1))
        probabilidades_estado = [
            p0 * rho**estado for estado in range(capacidad_total + 1)
        ]

    probabilidad_denegacion = probabilidades_estado[capacidad_total]
    tasa_arribo_efectiva = tasa_arribo * (1.0 - probabilidad_denegacion)
    promedio_clientes_sistema = sum(
        estado * probabilidad
        for estado, probabilidad in enumerate(probabilidades_estado)
    )
    promedio_clientes_cola = sum(
        max(estado - 1, 0) * probabilidad
        for estado, probabilidad in enumerate(probabilidades_estado)
    )

    if tasa_arribo_efectiva > 0.0:
        tiempo_promedio_sistema = promedio_clientes_sistema / tasa_arribo_efectiva
        tiempo_promedio_cola = promedio_clientes_cola / tasa_arribo_efectiva
    else:
        tiempo_promedio_sistema = None
        tiempo_promedio_cola = None

    probabilidades_longitud_cola = {
        0: probabilidades_estado[0] + probabilidades_estado[1],
    }
    for longitud_cola in range(1, capacidad_cola + 1):
        probabilidades_longitud_cola[longitud_cola] = probabilidades_estado[
            longitud_cola + 1
        ]

    return {
        "modelo": "M/M/1/K",
        "tasa_arribo": tasa_arribo,
        "tasa_servicio": tasa_servicio,
        "rho": rho,
        "estable": True,
        "capacidad_cola": capacidad_cola,
        "capacidad_total_sistema": capacidad_total,
        "probabilidades_estado": probabilidades_estado,
        "probabilidades_longitud_cola": probabilidades_longitud_cola,
        "probabilidad_denegacion": probabilidad_denegacion,
        "tasa_arribo_efectiva": tasa_arribo_efectiva,
        "promedio_clientes_sistema": promedio_clientes_sistema,
        "promedio_clientes_cola": promedio_clientes_cola,
        "tiempo_promedio_sistema": tiempo_promedio_sistema,
        "tiempo_promedio_cola": tiempo_promedio_cola,
        "utilizacion_servidor": 1.0 - probabilidades_estado[0],
    }
