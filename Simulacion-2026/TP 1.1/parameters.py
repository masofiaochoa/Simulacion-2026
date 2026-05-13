import statistics

def frecuencias_relativas_por_corrida(
        numero_elegido: int, corrida: list[int]) -> list[float]:
    contador = 0
    frecuencias_relativas = []
    for numero_tirada, valor in enumerate(corrida, start=1):
        if valor == numero_elegido:
            contador += 1
        frecuencia_relativa = contador / numero_tirada
        frecuencias_relativas.append(frecuencia_relativa)
    return frecuencias_relativas

def media_por_corrida(corrida: list[int]) -> list[float]:
    suma = 0
    medias = []
    for numero_tirada, valor in enumerate(corrida, start=1):
        suma += valor
        media = suma / numero_tirada
        medias.append(media)
    return medias

def desvios_estandar_por_corrida(corrida: list[int]) -> list[float]:
    return [
        statistics.stdev(corrida[:i]) if i > 1 else 0.0
        for i in range(1, len(corrida) + 1)
    ]

def varianza_por_corrida(corrida: list[int]) -> list[float]:
    return [
        statistics.variance(corrida[:i]) if i > 1 else 0.0
        for i in range(1, len(corrida) + 1)
    ]

def calcular_frecuencias_relativas(
    corridas: list[list[int]], numero_elegido: int
) -> list[list[float]]:
    return [
        frecuencias_relativas_por_corrida(numero_elegido, corrida)
        for corrida in corridas
    ]

def calcular_frecuencias_absolutas(corridas: list[list[int]]) -> list[list[int]]:
    return [[corrida.count(i) for i in range(37)] for corrida in corridas]

def calcular_promedios(corridas: list[list[int]]) -> dict[str, list[float]]:
    promedios = {
        'media': [],
        'desvio_estandar': [],
        'varianza': []
    }
    for corrida in corridas:
        promedios['media'].append(statistics.mean(corrida))
        promedios['desvio_estandar'].append(statistics.stdev(corrida))
        promedios['varianza'].append(statistics.variance(corrida))
    return promedios