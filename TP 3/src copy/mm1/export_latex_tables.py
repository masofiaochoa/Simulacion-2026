"""Exporta tablas seleccionadas de resultados M/M/1 a LaTeX."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


ETIQUETAS_METRICAS = {
    "promedio_clientes_sistema": "$L$",
    "promedio_clientes_cola": "$L_q$",
    "tiempo_promedio_sistema": "$W$",
    "tiempo_promedio_cola": "$W_q$",
    "utilizacion_servidor": "$\\rho_{serv}$",
    "probabilidad_denegacion": "$P_{den}$",
}


def principal() -> None:
    parser = argparse.ArgumentParser(description="Exporta tablas LaTeX M/M/1.")
    parser.add_argument(
        "--summary",
        "--resumen",
        dest="resumen",
        default="results/mm1/experiments/mm1_summary.csv",
        help="Ruta a mm1_summary.csv.",
    )
    parser.add_argument(
        "--output-dir",
        "--directorio-salida",
        dest="directorio_salida",
        default="report/tables",
        help="Directorio donde se escriben los fragmentos de tablas LaTeX.",
    )
    parser.add_argument(
        "--queue-probabilities",
        "--probabilidades-cola",
        dest="probabilidades_cola",
        default="results/mm1/experiments/mm1_queue_probabilities.csv",
        help="Ruta a mm1_queue_probabilities.csv.",
    )
    argumentos = parser.parse_args()

    filas = _leer_filas(Path(argumentos.resumen))
    filas_probabilidades_cola = _leer_filas(Path(argumentos.probabilidades_cola))
    directorio_salida = Path(argumentos.directorio_salida)
    directorio_salida.mkdir(parents=True, exist_ok=True)

    _escribir_tabla_infinita_estable(
        filas,
        directorio_salida / "mm1_infinite_steady_state.tex",
    )
    _escribir_tabla_probabilidades_cola_infinita_estable(
        filas_probabilidades_cola,
        directorio_salida / "mm1_infinite_queue_probabilities.tex",
    )
    _escribir_tabla_infinita_sin_regimen(
        filas,
        directorio_salida / "mm1_infinite_unstable.tex",
    )
    _escribir_tabla_probabilidad_denegacion(
        filas,
        directorio_salida / "mm1_denial_probability.tex",
    )

    print("Tablas LaTeX M/M/1 exportadas")
    print(f"  directorio de salida: {directorio_salida}")


def _leer_filas(ruta: Path) -> list[dict[str, str]]:
    with ruta.open("r", newline="", encoding="utf-8") as archivo_csv:
        return list(csv.DictReader(archivo_csv))


def _escribir_tabla_infinita_estable(
    filas: list[dict[str, str]],
    ruta: Path,
) -> None:
    seleccionadas = [
        fila
        for fila in filas
        if fila["capacidad_cola"] == "infinita"
        and fila["estado_teorico"] == "capacidad_infinita_regimen_estacionario"
    ]
    seleccionadas.sort(key=lambda fila: _a_float(fila["rho"]))

    lineas = [
        "% Generado desde results/mm1/experiments/mm1_summary.csv",
        "\\begin{table}[htbp]",
        "\\centering",
        "\\caption{Comparacion teorica y simulada para cola infinita estable.}",
        "\\label{tab:mm1-infinite-steady}",
        "\\begin{tabular}{llrrrr}",
        "\\toprule",
        "$\\rho$ & Metrica & Sim. & IC 95\\% & Teoria & Error \\% \\\\",
        "\\midrule",
    ]

    metricas = [
        "promedio_clientes_sistema",
        "promedio_clientes_cola",
        "tiempo_promedio_sistema",
        "tiempo_promedio_cola",
        "utilizacion_servidor",
    ]

    for indice_fila, fila in enumerate(seleccionadas):
        for indice_metrica, metrica in enumerate(metricas):
            rho = _formatear_numero(fila["rho"], 2) if indice_metrica == 0 else ""
            lineas.append(
                " & ".join(
                    [
                        rho,
                        ETIQUETAS_METRICAS[metrica],
                        _formatear_numero(fila[f"{metrica}_media"], 4),
                        _formatear_numero(fila[f"{metrica}_semiancho_ic95"], 4),
                        _formatear_numero(fila[f"{metrica}_teoria"], 4),
                        _formatear_numero(fila[f"{metrica}_error_porcentual"], 2),
                    ]
                )
                + " \\\\"
            )
        if indice_fila != len(seleccionadas) - 1:
            lineas.append("\\addlinespace")

    lineas.extend(
        [
            "\\bottomrule",
            "\\end{tabular}",
            "\\end{table}",
        ]
    )
    _escribir_latex(ruta, lineas)


def _escribir_tabla_probabilidades_cola_infinita_estable(
    filas: list[dict[str, str]],
    ruta: Path,
) -> None:
    longitudes = [str(longitud) for longitud in range(0, 6)]
    seleccionadas = [
        fila
        for fila in filas
        if fila["capacidad_cola"] == "infinita"
        and fila["estado_teorico"] == "capacidad_infinita_regimen_estacionario"
        and fila["longitud_cola"] in longitudes
    ]
    rhos = sorted({_formatear_numero(fila["rho"], 2) for fila in seleccionadas})
    por_clave = {
        (_formatear_numero(fila["rho"], 2), fila["longitud_cola"]): fila
        for fila in seleccionadas
    }

    lineas = [
        "% Generado desde results/mm1/experiments/mm1_queue_probabilities.csv",
        "\\begin{table}[htbp]",
        "\\centering",
        "\\caption{Probabilidad de longitud de cola para cola infinita estable.}",
        "\\label{tab:mm1-queue-probabilities}",
        "\\begin{tabular}{lccc}",
        "\\toprule",
        "$q$ & $\\rho=0.25$ & $\\rho=0.50$ & $\\rho=0.75$ \\\\",
        "\\midrule",
    ]

    for longitud in longitudes:
        celdas = [f"${longitud}$"]
        for rho in rhos:
            fila = por_clave[(rho, longitud)]
            celdas.append(
                "\\shortstack{"
                + _formatear_numero(fila["probabilidad_media"], 4)
                + "\\\\("
                + _formatear_numero(fila["teoria"], 4)
                + ")}"
            )
        lineas.append(" & ".join(celdas) + " \\\\")

    lineas.extend(
        [
            "\\bottomrule",
            "\\end{tabular}",
            *_lineas_nota_tabla(
                "Cada celda muestra simulacion media y, entre parentesis, "
                "valor teorico de $P(Q=q)$."
            ),
            "\\end{table}",
        ]
    )
    _escribir_latex(ruta, lineas)


def _escribir_tabla_infinita_sin_regimen(
    filas: list[dict[str, str]],
    ruta: Path,
) -> None:
    seleccionadas = [
        fila
        for fila in filas
        if fila["capacidad_cola"] == "infinita"
        and fila["estado_teorico"] == "capacidad_infinita_sin_regimen_estacionario"
    ]
    seleccionadas.sort(key=lambda fila: _a_float(fila["rho"]))

    lineas = [
        "% Generado desde results/mm1/experiments/mm1_summary.csv",
        "\\begin{table}[htbp]",
        "\\centering",
        "\\caption{Corridas con cola infinita sin regimen estacionario.}",
        "\\label{tab:mm1-infinite-unstable}",
        "\\begin{tabular}{rrrrrl}",
        "\\toprule",
        "$\\rho$ & $L$ sim. & $L_q$ sim. & $W$ sim. & $W_q$ sim. & Referencia \\\\",
        "\\midrule",
    ]

    for fila in seleccionadas:
        lineas.append(
            " & ".join(
                [
                    _formatear_numero(fila["rho"], 2),
                    _formatear_numero(fila["promedio_clientes_sistema_media"], 4),
                    _formatear_numero(fila["promedio_clientes_cola_media"], 4),
                    _formatear_numero(fila["tiempo_promedio_sistema_media"], 4),
                    _formatear_numero(fila["tiempo_promedio_cola_media"], 4),
                    "No estacionaria",
                ]
            )
            + " \\\\"
        )

    lineas.extend(
        [
            "\\bottomrule",
            "\\end{tabular}",
            "\\end{table}",
        ]
    )
    _escribir_latex(ruta, lineas)


def _escribir_tabla_probabilidad_denegacion(
    filas: list[dict[str, str]],
    ruta: Path,
) -> None:
    seleccionadas = [
        fila
        for fila in filas
        if fila["capacidad_cola"] != "infinita"
    ]
    capacidades = ["0", "2", "5", "10", "50"]
    rhos = sorted({_formatear_numero(fila["rho"], 2) for fila in seleccionadas})
    por_clave = {
        (_formatear_numero(fila["rho"], 2), fila["capacidad_cola"]): fila
        for fila in seleccionadas
    }

    lineas = [
        "% Generado desde results/mm1/experiments/mm1_summary.csv",
        "\\begin{table}[htbp]",
        "\\centering",
        "\\caption{Probabilidad de denegacion simulada y teorica para colas finitas.}",
        "\\label{tab:mm1-denial-probability}",
        "\\begin{tabular}{lccccc}",
        "\\toprule",
        "$\\rho$ & $B=0$ & $B=2$ & $B=5$ & $B=10$ & $B=50$ \\\\",
        "\\midrule",
    ]

    for rho in rhos:
        celdas = [rho]
        for capacidad in capacidades:
            fila = por_clave[(rho, capacidad)]
            celdas.append(
                "\\shortstack{"
                + _formatear_numero(fila["probabilidad_denegacion_media"], 4)
                + "\\\\("
                + _formatear_numero(fila["probabilidad_denegacion_teoria"], 4)
                + ")}"
            )
        lineas.append(" & ".join(celdas) + " \\\\")

    lineas.extend(
        [
            "\\bottomrule",
            "\\end{tabular}",
            *_lineas_nota_tabla(
                "Cada celda muestra simulacion media y, entre parentesis, "
                "valor teorico."
            ),
            "\\end{table}",
        ]
    )
    _escribir_latex(ruta, lineas)


def _a_float(valor: str) -> float:
    return float(valor)


def _formatear_numero(valor: str | float | None, decimales: int) -> str:
    if valor is None or valor == "":
        return "--"
    numero = float(valor)
    if abs(numero) < 0.5 * 10 ** (-decimales):
        numero = 0.0
    return f"{numero:.{decimales}f}"


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
