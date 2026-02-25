import pygame

TAM_CELDA = 64
ANCHO_GRID = 18
ALTO_GRID = 11
VELOCIDAD_MOVIMIENTO = 10

COLOR_SUELO = (139, 115, 85)
COLOR_MURO = (50, 50, 50)
COLOR_REJILLA = (80, 80, 80)
COLOR_RUTA = (100, 200, 100)
COLOR_CHEF = (208, 50, 53)
COLOR_TOMATE = (255, 0, 0)
COLOR_CEBOLLA = (255, 255, 255)
COLOR_TABLA_CORTAR = (255, 255, 255)
COLOR_OLLAS = (81, 102, 103)
COLOR_LAVA_PLATOS = (132, 149, 113)
COLOR_BASURA = (73, 110, 39)
COLOR_ENTREGA = (146, 127, 121)
COLOR_RECOGE_PLATOS = (41, 29, 36)


def dibujar_objetivos(ventana, tam_celda):
    pygame.draw.rect(ventana, COLOR_TOMATE, (13 * tam_celda, 8 * tam_celda, tam_celda, tam_celda))
    pygame.draw.rect(ventana, COLOR_CEBOLLA, (15 * tam_celda, 8 * tam_celda, tam_celda, tam_celda))
    pygame.draw.rect(ventana, COLOR_TABLA_CORTAR, (3 * tam_celda, 8 * tam_celda, tam_celda, tam_celda))
    pygame.draw.rect(ventana, COLOR_TABLA_CORTAR, (5 * tam_celda, 8 * tam_celda, tam_celda, tam_celda))
    pygame.draw.rect(ventana, COLOR_OLLAS, (3 * tam_celda, 2 * tam_celda, tam_celda, tam_celda))
    pygame.draw.rect(ventana, COLOR_OLLAS, (5 * tam_celda, 2 * tam_celda, tam_celda, tam_celda))
    pygame.draw.rect(ventana, COLOR_LAVA_PLATOS, (0 * tam_celda, 6 * tam_celda, tam_celda, tam_celda))
    pygame.draw.rect(ventana, COLOR_BASURA, (16 * tam_celda, 2 * tam_celda, tam_celda, tam_celda))
    pygame.draw.rect(ventana, COLOR_ENTREGA, (17 * tam_celda, 4 * tam_celda, tam_celda, tam_celda))
    pygame.draw.rect(ventana, COLOR_ENTREGA, (17 * tam_celda, 5 * tam_celda, tam_celda, tam_celda))
    pygame.draw.rect(ventana, COLOR_RECOGE_PLATOS, (17 * tam_celda, 6 * tam_celda, tam_celda, tam_celda))
