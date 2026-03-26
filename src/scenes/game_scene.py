import copy
import pygame
import pytmx

from config import (
    TAM_CELDA, ANCHO_GRID, ALTO_GRID, VELOCIDAD_MOVIMIENTO, TIEMPOS_ESPERA,
    COLOR_SUELO, COLOR_MURO, COLOR_REJILLA, PROB_INGREDIENTE_PODRIDO,
    TIEMPO_SIMULACION_MINUTOS, INTERVALO_NUEVO_PEDIDO_SEG
)
from src.systems.maps import MAPA_ORIGINAL, generar_pozos_y_olores
from src.systems.orders import (
    PLATOS,
    ENTREGAS,
    OLLAS,
    TABLAS,
    INGREDIENTES,
    generar_pedidos,
    expandir_objetivos,
    generar_objetivos_interceptor,
    verificar_ingrediente_podrido,
    calcular_puntaje_comida,
    calcular_limpieza_por_platos,
    evaluar_propina_difusa,
)
from src.systems.pathfinding import Pathfinder
from src.ui.render import render_frame
from src.entities.interceptor import Interceptor
from src.systems.maps import generar_pisos_lentos

class GameScene:
    def __init__(self, ventana, reloj, ordenes: int):
        self.ventana = ventana
        self.reloj = reloj
        self.ordenes = ordenes
        
        # --- NUEVO: PANTALLA VIRTUAL ---
        self.ancho_logico = ANCHO_GRID * TAM_CELDA
        self.alto_logico = ALTO_GRID * TAM_CELDA
        self.pantalla_virtual = pygame.Surface((self.ancho_logico, self.alto_logico))
        
        # --- CARGAR TMX MAPA ---
        self.tmx_data = pytmx.load_pygame("assets/map/mapa.tmx")
        self.map_surface = pygame.Surface((self.ancho_logico, self.alto_logico))
        self.map_surface.fill((0, 0, 0))
        
        for fila in range(ALTO_GRID):
            for col in range(ANCHO_GRID):
                x_celda, y_celda = col * TAM_CELDA, fila * TAM_CELDA
                color_celda = COLOR_SUELO if MAPA_ORIGINAL[fila][col] == 1 else COLOR_MURO
                pygame.draw.rect(self.map_surface, color_celda, (x_celda, y_celda, TAM_CELDA, TAM_CELDA))
                pygame.draw.rect(self.map_surface, COLOR_REJILLA, (x_celda, y_celda, TAM_CELDA, TAM_CELDA), 1)

        for layer in self.tmx_data.visible_layers:
            if isinstance(layer, pytmx.TiledTileLayer):
                for x, y, gid in layer:
                    tile = self.tmx_data.get_tile_image_by_gid(gid)
                    if tile:
                        scale_x = TAM_CELDA / self.tmx_data.tilewidth
                        scale_y = TAM_CELDA / self.tmx_data.tileheight
                        
                        new_w = int(tile.get_width() * scale_x)
                        new_h = int(tile.get_height() * scale_y)
                        
                        tile_scaled = pygame.transform.scale(tile, (new_w, new_h))
                        
                        blit_x = x * TAM_CELDA
                        blit_y = y * TAM_CELDA + TAM_CELDA - new_h
                        
                        self.map_surface.blit(tile_scaled, (blit_x, blit_y))
        
        # Direcciones: 0=Abajo, 1=Arriba, 2=Derecha, 3=Izquierda
        self.img_chef_dir = []
        
        img_front = pygame.image.load("assets/chef_01/chef01_front.png").convert_alpha()
        self.img_chef_dir.append(pygame.transform.scale(img_front, (TAM_CELDA, TAM_CELDA)))
        
        img_back = pygame.image.load("assets/chef_01/chef01_back.png").convert_alpha()
        self.img_chef_dir.append(pygame.transform.scale(img_back, (TAM_CELDA, TAM_CELDA)))
        
        img_side = pygame.image.load("assets/chef_01/chef01_side.png").convert_alpha()
        self.img_chef_dir.append(pygame.transform.scale(img_side, (TAM_CELDA, TAM_CELDA)))
        
        img_side_flipped = pygame.transform.flip(img_side, True, False)
        self.img_chef_dir.append(pygame.transform.scale(img_side_flipped, (TAM_CELDA, TAM_CELDA)))

        self.img_interceptor_dir = []
        
        img_int_front = pygame.image.load("assets/chef_02/chef02_front.png").convert_alpha()
        self.img_interceptor_dir.append(pygame.transform.scale(img_int_front, (TAM_CELDA, TAM_CELDA)))
        
        img_int_back = pygame.image.load("assets/chef_02/chef02_back.png").convert_alpha()
        self.img_interceptor_dir.append(pygame.transform.scale(img_int_back, (TAM_CELDA, TAM_CELDA)))
        
        img_int_side = pygame.image.load("assets/chef_02/chef02_side.png").convert_alpha()
        self.img_interceptor_dir.append(pygame.transform.scale(img_int_side, (TAM_CELDA, TAM_CELDA)))
        
        img_int_side_flipped = pygame.transform.flip(img_int_side, True, False)
        self.img_interceptor_dir.append(pygame.transform.scale(img_int_side_flipped, (TAM_CELDA, TAM_CELDA)))

        self.img_pozo = pygame.image.load("assets/obstacles/pozo.png").convert_alpha()
        self.img_pozo = pygame.transform.scale(self.img_pozo, (TAM_CELDA, TAM_CELDA))

        self.img_piso_mojado = pygame.image.load("assets/obstacles/piso_mojado.png").convert_alpha()
        self.img_piso_mojado = pygame.transform.scale(self.img_piso_mojado, (TAM_CELDA, TAM_CELDA))

    def run(self) -> bool:
        objetivo_platos_sucios = (16, 6)
        objetivo_lavado = (1, 6)
        retraso_plato_sucio_ms = 15000
        tiempo_lavado_ms = 5000

        mapa_actual = copy.deepcopy(MAPA_ORIGINAL)
        chef_pos = [1, 3]
        chef_direccion = 0  # Start facing front (down)
        ruta_disponible: list[tuple[int, int]] = []
        contador_frames = 0
        index_objetivo = 0
        ruta_objetivo = None
        ahora = pygame.time.get_ticks()

        platos_limpios = 3
        platos_sucios = 0
        temporizadores_sucios: list[int] = []

        en_reposicion_plato = False
        buscando_plato_sucio = False
        tiene_plato_sucio = False
        lavando_plato = False
        inicio_lavado = 0
        progreso_lavado = 0.0
        esperando_plato_sucio = False

        esperando_accion = False
        inicio_espera = 0
        tiempo_espera_actual = 0
        progreso_espera = 0.0

        ingrediente_podrido = False   # True durante el frame en que se detecta un ingrediente podrido
        podrido_flash_until = 0       # Timestamp hasta el cual mostrar el indicador de podrido

        ingredientes_platillo_chef = 0
        podridos_platillo_chef = 0
        inicio_platillo_chef = 0

        ingredientes_platillo_interceptor = 0
        podridos_platillo_interceptor = 0
        inicio_platillo_interceptor = 0

        resumen_entrega = ""
        resumen_entrega_until = 0
        mostrar_tiempo_agotado_until = 0
        resumen_final_lineas: list[str] = []
        mostrar_resumen_final = False

        entregas_chef = 0
        entregas_interceptor = 0
        propinas_totales_monedas = 0
        acumulado_comida = 0.0
        acumulado_limpieza = 0.0
        acumulado_tiempo = 0.0
        acumulado_podridos = 0
        acumulado_ingredientes = 0

        def limpieza_a_palabra(limpieza_num: float) -> str:
            if limpieza_num >= 80:
                return "Asquerosa"
            if limpieza_num >= 50:
                return "Descuidada"
            if limpieza_num >= 15:
                return "Aceptable"
            return "Impecable"

        def construir_resumen_final() -> list[str]:
            total_entregas = entregas_chef + entregas_interceptor
            prom_comida = (acumulado_comida / total_entregas) if total_entregas else 0.0
            prom_limpieza = (acumulado_limpieza / total_entregas) if total_entregas else 0.0
            prom_tiempo = (acumulado_tiempo / total_entregas) if total_entregas else 0.0
            tasa_podridos = (acumulado_podridos / acumulado_ingredientes * 100.0) if acumulado_ingredientes else 0.0

            return [
                f"Platos entregados: {total_entregas}",
                f"Chef: {entregas_chef} | Interceptor: {entregas_interceptor}",
                f"Propinas ganadas: {propinas_totales_monedas} monedas",
                f"Comida promedio: {prom_comida:.2f}/5",
                f"Limpieza promedio: {limpieza_a_palabra(prom_limpieza)}",
                f"Tiempo promedio por pedido: {prom_tiempo:.1f}s",
                f"Ingredientes podridos usados: {acumulado_podridos}/{acumulado_ingredientes} ({tasa_podridos:.1f}%)",
                f"Estado final de cocina: {limpieza_a_palabra(calcular_limpieza_por_platos(platos_sucios, len(temporizadores_sucios), capacidad=3))}",
            ]

        lista_pedidos = generar_pedidos(self.ordenes)
        lista_objetivos = expandir_objetivos(lista_pedidos)
        
        # Generar objetivos independientes para el interceptor
        lista_objetivos_interceptor = generar_objetivos_interceptor(self.ordenes)

        pozos_pos, zonas_olor = generar_pozos_y_olores(
            mapa_actual,
            chef_pos,
            lista_objetivos,
            cantidad_pozos=3,
            celdas_prohibidas=PLATOS,
        )
        for (px, py) in pozos_pos:
            mapa_actual[py][px] = 0
        pozo_descubierto = True

        pisos_lentos = generar_pisos_lentos(
            mapa_actual,
            chef_pos,
            lista_objetivos,
            cantidad=3,
            celdas_prohibidas=PLATOS,
        )

  
        zona_lenta = set()

        for (x, y) in pisos_lentos:
            zona_lenta.add((x, y))

            for dx, dy in [(0,1),(0,-1),(1,0),(-1,0)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < ANCHO_GRID and 0 <= ny < ALTO_GRID:
                    zona_lenta.add((nx, ny))


        print("Zonas de piso lento", zona_lenta)
        print("\n" + "=" * 40)
        print("NUEVA SIMULACIÓN INICIADA")
        print(f"DEBUG: Pozos generados en {pozos_pos}")
        if lista_pedidos:
            print(f"Pedidos Chef: {lista_pedidos}")
            print(f"Objetivos Chef: {lista_objetivos}")
            print(f"Objetivos Interceptor: {lista_objetivos_interceptor}")
            print(f"Pedido actual: {lista_pedidos[0]}")
        print("=" * 40 + "\n")

        pathfinder = Pathfinder(mapa_actual)

        # Interceptor: instancia separada que maneja su ruta y estados
        def encontrar_celda_libre(mapa, evitar: set | None = None):
            evitar = set(evitar or [])
            for y in range(len(mapa)):
                for x in range(len(mapa[0])):
                    if mapa[y][x] == 1 and (x, y) not in evitar and (x, y) != tuple(chef_pos):
                        return [x, y]
            return [1, 3]

        interceptor_start = encontrar_celda_libre(mapa_actual, evitar=set(lista_objetivos))
        # El interceptor usa su propia lista de objetivos para evitar traslape con el chef
        interceptor = Interceptor(interceptor_start, mapa_actual, lista_objetivos_interceptor)
        chef_freeze_until = 0

        def es_objetivo_valido(valor) -> bool:
            return (
                isinstance(valor, tuple)
                and len(valor) == 2
                and all(isinstance(v, int) for v in valor)
            )

        def registrar_entrega(tiempo_actual: int):
            total_pendiente = platos_sucios + len(temporizadores_sucios)
            if total_pendiente < 3:
                temporizadores_sucios.append(tiempo_actual + retraso_plato_sucio_ms)

        inicio_simulacion = pygame.time.get_ticks()
        duracion_max_ms = TIEMPO_SIMULACION_MINUTOS * 60 * 1000
        siguiente_pedido_ms = inicio_simulacion + (INTERVALO_NUEVO_PEDIDO_SEG * 1000)
        simulacion_activa = True

        ejecutando = True
        while ejecutando:
            ahora = pygame.time.get_ticks()

            transcurrido_global = ahora - inicio_simulacion
            if transcurrido_global >= duracion_max_ms:
                if simulacion_activa:
                    print(f"Simulación finalizada por tiempo ({TIEMPO_SIMULACION_MINUTOS} minutos completados). Pantalla congelada.")
                    simulacion_activa = False
                    mostrar_tiempo_agotado_until = ahora + 3000
                    resumen_final_lineas = construir_resumen_final()
                    mostrar_resumen_final = False
                tiempo_restante_ms = 0
            else:
                tiempo_restante_ms = duracion_max_ms - transcurrido_global

            if not simulacion_activa:
                for evento in pygame.event.get():
                    if evento.type == pygame.QUIT:
                        return False
                    if evento.type == pygame.KEYDOWN:
                        if evento.key == pygame.K_r:
                            return True
                        if evento.key == pygame.K_ESCAPE:
                            return False

                if mostrar_tiempo_agotado_until and ahora >= mostrar_tiempo_agotado_until:
                    mostrar_resumen_final = True
                
                interceptor_lavando = interceptor.lavando
                interceptor_progreso_lavado = interceptor.progreso_lavado
                interceptor_esperando = interceptor.esperando
                interceptor_progreso_espera = getattr(interceptor, 'progreso_espera', 0.0)

                render_frame(
                    self.pantalla_virtual, 
                    TAM_CELDA,
                    ANCHO_GRID,
                    ALTO_GRID,
                    mapa_actual,
                    chef_pos,
                    ruta_disponible,
                    zonas_olor,
                    pozo_descubierto,
                    pozos_pos,
                    pisos_lentos,
                    platos_limpios,
                    platos_sucios,
                    lavando_plato,
                    progreso_lavado,
                    interceptor.pos,
                    interceptor.ruta,
                    interceptor_lavando,
                    interceptor_progreso_lavado,
                    interceptor_esperando,
                    interceptor_progreso_espera,
                    esperando_accion, 
                    progreso_espera,
                    chef_freeze_until,
                    ahora,
                    False,
                    self.map_surface,
                    self.img_pozo,
                    self.img_piso_mojado,
                    self.img_chef_dir[chef_direccion],
                    self.img_interceptor_dir[interceptor.direccion],
                    ingrediente_podrido,
                    tiempo_restante_ms,
                    resumen_entrega,
                    resumen_entrega_until,
                    bool(mostrar_tiempo_agotado_until and ahora < mostrar_tiempo_agotado_until),
                    mostrar_resumen_final,
                    resumen_final_lineas,
                )
                
                self.ventana.blit(self.pantalla_virtual, (0, 0))
                pygame.display.flip()
                self.reloj.tick(60)
                continue

            if ahora >= siguiente_pedido_ms:
                nuevo_pedido_chef = generar_pedidos(1)
                nuevos_objetivos_chef = expandir_objetivos(nuevo_pedido_chef)
                lista_objetivos.extend(nuevos_objetivos_chef)
                
                nuevos_objetivos_int = generar_objetivos_interceptor(1)
                interceptor.lista_objetivos.extend(nuevos_objetivos_int)
                
                siguiente_pedido_ms += (INTERVALO_NUEVO_PEDIDO_SEG * 1000)
                print(f"Añadido nuevo pedido tras {INTERVALO_NUEVO_PEDIDO_SEG}s (total objetivos chef aumentados).")

            # Apagar el flash de ingrediente podrido cuando ya pasó su tiempo
            if ahora >= podrido_flash_until:
                ingrediente_podrido = False

            temporizadores_restantes: list[int] = []
            for tiempo_objetivo in temporizadores_sucios:
                if ahora >= tiempo_objetivo:
                    if platos_sucios < 3:
                        platos_sucios += 1
                        print(f"Plato sucio disponible en (17,6). Total sucios: {platos_sucios}")
                else:
                    temporizadores_restantes.append(tiempo_objetivo)
            temporizadores_sucios = temporizadores_restantes

            if esperando_accion:
                transcurrido_espera = ahora - inicio_espera
                progreso_espera = min(1.0, transcurrido_espera / tiempo_espera_actual)
                if transcurrido_espera >= tiempo_espera_actual:
                    esperando_accion = False
                    progreso_espera = 0.0
                    index_objetivo += 1  # Avanzamos al siguiente objetivo SOLO cuando termina
                    ruta_disponible = []
                    ruta_objetivo = None
                    contador_frames = 0
                    print(f"Acción completada en {objetivo_actual}")

            if lavando_plato:
                transcurrido = ahora - inicio_lavado
                progreso_lavado = min(1.0, transcurrido / tiempo_lavado_ms)
                if transcurrido >= tiempo_lavado_ms:
                    lavando_plato = False
                    progreso_lavado = 0.0
                    tiene_plato_sucio = False
                    platos_limpios += 1
                    en_reposicion_plato = False
                    esperando_plato_sucio = False
                    index_objetivo += 1
                    ruta_disponible = []
                    ruta_objetivo = None
                    contador_frames = 0
                    print(f"Lavado completado. Platos limpios disponibles: {platos_limpios}")

            

            if index_objetivo < len(lista_objetivos):
                objetivo_actual = lista_objetivos[index_objetivo]
            else:
                objetivo_actual = None

            if objetivo_actual is not None and not es_objetivo_valido(objetivo_actual):
                print(f"Objetivo invalido ({objetivo_actual}), se omite.")
                index_objetivo += 1
                ruta_disponible = []
                ruta_objetivo = None
                continue

            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    return False

                if evento.type == pygame.KEYDOWN:
                    if evento.key == pygame.K_r:
                        return True
                    if evento.key == pygame.K_ESCAPE:
                        return False

                if evento.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = pygame.mouse.get_pos()

                    cx, cy = mx // TAM_CELDA, my // TAM_CELDA
                    if 0 <= cx < ANCHO_GRID and 0 <= cy < ALTO_GRID:
                        if mapa_actual[cy][cx] == 1:
                            if evento.button == 3:
                                chef_pos = [cx, cy]
                                ruta_disponible = []
                                ruta_objetivo = None

            if (
                objetivo_actual in PLATOS
                and platos_limpios == 0
                and not en_reposicion_plato
                and not lavando_plato
            ):
                if platos_sucios > 0:
                    lista_objetivos[index_objetivo:index_objetivo] = [objetivo_platos_sucios, objetivo_lavado]
                    en_reposicion_plato = True
                    buscando_plato_sucio = True
                    esperando_plato_sucio = False
                    ruta_disponible = []
                    ruta_objetivo = None
                    contador_frames = 0
                    objetivo_actual = lista_objetivos[index_objetivo]
                    print("Sin platos limpios. Yendo por plato sucio para lavar.")
                else:
                    if not esperando_plato_sucio:
                        print("Sin platos limpios ni sucios disponibles. Esperando que aparezca uno sucio...")
                    esperando_plato_sucio = True
                    ruta_disponible = []
                    ruta_objetivo = None

            while (
                objetivo_actual is not None
                and tuple(chef_pos) == objetivo_actual
                and not lavando_plato
                and not esperando_accion
            ):
                if en_reposicion_plato and buscando_plato_sucio and objetivo_actual == objetivo_platos_sucios:
                    if platos_sucios > 0:
                        platos_sucios -= 1
                        tiene_plato_sucio = True
                        buscando_plato_sucio = False
                        print(f"Plato sucio recogido en (17,6). Sucios restantes: {platos_sucios}")

                elif en_reposicion_plato and tiene_plato_sucio and objetivo_actual == objetivo_lavado:
                    lavando_plato = True
                    inicio_lavado = ahora
                    progreso_lavado = 0.0
                    ruta_disponible = []
                    ruta_objetivo = None
                    contador_frames = 0
                    print("Lavando plato en (0,6)...")
                    break

                if objetivo_actual in PLATOS and platos_limpios > 0:
                    platos_limpios -= 1
                    print(f"Plato limpio tomado. Platos limpios restantes: {platos_limpios}")

                # --- Verificación de ingrediente podrido ---
                if objetivo_actual in INGREDIENTES:
                    if ingredientes_platillo_chef == 0:
                        inicio_platillo_chef = ahora
                    ingredientes_platillo_chef += 1
                    if verificar_ingrediente_podrido(PROB_INGREDIENTE_PODRIDO):
                        print(f"¡Ingrediente PODRIDO en {objetivo_actual}! Continuando pedido con él...")
                        podridos_platillo_chef += 1
                        ingrediente_podrido = True
                        podrido_flash_until = ahora + 1500  # Mostrar indicador 1.5s
                        # Antes se reinsertaba para recoger de nuevo, ahora el chef se lo queda.
                    else:
                        print(f"Ingrediente fresco recogido en {objetivo_actual}.")

                if objetivo_actual in ENTREGAS:
                    tiempo_platillo_seg = max(0.0, (ahora - inicio_platillo_chef) / 1000.0) if inicio_platillo_chef else 0.0
                    puntaje_comida = calcular_puntaje_comida(ingredientes_platillo_chef, podridos_platillo_chef)
                    puntaje_limpieza = calcular_limpieza_por_platos(platos_sucios, len(temporizadores_sucios), capacidad=3)
                    evaluacion_propina = evaluar_propina_difusa(tiempo_platillo_seg, puntaje_comida, puntaje_limpieza)
                    limpieza_txt = limpieza_a_palabra(puntaje_limpieza)
                    monedas_propina = int(round(evaluacion_propina['propina']))

                    entregas_chef += 1
                    propinas_totales_monedas += monedas_propina
                    acumulado_comida += puntaje_comida
                    acumulado_limpieza += puntaje_limpieza
                    acumulado_tiempo += tiempo_platillo_seg
                    acumulado_podridos += podridos_platillo_chef
                    acumulado_ingredientes += ingredientes_platillo_chef

                    registrar_entrega(ahora)
                    print(
                        "Pedido entregado. "
                        f"Comida={puntaje_comida:.2f}/5 (podridos {podridos_platillo_chef}/{ingredientes_platillo_chef}), "
                        f"Tiempo={tiempo_platillo_seg:.1f}s, Limpieza={limpieza_txt}, "
                        f"Propina={monedas_propina} monedas"
                    )
                    resumen_entrega = (
                        f"Comida={puntaje_comida:.2f}/5 | Podridos {podridos_platillo_chef}/{ingredientes_platillo_chef} | "
                        f"Tiempo={tiempo_platillo_seg:.1f}s | Limpieza={limpieza_txt} | Propina={monedas_propina} monedas"
                    )
                    resumen_entrega_until = ahora + 9000

                    ingredientes_platillo_chef = 0
                    podridos_platillo_chef = 0
                    inicio_platillo_chef = 0

                if objetivo_actual in TIEMPOS_ESPERA:
                    esperando_accion = True
                    inicio_espera = ahora
                    tiempo_espera_actual = TIEMPOS_ESPERA[objetivo_actual]
                    ruta_disponible = []
                    ruta_objetivo = None
                    contador_frames = 0
                    print(f"Esperando {tiempo_espera_actual/1000}s en {objetivo_actual}...")
                    break 
                else:
                    index_objetivo += 1
                    if index_objetivo < len(lista_objetivos):
                        objetivo_actual = lista_objetivos[index_objetivo]
                        ruta_disponible = []
                        ruta_objetivo = None
                        contador_frames = 0
                    else:
                        objetivo_actual = None
                        print("Todos los pedidos completados.")
            if objetivo_actual is not None and not es_objetivo_valido(objetivo_actual):
                print(f"Objetivo invalido ({objetivo_actual}), se omite.")
                index_objetivo += 1
                ruta_objetivo = None
                ruta_disponible = []
                continue
            if (
                not lavando_plato
                and objetivo_actual is not None
                and (ruta_objetivo != objetivo_actual or not ruta_disponible)
            ):
                # Bloquear posición actual del interceptor temporalmente
                ix, iy = interceptor.pos
                val_original = mapa_actual[iy][ix]
                if tuple(interceptor.pos) != objetivo_actual:
                    mapa_actual[iy][ix] = 0
                pathfinder.set_matrix(mapa_actual)

                ruta_disponible = pathfinder.obtener_ruta(chef_pos, objetivo_actual)

                # Fallback: intentar sin bloquear si no hubo ruta
                if not ruta_disponible and val_original == 1 and tuple(interceptor.pos) != objetivo_actual:
                    mapa_actual[iy][ix] = 1
                    pathfinder.set_matrix(mapa_actual)
                    ruta_disponible = pathfinder.obtener_ruta(chef_pos, objetivo_actual)

                # Siempre restaurar el valor original
                mapa_actual[iy][ix] = val_original
                pathfinder.set_matrix(mapa_actual)

                ruta_objetivo = objetivo_actual
                contador_frames = 0

                if not ruta_disponible and tuple(chef_pos) != objetivo_actual:
                    print(f"Objetivo inalcanzable, saltando: {objetivo_actual}")
                    index_objetivo += 1
                    ruta_objetivo = None
                    ruta_disponible = []

                 
        
            if ruta_disponible and not lavando_plato:
                contador_frames += 1
                velcodad_actual = VELOCIDAD_MOVIMIENTO
                if tuple(chef_pos) in zona_lenta:
                    velcodad_actual = VELOCIDAD_MOVIMIENTO * 3
                if contador_frames >= velcodad_actual and ahora >= chef_freeze_until:
                    siguiente_paso = ruta_disponible[0]

                    # Recálculo dinámico si el interceptor está en el siguiente paso
                    if list(siguiente_paso) == interceptor.pos:
                        ruta_disponible = []
                        contador_frames = 0
                    else:
                        siguiente_paso = ruta_disponible.pop(0)

                        # Determinar dirección
                        if siguiente_paso[0] > chef_pos[0]:
                            chef_direccion = 2  # Derecha
                        elif siguiente_paso[0] < chef_pos[0]:
                            chef_direccion = 3  # Izquierda
                        elif siguiente_paso[1] < chef_pos[1]:
                            chef_direccion = 1  # Arriba
                        elif siguiente_paso[1] > chef_pos[1]:
                            chef_direccion = 0  # Abajo

                        chef_pos[0], chef_pos[1] = siguiente_paso[0], siguiente_paso[1]
                        contador_frames = 0

                    if not ruta_disponible:
                        print(f"Destino: {chef_pos}")
                        if objetivo_actual is not None and tuple(chef_pos) == objetivo_actual:
                            ruta_objetivo = None

            # Interceptor update (mueve y devuelve eventos)
            eventos = interceptor.update(
                ahora,
                chef_pos,
                ruta_disponible,
                mapa_actual,
                lista_objetivos_interceptor,
                zona_lenta,
                tiempo_lavado_ms,
                VELOCIDAD_MOVIMIENTO,
                TIEMPOS_ESPERA,
                ruta_objetivo,            # <-- olla que el chef tiene como objetivo actual
            )

            ruta_interceptor = interceptor.ruta
            interceptor_pos = interceptor.pos

            if 'freeze_until' in eventos:
                chef_freeze_until = eventos['freeze_until']
                print("Interceptor adjacent: congelando al chef")
                # Pausar temporizadores del chef durante la congelación (no cancelarlos)
                freeze_dur = chef_freeze_until - ahora
                if esperando_accion:
                    inicio_espera += freeze_dur
                    print("Pausando progreso de espera del chef durante la congelación.")
                if lavando_plato:
                    inicio_lavado += freeze_dur
                    print("Pausando progreso de lavado del chef durante la congelación.")

            if 'arrived' in eventos:
                objetivo_interceptor = eventos['arrived']
                if objetivo_interceptor in TIEMPOS_ESPERA:
                    interceptor.start_wait(TIEMPOS_ESPERA[objetivo_interceptor], ahora)
                    print(f"Interceptor esperando {TIEMPOS_ESPERA[objetivo_interceptor]/1000}s en {objetivo_interceptor}...")
                else:
                    if objetivo_interceptor == objetivo_platos_sucios:
                        if platos_sucios > 0:
                            platos_sucios -= 1
                            print(f"Interceptor recogió plato sucio en {objetivo_interceptor}. Sucios restantes: {platos_sucios}")
                            interceptor.advance_objetivo()
                    elif objetivo_interceptor == objetivo_lavado:
                        interceptor.start_washing(ahora)
                        print("Interceptor lavando plato...")
                    elif objetivo_interceptor in PLATOS:
                        if platos_limpios > 0:
                            platos_limpios -= 1
                            print(f"Interceptor tomó plato limpio en {objetivo_interceptor}. Platos limpios restantes: {platos_limpios}")
                            interceptor.advance_objetivo()
                    elif objetivo_interceptor in ENTREGAS:
                        registrar_entrega(ahora)
                        print("Interceptor entregó un pedido. Platos sucios llegarán pronto.")
                        interceptor.advance_objetivo()

                    # --- Verificación de ingrediente podrido para el interceptor ---
                    if objetivo_interceptor in INGREDIENTES:
                        if ingredientes_platillo_interceptor == 0:
                            inicio_platillo_interceptor = ahora
                        ingredientes_platillo_interceptor += 1
                        if verificar_ingrediente_podrido(PROB_INGREDIENTE_PODRIDO):
                            print(f"¡Ingrediente PODRIDO en {objetivo_interceptor}! Interceptor continúa pedido con él...")
                            podridos_platillo_interceptor += 1
                            # Antes se usaba interceptor.reinsertar_objetivo(), ahora se lo queda.
                        else:
                            print(f"Interceptor recogió ingrediente fresco en {objetivo_interceptor}.")

                    if objetivo_interceptor in ENTREGAS:
                        tiempo_platillo_seg_int = max(0.0, (ahora - inicio_platillo_interceptor) / 1000.0) if inicio_platillo_interceptor else 0.0
                        puntaje_comida_int = calcular_puntaje_comida(ingredientes_platillo_interceptor, podridos_platillo_interceptor)
                        puntaje_limpieza_int = calcular_limpieza_por_platos(platos_sucios, len(temporizadores_sucios), capacidad=3)
                        evaluacion_propina_int = evaluar_propina_difusa(tiempo_platillo_seg_int, puntaje_comida_int, puntaje_limpieza_int)
                        limpieza_txt_int = limpieza_a_palabra(puntaje_limpieza_int)
                        monedas_propina_int = int(round(evaluacion_propina_int['propina']))

                        entregas_interceptor += 1
                        propinas_totales_monedas += monedas_propina_int
                        acumulado_comida += puntaje_comida_int
                        acumulado_limpieza += puntaje_limpieza_int
                        acumulado_tiempo += tiempo_platillo_seg_int
                        acumulado_podridos += podridos_platillo_interceptor
                        acumulado_ingredientes += ingredientes_platillo_interceptor

                        print(
                            "Entrega interceptor. "
                            f"Comida={puntaje_comida_int:.2f}/5 (podridos {podridos_platillo_interceptor}/{ingredientes_platillo_interceptor}), "
                            f"Tiempo={tiempo_platillo_seg_int:.1f}s, Limpieza={limpieza_txt_int}, "
                            f"Propina={monedas_propina_int} monedas"
                        )
                        resumen_entrega = (
                            f"Comida={puntaje_comida_int:.2f}/5 | Podridos {podridos_platillo_interceptor}/{ingredientes_platillo_interceptor} | "
                            f"Tiempo={tiempo_platillo_seg_int:.1f}s | Limpieza={limpieza_txt_int} | Propina={monedas_propina_int} monedas"
                        )
                        resumen_entrega_until = ahora + 9000
                        ingredientes_platillo_interceptor = 0
                        podridos_platillo_interceptor = 0
                        inicio_platillo_interceptor = 0

            if 'washer_done' in eventos:
                platos_limpios += 1
                print(f"Interceptor completó lavado. Platos limpios disponibles: {platos_limpios}")

            # preparar datos visuales del interceptor para el renderer
            interceptor_lavando = interceptor.lavando
            interceptor_progreso_lavado = interceptor.progreso_lavado
            interceptor_esperando = interceptor.esperando
            interceptor_progreso_espera = getattr(interceptor, 'progreso_espera', 0.0)

            render_frame(
                self.pantalla_virtual, 
                TAM_CELDA,
                ANCHO_GRID,
                ALTO_GRID,
                mapa_actual,
                chef_pos,
                ruta_disponible,
                zonas_olor,
                pozo_descubierto,
                pozos_pos,
                pisos_lentos,
                platos_limpios,
                platos_sucios,
                lavando_plato,
                progreso_lavado,
                interceptor_pos,
                ruta_interceptor,
                interceptor_lavando,
                interceptor_progreso_lavado,
                interceptor_esperando,
                interceptor_progreso_espera,
                esperando_accion,  # <- NUEVO
                progreso_espera,   # <- NUEVO
                chef_freeze_until,
                ahora,
                ('freeze_until' in eventos),
                self.map_surface,
                self.img_pozo,
                self.img_piso_mojado,
                self.img_chef_dir[chef_direccion],
                self.img_interceptor_dir[interceptor.direccion],
                ingrediente_podrido,
                tiempo_restante_ms,
                resumen_entrega,
                resumen_entrega_until,
                bool(mostrar_tiempo_agotado_until and ahora < mostrar_tiempo_agotado_until),
                mostrar_resumen_final,
                resumen_final_lineas,
            )
            
            
            self.ventana.blit(self.pantalla_virtual, (0, 0))
            
            pygame.display.flip()
            self.reloj.tick(60)

        return False