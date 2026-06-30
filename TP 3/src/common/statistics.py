"""Ayudantes estadisticos para replicas independientes de simulacion."""

from __future__ import annotations

import math


def media(valores: list[float]) -> float | None:
    valores_limpios = _limpiar(valores)
    if not valores_limpios:
        return None
    return sum(valores_limpios) / len(valores_limpios)


def desvio_estandar_muestral(valores: list[float]) -> float | None:
    valores_limpios = _limpiar(valores)
    n = len(valores_limpios)
    if n < 2:
        return None

    promedio = sum(valores_limpios) / n
    varianza = sum((valor - promedio) ** 2 for valor in valores_limpios) / (n - 1)
    return math.sqrt(varianza)


def semiancho_intervalo_confianza(
    valores: list[float],
    confianza: float = 0.95,
) -> float | None:
    if confianza != 0.95:
        raise ValueError("solo se soportan intervalos de confianza del 95 por ciento")

    valores_limpios = _limpiar(valores)
    n = len(valores_limpios)
    if n < 2:
        return None

    desvio = desvio_estandar_muestral(valores_limpios)
    if desvio is None:
        return None

    return t_critico_975(n - 1) * desvio / math.sqrt(n)


def t_critico_975(grados_libertad: int) -> float:
    """Devuelve el valor critico t bilateral para 95 por ciento."""

    tabla = {
        1: 12.706,
        2: 4.303,
        3: 3.182,
        4: 2.776,
        5: 2.571,
        6: 2.447,
        7: 2.365,
        8: 2.306,
        9: 2.262,
        10: 2.228,
        11: 2.201,
        12: 2.179,
        13: 2.160,
        14: 2.145,
        15: 2.131,
        16: 2.120,
        17: 2.110,
        18: 2.101,
        19: 2.093,
        20: 2.086,
        21: 2.080,
        22: 2.074,
        23: 2.069,
        24: 2.064,
        25: 2.060,
        26: 2.056,
        27: 2.052,
        28: 2.048,
        29: 2.045,
        30: 2.042,
    }
    return tabla.get(grados_libertad, 1.96)


def error_porcentual(observado: float | None, esperado: float | None) -> float | None:
    if observado is None or esperado is None:
        return None
    if abs(esperado) < 1e-12:
        return 0.0 if abs(observado) < 1e-12 else None
    return 100.0 * (observado - esperado) / esperado


def _limpiar(valores: list[float]) -> list[float]:
    return [
        valor
        for valor in valores
        if valor is not None and not math.isnan(valor)
    ]
