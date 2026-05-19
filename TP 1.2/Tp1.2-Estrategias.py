import math
import random
import sys
import matplotlib as mpl
import numpy as np
import matplotlib.pyplot as plt
#retorno apuesta (por numero)
def calcular_apuesta_ganadora(apuesta):
    return apuesta * 35  #El payout de una ruleta normal, en un valor unico es de 35:1

# Ruleta
def ruleta():
    valor = random.randint(0, 36)
    return valor

# Grafica    
def graficas_muestra(balancesArray, resumenFrecRel, valoresArray,
                     cant_corridas, numero_elegido, strategy_name):

    cantidad_muestra = min(8, cant_corridas)
    indices_random = random.sample(range(cant_corridas), cantidad_muestra)

    plt.figure(figsize=(14, 10))

    # Balance - flujo de caja
    plt.subplot(2, 2, 1)
    for i in indices_random:
        plt.plot(balancesArray[i], label=f'Corrida {i+1}')
    plt.title('Balance - Flujo de caja')
    plt.axhline(y=initial_capital, linestyle='--', color='r',label="fci (flujo de caja inicial)") #solo funciona con capital finito
    plt.xlabel('n (número de tiradas)')
    plt.ylabel('cc (cantidad de capital)')
    plt.legend()


    # Frecuencia relativa acumulada
    plt.subplot(2, 2, 2)
    for i in indices_random:
        plt.plot(resumenFrecRel[i], label=f'Corrida {i+1}')
    plt.axhline(1/37, linestyle='--', label='(frsa) frecuencia relativa de obtener la apuesta favorable segun n')
    plt.title(f'Frecuencia relativa ({numero_elegido})')
    plt.xlabel('n (número de tiradas)')
    plt.ylabel('fr (frecuencia relativa)')
    plt.legend()

    # Frecuencia final
    plt.subplot(2, 2, 3)

    frecuencias_finales = [
        valoresArray[i].count(numero_elegido)/len(valoresArray[i])
        for i in indices_random
    ]

    plt.bar(
        [f'C{i+1}' for i in indices_random],
        frecuencias_finales
    )

    plt.axhline(1/37, linestyle='--')
    plt.title('Frecuencia final')

    # Distribución de apariciones
    plt.subplot(2, 2, 4)

    apariciones = [
        valoresArray[i].count(numero_elegido)
        for i in indices_random
    ]

    plt.bar(
        [f'C{i+1}' for i in indices_random],
        apariciones
    )

    plt.title(f'Apariciones del número {numero_elegido}')

    plt.tight_layout()
    plt.show()
    plt.savefig('muestras.png')

# Estrategias

#Duplica apuesta al perder, vuelve a la apuesta inicial al ganar
def martingala_strategy(initial_bet, cant_tiradas, initial_capital, capital, numero_elegido):
    balanceArray = []
    betArray = []
    valores = []
    frecRelPorTiradaArray = []
    frec_abs = 0

    if capital == "f":
        balanceArray.append(initial_capital)
    else:
        balanceArray.append(0)
    betArray.append(initial_bet)
    for i in range(cant_tiradas):
        if betArray[i] <= balanceArray[i] or balanceArray[0] == 0:
            valor = ruleta()
            valores.append(valor)
            if valor == numero_elegido:
                apuesta_ganadora = calcular_apuesta_ganadora(betArray[i])
                balanceArray.append(balanceArray[i] + apuesta_ganadora)
                betArray.append(betArray[0]) #Gana y vuelve a la apuesta inicial
                frec_abs += 1
            else:
                balanceArray.append(balanceArray[i] - betArray[i])
                betArray.append(betArray[i] * 2) #Pierde y duplica la proxima apuesta por dos
        else:
            if capital == "f":
                balanceArray.append(0) #Para visualizar la quiebra en caso de ser capital finito
            break

        frecRelPorTiradaArray.append(frec_abs/(i+1))

    return balanceArray, betArray, valores, frecRelPorTiradaArray


#Al ganar, resta una 'unidad' (En este caso una apuesta inicial) a la apuesta siguiente, al perder suma una unidad a la apuesta siguiente
def dalembert_strategy(initial_bet, cant_tiradas, initial_capital, capital, numero_elegido):
    balanceArray = []
    betArray = []
    valores = []
    frecRelPorTiradaArray = []
    frec_abs = 0

    if capital == "f":
        balanceArray.append(initial_capital)
    else:
        balanceArray.append(0)
    betArray.append(initial_bet)
    unidadBase = initial_bet

    for i in range(cant_tiradas):
        if betArray[i] <= balanceArray[i] or balanceArray[0] == 0:
            valor = ruleta()
            valores.append(valor)
            if valor == numero_elegido:
                frec_abs += 1
                apuesta_ganadora = calcular_apuesta_ganadora(betArray[i])
                balanceArray.append(balanceArray[i] + apuesta_ganadora)
                # para que no llegue a apuesta 0 en caso de ganar
                if (betArray[i]-unidadBase) < unidadBase:
                    betArray.append(unidadBase)
                else:
                    betArray.append(betArray[i] - unidadBase)

            else:
                balanceArray.append(balanceArray[i] - betArray[i])
                betArray.append(betArray[i] + unidadBase)
        else:
            if capital == "f":
                balanceArray.append(0) #Para visualizar la quiebra en caso de ser capital finito
            break

        frecRelPorTiradaArray.append(frec_abs/(i+1))
    return balanceArray, betArray, valores, frecRelPorTiradaArray

