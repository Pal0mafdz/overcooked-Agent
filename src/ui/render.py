import pygame

from config import (
    COLOR_SUELO,
    COLOR_MURO,
    COLOR_REJILLA,
    COLOR_RUTA,
    COLOR_CHEF,
    COLOR_INTERCEPTOR,
    COLOR_DISTRACTION,
    COLOR_RUTA_INTERCEPTOR,
    dibujar_objetivos,
)


def render_frame(
    ventana,
    tam_celda: int,
    ancho_grid: int,
    alto_grid: int,
    mapa_actual: list[list[int]],
    chef_pos: list[int],
    ruta_chef: list[tuple[int, int]],
    zonas_olor: list[tuple[int, int]],
    pozo_descubierto: bool,
    pozos_pos: list[tuple[int, int]],
    interceptor_pos: list[int],
    ruta_interceptor: list[tuple[int, int]],
    tiempo_distraccion: float,
    distancia_al_chef: int,
    esta_persiguiendo: bool,
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
        for (px, py) in pozos_pos:
            pygame.draw.rect(
                ventana,
                (0, 0, 0),
                (px * tam_celda + 10, py * tam_celda + 10, tam_celda - 20, tam_celda - 20),
            )

    # Dibujar zona de distracción si está activa
    if tiempo_distraccion > 0:
        pygame.draw.circle(ventana, COLOR_DISTRACTION,
                          (chef_pos[0] * tam_celda + tam_celda//2,
                           chef_pos[1] * tam_celda + tam_celda//2),
                          tam_celda//2, 3)

    # Dibujar rutas
    for rx, ry in ruta_chef:
        pygame.draw.rect(ventana, COLOR_RUTA, (rx * tam_celda + 2, ry * tam_celda + 2, 60, 60))

    for rx, ry in ruta_interceptor:
        pygame.draw.rect(ventana, COLOR_RUTA_INTERCEPTOR, (rx * tam_celda + 2, ry * tam_celda + 2, 60, 60))

    # Dibujar al Chef Principal
    centro_chef = (chef_pos[0] * tam_celda + tam_celda // 2, chef_pos[1] * tam_celda + tam_celda // 2)
    pygame.draw.circle(ventana, COLOR_CHEF, centro_chef, 22)

    # Dibujar al Interceptor
    centro_interceptor = (interceptor_pos[0] * tam_celda + tam_celda // 2, interceptor_pos[1] * tam_celda + tam_celda // 2)
    pygame.draw.circle(ventana, COLOR_INTERCEPTOR, centro_interceptor, 18)

    # Mostrar información en la esquina
    font = pygame.font.SysFont(None, 24)
    info_texto = [
        f"Distancia: {distancia_al_chef}",
        f"Persiguiendo: {esta_persiguiendo}",
        f"Distracción: {tiempo_distraccion:.1f}s" if tiempo_distraccion > 0 else "Distracción: No"
    ]

    for i, texto in enumerate(info_texto):
        color_texto = (255, 255, 255)
        superficie_texto = font.render(texto, True, color_texto)
        ventana.blit(superficie_texto, (10, 10 + i * 25))
