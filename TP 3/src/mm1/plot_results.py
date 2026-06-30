"""Genera graficos SVG para los resumenes de experimentos M/M/1."""

from __future__ import annotations

import argparse
from pathlib import Path

from src.common.csv_utils import leer_filas_csv

COLORES = [
    "#1f77b4",
    "#d62728",
    "#2ca02c",
    "#9467bd",
    "#ff7f0e",
    "#17becf",
]

ETIQUETAS_METRICAS = {
    "promedio_clientes_sistema": "Clientes promedio en sistema",
    "promedio_clientes_cola": "Clientes promedio en cola",
    "tiempo_promedio_sistema": "Tiempo promedio en sistema",
    "tiempo_promedio_cola": "Tiempo promedio en cola",
    "utilizacion_servidor": "Utilizacion del servidor",
}

NOMBRES_ARCHIVO_METRICAS = {
    "promedio_clientes_sistema": "average_number_in_system",
    "promedio_clientes_cola": "average_number_in_queue",
    "tiempo_promedio_sistema": "average_time_in_system",
    "tiempo_promedio_cola": "average_time_in_queue",
    "utilizacion_servidor": "server_utilization",
}


def principal() -> None:
    parser = argparse.ArgumentParser(description="Grafica resultados de experimentos M/M/1.")
    parser.add_argument(
        "--input-dir",
        "--directorio-entrada",
        dest="directorio_entrada",
        default="results/mm1/experiments",
        help="Directorio que contiene mm1_summary.csv.",
    )
    parser.add_argument(
        "--output-dir",
        "--directorio-salida",
        dest="directorio_salida",
        default="figures/mm1",
        help="Directorio donde se escriben las figuras SVG.",
    )
    parser.add_argument(
        "--timeseries",
        "--serie-temporal",
        dest="serie_temporal",
        default="results/mm1/smoke_timeseries/mm1_single_timeseries.csv",
        help="CSV con una serie temporal representativa de M/M/1.",
    )
    parser.add_argument(
        "--report-output-dir",
        "--directorio-informe",
        dest="directorio_informe",
        default="report/figures/mm1",
        help="Directorio donde se escribe la copia PDF temporal para el informe.",
    )
    parser.add_argument(
        "--sin-pdf-informe",
        action="store_true",
        help="No genera copia PDF temporal para el informe.",
    )
    argumentos = parser.parse_args()

    directorio_entrada = Path(argumentos.directorio_entrada)
    directorio_salida = Path(argumentos.directorio_salida)
    directorio_salida.mkdir(parents=True, exist_ok=True)

    filas_resumen = leer_filas_csv(directorio_entrada / "mm1_summary.csv")
    _graficar_metricas_cola_infinita(filas_resumen, directorio_salida)
    _graficar_probabilidad_denegacion(filas_resumen, directorio_salida)
    ruta_temporal = Path(argumentos.serie_temporal)
    if ruta_temporal.exists():
        series_temporales = _series_temporales_clientes(leer_filas_csv(ruta_temporal))
        _graficar_evolucion_temporal(
            series_temporales,
            directorio_salida / "mm1_temporal_clientes_rho_075.svg",
        )
        if not argumentos.sin_pdf_informe:
            _intentar_exportar_pdf_temporal(
                series_temporales,
                Path(argumentos.directorio_informe) / "mm1_temporal_clientes_rho_075.pdf",
            )
    else:
        print(f"  aviso: no se encontro serie temporal {ruta_temporal}")

    print("Figuras M/M/1 generadas")
    print(f"  directorio de salida: {directorio_salida}")


def _graficar_metricas_cola_infinita(
    filas_resumen: list[dict[str, str]],
    directorio_salida: Path,
) -> None:
    filas = [
        fila
        for fila in filas_resumen
        if fila["capacidad_cola"] == "infinita"
        and fila["estado_teorico"] == "capacidad_infinita_regimen_estacionario"
    ]
    filas.sort(key=lambda fila: _a_float(fila["rho"]) or 0.0)

    for metrica, etiqueta in ETIQUETAS_METRICAS.items():
        puntos_simulacion = [
            (_a_float(fila["rho"]), _a_float(fila[f"{metrica}_media"]))
            for fila in filas
        ]
        puntos_teoria = [
            (_a_float(fila["rho"]), _a_float(fila[f"{metrica}_teoria"]))
            for fila in filas
        ]
        _escribir_grafico_lineas_xy(
            [
                {
                    "etiqueta": "Media simulada",
                    "puntos": _puntos_validos(puntos_simulacion),
                    "color": COLORES[0],
                    "guiones": "",
                },
                {
                    "etiqueta": "Teoria",
                    "puntos": _puntos_validos(puntos_teoria),
                    "color": COLORES[1],
                    "guiones": "6 4",
                },
            ],
            directorio_salida / f"mm1_infinite_{NOMBRES_ARCHIVO_METRICAS[metrica]}.svg",
            titulo=f"M/M/1 cola infinita - {etiqueta}",
            etiqueta_x="rho",
            etiqueta_y=etiqueta,
        )


