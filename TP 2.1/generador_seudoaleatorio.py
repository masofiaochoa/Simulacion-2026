import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import random
import os
from math import sqrt, erfc
from scipy.fftpack import fft
from scipy.stats import chisquare
from collections import Counter

# ==========================================
# 1. CREACIÓN DE LA CARPETA
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
output_dir = os.path.join(BASE_DIR, "graficas")
os.makedirs(output_dir, exist_ok=True)

# ==========================================
# 2. GENERADORES
# ==========================================
def cuadrados_medios(seed, n, digits=4):
    results = []
    current = seed
    for _ in range(n):
        squared = str(current**2).zfill(2*digits)
        mid = len(squared) // 2
        next_val = int(squared[mid - digits//2: mid + digits//2]) 
        results.append(next_val / (10**digits)) 
        current = next_val
    return results

def gcl(seed, a, c, m, n): 
    values = []
    x = seed
    for _ in range(n):
        x = (a * x + c) % m
        values.append(x / m)
    return values

def xorshift(seed, n):
    results = []
    x = seed
    for _ in range(n):  
        x ^= (x << 13) & 0xFFFFFFFF 
        x ^= (x >> 17) 
        x ^= (x << 5) & 0xFFFFFFFF 
        results.append((x & 0xFFFFFFFF) / 0xFFFFFFFF)
    return results

# ==========================================
# 3. Pruebas estadísticas basadas en NIST SP800-22 -> Obtenidas de: https://www.random.org/analysis/
# ==========================================

#No es una prueba como tal sino un helper para los tests
#Convierte valores sobre la media (0.5) a 1 y valores debajo de la media a 0
def valores_a_bits(valores):
    return ''.join('1' if v >= 0.5 else '0' for v in valores)

# Test Monobit:
# Verifica que la cantidad de bits 0 y 1 sea aproximadamente la misma. (Por arriba y por debajo de la media)
def frequency_monobit_test(bitstring):
    n = len(bitstring)

    ones = bitstring.count('1')
    zeros = bitstring.count('0')

    s = abs(ones - zeros)

    test_stat = s / sqrt(n)

    p = erfc(test_stat / sqrt(2))

    return float(p)

# Test Runs:
# Evalúa si las secuencias consecutivas de 0s y 1s tienen una longitud y frecuencia esperadas.
def runs_test(bitstring):
    n = len(bitstring)

    if n < 100:
        return 0.0

    pi = bitstring.count('1') / n

    tau = 2 / sqrt(n)

    if abs(pi - 0.5) >= tau:
        return 0.0

    V_n = 1 + sum(
        bitstring[i] != bitstring[i - 1]
        for i in range(1, n)
    )

    numerator = abs(
        V_n - 2 * n * pi * (1 - pi)
    )

    denominator = (
        2 * sqrt(2 * n) * pi * (1 - pi)
    )

    if denominator == 0:
        return 0.0

    p = erfc(numerator / denominator)

    return float(p)

# Test Serial:
# Comprueba que los pares de bits (00, 01, 10 y 11) aparezcan con frecuencias similares.
def serial_test(bitstring):

    pairs = [
        bitstring[i:i+2]
        for i in range(0, len(bitstring)-1, 2)
    ]

    freq = Counter(pairs)

    values = [
        freq.get(pair, 0)
        for pair in ['00', '01', '10', '11']
    ]

    expected = [len(pairs)/4] * 4

    stat, p = chisquare(
        values,
        f_exp=expected
    )

    return float(p)

# Test Spectral:
# Detecta patrones periódicos o repeticiones utilizando la Transformada Rápida de Fourier (FFT).
def spectral_test(bitstring):

    n = len(bitstring)

    X = np.array([
        2 * int(b) - 1
        for b in bitstring
    ])

    S = fft(X)

    M = np.abs(S[:n // 2])

    T = np.sqrt(
        np.log(1 / 0.05) * n
    )

    N0 = 0.95 * n / 2

    N1 = np.sum(M < T)

    d = (
        (N1 - N0)
        /
        np.sqrt(
            n * 0.95 * 0.05 / 4
        )
    )

    p = erfc(
        np.abs(d) / np.sqrt(2)
    )

    return float(p)

# Test de Frecuencia (Chi-cuadrado):
# Verifica si los números generados se distribuyen uniformemente en el intervalo [0,1).
def test_frecuencia(valores, bins=10):
    counts, _ = np.histogram(valores, bins=bins, range=(0.0, 1.0))
    esperado = len(valores) / bins
    chi2 = sum((o - esperado) ** 2 / esperado for o in counts)
    return chi2, counts

# ==========================================
# 4. EJECUCIÓN
# ==========================================
n = 10000

# Semillas ajustadas
cuadrados_vals = cuadrados_medios(seed=3708, n=n) 
gcl_vals = gcl(seed=7, a=1664525, c=1013904223, m=2**32, n=n) 
xorshift_vals = xorshift(seed=123456789, n=n)
python_vals = [random.random() for _ in range(n)]

df = pd.DataFrame({
    "Cuadrados": cuadrados_vals,
    "GCL": gcl_vals,
    "XorShift": xorshift_vals,
    "Python": python_vals
})
"""
tests = {}
for name in df.columns:
    vals = df[name]
    tests[name] = {
        "Media": test_media(vals),
        "Autocorrelación": test_autocorrelacion(vals),
        "Corridas": test_corridas(vals),
        "Chi2 (Frecuencia)": test_frecuencia(vals)[0]
    }
"""
tests = {}
for name in df.columns:
    vals = df[name]
    bits = valores_a_bits(vals)

    chi2, _ = test_frecuencia(vals)

    tests[name] = {
        "Chi2": chi2,
        "Monobit p": frequency_monobit_test(bits),
        "Runs p": runs_test(bits),
        "Serial p": serial_test(bits),
        "Spectral p": spectral_test(bits)
    }

resultados_df = pd.DataFrame(tests).T
print("--- Resultados de las Pruebas ---")
print(resultados_df)

# ==========================================
# 5. GUARDAR GRÁFICOS
# ==========================================
for col in df.columns:
    plt.figure(figsize=(6, 4))
    plt.hist(df[col], bins=10, range=(0.0, 1.0), alpha=0.7, color="skyblue", edgecolor="black")
    plt.title(f"Histograma: {col}")
    plt.xlabel("Valor")
    plt.ylabel("Frecuencia")
    plt.tight_layout()
    
    ruta_histograma = os.path.join(output_dir, f"histograma_{col.lower()}.png")
    plt.savefig(ruta_histograma)
    plt.close()

def generar_imagen(datos, nombre_archivo):
    if len(datos) != 10000:
        raise ValueError("Cada columna debe tener 10.000 números")

    matriz = np.array(datos).reshape((100, 100))
    plt.figure(figsize=(4, 4))
    plt.imshow(matriz, cmap='gray', interpolation='nearest')
    plt.axis('off')

    ruta_completa = os.path.join(output_dir, f"{nombre_archivo}.png")
    plt.savefig(ruta_completa, bbox_inches='tight', pad_inches=0)
    plt.close()

for nombre_columna in df.columns:
    generar_imagen(df[nombre_columna], nombre_columna)

print(f"\n¡Éxito! Todas las imágenes se guardaron en: {output_dir}")