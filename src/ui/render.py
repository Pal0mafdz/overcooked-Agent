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
    pozos_pos: list[tuple[int, int]],
    pisos_lentos: list[tuple[int, int]],

    platos_limpios: int,
    platos_sucios: int,
    lavando_plato: bool,
    progreso_lavado: float,
    esperando_accion: bool = False, 
    progreso_espera: float = 0.0    
):
    ventana.fill((0, 0, 0))
    fuente_coord = pygame.font.SysFont(None, 20)

    for fila in range(alto_grid):
        for col in range(ancho_grid):
            x, y = col * tam_celda, fila * tam_celda
            color_celda = COLOR_SUELO if mapa_actual[fila][col] == 1 else COLOR_MURO
            pygame.draw.rect(ventana, color_celda, (x, y, tam_celda, tam_celda))
            pygame.draw.rect(ventana, COLOR_REJILLA, (x, y, tam_celda, tam_celda), 1)


    for (x, y) in pisos_lentos:
        pygame.draw.rect(
            ventana,
            (100, 180, 255), 
            (x * tam_celda, y * tam_celda, tam_celda, tam_celda),
     )

    for col in range(ancho_grid):
        texto_col = fuente_coord.render(str(col), True, (255, 255, 255))
        x_col = col * tam_celda + (tam_celda - texto_col.get_width()) // 2
        ventana.blit(texto_col, (x_col, 2))

    for fila in range(alto_grid):
        texto_fila = fuente_coord.render(str(fila), True, (255, 255, 255))
        y_fila = fila * tam_celda + (tam_celda - texto_fila.get_height()) // 2
        ventana.blit(texto_fila, (4, y_fila))

    texto_limpios = fuente_coord.render(f"L:{platos_limpios}", True, (200, 240, 255))
    ventana.blit(texto_limpios, (1 * tam_celda + 4, 2 * tam_celda + 4))

    texto_sucios = fuente_coord.render(f"S:{platos_sucios}", True, (255, 220, 150))
    ventana.blit(texto_sucios, (16 * tam_celda + 4, 6 * tam_celda + 4))

    dibujar_objetivos(ventana, tam_celda)

    for olor in zonas_olor:
        pygame.draw.rect(ventana, (180, 180, 80), (olor[0] * tam_celda + 4, olor[1] * tam_celda + 4, tam_celda - 8, tam_celda - 8))

    if pozo_descubierto:
        for (px, py) in pozos_pos:
            pygame.draw.rect(ventana, (0, 0, 0), (px * tam_celda + 10, py * tam_celda + 10, tam_celda - 20, tam_celda - 20))

    for rx, ry in ruta_disponible:
        pygame.draw.rect(ventana, COLOR_RUTA, (rx * tam_celda + 2, ry * tam_celda, 60, 60))

    centro_chef = (chef_pos[0] * tam_celda + tam_celda // 2, chef_pos[1] * tam_celda + tam_celda // 2)
    pygame.draw.circle(ventana, COLOR_CHEF, centro_chef, 22)

    if lavando_plato:
        barra_x = 0 * tam_celda + 6
        barra_y = 6 * tam_celda + tam_celda - 14
        barra_w = tam_celda - 12
        barra_h = 8
        pygame.draw.rect(ventana, (40, 40, 40), (barra_x, barra_y, barra_w, barra_h))
        pygame.draw.rect(ventana, (120, 220, 120), (barra_x, barra_y, int(barra_w * progreso_lavado), barra_h))
        pygame.draw.rect(ventana, (220, 220, 220), (barra_x, barra_y, barra_w, barra_h), 1)

    if esperando_accion:
        barra_acc_x = chef_pos[0] * tam_celda
        barra_acc_y = chef_pos[1] * tam_celda - 12 
        barra_acc_w = tam_celda
        barra_acc_h = 8
        pygame.draw.rect(ventana, (40, 40, 40), (barra_acc_x, barra_acc_y, barra_acc_w, barra_acc_h))
        pygame.draw.rect(ventana, (255, 165, 0), (barra_acc_x, barra_acc_y, int(barra_acc_w * progreso_espera), barra_acc_h))
        pygame.draw.rect(ventana, (220, 220, 220), (barra_acc_x, barra_acc_y, barra_acc_w, barra_acc_h), 1)
