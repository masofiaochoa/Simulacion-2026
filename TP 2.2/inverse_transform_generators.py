import math
from scipy.stats import norm, gamma
from base_generator import generar_U01
from probability_functions import (
    pmf_pascal,
    pmf_binomial,
    pmf_hipergeometrica,
    pmf_poisson,
)


# 1. UNIFORME (continua) - Método: Transformada Inversa
def generar_uniforme(a, b):
    if a >= b:
        raise ValueError("El parámetro 'a' debe ser menor que 'b'.")
    u = generar_U01()
    return a + (b - a) * u


# 2. EXPONENCIAL (continua) - Método: Transformada Inversa
def generar_exponencial(lam):
    if lam <= 0:
        raise ValueError("El parámetro 'lam' (lambda) debe ser positivo.")
    u = generar_U01()
    if u == 0:
        return float("inf")
    return -math.log(u) / lam


# 3. GAMMA (continua) - Método: Transformada Inversa
def generar_gamma(k, theta):
    if k <= 0 or theta <= 0:
        raise ValueError("k y theta deben ser positivos.")
    u = generar_U01()
    return gamma.ppf(u, a=k, scale=theta)


# 4. NORMAL (continua) - Método: Transformada Inversa
def generar_normal(mu, sigma):
    if sigma < 0:
        raise ValueError("Sigma (desviación estándar) debe ser no negativa.")
    if sigma == 0:
        return mu
    u = generar_U01()
    z0 = norm.ppf(u)
    return mu + sigma * z0


# 5. PASCAL (discreta) - Método: Transformada Inversa
def generar_pascal(r_exitos, p_exito):
    if not isinstance(r_exitos, int) or r_exitos <= 0:
        raise ValueError("r_exitos entero > 0")
    if not (0 < p_exito <= 1):
        raise ValueError("p_exito en (0, 1]")
    if p_exito == 1.0:
        return 0
    u = generar_U01()
    k = 0
    cum_sum = pmf_pascal(0, r_exitos, p_exito)
    while u > cum_sum:
        k += 1
        cum_sum += pmf_pascal(k, r_exitos, p_exito)
    return k


# 6. BINOMIAL (discreta) - Método: Transformada Inversa
def generar_binomial(n_ensayos, p_exito):
    if not isinstance(n_ensayos, int) or n_ensayos < 0:
        raise ValueError("n_ensayos entero >= 0")
    if not (0 <= p_exito <= 1):
        raise ValueError("p_exito en [0, 1]")
    if n_ensayos == 0:
        return 0
    u = generar_U01()
    k = 0
    cum_sum = pmf_binomial(0, n_ensayos, p_exito)
    while u > cum_sum and k < n_ensayos:
        k += 1
        cum_sum += pmf_binomial(k, n_ensayos, p_exito)
    return k


# 7. HIPERGEOMÉTRICA (discreta) - Método: Transformada Inversa
def generar_hipergeometrica(N_pop, K_ex_pop, n_muestra):
    if not all(isinstance(x, int) for x in [N_pop, K_ex_pop, n_muestra]):
        raise ValueError("Params enteros")
    if not (0 <= K_ex_pop <= N_pop and 0 <= n_muestra <= N_pop):
        raise ValueError("Params inconsistentes")
    if n_muestra == 0:
        return 0
    
    k_min = max(0, n_muestra - (N_pop - K_ex_pop))
    k_max = min(n_muestra, K_ex_pop)
    
    u = generar_U01()
    k = k_min
    cum_sum = pmf_hipergeometrica(k, N_pop, K_ex_pop, n_muestra)
    while u > cum_sum and k < k_max:
        k += 1
        cum_sum += pmf_hipergeometrica(k, N_pop, K_ex_pop, n_muestra)
    return k


# 8. POISSON (discreta) - Método: Transformada Inversa
def generar_poisson(lam):
    if lam < 0:
        raise ValueError("lambda >= 0")
    if lam == 0:
        return 0
    u = generar_U01()
    k = 0
    cum_sum = pmf_poisson(0, lam)
    while u > cum_sum:
        k += 1
        cum_sum += pmf_poisson(k, lam)
    return k


# 9. EMPÍRICA DISCRETA (discreta) - Método: Transformada Inversa
def generar_empirica_discreta(valores, probabilidades):
    if len(valores) != len(probabilidades):
        raise ValueError("Longitudes no coinciden")
    u = generar_U01()
    cum_sum = 0.0
    for val, prob in zip(valores, probabilidades):
        cum_sum += prob
        if u <= cum_sum:
            return val
    return valores[-1]