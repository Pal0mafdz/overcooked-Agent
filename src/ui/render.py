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
    tiempo_restante_ms: int = 0,
    resumen_entrega: str | None = None,
    resumen_entrega_until: int = 0,
    mostrar_tiempo_agotado: bool = False,
    mostrar_resumen_final: bool = False,
    resumen_final_lineas: list[str] | None = None,
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

    # --- Temporizador Global ---
    if tiempo_restante_ms > 0:
        segs_totales = tiempo_restante_ms // 1000
        mins = segs_totales // 60
        segs = segs_totales % 60
        texto_timer = f"{mins:02d}:{segs:02d}"
        fuente_timer = pygame.font.SysFont(None, 48)
        color_t = (255, 100, 100) if segs_totales <= 30 else (255, 255, 255)
        surf_timer = fuente_timer.render(texto_timer, True, color_t)
        ventana.blit(surf_timer, (ancho_grid * tam_celda // 2 - surf_timer.get_width() // 2, 10))

    # --- Resumen de entrega (esquina inferior derecha) ---
    if resumen_entrega and (resumen_entrega_until == 0 or ahora <= resumen_entrega_until):
        panel_w = int(tam_celda * 8.3)
        panel_h = int(tam_celda * 3.1)
        panel_x = ancho_grid * tam_celda - panel_w - 12
        panel_y = alto_grid * tam_celda - panel_h - 12

        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel.fill((18, 24, 30, 220))
        ventana.blit(panel, (panel_x, panel_y))
        pygame.draw.rect(ventana, (255, 210, 90), (panel_x, panel_y, panel_w, panel_h), 2)

        fuente_titulo = pygame.font.SysFont(None, 36)
        fuente_detalle = pygame.font.SysFont(None, 26)
        titulo = fuente_titulo.render("Entrega", True, (255, 225, 120))
        ventana.blit(titulo, (panel_x + 10, panel_y + 8))

        max_detalle_w = panel_w - 20
        palabras = resumen_entrega.split(" ")
        lineas: list[str] = []
        actual = ""
        for palabra in palabras:
            candidato = palabra if not actual else f"{actual} {palabra}"
            if fuente_detalle.size(candidato)[0] <= max_detalle_w:
                actual = candidato
            else:
                if actual:
                    lineas.append(actual)
                actual = palabra
        if actual:
            lineas.append(actual)

        y_linea = panel_y + 52
        max_lineas = 4
        for linea in lineas[:max_lineas]:
            surf = fuente_detalle.render(linea, True, (235, 240, 245))
            ventana.blit(surf, (panel_x + 10, y_linea))
            y_linea += 27

    if mostrar_tiempo_agotado:
        overlay = pygame.Surface((ancho_grid * tam_celda, alto_grid * tam_celda), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 130))
        ventana.blit(overlay, (0, 0))

        fuente_tiempo = pygame.font.SysFont(None, 130)
        texto_tiempo = fuente_tiempo.render("¡TIEMPO!", True, (255, 80, 80))
        sombra = fuente_tiempo.render("¡TIEMPO!", True, (20, 20, 20))
        cx = ancho_grid * tam_celda // 2
        cy = alto_grid * tam_celda // 2
        ventana.blit(sombra, (cx - sombra.get_width() // 2 + 4, cy - sombra.get_height() // 2 + 4))
        ventana.blit(texto_tiempo, (cx - texto_tiempo.get_width() // 2, cy - texto_tiempo.get_height() // 2))

    if mostrar_resumen_final and resumen_final_lineas:
        overlay = pygame.Surface((ancho_grid * tam_celda, alto_grid * tam_celda), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 165))
        ventana.blit(overlay, (0, 0))

        panel_w = int(ancho_grid * tam_celda * 0.78)
        panel_h = int(alto_grid * tam_celda * 0.74)
        panel_x = (ancho_grid * tam_celda - panel_w) // 2
        panel_y = (alto_grid * tam_celda - panel_h) // 2

        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel.fill((17, 22, 28, 235))
        ventana.blit(panel, (panel_x, panel_y))
        pygame.draw.rect(ventana, (255, 210, 90), (panel_x, panel_y, panel_w, panel_h), 3)

        fuente_titulo = pygame.font.SysFont(None, 52)
        fuente_linea = pygame.font.SysFont(None, 32)
        fuente_hint = pygame.font.SysFont(None, 26)

        titulo = fuente_titulo.render("Resumen Final", True, (255, 225, 120))
        ventana.blit(titulo, (panel_x + (panel_w - titulo.get_width()) // 2, panel_y + 18))

        y = panel_y + 92
        for linea in resumen_final_lineas[:10]:
            surf = fuente_linea.render(linea, True, (235, 240, 245))
            ventana.blit(surf, (panel_x + 28, y))
            y += 36

        hint = fuente_hint.render("ESC para salir | R para reiniciar", True, (200, 205, 210))
        ventana.blit(hint, (panel_x + panel_w - hint.get_width() - 20, panel_y + panel_h - 36))

