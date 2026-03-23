import pygame

from config import (
    COLOR_SUELO,
    COLOR_MURO,
    COLOR_REJILLA,
    COLOR_RUTA,
    COLOR_CHEF,
    COLOR_INTERCEPTOR,
    COLOR_RUTA_INTERCEPTOR,
    COLOR_INGREDIENTE_PODRIDO,
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
    interceptor_pos: list[int] | None = None,
    ruta_interceptor: list[tuple[int, int]] | None = None,
    interceptor_lavando: bool = False,
    interceptor_progreso_lavado: float = 0.0,
    interceptor_esperando: bool = False,
    interceptor_progreso_espera: float = 0.0,
    esperando_accion: bool = False, 
    progreso_espera: float = 0.0,
    chef_freeze_until: int = 0,
    ahora: int = 0,
    interception_happened: bool = False,
    map_surface: pygame.Surface | None = None,
    img_pozo: pygame.Surface | None = None,
    img_piso_mojado: pygame.Surface | None = None,
    img_chef: pygame.Surface | None = None,
    img_interceptor: pygame.Surface | None = None,
    ingrediente_podrido: bool = False,
):
    ventana.fill((0, 0, 0))
    fuente_coord = pygame.font.SysFont(None, 20)

    if map_surface:
        ventana.blit(map_surface, (0, 0))
    else:
        for fila in range(alto_grid):
            for col in range(ancho_grid):
                x, y = col * tam_celda, fila * tam_celda
                color_celda = COLOR_SUELO if mapa_actual[fila][col] == 1 else COLOR_MURO
                pygame.draw.rect(ventana, color_celda, (x, y, tam_celda, tam_celda))
                pygame.draw.rect(ventana, COLOR_REJILLA, (x, y, tam_celda, tam_celda), 1)


    for (x, y) in pisos_lentos:
        if img_piso_mojado:
            ventana.blit(img_piso_mojado, (x * tam_celda, y * tam_celda))
        else:
            pygame.draw.rect(
                ventana,
                (100, 180, 255), 
                (x * tam_celda, y * tam_celda, tam_celda, tam_celda),
            )


    texto_limpios = fuente_coord.render(f"L:{platos_limpios}", True, (200, 240, 255))
    ventana.blit(texto_limpios, (1 * tam_celda + 4, 2 * tam_celda + 4))

    texto_sucios = fuente_coord.render(f"S:{platos_sucios}", True, (255, 220, 150))
    ventana.blit(texto_sucios, (16 * tam_celda + 4, 6 * tam_celda + 4))

    # Genera la celda amarilla del olor
    # for olor in zonas_olor:
    #     pygame.draw.rect(ventana, (180, 180, 80), (olor[0] * tam_celda + 4, olor[1] * tam_celda + 4, tam_celda - 8, tam_celda - 8))

    if pozo_descubierto:
        for (px, py) in pozos_pos:
            if img_pozo:
                ventana.blit(img_pozo, (px * tam_celda, py * tam_celda))
            else:
                pygame.draw.rect(ventana, (0, 0, 0), (px * tam_celda + 10, py * tam_celda + 10, tam_celda - 20, tam_celda - 20))

    for rx, ry in ruta_disponible:
        pygame.draw.rect(ventana, COLOR_RUTA, (rx * tam_celda + 2, ry * tam_celda, 60, 60))
    # ruta del chef (verde por defecto) ya dibujada arriba

    if img_chef:
        ventana.blit(img_chef, (chef_pos[0] * tam_celda, chef_pos[1] * tam_celda))
    else:
        centro_chef = (chef_pos[0] * tam_celda + tam_celda // 2, chef_pos[1] * tam_celda + tam_celda // 2)
        pygame.draw.circle(ventana, COLOR_CHEF, centro_chef, 22)

    # Dibujar ruta y agente interceptor si se pasan
    if ruta_interceptor:
        for rx, ry in ruta_interceptor:
            pygame.draw.rect(ventana, COLOR_RUTA_INTERCEPTOR, (rx * tam_celda + 2, ry * tam_celda + 2, tam_celda - 4, tam_celda - 4))
    if interceptor_pos:
        if img_interceptor:
            ventana.blit(img_interceptor, (interceptor_pos[0] * tam_celda, interceptor_pos[1] * tam_celda))
        else:
            centro_int = (interceptor_pos[0] * tam_celda + tam_celda // 2, interceptor_pos[1] * tam_celda + tam_celda // 2)
            pygame.draw.circle(ventana, COLOR_INTERCEPTOR, centro_int, 18)

    # dibujar barra de lavado del interceptor
    if interceptor_lavando and interceptor_pos:
        barra_x = interceptor_pos[0] * tam_celda + 6
        barra_y = interceptor_pos[1] * tam_celda + tam_celda - 14
        barra_w = tam_celda - 12
        barra_h = 8
        pygame.draw.rect(ventana, (40, 40, 40), (barra_x, barra_y, barra_w, barra_h))
        pygame.draw.rect(ventana, (120, 180, 255), (barra_x, barra_y, int(barra_w * interceptor_progreso_lavado), barra_h))
        pygame.draw.rect(ventana, (220, 220, 220), (barra_x, barra_y, barra_w, barra_h), 1)

    if interceptor_esperando and interceptor_pos:
        barra_acc_x = interceptor_pos[0] * tam_celda
        barra_acc_y = interceptor_pos[1] * tam_celda - 12 
        barra_acc_w = tam_celda
        barra_acc_h = 8
        pygame.draw.rect(ventana, (40, 40, 40), (barra_acc_x, barra_acc_y, barra_acc_w, barra_acc_h))
        pygame.draw.rect(ventana, (100, 150, 255), (barra_acc_x, barra_acc_y, int(barra_acc_w * interceptor_progreso_espera), barra_acc_h))
        pygame.draw.rect(ventana, (220, 220, 220), (barra_acc_x, barra_acc_y, barra_acc_w, barra_acc_h), 1)

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

    # Mostrar indicador de congelamiento del chef
    if chef_freeze_until and ahora:
        restante = max(0, chef_freeze_until - ahora)
        total = 3000
        if restante > 0:
            # overlay tint on chef tile
            chef_tile = (chef_pos[0] * tam_celda, chef_pos[1] * tam_celda, tam_celda, tam_celda)
            s = pygame.Surface((tam_celda, tam_celda), pygame.SRCALPHA)
            s.fill((60, 140, 200, 120))
            ventana.blit(s, (chef_tile[0], chef_tile[1]))

            # freeze progress bar above chef
            barra_x = chef_pos[0] * tam_celda
            barra_y = chef_pos[1] * tam_celda - 22
            barra_w = tam_celda
            barra_h = 8
            pygame.draw.rect(ventana, (30, 30, 30), (barra_x, barra_y, barra_w, barra_h))
            # barra de congelamiento (rosa)
            pygame.draw.rect(ventana, (255, 105, 180), (barra_x, barra_y, int(barra_w * (restante / total)), barra_h))
            pygame.draw.rect(ventana, (220, 220, 220), (barra_x, barra_y, barra_w, barra_h), 1)

    # flash indicator when interception happened this frame
    if interception_happened:
        fx = chef_pos[0] * tam_celda + tam_celda // 2
        fy = chef_pos[1] * tam_celda + tam_celda // 2
        pygame.draw.circle(ventana, (255, 240, 50), (fx, fy), 28, 4)

    # --- Indicador de ingrediente podrido ---
    if ingrediente_podrido:
        # Overlay marrón semitransparente sobre la celda del chef
        s = pygame.Surface((tam_celda, tam_celda), pygame.SRCALPHA)
        s.fill((*COLOR_INGREDIENTE_PODRIDO, 160))
        ventana.blit(s, (chef_pos[0] * tam_celda, chef_pos[1] * tam_celda))
        # Texto flotante "!Podrido!" encima del chef
        fuente_podrido = pygame.font.SysFont(None, 22)
        texto_podrido = fuente_podrido.render("¡Podrido!", True, (255, 230, 80))
        ventana.blit(texto_podrido, (chef_pos[0] * tam_celda + 2, chef_pos[1] * tam_celda - 20))
