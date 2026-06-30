"""Simulador diario de inventario con politica de revision continua (Q, r)."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PoliticaInventario:
    nombre: str
    Q: int
    r: int


@dataclass(frozen=True)
class ParametrosInventario:
    horizonte_dias: int
    demanda_media_diaria: float
    inventario_inicial: int
    tiempo_entrega_dias: int
    costo_fijo_orden: float
    costo_mantenimiento_unidad_dia: float
    costo_faltante_unidad: float
    politica: PoliticaInventario
    semilla: int | None = None


@dataclass(frozen=True)
class PedidoPendiente:
    dia_llegada: int
    cantidad: int


@dataclass
class ResultadoInventario:
    parametros: ParametrosInventario
    demanda_total: int
    demanda_satisfecha: int
    unidades_faltantes: int
    ordenes_emitidas: int
    inventario_promedio: float
    costo_orden: float
    costo_mantenimiento: float
    costo_faltante: float
    costo_total: float
    nivel_servicio: float
    serie_temporal: list[dict[str, Any]]

    def fila_metricas(self) -> dict[str, Any]:
        parametros = self.parametros
        politica = parametros.politica
        return {
            "politica": politica.nombre,
            "semilla": parametros.semilla,
            "horizonte_dias": parametros.horizonte_dias,
            "Q": politica.Q,
            "r": politica.r,
            "demanda_media_diaria": parametros.demanda_media_diaria,
            "inventario_inicial": parametros.inventario_inicial,
            "tiempo_entrega_dias": parametros.tiempo_entrega_dias,
            "costo_fijo_orden": parametros.costo_fijo_orden,
            "costo_mantenimiento_unidad_dia": (
                parametros.costo_mantenimiento_unidad_dia
            ),
            "costo_faltante_unidad": parametros.costo_faltante_unidad,
            "demanda_total": self.demanda_total,
            "demanda_satisfecha": self.demanda_satisfecha,
            "unidades_faltantes": self.unidades_faltantes,
            "ordenes_emitidas": self.ordenes_emitidas,
            "inventario_promedio": self.inventario_promedio,
            "costo_orden": self.costo_orden,
            "costo_mantenimiento": self.costo_mantenimiento,
            "costo_faltante": self.costo_faltante,
            "costo_total": self.costo_total,
            "nivel_servicio": self.nivel_servicio,
        }


def simular_inventario(parametros: ParametrosInventario) -> ResultadoInventario:
    """Simula un sistema de inventario por dias con ventas perdidas."""

    _validar_parametros(parametros)

    generador = random.Random(parametros.semilla)
    inventario_disponible = parametros.inventario_inicial
    pedidos_pendientes: list[PedidoPendiente] = []

    demanda_total = 0
    demanda_satisfecha = 0
    unidades_faltantes = 0
    ordenes_emitidas = 0

    inventario_acumulado = 0.0
    costo_orden = 0.0
    costo_mantenimiento = 0.0
    costo_faltante = 0.0
    serie_temporal: list[dict[str, Any]] = []

    for dia in range(1, parametros.horizonte_dias + 1):
        cantidad_recibida = sum(
            pedido.cantidad
            for pedido in pedidos_pendientes
            if pedido.dia_llegada <= dia
        )
        pedidos_pendientes = [
            pedido
            for pedido in pedidos_pendientes
            if pedido.dia_llegada > dia
        ]
        inventario_disponible += cantidad_recibida

        demanda_diaria = _generar_poisson(
            generador,
            parametros.demanda_media_diaria,
        )
        satisfecha_dia = min(inventario_disponible, demanda_diaria)
        faltantes_dia = demanda_diaria - satisfecha_dia
        inventario_disponible -= satisfecha_dia

        demanda_total += demanda_diaria
        demanda_satisfecha += satisfecha_dia
        unidades_faltantes += faltantes_dia

        costo_mantenimiento_dia = (
            inventario_disponible * parametros.costo_mantenimiento_unidad_dia
        )
        costo_faltante_dia = faltantes_dia * parametros.costo_faltante_unidad
        costo_orden_dia = 0.0
        orden_emitida = 0
        cantidad_ordenada = 0

        costo_mantenimiento += costo_mantenimiento_dia
        costo_faltante += costo_faltante_dia
        inventario_acumulado += inventario_disponible

        unidades_en_pedido = sum(pedido.cantidad for pedido in pedidos_pendientes)
        posicion_antes_orden = inventario_disponible + unidades_en_pedido

        if posicion_antes_orden <= parametros.politica.r:
            orden_emitida = 1
            cantidad_ordenada = parametros.politica.Q
            ordenes_emitidas += 1
            costo_orden_dia = parametros.costo_fijo_orden
            costo_orden += costo_orden_dia
            pedidos_pendientes.append(
                PedidoPendiente(
                    dia_llegada=dia + parametros.tiempo_entrega_dias,
                    cantidad=parametros.politica.Q,
                )
            )

        unidades_en_pedido = sum(pedido.cantidad for pedido in pedidos_pendientes)
        costo_total_acumulado = costo_orden + costo_mantenimiento + costo_faltante
        serie_temporal.append(
            {
                "dia": dia,
                "inventario_disponible": inventario_disponible,
                "posicion_inventario": inventario_disponible + unidades_en_pedido,
                "unidades_en_pedido": unidades_en_pedido,
                "pedidos_recibidos": cantidad_recibida,
                "demanda_diaria": demanda_diaria,
                "demanda_satisfecha": satisfecha_dia,
                "unidades_faltantes": faltantes_dia,
                "orden_emitida": orden_emitida,
                "cantidad_ordenada": cantidad_ordenada,
                "costo_orden_dia": costo_orden_dia,
                "costo_mantenimiento_dia": costo_mantenimiento_dia,
                "costo_faltante_dia": costo_faltante_dia,
                "costo_total_dia": (
                    costo_orden_dia + costo_mantenimiento_dia + costo_faltante_dia
                ),
                "costo_orden_acumulado": costo_orden,
                "costo_mantenimiento_acumulado": costo_mantenimiento,
                "costo_faltante_acumulado": costo_faltante,
                "costo_total_acumulado": costo_total_acumulado,
            }
        )

    nivel_servicio = (
        demanda_satisfecha / demanda_total
        if demanda_total > 0
        else 1.0
    )
    return ResultadoInventario(
        parametros=parametros,
        demanda_total=demanda_total,
        demanda_satisfecha=demanda_satisfecha,
        unidades_faltantes=unidades_faltantes,
        ordenes_emitidas=ordenes_emitidas,
        inventario_promedio=inventario_acumulado / parametros.horizonte_dias,
        costo_orden=costo_orden,
        costo_mantenimiento=costo_mantenimiento,
        costo_faltante=costo_faltante,
        costo_total=costo_orden + costo_mantenimiento + costo_faltante,
        nivel_servicio=nivel_servicio,
        serie_temporal=serie_temporal,
    )


def _generar_poisson(generador: random.Random, media: float) -> int:
    """Genera una variable Poisson con el algoritmo de Knuth."""

    limite = math.exp(-media)
    producto = 1.0
    k = 0
    while producto > limite:
        k += 1
        producto *= generador.random()
    return k - 1


def _validar_parametros(parametros: ParametrosInventario) -> None:
    if parametros.horizonte_dias <= 0:
        raise ValueError("horizonte_dias debe ser mayor que cero")
    if parametros.demanda_media_diaria <= 0:
        raise ValueError("demanda_media_diaria debe ser mayor que cero")
    if parametros.inventario_inicial < 0:
        raise ValueError("inventario_inicial debe ser cero o mayor")
    if parametros.tiempo_entrega_dias < 0:
        raise ValueError("tiempo_entrega_dias debe ser cero o mayor")
    if parametros.costo_fijo_orden < 0:
        raise ValueError("costo_fijo_orden debe ser cero o mayor")
    if parametros.costo_mantenimiento_unidad_dia < 0:
        raise ValueError("costo_mantenimiento_unidad_dia debe ser cero o mayor")
    if parametros.costo_faltante_unidad < 0:
        raise ValueError("costo_faltante_unidad debe ser cero o mayor")
    if parametros.politica.Q <= 0:
        raise ValueError("Q debe ser mayor que cero")
    if parametros.politica.r < 0:
        raise ValueError("r debe ser cero o mayor")

