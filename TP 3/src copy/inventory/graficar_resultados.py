"""Genera graficos SVG para los resultados de inventario."""

from __future__ import annotations

import argparse
import re
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path
from typing import Any

from src.common.csv_utils import leer_filas_csv


COLORES = [
    "#1f77b4",
    "#d62728",
    "#2ca02c",
    "#9467bd",
    "#ff7f0e",
    "#17becf",
]


def principal() -> None:
    parser = argparse.ArgumentParser(
        description="Grafica resultados de experimentos de inventario."
    )
    parser.add_argument(
        "--input-dir",
        "--directorio-entrada",
        dest="directorio_entrada",
        default="results/inventory/experiments",
        help="Directorio que contiene los CSV de inventario.",
    )
    parser.add_argument(
        "--output-dir",
        "--directorio-salida",
        dest="directorio_salida",
        default="figures/inventory",
        help="Directorio donde se escriben las figuras SVG.",
    )
    parser.add_argument(
        "--report-output-dir",
        "--directorio-informe",
        dest="directorio_informe",
        default="report/figures/inventory",
        help="Directorio donde se escriben copias PDF para el informe.",
    )
    parser.add_argument(
        "--sin-pdf-informe",
        action="store_true",
        help="No genera copias PDF de las figuras para el informe.",
    )
    argumentos = parser.parse_args()

    directorio_entrada = Path(argumentos.directorio_entrada)
    directorio_salida = Path(argumentos.directorio_salida)
    directorio_salida.mkdir(parents=True, exist_ok=True)

    filas_series = leer_filas_csv(directorio_entrada / "inventario_series.csv")
    filas_resumen = leer_filas_csv(directorio_entrada / "inventario_resumen.csv")

    rutas_svg = [
        _graficar_promedio_diario(
            filas_series,
            "inventario_disponible",
            directorio_salida / "inventario_disponible.svg",
            "Inventario disponible promedio por politica",
            "Dia",
            "Unidades",
        ),
        _graficar_promedio_diario(
            filas_series,
            "demanda_diaria",
            directorio_salida / "demanda_diaria.svg",
            "Demanda diaria promedio por politica",
            "Dia",
            "Unidades por dia",
        ),
        _graficar_promedio_diario(
            filas_series,
            "costo_total_acumulado",
            directorio_salida / "costos_acumulados.svg",
            "Costo total acumulado promedio por politica",
            "Dia",
            "Costo acumulado",
        ),
        _graficar_barras_resumen(
            filas_resumen,
            "costo_total",
            directorio_salida / "costo_total_por_politica.svg",
            "Costo total promedio por politica",
            "Politica",
            "Costo total",
        ),
        _graficar_barras_resumen(
            filas_resumen,
            "nivel_servicio",
            directorio_salida / "nivel_servicio_por_politica.svg",
            "Nivel de servicio promedio por politica",
            "Politica",
            "Nivel de servicio",
            y_maximo=1.0,
        ),
    ]

    if not argumentos.sin_pdf_informe:
        _intentar_exportar_pdf_para_informe(
            rutas_svg,
            Path(argumentos.directorio_informe),
        )

    print("Figuras de inventario generadas")
    print(f"  directorio SVG: {directorio_salida}")
    if not argumentos.sin_pdf_informe:
        print(f"  directorio PDF para informe: {argumentos.directorio_informe}")


def _graficar_promedio_diario(
    filas_series: list[dict[str, str]],
    columna: str,
    ruta: Path,
    titulo: str,
    etiqueta_x: str,
    etiqueta_y: str,
) -> Path:
    series = _series_promedio_diario(filas_series, columna)
    _escribir_grafico_lineas_xy(series, ruta, titulo, etiqueta_x, etiqueta_y)
    return ruta


def _graficar_barras_resumen(
    filas_resumen: list[dict[str, str]],
    metrica: str,
    ruta: Path,
    titulo: str,
    etiqueta_x: str,
    etiqueta_y: str,
    y_maximo: float | None = None,
) -> Path:
    valores = []
    for indice, fila in enumerate(filas_resumen):
        valores.append(
            {
                "etiqueta": fila["politica"],
                "valor": _a_float(fila[f"{metrica}_media"]) or 0.0,
                "error": _a_float(fila[f"{metrica}_semiancho_ic95"]) or 0.0,
                "color": COLORES[indice % len(COLORES)],
            }
        )
    _escribir_grafico_barras(
        valores,
        ruta,
        titulo,
        etiqueta_x,
        etiqueta_y,
        y_maximo,
    )
    return ruta