def _graficar_probabilidad_denegacion(
    filas_resumen: list[dict[str, str]],
    directorio_salida: Path,
) -> None:
    filas = [
        fila
        for fila in filas_resumen
        if fila["capacidad_cola"] != "infinita"
    ]
    capacidades = sorted(
        {
            int(fila["capacidad_cola"])
            for fila in filas
        }
    )
    rhos = sorted({_a_float(fila["rho"]) for fila in filas})

    series = []
    for indice, rho in enumerate(rhos):
        puntos = []
        for capacidad in capacidades:
            coincidencia = next(
                fila
                for fila in filas
                if int(fila["capacidad_cola"]) == capacidad
                and _a_float(fila["rho"]) == rho
            )
            puntos.append(
                (
                    str(capacidad),
                    _a_float(coincidencia["probabilidad_denegacion_media"]),
                )
            )
        series.append(
            {
                "etiqueta": f"rho={rho:g}",
                "puntos": _puntos_categoria_validos(puntos),
                "color": COLORES[indice % len(COLORES)],
                "guiones": "",
            }
        )

    _escribir_grafico_lineas_categorias(
        series,
        directorio_salida / "mm1_denial_probability_by_capacity.svg",
        titulo="M/M/1/K - Probabilidad de denegacion por capacidad de cola",
        etiqueta_x="Capacidad de cola",
        etiqueta_y="Probabilidad de denegacion",
        categorias=[str(capacidad) for capacidad in capacidades],
    )


def _series_temporales_clientes(
    filas_temporales: list[dict[str, str]],
) -> list[dict]:
    return [
        {
            "etiqueta": "Clientes en sistema",
            "puntos": [
                (float(fila["tiempo"]), float(fila["clientes_sistema"]))
                for fila in filas_temporales
            ],
            "color": COLORES[0],
            "guiones": "",
        },
        {
            "etiqueta": "Clientes en cola",
            "puntos": [
                (float(fila["tiempo"]), float(fila["clientes_cola"]))
                for fila in filas_temporales
            ],
            "color": COLORES[1],
            "guiones": "6 4",
        },
    ]


def _graficar_evolucion_temporal(series: list[dict], ruta: Path) -> None:
    _escribir_grafico_lineas_temporales(
        series,
        ruta,
        titulo="M/M/1 - Evolucion temporal de clientes (rho=0.75)",
        etiqueta_x="Tiempo simulado (horas)",
        etiqueta_y="Clientes",
    )


def _escribir_grafico_lineas_xy(
    series: list[dict],
    ruta: Path,
    titulo: str,
    etiqueta_x: str,
    etiqueta_y: str,
) -> None:
    todos_los_puntos = [
        punto
        for serie in series
        for punto in serie["puntos"]
    ]
    if not todos_los_puntos:
        return

    valores_x = [punto[0] for punto in todos_los_puntos]
    valores_y = [punto[1] for punto in todos_los_puntos]
    x_min, x_max = min(valores_x), max(valores_x)
    y_min, y_max = 0.0, max(valores_y)
    if y_max == y_min:
        y_max = y_min + 1.0

    grafico = _Grafico(ruta, titulo, etiqueta_x, etiqueta_y)
    grafico.comenzar()
    grafico.dibujar_ejes([f"{valor:g}" for valor in valores_x], y_min, y_max)
    for serie in series:
        puntos = [
            (
                grafico.escalar_x(punto[0], x_min, x_max),
                grafico.escalar_y(punto[1], y_min, y_max),
            )
            for punto in serie["puntos"]
        ]
        grafico.dibujar_linea(puntos, serie["color"], serie["guiones"])
        grafico.dibujar_puntos(puntos, serie["color"])
    grafico.dibujar_leyenda(series)
    grafico.finalizar()


