## ENUNCIADO ##
#El trabajo de investigación consiste en construir un programa en lenguaje Python 3.x que simule el funcionamiento del
#plato de una ruleta. Para esto se debe tener en cuenta los siguientes temas:
#• Generación de valores aleatorios enteros.
#• Uso de listas para el almacenamiento de datos.
#• Uso de la estructura de control FOR para iterar las listas.
#• Empleo de funciones estadísticas.
#• Gráficos de los resultados mediante el paquete Matplotlib.
#• Ingreso por consola de parámetros para la simulación (cantidad de tiradas, corridas y número elegido, ejemplo
#python programa.py -c XXX -n YYY -e ZZ).
import random
import sys
import matplotlib.pyplot as plt
import statistics
import numpy as np

# ruleta
def ruleta():
    return random.randint(0, 36)

# validaciones del comando
if len(sys.argv) != 7:
    print("Uso: python tp11.py -c CANT_CORRIDAS -n CANT_TIRADAS -e NUMERO")
    sys.exit()

for i in range(len(sys.argv)):
    if sys.argv[i] == "-c":
        cant_corridas = int(sys.argv[i + 1])
    elif sys.argv[i] == "-n":
        cant_tiradas = int(sys.argv[i + 1])
    elif sys.argv[i] == "-e":
        numero_elegido = int(sys.argv[i + 1])

# valores teoricos esperados
frecuencia_esperada = 1 / 37
promedio_esperado = np.mean(range(37))
varianza_esperada = np.var(range(37))
desvio_esperado = np.std(range(37))

# los acumuladores de las tiradas
freq_total = [0] * cant_tiradas
prom_total = [0] * cant_tiradas
var_total = [0] * cant_tiradas
std_total = [0] * cant_tiradas

# simulacion, main, lo que querramos que sea
# esto podria ser una funcion aparte para mas simplicidad
for c in range(cant_corridas):

    aciertos = 0
    suma = 0
    valores = []

    for i in range(cant_tiradas):

        valor = ruleta()
        valores.append(valor)

        # Frecuencia
        if valor == numero_elegido:
            aciertos += 1
        freq_total[i] += aciertos / (i + 1)

        # Promedio
        suma += valor
        prom_total[i] += suma / (i + 1)

        # Varianza y desvío
        if i > 0:
            var_total[i] += statistics.variance(valores)
            std_total[i] += statistics.stdev(valores)
        else:
            var_total[i] += 0
            std_total[i] += 0

#  PROMEDIO FINAL ENTRE CORRIDAS
freq_prom = [x / cant_corridas for x in freq_total]
prom_prom = [x / cant_corridas for x in prom_total]
var_prom = [x / cant_corridas for x in var_total]
std_prom = [x / cant_corridas for x in std_total]

#### OJO ####
# hay que hacer mínimo 8 gráficas
# estas graficas tmb podrian ser funciones distintas... veré dsp de hacerlo...
plt.figure(figsize=(12, 8))

# Frecuencia
plt.subplot(2, 2, 1)
plt.plot(freq_prom, color='red', label="frn (frecuencia relativa del número X con respecto a n)")
plt.axhline(y=frecuencia_esperada, color='blue', linestyle='--', label="fre (esperada)")
plt.title("Frecuencia relativa")
plt.xlabel("n (número de tiradas)")
plt.ylabel("fr (frecuencia relativa)")
plt.legend()

# Promedio
plt.subplot(2, 2, 2)
plt.plot(prom_prom, color='red', label="vpn (valor promedio de las tiradas con respecto a n)")
plt.axhline(y=promedio_esperado, color='blue', linestyle='--', label="vpe (valor promedio esperado)")
plt.title("Valor promedio")
plt.xlabel("n (número de tiradas)")
plt.ylabel("vp (valor promedio de las tiradas)")
plt.legend()

# Desvío
plt.subplot(2, 2, 3)
plt.plot(std_prom, color='red', label="vd (valor del desvío del número X n)")
plt.axhline(y=desvio_esperado, color='blue', linestyle='--', label="vde (valor del desvío esperado)")
plt.title("Desvío estándar")
plt.xlabel("n (número de tiradas)")
plt.ylabel("vd (valor del desvío)")
plt.legend()

# Varianza
plt.subplot(2, 2, 4)
plt.plot(var_prom, color='red', label="vnv (valor de la varianza del número X con respecto a n)")
plt.axhline(y=varianza_esperada, color='blue', linestyle='--', label="vve (valor de la varianza esperada)")
plt.title("Varianza")
plt.xlabel("n (número de tiradas)")
plt.ylabel("vv (valor de la varianza)")
plt.legend()

plt.tight_layout()
plt.show()