#Secuencia fibonacci multiplicada por la apuesta inicial
def fibonacci_strategy(initial_bet, cant_tiradas, initial_capital, capital, numero_elegido):
    balanceArray = []
    betArray = []
    valores = []
    frecRelPorTiradaArray = []
    frec_abs = 0

    if capital == "f":
        balanceArray.append(initial_capital)
    else:
        balanceArray.append(0)
    betArray.append(initial_bet)
    valoresfib = [0, initial_bet, initial_bet]
    for i in range(cant_tiradas):
        if betArray[i] <= balanceArray[i] or balanceArray[0] == 0:
            valor = ruleta()
            valores.append(valor)
            if valor == numero_elegido:
                frec_abs += 1
                apuesta_ganadora = calcular_apuesta_ganadora(valoresfib[1])
                balanceArray.append(balanceArray[i] + apuesta_ganadora)
                if valoresfib[0] == 0 or valoresfib[0] == initial_bet:
                    valoresfib = [0, initial_bet, initial_bet]
                else:
                    prevant = valoresfib[0]
                    actant = valoresfib[1]
                    act = actant-prevant
                    valoresfib = [prevant-act, act, prevant]
            else:
                balanceArray.append(balanceArray[i] - valoresfib[1])
                actant = valoresfib[1]
                posant = valoresfib[2]
                valoresfib = [actant, posant, actant+posant]
            betArray.append(valoresfib[1])
        else:
            if capital == "f":
                balanceArray.append(0) #Para visualizar la quiebra en caso de ser capital finito
            break

        frecRelPorTiradaArray.append(frec_abs/(i+1))

    return balanceArray, betArray, valores, frecRelPorTiradaArray

#Martin gala pero al reves, duplica al ganar y vuelve a la apuesta inicial al perder
def paroli_strategy(initial_bet, cant_tiradas, initial_capital, capital, numero_elegido):
    balanceArray = []
    betArray = []
    valores = []
    frecRelPorTiradaArray = []
    frec_abs = 0

    if capital == "f":
        balanceArray.append(initial_capital)
    else:
        balanceArray.append(0)
    betArray.append(initial_bet)

    for i in range(cant_tiradas):
        if betArray[i] <= balanceArray[i] or balanceArray[0] == 0:
            valor = ruleta()
            valores.append(valor)
            if valor == numero_elegido:
                frec_abs += 1
                apuesta_ganadora = calcular_apuesta_ganadora(betArray[i])
                balanceArray.append(balanceArray[i] + apuesta_ganadora)

                betArray.append(betArray[i]*2)

            else:
                balanceArray.append(balanceArray[i] - betArray[i])

                betArray.append(initial_bet)
        else:
            if capital == "f":
                balanceArray.append(0) #Para visualizar la quiebra en caso de ser capital finito
            break

        frecRelPorTiradaArray.append(frec_abs/(i+1))

    return balanceArray, betArray, valores, frecRelPorTiradaArray


def simulate_game(strategy, initial_bet, cant_tiradas, cant_corridas,
                  initial_capital, capital, strategy_name, numero_elegido):

    balancesArray = []
    resumenFrecRel = []
    valoresArray = []

    for i in range(cant_corridas):
        resultados = strategy(
            initial_bet,
            cant_tiradas,
            initial_capital,
            capital,
            numero_elegido
        )

        balanceArray = resultados[0]
        valores = resultados[2]
        frecRelPorTiradaArray = resultados[3]

        balancesArray.append(balanceArray)
        resumenFrecRel.append(frecRelPorTiradaArray)
        valoresArray.append(valores)
        
    
    graficas_muestra(
            balancesArray,
            resumenFrecRel,
            valoresArray,
            cant_corridas,
            numero_elegido,
            strategy_name
        )

if len(sys.argv) != 11:
    print("Uso: python Tp1.2-Estrategias.py -c <cant_tiradas> -n <corridas> -e <numero_elegido|auto> -s <estrategia(m/d/f/o)> -a <capital(i/f)>")
    sys.exit(1)

#tiradas
cant_tiradas = int(sys.argv[2])
cant_corridas = int(sys.argv[4])

if sys.argv[6] == "auto":
    numero_elegido = random.randint(0, 36)
else:
    numero_elegido = int(sys.argv[6])

estrategia = sys.argv[8]
capital = sys.argv[10]

print(f"Número elegido: {numero_elegido}")

# Parametros ingresados por la consola

if capital == "f":
    initial_capital = int(input("Ingrese el capital inicial: "))
elif capital == "i":
    initial_capital = math.inf
    print("Capital infinito")
    
initial_bet = int(input("Ingrese el monto de la apuesta inicial: "))

if (estrategia) == "m":
    # Simulación de la estrategia de Martingala
    simulate_game(martingala_strategy, initial_bet, cant_tiradas,
                  cant_corridas, initial_capital, capital, "Martin Gala", numero_elegido)
elif (estrategia) == "d":
    # Simulación de la estrategia de D'Alembert
    simulate_game(dalembert_strategy, initial_bet, cant_tiradas,
                  cant_corridas, initial_capital, capital, "D'Alembert", numero_elegido)
elif (estrategia) == "f":
    # Simulación de la estrategia de Fibonacci
    simulate_game(fibonacci_strategy, initial_bet, cant_tiradas,
                  cant_corridas, initial_capital, capital, "Fibonacci", numero_elegido)
elif (estrategia) == "o":
    # Simulación de la estrategia de Paroli
    simulate_game(paroli_strategy, initial_bet, cant_tiradas,
                  cant_corridas, initial_capital, capital, "Paroli", numero_elegido)
