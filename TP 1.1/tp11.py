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

#-----------------
#PASAJE Y VALIDACION DE ARGUMENTOS
#-----------------
if len(sys.argv) != 7:
    print("Uso: python tp11.py -c CANT_TIRADAS -n CANT_CORRIDAS -e NUMERO")
    sys.exit()

# Ingreso por consola de parámetros para la simulación (cantidad de tiradas, corridas y número elegido, ejemplo
# python programa.py -c XXX -n YYY -e ZZ).
for i in range(len(sys.argv)):
    if sys.argv[i] == "-c":
        cant_tiradas = int(sys.argv[i + 1])
    elif sys.argv[i] == "-n":
        cant_corridas = int(sys.argv[i + 1])
    elif sys.argv[i] == "-e":
        numero_elegido = int(sys.argv[i + 1])
        
#-----------------
#VALORES ESPERADOS
#-----------------
FRECUENCIA_ESPERADA = 1 / 37
PROMEDIO_ESPERADO = np.mean(range(37))
VARIANZA_ESPERADA = np.var(range(37))
DESVIO_ESPERADO = np.std(range(37))


#-----------------
#FUNCIONES
#-----------------

#Devuelve un entero aleatorio comprendido entre 0 y 36 (37 valores posibles)
def ruleta():
    return random.randint(0, 36)
    

#Simula una x cantidad de corridas con una y cantidad de tiradas y para el numero elegido calcula
#frecuencia en la que se selecciona el numero elegido
#promedio de valores obtenidos
#varianza
#desvío estandar
def simularJuego(cant_corridas, cant_tiradas, numero_elegido):

    frecuencias_por_corrida = []
    promedios_por_corrida = []
    varianzas_por_corrida = []
    desvios_por_corrida = []

    for c in range(cant_corridas):
        aciertos = 0
        suma = 0
        valores = []

        frecuencia_corrida = []
        promedio_corrida = []
        varianza_corrida = []
        desvio_corrida = []

        for i in range(cant_tiradas):
            valor = ruleta()
            valores.append(valor)

            # Frecuencia
            if valor == numero_elegido:
                aciertos += 1
            frecuencia_corrida.append(aciertos / (i + 1))

            # Promedio
            suma += valor
            promedio_corrida.append(suma / (i + 1))

            # Varianza y desvío
            if i > 0:
                varianza_corrida.append(statistics.variance(valores))
                desvio_corrida.append(statistics.stdev(valores))
            else:
                varianza_corrida.append(0)
                desvio_corrida.append(0)

        frecuencias_por_corrida.append(frecuencia_corrida)
        promedios_por_corrida.append(promedio_corrida)
        varianzas_por_corrida.append(varianza_corrida)
        desvios_por_corrida.append(desvio_corrida)

    return frecuencias_por_corrida, promedios_por_corrida, varianzas_por_corrida, desvios_por_corrida




