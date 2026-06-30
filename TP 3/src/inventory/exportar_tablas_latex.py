"""Exporta tablas seleccionadas de resultados de inventario a LaTeX."""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path


def principal() -> None:
    parser = argparse.ArgumentParser(
        description="Exporta tablas LaTeX de inventario."
    )
    parser.add_argument(
        "--summary",
        "--resumen",
        dest="resumen",
        default="results/inventory/experiments/inventario_resumen.csv",
        help="Ruta a inventario_resumen.csv.",
    )
    parser.add_argument(
        "--output-dir",
        "--directorio-salida",
        dest="directorio_salida",
        default="report/tables",
        help="Directorio donde se escriben los fragmentos de tablas LaTeX.",
    )
    argumentos = parser.parse_args()

    filas = _leer_filas(Path(argumentos.resumen))
    directorio_salida = Path(argumentos.directorio_salida)
    directorio_salida.mkdir(parents=True, exist_ok=True)

    _escribir_tabla_resumen_politicas(
        filas,
        directorio_salida / "inventario_resumen_politicas.tex",
    )
    _escribir_tabla_costos(
        filas,
        directorio_salida / "inventario_costos.tex",
    )
    _escribir_tabla_comparacion_esperada(
        filas,
        directorio_salida / "inventario_comparacion_esperada.tex",
    )

    print("Tablas LaTeX de inventario exportadas")
    print(f"  directorio de salida: {directorio_salida}")


def _leer_filas(ruta: Path) -> list[dict[str, str]]:
    with ruta.open("r", newline="", encoding="utf-8") as archivo_csv:
        return list(csv.DictReader(archivo_csv))


def _escribir_tabla_resumen_politicas(
    filas: list[dict[str, str]],
    ruta: Path,
) -> None:
    lineas = [
        "% Generado desde results/inventory/experiments/inventario_resumen.csv",
        "\\begin{table}[htbp]",
        "\\centering",
        "\\caption{Resumen de desempeno por politica de inventario.}",
        "\\label{tab:inventario-resumen-politicas}",
        "\\begin{tabular}{lrrrrrr}",
        "\\toprule",
        "Politica & $Q$ & $r$ & Costo total & IC 95\\% & Servicio & Faltantes \\\\",
        "\\midrule",
    ]

    for fila in filas:
        lineas.append(
            " & ".join(
                [
                    _politica_latex(fila["politica"]),
                    _formatear_numero(fila["Q"], 0),
                    _formatear_numero(fila["r"], 0),
                    _formatear_numero(fila["costo_total_media"], 2),
                    _formatear_numero(fila["costo_total_semiancho_ic95"], 2),
                    _formatear_porcentaje(fila["nivel_servicio_media"]),
                    _formatear_numero(fila["unidades_faltantes_media"], 2),
                ]
            )
            + " \\\\"
        )

    lineas.extend(
        [
            "\\bottomrule",
            "\\end{tabular}",
            *_lineas_nota_tabla(
                "El nivel de servicio se calcula como demanda satisfecha sobre "
                "demanda total. Los faltantes corresponden a ventas perdidas."
            ),
            "\\end{table}",
        ]
    )
    _escribir_latex(ruta, lineas)


def _escribir_tabla_costos(
    filas: list[dict[str, str]],
    ruta: Path,
) -> None:
    lineas = [
        "% Generado desde results/inventory/experiments/inventario_resumen.csv",
        "\\begin{table}[htbp]",
        "\\centering",
        "\\caption{Costos promedio por componente en el modelo de inventario.}",
        "\\label{tab:inventario-costos}",
        "\\begin{tabular}{lrrrr}",
        "\\toprule",
        "Politica & Orden & Mantenimiento & Faltante & Total \\\\",
        "\\midrule",
    ]

    for fila in filas:
        lineas.append(
            " & ".join(
                [
                    _politica_latex(fila["politica"]),
                    _formatear_numero(fila["costo_orden_media"], 2),
                    _formatear_numero(fila["costo_mantenimiento_media"], 2),
                    _formatear_numero(fila["costo_faltante_media"], 2),
                    _formatear_numero(fila["costo_total_media"], 2),
                ]
            )
            + " \\\\"
        )

    lineas.extend(
        [
            "\\bottomrule",
            "\\end{tabular}",
            *_lineas_nota_tabla(
                "Todos los valores son promedios sobre las replicas de cada "
                "politica y usan el horizonte de 365 dias."
            ),
            "\\end{table}",
        ]
    )
    _escribir_latex(ruta, lineas)


