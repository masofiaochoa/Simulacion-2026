import random
from config import METODO_ALEATORIO

class GCLState:
    def __init__(self, seed=7, a=1664525, c=1013904223, m=2**32):
        self.x = seed
        self.a = a
        self.c = c
        self.m = m
        
    def next_val(self):
        self.x = (self.a * self.x + self.c) % self.m
        return self.x / self.m

class XorShiftState:
    def __init__(self, seed=123456789):
        self.x = seed
        
    def next_val(self):
        self.x ^= (self.x << 13) & 0xFFFFFFFF
        self.x ^= (self.x >> 17)
        self.x ^= (self.x << 5) & 0xFFFFFFFF
        return (self.x & 0xFFFFFFFF) / 0xFFFFFFFF

# Inicialización de instancias globales para mantener el estado
_gcl_instance = GCLState()
_xorshift_instance = XorShiftState()

def generar_U01():
    if METODO_ALEATORIO == "gcl":
        return _gcl_instance.next_val()
    elif METODO_ALEATORIO == "xorshift":
        return _xorshift_instance.next_val()
    else:
        return random.random()