def funcionPrincipal():
    frecuencias_por_corrida, promedios_por_corrida, varianzas_por_corrida, desvios_por_corrida = simularJuego(cant_corridas, cant_tiradas, numero_elegido)    
    
    #PROMEDIO GENERAL DE LAS MEDIDAS ENTRE TODAS LAS CORRIDAS
    frencuencia_promedio = np.mean(frecuencias_por_corrida, axis=0)
    promedio_promedio = np.mean(promedios_por_corrida, axis=0)
    varianza_promedio = np.mean(varianzas_por_corrida, axis=0)
    desvio_promedio = np.mean(desvios_por_corrida, axis=0)
        
    
    ####GRAFICAS
    plt.figure(figsize=(12, 8))

    # Frecuencia Promedio
    plt.subplot(2, 2, 1)
    plt.plot(frencuencia_promedio, color='red', label="frn (frecuencia relativa del número X con respecto a n)")
    plt.axhline(y=FRECUENCIA_ESPERADA, color='black', linestyle='--', label="fre (frecuencia relativa esperada)")
    plt.title("Frecuencia relativa promedio de todas las tiradas")
    plt.xlabel("n (número de tiradas)")
    plt.ylabel("fr (frecuencia relativa)")
    plt.legend()

    # Promedio Promedio
    plt.subplot(2, 2, 2)
    plt.plot(promedio_promedio, color='red', label="vpn (valor promedio de las tiradas con respecto a n)")
    plt.axhline(y=PROMEDIO_ESPERADO, color='black', linestyle='--', label="vpe (valor promedio esperado)")
    plt.title("Valor promedio de todas las tiradas")
    plt.xlabel("n (número de tiradas)")
    plt.ylabel("vp (valor promedio de las tiradas)")
    plt.legend()

    # Desvío Promedio
    plt.subplot(2, 2, 3)
    plt.plot(desvio_promedio, color='red', label="vd (valor del desvío del número X n)")
    plt.axhline(y=DESVIO_ESPERADO, color='black', linestyle='--', label="vde (valor del desvío esperado)")
    plt.title("Desvío estándar promedio de todas las tiradas")
    plt.xlabel("n (número de tiradas)")
    plt.ylabel("vd (valor del desvío)")
    plt.legend()

    # Varianza Promedio
    plt.subplot(2, 2, 4)
    plt.plot(varianza_promedio, color='red', label="vnv (valor de la varianza del número X con respecto a n)")
    plt.axhline(y=VARIANZA_ESPERADA, color='black', linestyle='--', label="vve (valor de la varianza esperado)")
    plt.title("Varianza promedio de todas las tiradas")
    plt.xlabel("n (número de tiradas)")
    plt.ylabel("vv (valor de la varianza)")
    plt.legend()

    plt.tight_layout()
    plt.show()
    
    # -------------------------
    # Muestra 5 corridas (o las que haya) aleatorias
    # -------------------------
    cantidad_muestra = min(5, cant_corridas) #Si el usuario pidiero <5 corridas entonces cantidad_muestra = cant_corridas (solicitadas por el usuario)
    indices_random = random.sample(range(cant_corridas), cantidad_muestra)

    plt.figure(figsize=(12, 8))

    # Frecuencia
    plt.subplot(2, 2, 1)
    for i in indices_random:
        plt.plot(frecuencias_por_corrida[i], label=f"Frecuencia relativa corrida {i+1}")
    plt.axhline(y=FRECUENCIA_ESPERADA, color='black', linestyle='--', label="fre (frecuencia relativa esperada)")
    plt.title(f"Frecuencia relativa de {cantidad_muestra} corridas aleatorias")
    plt.xlabel("n")
    plt.ylabel("Frecuencia")
    plt.legend()

    # Promedio
    plt.subplot(2, 2, 2)
    for i in indices_random:
        plt.plot(promedios_por_corrida[i], label=f"Promedio corrida {i+1}")
    plt.axhline(y=PROMEDIO_ESPERADO, color='black', linestyle='--', label="vpe (valor promedio esperado)")
    plt.title(f"Valor promedio de {cantidad_muestra} corridas aleatorias")
    plt.xlabel("n")
    plt.ylabel("Promedio")
    plt.legend()

    # Desvío
    plt.subplot(2, 2, 3)
    for i in indices_random:
        plt.plot(desvios_por_corrida[i], label=f"Desvío estándar corrida {i+1}")
    plt.axhline(y=DESVIO_ESPERADO, color='black', linestyle='--', label="vde (valor del desvío esperado)")
    plt.title(f"Desvío estándar de {cantidad_muestra} corridas aleatorias")
    plt.xlabel("n")
    plt.ylabel("Desvío")
    plt.legend()

    # Varianza
    plt.subplot(2, 2, 4)
    for i in indices_random:
        plt.plot(varianzas_por_corrida[i], label=f"Varianza corrida {i+1}")
    plt.axhline(y=VARIANZA_ESPERADA, color='black', linestyle='--', label="vve (valor de la varianza esperado)")
    plt.title(f"Varianza de {cantidad_muestra} corridas aleatorias")
    plt.xlabel("n")
    plt.ylabel("Varianza")
    plt.legend()

    plt.tight_layout()
    plt.show()
    
    
funcionPrincipal();