def _escribir_tabla_comparacion_esperada(
    filas: list[dict[str, str]],
    ruta: Path,
) -> None:
    lineas = [
        "% Generado desde results/inventory/experiments/inventario_resumen.csv",
        "\\begin{table}[htbp]",
        "\\centering",
        "\\caption{Comparacion contra una referencia esperada simplificada de inventario.}",
        "\\label{tab:inventario-comparacion-esperada}",
        "\\begin{tabular}{lrrrrr}",
        "\\toprule",
        "Politica & Costo esp. & Python & Dif. \\% & Faltantes esp. & Faltantes Python \\\\",
        "\\midrule",
    ]

    for fila in filas:
        referencia = _referencia_esperada(fila)
        costo_python = float(fila["costo_total_media"])
        faltantes_python = float(fila["unidades_faltantes_media"])
        lineas.append(
            " & ".join(
                [
                    _politica_latex(fila["politica"]),
                    _formatear_numero(referencia["costo_total"], 2),
                    _formatear_numero(costo_python, 2),
                    _formatear_numero(
                        _error_porcentual(costo_python, referencia["costo_total"]),
                        2,
                    ),
                    _formatear_numero(referencia["faltantes"], 2),
                    _formatear_numero(faltantes_python, 2),
                ]
            )
            + " \\\\"
        )

    lineas.extend(
        [
            "\\bottomrule",
            "\\end{tabular}",
            *_lineas_nota_tabla(
                "La referencia usa demanda media, ciclos esperados $D/Q$, "
                "inventario medio $Q/2+\\max(r-\\lambda_D L,0)$ y faltante "
                "esperado $E[(D_L-r)^+]$ con $D_L\\sim Poisson(\\lambda_D L)$."
            ),
            "\\end{table}",
        ]
    )
    _escribir_latex(ruta, lineas)


def _referencia_esperada(fila: dict[str, str]) -> dict[str, float]:
    Q = float(fila["Q"])
    r = float(fila["r"])
    horizonte = float(fila["horizonte_dias"])
    demanda_media_diaria = float(fila["demanda_media_diaria"])
    tiempo_entrega = float(fila["tiempo_entrega_dias"])
    costo_fijo_orden = float(fila["costo_fijo_orden"])
    costo_mantenimiento = float(fila["costo_mantenimiento_unidad_dia"])
    costo_faltante = float(fila["costo_faltante_unidad"])

    demanda_esperada = demanda_media_diaria * horizonte
    ciclos_esperados = demanda_esperada / Q
    demanda_entrega_media = demanda_media_diaria * tiempo_entrega
    stock_seguridad = max(r - demanda_entrega_media, 0.0)
    inventario_promedio = Q / 2.0 + stock_seguridad
    faltante_por_ciclo = _perdida_esperada_poisson(demanda_entrega_media, r)
    faltantes = ciclos_esperados * faltante_por_ciclo

    costo_orden = ciclos_esperados * costo_fijo_orden
    costo_mantenimiento_total = inventario_promedio * horizonte * costo_mantenimiento
    costo_faltante_total = faltantes * costo_faltante

    return {
        "costo_orden": costo_orden,
        "costo_mantenimiento": costo_mantenimiento_total,
        "costo_faltante": costo_faltante_total,
        "costo_total": costo_orden + costo_mantenimiento_total + costo_faltante_total,
        "faltantes": faltantes,
    }


def _perdida_esperada_poisson(media: float, punto_reorden: float) -> float:
    limite = max(int(math.ceil(media + 12.0 * math.sqrt(media + 1.0))), int(punto_reorden) + 50)
    probabilidad = math.exp(-media)
    perdida = max(0.0 - punto_reorden, 0.0) * probabilidad

    for valor in range(1, limite + 1):
        probabilidad *= media / valor
        perdida += max(valor - punto_reorden, 0.0) * probabilidad

    return perdida


def _error_porcentual(observado: float, esperado: float) -> float | None:
    if abs(esperado) < 1e-12:
        return None
    return 100.0 * (observado - esperado) / esperado


def _politica_latex(nombre: str) -> str:
    return "\\texttt{" + nombre.replace("_", "\\_") + "}"


def _formatear_numero(valor: str | float | None, decimales: int) -> str:
    if valor is None or valor == "":
        return "--"
    numero = float(valor)
    if abs(numero) < 0.5 * 10 ** (-decimales):
        numero = 0.0
    return f"{numero:.{decimales}f}"


def _formatear_porcentaje(valor: str | float | None) -> str:
    if valor is None or valor == "":
        return "--"
    return f"{100.0 * float(valor):.2f}\\%"


def _lineas_nota_tabla(texto: str) -> list[str]:
    return [
        "\\par\\smallskip",
        "\\begin{minipage}{0.95\\linewidth}",
        "\\centering\\footnotesize",
        texto,
        "\\end{minipage}",
    ]


def _escribir_latex(ruta: Path, lineas: list[str]) -> None:
    ruta.write_bytes(("\n".join(lineas) + "\n").encode("utf-8"))


if __name__ == "__main__":
    principal()
