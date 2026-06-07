import math
from base_generator import generar_U01


# 1. UNIFORME (continua) - Método: RECHAZO
def generar_uniforme_rechazo(a, b):
    if a >= b:
        raise ValueError("El parámetro 'a' debe ser menor que 'b'.")
    
    # Propuesta: Y ~ U(a - d, b + d) con d = (b - a) * 0.5
    # Esto define una envolvente constante y rectangular sobre el dominio extendido.
    d = (b - a) * 0.5
    rango_propuesto = 2 * d + (b - a)  # = 2 * (b - a)
    min_propuesto = a - d
    
    while True:
        u1 = generar_U01()
        y_candidato = min_propuesto + rango_propuesto * u1
        # Criterio de aceptación: si el candidato cae dentro del intervalo real [a, b]
        if a <= y_candidato <= b:
            return y_candidato


# 2. EXPONENCIAL (continua) - Método: RECHAZO
def generar_exponencial_rechazo(lam):
    if lam <= 0:
        raise ValueError("El parámetro 'lam' (lambda) debe ser positivo.")
    
    # Propuesta: Y ~ U(0, M) con M = 10 / lambda (cubre el 99.998% de la distribución)
    M = 10.0 / lam
    
    while True:
        u1 = generar_U01()
        y_candidato = M * u1
        u2 = generar_U01()
        # Aceptación con probabilidad e^(-lambda * Y)
        if u2 <= math.exp(-lam * y_candidato):
            return y_candidato


# 3. NORMAL (continua) - Método: RECHAZO
def generar_normal_rechazo(mu, sigma):
    if sigma < 0:
        raise ValueError("Sigma (desviación estándar) debe ser no negativa.")
    if sigma == 0:
        return mu
        
    # Usamos una distribución envolvente Laplace (doble exponencial) Y ~ Laplace(0,1)
    # cuya densidad es g(y) = 0.5 * e^(-|y|).
    while True:
        # Generar E ~ Exp(1) usando transformada inversa
        u1 = generar_U01()
        while u1 == 0:  # Evitar log(0)
            u1 = generar_U01()
        E = -math.log(u1)
        
        # Asignar un signo aleatorio para obtener Laplace(0,1)
        u2 = generar_U01()
        signo = 1 if u2 >= 0.5 else -1
        y_candidato = signo * E
        
        # Criterio de aceptación de Von Neumann: u3 <= e^(- (E - 1)^2 / 2)
        u3 = generar_U01()
        if u3 <= math.exp(-((E - 1) ** 2) / 2.0):
            return mu + sigma * y_candidato