def _escribir_grafico_lineas_categorias(
    series: list[dict],
    ruta: Path,
    titulo: str,
    etiqueta_x: str,
    etiqueta_y: str,
    categorias: list[str],
) -> None:
    todos_los_puntos = [
        punto
        for serie in series
        for punto in serie["puntos"]
    ]
    if not todos_los_puntos:
        return

    valores_y = [punto[1] for punto in todos_los_puntos]
    y_min, y_max = 0.0, max(valores_y)
    if y_max == y_min:
        y_max = y_min + 1.0

    posiciones_categoria = {
        categoria: indice
        for indice, categoria in enumerate(categorias)
    }
    grafico = _Grafico(ruta, titulo, etiqueta_x, etiqueta_y)
    grafico.comenzar()
    grafico.dibujar_ejes(categorias, y_min, y_max)
    for serie in series:
        puntos = [
            (
                grafico.escalar_x(
                    posiciones_categoria[punto[0]],
                    0,
                    max(len(categorias) - 1, 1),
                ),
                grafico.escalar_y(punto[1], y_min, y_max),
            )
            for punto in serie["puntos"]
        ]
        grafico.dibujar_linea(puntos, serie["color"], serie["guiones"])
        grafico.dibujar_puntos(puntos, serie["color"])
    grafico.dibujar_leyenda(series)
    grafico.finalizar()


def _escribir_grafico_lineas_temporales(
    series: list[dict],
    ruta: Path,
    titulo: str,
    etiqueta_x: str,
    etiqueta_y: str,
) -> None:
    todos_los_puntos = [
        punto
        for serie in series
        for punto in serie["puntos"]
    ]
    if not todos_los_puntos:
        return

    valores_x = [punto[0] for punto in todos_los_puntos]
    valores_y = [punto[1] for punto in todos_los_puntos]
    x_min, x_max = min(valores_x), max(valores_x)
    y_min, y_max = 0.0, max(valores_y)
    if y_max == y_min:
        y_max = y_min + 1.0

    grafico = _Grafico(ruta, titulo, etiqueta_x, etiqueta_y)
    grafico.comenzar()
    grafico.dibujar_ejes(_etiquetas_temporales(x_min, x_max), y_min, y_max)
    for serie in series:
        puntos = [
            (
                grafico.escalar_x(punto[0], x_min, x_max),
                grafico.escalar_y(punto[1], y_min, y_max),
            )
            for punto in serie["puntos"]
        ]
        grafico.dibujar_linea(puntos, serie["color"], serie["guiones"])
    grafico.dibujar_leyenda(series)
    grafico.finalizar()


def _intentar_exportar_pdf_temporal(series: list[dict], ruta_pdf: Path) -> None:
    try:
        from reportlab.lib import colors
        from reportlab.pdfgen import canvas
    except ImportError:
        print("  aviso: reportlab no esta disponible; no se genero PDF temporal")
        return

    todos_los_puntos = [
        punto
        for serie in series
        for punto in serie["puntos"]
    ]
    if not todos_los_puntos:
        return

    ruta_pdf.parent.mkdir(parents=True, exist_ok=True)
    ancho = _Grafico.ancho
    alto = _Grafico.alto
    izquierda = _Grafico.izquierda
    derecha = ancho - _Grafico.derecha
    abajo = _Grafico.abajo
    arriba = alto - _Grafico.arriba
    ancho_trazado = derecha - izquierda
    alto_trazado = arriba - abajo
    x_min = min(punto[0] for punto in todos_los_puntos)
    x_max = max(punto[0] for punto in todos_los_puntos)
    y_min = 0.0
    y_max = max(punto[1] for punto in todos_los_puntos) or 1.0

    lienzo = canvas.Canvas(str(ruta_pdf), pagesize=(ancho, alto))
    lienzo.setFillColor(colors.white)
    lienzo.rect(0, 0, ancho, alto, stroke=0, fill=1)
    lienzo.setFillColor(colors.black)
    lienzo.setFont("Helvetica-Bold", 22)
    lienzo.drawCentredString(
        ancho / 2,
        alto - 32,
        "M/M/1 - Evolucion temporal de clientes (rho=0.75)",
    )

    lienzo.setStrokeColor(colors.HexColor("#e6e6e6"))
    lienzo.setLineWidth(1)
    for indice in range(6):
        fraccion = indice / 5
        y = abajo + fraccion * alto_trazado
        valor = y_min + fraccion * (y_max - y_min)
        lienzo.line(izquierda, y, derecha, y)
        lienzo.setFont("Helvetica", 12)
        lienzo.setFillColor(colors.black)
        lienzo.drawRightString(izquierda - 10, y - 4, f"{valor:.3g}")
        lienzo.setStrokeColor(colors.HexColor("#e6e6e6"))

    lienzo.setStrokeColor(colors.HexColor("#222222"))
    lienzo.setLineWidth(1.5)
    lienzo.line(izquierda, abajo, derecha, abajo)
    lienzo.line(izquierda, abajo, izquierda, arriba)

    for indice, etiqueta in enumerate(_etiquetas_temporales(x_min, x_max)):
        x = izquierda + indice / 4 * ancho_trazado
        lienzo.setFont("Helvetica", 12)
        lienzo.drawCentredString(x, abajo - 24, etiqueta)
    lienzo.setFont("Helvetica", 14)
    lienzo.drawCentredString(izquierda + ancho_trazado / 2, 24, "Tiempo simulado (horas)")

    lienzo.saveState()
    lienzo.translate(26, abajo + alto_trazado / 2)
    lienzo.rotate(90)
    lienzo.drawCentredString(0, 0, "Clientes")
    lienzo.restoreState()

    for indice, serie in enumerate(series):
        color = colors.HexColor(serie["color"])
        lienzo.setStrokeColor(color)
        lienzo.setLineWidth(2.5)
        if serie["guiones"]:
            lienzo.setDash([6, 4])
        else:
            lienzo.setDash()
        camino = lienzo.beginPath()
        for punto_indice, (x_valor, y_valor) in enumerate(serie["puntos"]):
            x = izquierda + (x_valor - x_min) / (x_max - x_min) * ancho_trazado
            y = abajo + (y_valor - y_min) / (y_max - y_min) * alto_trazado
            if punto_indice == 0:
                camino.moveTo(x, y)
            else:
                camino.lineTo(x, y)
        lienzo.drawPath(camino, stroke=1, fill=0)
        lienzo.setDash()

        y_leyenda = arriba - 8 - indice * 24
        x_leyenda = derecha + 32
        lienzo.setStrokeColor(color)
        lienzo.line(x_leyenda, y_leyenda, x_leyenda + 28, y_leyenda)
        lienzo.setFillColor(colors.black)
        lienzo.setFont("Helvetica", 13)
        lienzo.drawString(x_leyenda + 38, y_leyenda - 4, serie["etiqueta"])

    lienzo.showPage()
    lienzo.save()