def _series_promedio_diario(
    filas_series: list[dict[str, str]],
    columna: str,
) -> list[dict[str, Any]]:
    acumulados: dict[tuple[str, int], float] = defaultdict(float)
    conteos: dict[tuple[str, int], int] = defaultdict(int)
    politicas = _politicas_en_orden(filas_series)

    for fila in filas_series:
        politica = fila["politica"]
        dia = int(fila["dia"])
        acumulados[(politica, dia)] += float(fila[columna])
        conteos[(politica, dia)] += 1

    series = []
    for indice, politica in enumerate(politicas):
        dias = sorted(
            dia
            for politica_clave, dia in acumulados
            if politica_clave == politica
        )
        puntos = [
            (dia, acumulados[(politica, dia)] / conteos[(politica, dia)])
            for dia in dias
        ]
        series.append(
            {
                "etiqueta": politica,
                "puntos": puntos,
                "color": COLORES[indice % len(COLORES)],
                "guiones": "",
            }
        )
    return series


def _escribir_grafico_lineas_xy(
    series: list[dict[str, Any]],
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
    y_max = y_max * 1.08 if y_max > 0 else 1.0

    grafico = _Grafico(ruta, titulo, etiqueta_x, etiqueta_y)
    grafico.comenzar()
    grafico.dibujar_ejes(_etiquetas_eje_x(x_min, x_max), y_min, y_max)
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


def _escribir_grafico_barras(
    valores: list[dict[str, Any]],
    ruta: Path,
    titulo: str,
    etiqueta_x: str,
    etiqueta_y: str,
    y_maximo: float | None,
) -> None:
    if not valores:
        return

    categorias = [valor["etiqueta"] for valor in valores]
    y_min = 0.0
    y_max = max(valor["valor"] + valor["error"] for valor in valores)
    if y_maximo is not None:
        y_max = y_maximo
    else:
        y_max = y_max * 1.15 if y_max > 0 else 1.0

    grafico = _Grafico(ruta, titulo, etiqueta_x, etiqueta_y)
    grafico.comenzar()
    grafico.dibujar_ejes(categorias, y_min, y_max)

    ancho_barra = min(88.0, grafico.ancho_trazado / max(len(valores) * 2.2, 1))
    for indice, valor in enumerate(valores):
        x = grafico.escalar_x(indice, 0, max(len(valores) - 1, 1))
        y = grafico.escalar_y(valor["valor"], y_min, y_max)
        base = grafico.alto - grafico.abajo
        alto = base - y
        grafico.dibujar_barra(x - ancho_barra / 2, y, ancho_barra, alto, valor["color"])
        if valor["error"] > 0:
            y_bajo = grafico.escalar_y(max(valor["valor"] - valor["error"], y_min), y_min, y_max)
            y_alto = grafico.escalar_y(min(valor["valor"] + valor["error"], y_max), y_min, y_max)
            grafico.dibujar_error(x, y_bajo, y_alto)

    grafico.finalizar()


class _Grafico:
    ancho = 960
    alto = 560
    izquierda = 86
    derecha = 220
    arriba = 70
    abajo = 88

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

    def dibujar_ejes(self, etiquetas_x: list[str], y_min: float, y_max: float) -> None:
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

        for indice, etiqueta in enumerate(etiquetas_x):
            denominador = max(len(etiquetas_x) - 1, 1)
            x = izquierda + indice / denominador * self.ancho_trazado
            self._partes.append(
                f'<text x="{x:.2f}" y="{abajo + 25}" text-anchor="middle" '
                f'font-family="Arial" font-size="12">{_escapar(etiqueta)}</text>'
            )

        self._partes.append(
            f'<text x="{izquierda + self.ancho_trazado / 2}" y="{self.alto - 25}" '
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

    def dibujar_barra(
        self,
        x: float,
        y: float,
        ancho: float,
        alto: float,
        color: str,
    ) -> None:
        self._partes.append(
            f'<rect x="{x:.2f}" y="{y:.2f}" width="{ancho:.2f}" height="{alto:.2f}" '
            f'fill="{color}" opacity="0.88"/>'
        )

    def dibujar_error(self, x: float, y_bajo: float, y_alto: float) -> None:
        self._partes.append(
            f'<line x1="{x:.2f}" y1="{y_bajo:.2f}" x2="{x:.2f}" y2="{y_alto:.2f}" '
            f'stroke="#222" stroke-width="1.6"/>'
        )
        self._partes.append(
            f'<line x1="{x - 8:.2f}" y1="{y_alto:.2f}" x2="{x + 8:.2f}" '
            f'y2="{y_alto:.2f}" stroke="#222" stroke-width="1.6"/>'
        )
        self._partes.append(
            f'<line x1="{x - 8:.2f}" y1="{y_bajo:.2f}" x2="{x + 8:.2f}" '
            f'y2="{y_bajo:.2f}" stroke="#222" stroke-width="1.6"/>'
        )

    def dibujar_leyenda(self, series: list[dict[str, Any]]) -> None:
        x = self.ancho - self.derecha + 30
        y = self.arriba + 8
        for indice, serie in enumerate(series):
            y_pos = y + indice * 24
            self._partes.append(
                f'<line x1="{x}" y1="{y_pos}" x2="{x + 28}" y2="{y_pos}" '
                f'stroke="{serie["color"]}" stroke-width="2.5"/>'
            )
            self._partes.append(
                f'<text x="{x + 38}" y="{y_pos + 4}" font-family="Arial" '
                f'font-size="13">{_escapar(serie["etiqueta"])}</text>'
            )

    def finalizar(self) -> None:
        self._partes.append("</svg>")
        self.ruta.parent.mkdir(parents=True, exist_ok=True)
        self.ruta.write_bytes(("\n".join(self._partes) + "\n").encode("utf-8"))


def _intentar_exportar_pdf_para_informe(
    rutas_svg: list[Path],
    directorio_informe: Path,
) -> None:
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib import colors
    except ImportError:
        print("  aviso: reportlab no esta disponible; no se generaron PDF")
        return

    directorio_informe.mkdir(parents=True, exist_ok=True)
    for ruta_svg in rutas_svg:
        ruta_pdf = directorio_informe / f"{ruta_svg.stem}.pdf"
        try:
            _convertir_svg_basico_a_pdf(ruta_svg, ruta_pdf, canvas, colors)
        except Exception as error:  # pragma: no cover - conversion auxiliar
            print(f"  aviso: no se pudo convertir {ruta_svg.name}: {error}")


def _convertir_svg_basico_a_pdf(
    ruta_svg: Path,
    ruta_pdf: Path,
    canvas_modulo: Any,
    colores_modulo: Any,
) -> None:
    arbol = ET.parse(ruta_svg)
    raiz = arbol.getroot()
    ancho = _numero(raiz.attrib.get("width"), 960.0)
    alto = _numero(raiz.attrib.get("height"), 560.0)

    lienzo = canvas_modulo.Canvas(str(ruta_pdf), pagesize=(ancho, alto))
    for elemento in raiz:
        etiqueta = _etiqueta_local(elemento.tag)
        if etiqueta == "rect":
            _pdf_rect(lienzo, colores_modulo, elemento, alto, ancho)
        elif etiqueta == "line":
            _pdf_linea(lienzo, colores_modulo, elemento, alto)
        elif etiqueta == "polyline":
            _pdf_polilinea(lienzo, colores_modulo, elemento, alto)
        elif etiqueta == "circle":
            _pdf_circulo(lienzo, colores_modulo, elemento, alto)
        elif etiqueta == "text":
            _pdf_texto(lienzo, colores_modulo, elemento, alto)
    lienzo.showPage()
    lienzo.save()


def _pdf_rect(lienzo: Any, colores_modulo: Any, elemento: ET.Element, alto_svg: float, ancho_svg: float) -> None:
    x = _numero(elemento.attrib.get("x"), 0.0)
    y = _numero(elemento.attrib.get("y"), 0.0)
    ancho = ancho_svg if elemento.attrib.get("width") == "100%" else _numero(elemento.attrib.get("width"), 0.0)
    alto = alto_svg if elemento.attrib.get("height") == "100%" else _numero(elemento.attrib.get("height"), 0.0)
    fill = elemento.attrib.get("fill", "#ffffff")
    lienzo.setFillColor(_color(colores_modulo, fill))
    lienzo.rect(x, alto_svg - y - alto, ancho, alto, stroke=0, fill=1)


def _pdf_linea(lienzo: Any, colores_modulo: Any, elemento: ET.Element, alto_svg: float) -> None:
    lienzo.setStrokeColor(_color(colores_modulo, elemento.attrib.get("stroke", "#000000")))
    lienzo.setLineWidth(_numero(elemento.attrib.get("stroke-width"), 1.0))
    _aplicar_guiones(lienzo, elemento.attrib.get("stroke-dasharray"))
    x1 = _numero(elemento.attrib.get("x1"), 0.0)
    x2 = _numero(elemento.attrib.get("x2"), 0.0)
    y1 = alto_svg - _numero(elemento.attrib.get("y1"), 0.0)
    y2 = alto_svg - _numero(elemento.attrib.get("y2"), 0.0)
    lienzo.line(x1, y1, x2, y2)
    lienzo.setDash()


def _pdf_polilinea(lienzo: Any, colores_modulo: Any, elemento: ET.Element, alto_svg: float) -> None:
    puntos = _puntos_svg(elemento.attrib.get("points", ""), alto_svg)
    if not puntos:
        return
    lienzo.setStrokeColor(_color(colores_modulo, elemento.attrib.get("stroke", "#000000")))
    lienzo.setLineWidth(_numero(elemento.attrib.get("stroke-width"), 1.0))
    _aplicar_guiones(lienzo, elemento.attrib.get("stroke-dasharray"))
    camino = lienzo.beginPath()
    camino.moveTo(*puntos[0])
    for punto in puntos[1:]:
        camino.lineTo(*punto)
    lienzo.drawPath(camino, stroke=1, fill=0)
    lienzo.setDash()


def _pdf_circulo(lienzo: Any, colores_modulo: Any, elemento: ET.Element, alto_svg: float) -> None:
    cx = _numero(elemento.attrib.get("cx"), 0.0)
    cy = alto_svg - _numero(elemento.attrib.get("cy"), 0.0)
    radio = _numero(elemento.attrib.get("r"), 0.0)
    lienzo.setFillColor(_color(colores_modulo, elemento.attrib.get("fill", "#000000")))
    lienzo.circle(cx, cy, radio, stroke=0, fill=1)


def _pdf_texto(lienzo: Any, colores_modulo: Any, elemento: ET.Element, alto_svg: float) -> None:
    texto = "".join(elemento.itertext())
    if not texto:
        return
    tamanio = _numero(elemento.attrib.get("font-size"), 12.0)
    fuente = "Helvetica-Bold" if elemento.attrib.get("font-weight") == "700" else "Helvetica"
    lienzo.setFont(fuente, tamanio)
    lienzo.setFillColor(_color(colores_modulo, elemento.attrib.get("fill", "#000000")))
    x = _numero(elemento.attrib.get("x"), 0.0)
    y_svg = _numero(elemento.attrib.get("y"), 0.0)
    y = alto_svg - y_svg
    ancla = elemento.attrib.get("text-anchor", "start")
    transformacion = elemento.attrib.get("transform", "")
    rotacion = re.search(r"rotate\((-?\d+(?:\.\d+)?) ([\d.]+) ([\d.]+)\)", transformacion)

    if rotacion:
        angulo = float(rotacion.group(1))
        cx = float(rotacion.group(2))
        cy_svg = float(rotacion.group(3))
        lienzo.saveState()
        lienzo.translate(cx, alto_svg - cy_svg)
        lienzo.rotate(-angulo)
        _dibujar_texto_anclado(lienzo, texto, x - cx, -(y_svg - cy_svg), ancla)
        lienzo.restoreState()
        return

    _dibujar_texto_anclado(lienzo, texto, x, y, ancla)


def _dibujar_texto_anclado(
    lienzo: Any,
    texto: str,
    x: float,
    y: float,
    ancla: str,
) -> None:
    if ancla == "middle":
        lienzo.drawCentredString(x, y, texto)
    elif ancla == "end":
        lienzo.drawRightString(x, y, texto)
    else:
        lienzo.drawString(x, y, texto)


def _aplicar_guiones(lienzo: Any, guiones: str | None) -> None:
    if not guiones:
        lienzo.setDash()
        return
    lienzo.setDash([float(valor) for valor in guiones.split()])


def _puntos_svg(cadena: str, alto_svg: float) -> list[tuple[float, float]]:
    puntos = []
    for par in cadena.split():
        x_texto, y_texto = par.split(",")
        puntos.append((float(x_texto), alto_svg - float(y_texto)))
    return puntos


def _politicas_en_orden(filas: list[dict[str, str]]) -> list[str]:
    politicas = []
    vistas = set()
    for fila in filas:
        politica = fila["politica"]
        if politica not in vistas:
            vistas.add(politica)
            politicas.append(politica)
    return politicas


def _etiquetas_eje_x(x_min: int, x_max: int) -> list[str]:
    return [
        str(round(x_min + (x_max - x_min) * fraccion / 4))
        for fraccion in range(5)
    ]


def _a_float(valor: str | None) -> float | None:
    if valor is None or valor == "":
        return None
    return float(valor)


def _numero(valor: str | None, defecto: float) -> float:
    if valor is None:
        return defecto
    return float(valor.replace("px", ""))


def _color(colores_modulo: Any, valor: str) -> Any:
    if valor.startswith("#"):
        return colores_modulo.HexColor(valor)
    return getattr(colores_modulo, valor, colores_modulo.black)


def _etiqueta_local(etiqueta: str) -> str:
    return etiqueta.rsplit("}", 1)[-1]


def _escapar(valor: str) -> str:
    return (
        valor.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


if __name__ == "__main__":
    principal()

