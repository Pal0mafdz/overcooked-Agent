import pygame

from config import (
    COLOR_SUELO,
    COLOR_MURO,
    COLOR_REJILLA,
    COLOR_RUTA,
    COLOR_CHEF,
    dibujar_objetivos,
)


def render_frame(
    ventana,
    tam_celda: int,
    ancho_grid: int,
    alto_grid: int,
    mapa_actual: list[list[int]],
    chef_pos: list[int],
    ruta_disponible: list[tuple[int, int]],
    zonas_olor: list[tuple[int, int]],
    pozo_descubierto: bool,
    pozo_pos: tuple[int, int],
):
    ventana.fill((0, 0, 0))

    for fila in range(alto_grid):
        for col in range(ancho_grid):
            x, y = col * tam_celda, fila * tam_celda
            color_celda = COLOR_SUELO if mapa_actual[fila][col] == 1 else COLOR_MURO
            pygame.draw.rect(ventana, color_celda, (x, y, tam_celda, tam_celda))
            pygame.draw.rect(ventana, COLOR_REJILLA, (x, y, tam_celda, tam_celda), 1)

    dibujar_objetivos(ventana, tam_celda)

    for olor in zonas_olor:
        pygame.draw.rect(
            ventana,
            (180, 180, 80),
            (olor[0] * tam_celda + 4, olor[1] * tam_celda + 4, tam_celda - 8, tam_celda - 8),
        )

    if pozo_descubierto:
        pygame.draw.rect(
            ventana,
            (0, 0, 0),
            (pozo_pos[0] * tam_celda + 10, pozo_pos[1] * tam_celda + 10, tam_celda - 20, tam_celda - 20),
        )

    for rx, ry in ruta_disponible:
        pygame.draw.rect(ventana, COLOR_RUTA, (rx * tam_celda + 2, ry * tam_celda, 60, 60))

    centro_chef = (chef_pos[0] * tam_celda + tam_celda // 2, chef_pos[1] * tam_celda + tam_celda // 2)
    pygame.draw.circle(ventana, COLOR_CHEF, centro_chef, 22)
