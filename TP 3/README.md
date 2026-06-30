# TP 3 - Simulacion de un modelo M/M/1 e Inventario

Repositorio del Trabajo Practico 3 de Simulacion. El proyecto estudia dos sistemas mediante teoria cuando corresponde, simulacion en Python, graficos, tablas e informe LaTeX:

- Una cola `M/M/1` con capacidad infinita y colas finitas `M/M/1/K`.
- Un modelo de inventario con politica de revision continua `(Q, r)`.
- Una comparacion posterior con AnyLogic, pendiente de integrar cuando esten los resultados manuales.

## Estado actual

El bloque `M/M/1` contiene simulador, formulas teoricas, matriz experimental, resultados CSV, graficos SVG/PDF y tablas LaTeX. Los casos de cola infinita con `rho >= 1` se simulan por horizonte finito, pero se marcan como casos sin regimen estacionario y no se comparan contra formulas estacionarias.

El bloque de inventario contiene simulador Python, resultados por politica, graficos SVG/PDF, tablas LaTeX y una referencia esperada simplificada para comparar costos. El modelo usa demanda diaria Poisson, ventas perdidas y politica `(Q, r)`.

AnyLogic se esta trabajando en paralelo. En `docs/` ya hay guias paso a paso para construir ambos modelos y luego registrar resultados comparables.

## Estructura

```text
.
|-- AGENTS.md
|-- TP 3 - Simulación de un modelo MM1 e Inventario.md
|-- config/
|   |-- default_parameters.json
|-- docs/
|-- src/
|   |-- common/
|   |-- inventory/
|   |-- mm1/
|-- results/
|   |-- inventory/
|   |-- mm1/
|-- figures/
|   |-- inventory/
|   |-- mm1/
|-- report/
|   |-- main.tex
|   |-- arxiv.sty
|   |-- sections/
|   |-- tables/
|   |-- figures/
|       |-- inventory/
|       |-- mm1/
```

## Configuracion

`config/default_parameters.json` centraliza los parametros editables.

Para `M/M/1` define:

- unidad de tiempo: horas;
- `mu = 10` clientes/hora;
- factores de arribo: `0.25`, `0.50`, `0.75`, `1.00`, `1.25`;
- capacidades de cola: infinita, `0`, `2`, `5`, `10`, `50`;
- horizonte: `10000` horas;
- replicas: `10`;
- semilla base: `20260626`.

Para inventario define:

- unidad de tiempo: dias;
- politica `(Q, r)`;
- horizonte de `365` dias;
- demanda Poisson media de `20` unidades/dia;
- tiempo de entrega de `3` dias;
- costos de orden, mantenimiento y faltante;
- politicas `bajo_inventario`, `balanceada` y `alto_servicio`.

## Codigo Python

El codigo esta organizado como paquete Python bajo `src/`.

`src/common/` contiene helpers compartidos para CSV y estadistica.

`src/mm1/` contiene:

- `theory.py`: formulas teoricas para `M/M/1` y `M/M/1/K`;
- `simulator.py`: simulador de eventos discretos;
- `run_single.py`: corrida individual;
- `run_experiments.py`: matriz completa;
- `plot_results.py`: graficos SVG y figura temporal;
- `export_latex_tables.py`: tablas LaTeX.

`src/inventory/` contiene:

- `simulador.py`: simulador diario de inventario `(Q, r)`;
- `experimentos.py`: replicas y resumenes por politica;
- `ejecutar_experimentos.py`: runner principal;
- `graficar_resultados.py`: graficos SVG/PDF;
- `exportar_tablas_latex.py`: tablas LaTeX, incluida la comparacion esperada.

## Como ejecutar

Desde la raiz del proyecto:

```bash
python -m src.mm1.run_single
python -m src.mm1.run_experiments
python -m src.mm1.plot_results
python -m src.mm1.export_latex_tables
```

Para inventario:

```bash
python -m src.inventory.ejecutar_experimentos
python -m src.inventory.graficar_resultados
python -m src.inventory.exportar_tablas_latex
```

## Resultados

Resultados `M/M/1`:

- `results/mm1/experiments/mm1_runs.csv`;
- `results/mm1/experiments/mm1_summary.csv`;
- `results/mm1/experiments/mm1_summary_long.csv`;
- `results/mm1/experiments/mm1_queue_probabilities.csv`.

Resultados de inventario:

- `results/inventory/experiments/inventario_corridas.csv`;
- `results/inventory/experiments/inventario_resumen.csv`;
- `results/inventory/experiments/inventario_series.csv`.

Figuras:

- `figures/mm1/`;
- `figures/inventory/`;
- copias PDF en `report/figures/`.

## Informe

El informe LaTeX esta en `report/` y usa un template simple estilo arXiv. El archivo principal es:

```text
report/main.tex
```

Para compilar en Overleaf, subir la carpeta `report/` completa y elegir `main.tex` como archivo principal.

## Notas conceptuales

Para `M/M/1` con cola infinita:

- si `rho < 1`, existe regimen estacionario y se comparan simulacion y teoria;
- si `rho >= 1`, no existe regimen estacionario, por lo que las corridas se informan como resultados de horizonte finito.

Para `M/M/1/K` con capacidad finita, todos los valores de `rho` tienen referencia estacionaria porque los arribos excedentes se rechazan cuando el sistema esta lleno.

Para inventario, la comparacion esperada usa una referencia simplificada basada en demanda media, ciclos `D/Q`, inventario promedio aproximado y faltantes esperados durante el tiempo de entrega. Esa referencia sirve como contraste, pero la decision final se basa en las replicas Python.

## AnyLogic

Las guias para construir los modelos estan en:

- `docs/2026-06-28-guia-anylogic-mm1.md`;
- `docs/2026-06-28-guia-anylogic-inventario.md`.

Cuando existan resultados exportados de AnyLogic, se deben guardar o documentar en `data/anylogic/` e integrar al informe final.

## Pendientes

- Integrar resultados reales de AnyLogic para ambos modelos.
- Completar datos reales de autores/integrantes.
- Compilar y revisar visualmente el PDF final en Overleaf o en una instalacion local de LaTeX.