class _Grafico:
    ancho = 960
    alto = 560
    izquierda = 86
    derecha = 230
    arriba = 70
    abajo = 80

    def __init__(self, ruta: Path, titulo: str, etiqueta_x: str, etiqueta_y: str):
        self.ruta = ruta
        self.titulo = titulo
        self.etiqueta_x = etiqueta_x
        self.etiqueta_y = etiqueta_y
        self._partes: list[str] = []

    @property
    def ancho_trazado(self) -> int:
        return self.ancho - self.izquierda - self.derecha

    @property
    def alto_trazado(self) -> int:
        return self.alto - self.arriba - self.abajo

    def comenzar(self) -> None:
        self._partes.append(
            f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'width="{self.ancho}" height="{self.alto}" '
            f'viewBox="0 0 {self.ancho} {self.alto}">'
        )
        self._partes.append('<rect width="100%" height="100%" fill="#ffffff"/>')
        self._partes.append(
            f'<text x="{self.ancho / 2}" y="32" text-anchor="middle" '
            f'font-family="Arial" font-size="22" font-weight="700">'
            f'{_escapar(self.titulo)}</text>'
        )

    def dibujar_ejes(
        self,
        etiquetas_x: list[str],
        y_min: float,
        y_max: float,
    ) -> None:
        izquierda = self.izquierda
        derecha = self.ancho - self.derecha
        arriba = self.arriba
        abajo = self.alto - self.abajo

        for indice in range(6):
            fraccion = indice / 5
            y = abajo - fraccion * self.alto_trazado
            valor = y_min + fraccion * (y_max - y_min)
            self._partes.append(
                f'<line x1="{izquierda}" y1="{y:.2f}" x2="{derecha}" y2="{y:.2f}" '
                f'stroke="#e6e6e6" stroke-width="1"/>'
            )
            self._partes.append(
                f'<text x="{izquierda - 10}" y="{y + 4:.2f}" text-anchor="end" '
                f'font-family="Arial" font-size="12">{valor:.3g}</text>'
            )

        self._partes.append(
            f'<line x1="{izquierda}" y1="{abajo}" x2="{derecha}" y2="{abajo}" '
            f'stroke="#222" stroke-width="1.5"/>'
        )
        self._partes.append(
            f'<line x1="{izquierda}" y1="{arriba}" x2="{izquierda}" y2="{abajo}" '
            f'stroke="#222" stroke-width="1.5"/>'
        )

        etiquetas = _unicos_preservando_orden(etiquetas_x)
        for indice, etiqueta in enumerate(etiquetas):
            denominador = max(len(etiquetas) - 1, 1)
            x = izquierda + indice / denominador * self.ancho_trazado
            self._partes.append(
                f'<text x="{x:.2f}" y="{abajo + 24}" text-anchor="middle" '
                f'font-family="Arial" font-size="12">{_escapar(etiqueta)}</text>'
            )

        self._partes.append(
            f'<text x="{izquierda + self.ancho_trazado / 2}" y="{self.alto - 24}" '
            f'text-anchor="middle" font-family="Arial" font-size="14">'
            f'{_escapar(self.etiqueta_x)}</text>'
        )
        self._partes.append(
            f'<text x="26" y="{arriba + self.alto_trazado / 2}" '
            f'text-anchor="middle" font-family="Arial" font-size="14" '
            f'transform="rotate(-90 26 {arriba + self.alto_trazado / 2})">'
            f'{_escapar(self.etiqueta_y)}</text>'
        )

    def escalar_x(self, valor: float, minimo: float, maximo: float) -> float:
        if maximo == minimo:
            return self.izquierda + self.ancho_trazado / 2
        return self.izquierda + (valor - minimo) / (maximo - minimo) * self.ancho_trazado

    def escalar_y(self, valor: float, minimo: float, maximo: float) -> float:
        return (
            self.alto
            - self.abajo
            - (valor - minimo) / (maximo - minimo) * self.alto_trazado
        )

    def dibujar_linea(
        self,
        puntos: list[tuple[float, float]],
        color: str,
        guiones: str,
    ) -> None:
        if len(puntos) < 2:
            return
        comandos = " ".join(f"{x:.2f},{y:.2f}" for x, y in puntos)
        atributo_guiones = f' stroke-dasharray="{guiones}"' if guiones else ""
        self._partes.append(
            f'<polyline points="{comandos}" fill="none" stroke="{color}" '
            f'stroke-width="2.5"{atributo_guiones}/>'
        )

    def dibujar_puntos(self, puntos: list[tuple[float, float]], color: str) -> None:
        for x, y in puntos:
            self._partes.append(
                f'<circle cx="{x:.2f}" cy="{y:.2f}" r="4" '
                f'fill="{color}" stroke="#fff" stroke-width="1"/>'
            )

    def dibujar_leyenda(self, series: list[dict]) -> None:
        x = self.ancho - self.derecha + 32
        y = self.arriba + 8
        for indice, serie in enumerate(series):
            y_pos = y + indice * 24
            atributo_guiones = (
                f' stroke-dasharray="{serie["guiones"]}"'
                if serie["guiones"]
                else ""
            )
            self._partes.append(
                f'<line x1="{x}" y1="{y_pos}" x2="{x + 28}" y2="{y_pos}" '
                f'stroke="{serie["color"]}" stroke-width="2.5"{atributo_guiones}/>'
            )
            self._partes.append(
                f'<text x="{x + 38}" y="{y_pos + 4}" font-family="Arial" '
                f'font-size="13">{_escapar(serie["etiqueta"])}</text>'
            )

    def finalizar(self) -> None:
        self._partes.append("</svg>")
        self.ruta.parent.mkdir(parents=True, exist_ok=True)
        self.ruta.write_bytes(("\n".join(self._partes) + "\n").encode("utf-8"))


def _a_float(valor: str) -> float | None:
    if valor is None or valor == "":
        return None
    return float(valor)


def _puntos_validos(
    puntos: list[tuple[float | None, float | None]],
) -> list[tuple[float, float]]:
    return [
        (x, y)
        for x, y in puntos
        if x is not None and y is not None
    ]


def _puntos_categoria_validos(
    puntos: list[tuple[str, float | None]],
) -> list[tuple[str, float]]:
    return [
        (x, y)
        for x, y in puntos
        if y is not None
    ]


def _unicos_preservando_orden(valores: list[str]) -> list[str]:
    vistos = set()
    salida = []
    for valor in valores:
        if valor not in vistos:
            vistos.add(valor)
            salida.append(valor)
    return salida


def _etiquetas_temporales(x_min: float, x_max: float) -> list[str]:
    return [
        f"{x_min + (x_max - x_min) * fraccion / 4:.0f}"
        for fraccion in range(5)
    ]


def _escapar(valor: str) -> str:
    return (
        valor.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


if __name__ == "__main__":
    principal()
