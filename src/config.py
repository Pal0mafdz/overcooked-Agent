import pygame

TAM_CELDA = 64
ANCHO_GRID = 18
ALTO_GRID = 11
VELOCIDAD_MOVIMIENTO = 8
PROB_INGREDIENTE_PODRIDO = 0.3   # Probabilidad de que un ingrediente esté podrido (0.0 - 1.0)

TIEMPO_SIMULACION_MINUTOS = 4
INTERVALO_NUEVO_PEDIDO_SEG = 15

COLOR_SUELO = (139, 115, 85)
COLOR_MURO = (50, 50, 50)
COLOR_REJILLA = (80, 80, 80)
COLOR_RUTA = (100, 200, 100)
COLOR_CHEF = (208, 50, 53)
COLOR_TOMATE = (255, 0, 0)
COLOR_CEBOLLA = (255, 255, 255)
COLOR_INTERCEPTOR = (50, 120, 255)
COLOR_RUTA_INTERCEPTOR = (100, 150, 255)
COLOR_TABLA_CORTAR = (255, 255, 255)
COLOR_OLLAS = (81, 102, 103)
COLOR_LAVA_PLATOS = (132, 149, 113)
COLOR_BASURA = (73, 110, 39)
COLOR_ENTREGA = (146, 127, 121)
COLOR_RECOGE_PLATOS = (41, 29, 36)
COLOR_PLATO = (255,255,240)
COLOR_INGREDIENTE_BUENO   = (100, 220, 100)   # Verde: ingrediente fresco
COLOR_INGREDIENTE_PODRIDO = (120,  80,  20)   # Marrón: ingrediente podrido

TIEMPOS_ESPERA = {
    (13, 7): 1000,   # Ir por tomate (1 segundo)
    (15, 7): 1000,   # Ir por cebolla (1 segundo)
    (5, 7): 2000,    # Cortar en tabla 1 (2 segundos)
    (3, 7): 2000,    # Cortar en tabla 2 (2 segundos)
    (3, 3): 2000,    # Cocinar en olla 1 (2 segundos)
    (5, 3): 2000,    # Cocinar en olla 2 (2 segundos)
    (1, 3): 1000,    # Agarrar plato limpio (1 segundo)
    (1, 4): 1000,    # Agarrar plato limpio (1 segundo)
    (1, 5): 1000,    # Agarrar plato limpio (1 segundo)
    (16, 4): 1000,   # Entregar orden (1 segundos)
    (16, 5): 1000    # Entregar orden (1 segundos)
}