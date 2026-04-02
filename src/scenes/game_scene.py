import copy
import pygame
import pytmx

from src.config import (
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
    DEFAULT_TIEMPO_FUZZY,
    TIEMPO_FUZZY,
    DEFAULT_COMIDA_FUZZY,
    COMIDA_FUZZY,
    DEFAULT_LIMPIEZA_FUZZY,
    LIMPIEZA_FUZZY,
    DEFAULT_PROPINA_FUZZY,
    PROPINA_FUZZY,
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
        
        from src.entities.chef import Chef
        from src.systems.kitchen import KitchenState
        
        chef = Chef([1, 3])
        kitchen = KitchenState(platos_iniciales=3, max_sucios=3)

        index_objetivo = 0
        ahora = pygame.time.get_ticks()

        ingrediente_podrido = False   # True durante el frame en que se detecta un ingrediente podrido
        podrido_flash_until = 0       # Timestamp hasta el cual mostrar el indicador de podrido

        ingredientes_platillo_interceptor = 0
        podridos_platillo_interceptor = 0
        inicio_platillo_interceptor = 0

        resumen_entrega = ""
        resumen_entrega_until = 0
        mostrar_tiempo_agotado_until = 0
        resumen_final_lineas: list[str] = []
        mostrar_resumen_final = False

        entregas_interceptor = 0

        def limpieza_a_palabra(limpieza_num: float) -> str:
            if limpieza_num >= 80:
                return "Asquerosa"
            if limpieza_num >= 50:
                return "Descuidada"
            if limpieza_num >= 15:
                return "Aceptable"
            return "Impecable"

        def construir_resumen_final() -> list[str]:
            total_entregas = chef.entregas + entregas_interceptor
            prom_comida = (kitchen.acumulado_comida / total_entregas) if total_entregas else 0.0
            prom_limpieza = (kitchen.acumulado_limpieza / total_entregas) if total_entregas else 0.0
            prom_tiempo = (kitchen.acumulado_tiempo / total_entregas) if total_entregas else 0.0
            tasa_podridos = (kitchen.acumulado_podridos / kitchen.acumulado_ingredientes * 100.0) if kitchen.acumulado_ingredientes else 0.0

            base_lines = [
                f"Platos entregados: {total_entregas}",
                f"Chef: {chef.entregas} | Interceptor: {entregas_interceptor}",
                f"Propinas ganadas: ${kitchen.propinas_totales_monedas:.2f} MXN",
                f"Comida promedio: {prom_comida:.2f}/5",
                f"Limpieza promedio: {limpieza_a_palabra(prom_limpieza)}",
                f"Tiempo promedio por pedido: {prom_tiempo:.1f}s",
                f"Ingredientes podridos usados: {kitchen.acumulado_podridos}/{kitchen.acumulado_ingredientes} ({tasa_podridos:.1f}%)",
                f"Estado final de cocina: {limpieza_a_palabra(calcular_limpieza_por_platos(kitchen.platos_sucios, len(kitchen.temporizadores_sucios), capacidad=3))}",
            ]

            def fmt(d):
                return " | ".join([f"{k}: {tuple(round(v, 1) for v in vals)}" for k, vals in d.items()])
                
            base_lines.append("--- PESOS DE LÓGICA DIFUSA ---")
            base_lines.append(f"[D] Tiempo: {fmt(DEFAULT_TIEMPO_FUZZY)}")
            base_lines.append(f"[E] Tiempo: {fmt(TIEMPO_FUZZY)}")
            base_lines.append(f"[D] Comida: {fmt(DEFAULT_COMIDA_FUZZY)}")
            base_lines.append(f"[E] Comida: {fmt(COMIDA_FUZZY)}")
            base_lines.append(f"[D] Limpieza: {fmt(DEFAULT_LIMPIEZA_FUZZY)}")
            base_lines.append(f"[E] Limpieza: {fmt(LIMPIEZA_FUZZY)}")
            base_lines.append(f"[D] Propina: {fmt(DEFAULT_PROPINA_FUZZY)}")
            base_lines.append(f"[E] Propina: {fmt(PROPINA_FUZZY)}")

            return base_lines

        lista_pedidos = generar_pedidos(self.ordenes)
        lista_objetivos = expandir_objetivos(lista_pedidos)
        
        # Generar objetivos independientes para el interceptor
        lista_objetivos_interceptor = generar_objetivos_interceptor(self.ordenes)

        celdas_interactivas = set(PLATOS) | set(INGREDIENTES) | set(ENTREGAS) | set(OLLAS) | set(TABLAS) | {objetivo_platos_sucios, objetivo_lavado}

        pozos_pos, zonas_olor = generar_pozos_y_olores(
            mapa_actual,
            chef.pos,
            lista_objetivos,
            cantidad_pozos=3,
            celdas_prohibidas=celdas_interactivas,
        )
        for (px, py) in pozos_pos:
            mapa_actual[py][px] = 0
        pozo_descubierto = True

        pisos_lentos = generar_pisos_lentos(
            mapa_actual,
            chef.pos,
            lista_objetivos,
            cantidad=3,
            celdas_prohibidas=celdas_interactivas,
        )

  
        zona_lenta = set()

        for (x, y) in pisos_lentos:
            zona_lenta.add((x, y))

            for dx, dy in [(0,1),(0,-1),(1,0),(-1,0)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < ANCHO_GRID and 0 <= ny < ALTO_GRID:
                    if (nx, ny) not in celdas_interactivas:
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
                    if mapa[y][x] == 1 and (x, y) not in evitar and (x, y) != tuple(chef.pos):
                        return [x, y]
            return [1, 3]

        interceptor_start = encontrar_celda_libre(mapa_actual, evitar=set(lista_objetivos))
        # El interceptor usa su propia lista de objetivos para evitar traslape con el chef
        interceptor = Interceptor(interceptor_start, mapa_actual, lista_objetivos_interceptor)
        chef.freeze_until = 0

        def es_objetivo_valido(valor) -> bool:
            return (
                isinstance(valor, tuple)
                and len(valor) == 2
                and all(isinstance(v, int) for v in valor)
            )

        def registrar_entrega(tiempo_actual: int):
            total_pendiente = kitchen.platos_sucios + len(kitchen.temporizadores_sucios)
            if total_pendiente < 3:
                kitchen.temporizadores_sucios.append(tiempo_actual + retraso_plato_sucio_ms)

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
                    print("\n" + "="*50)
                    print(" COMPARATIVA DE CONFIGURACIONES DIFUSAS (GA)")
                    print("="*50)
                    print("--- CONFIGURACIÓN POR DEFECTO ---")
                    print(f"TIEMPO:   {DEFAULT_TIEMPO_FUZZY}")
                    print(f"COMIDA:   {DEFAULT_COMIDA_FUZZY}")
                    print(f"LIMPIEZA: {DEFAULT_LIMPIEZA_FUZZY}")
                    print(f"PROPINA:  {DEFAULT_PROPINA_FUZZY}")
                    print("\n--- CONFIGURACIÓN ACTIVA (Entrenada / Cargada) ---")
                    print(f"TIEMPO:   {TIEMPO_FUZZY}")
                    print(f"COMIDA:   {COMIDA_FUZZY}")
                    print(f"LIMPIEZA: {LIMPIEZA_FUZZY}")
                    print(f"PROPINA:  {PROPINA_FUZZY}")
                    print("="*50 + "\n")
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
                    chef,
                    kitchen,
                    zonas_olor,
                    pozo_descubierto,
                    pozos_pos,
                    pisos_lentos,
                    interceptor.pos,
                    interceptor.ruta,
                    interceptor_lavando,
                    interceptor_progreso_lavado,
                    interceptor_esperando,
                    interceptor_progreso_espera,
                    ahora,
                    False,
                    self.map_surface,
                    self.img_pozo,
                    self.img_piso_mojado,
                    self.img_chef_dir[chef.direccion],
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
            for tiempo_objetivo in kitchen.temporizadores_sucios:
                if ahora >= tiempo_objetivo:
                    if kitchen.platos_sucios < 3:
                        kitchen.platos_sucios += 1
                        print(f"Plato sucio disponible en (17,6). Total sucios: {kitchen.platos_sucios}")
                else:
                    temporizadores_restantes.append(tiempo_objetivo)
            kitchen.temporizadores_sucios = temporizadores_restantes

            eventos_chef, index_objetivo, objetivo_actual, str_entrega, duration_entrega = chef.update(
                ahora=ahora,
                mapa_actual=mapa_actual,
                lista_objetivos=lista_objetivos,
                index_objetivo=index_objetivo,
                kitchen=kitchen,
                pathfinder=pathfinder,
                interceptor_pos=interceptor.pos,
                tiempo_lavado_ms=tiempo_lavado_ms,
                tiempos_espera=TIEMPOS_ESPERA,
                velocidad_movimiento=VELOCIDAD_MOVIMIENTO,
                zona_lenta=zona_lenta,
                objetivo_platos_sucios=objetivo_platos_sucios,
                objetivo_lavado=objetivo_lavado,
                prob_podrido=PROB_INGREDIENTE_PODRIDO,
                platos_coords=PLATOS,
                ingredientes_coords=INGREDIENTES,
                entregas_coords=ENTREGAS
            )

            if 'ingrediente_podrido' in eventos_chef:
                ingrediente_podrido = True
                podrido_flash_until = ahora + 1500

            if str_entrega:
                resumen_entrega = str_entrega
                resumen_entrega_until = ahora + duration_entrega

            # Interceptor update (mueve y devuelve eventos)
            eventos = interceptor.update(
                ahora,
                chef.pos,
                chef.ruta_disponible,
                mapa_actual,
                lista_objetivos_interceptor,
                zona_lenta,
                tiempo_lavado_ms,
                VELOCIDAD_MOVIMIENTO,
                TIEMPOS_ESPERA,
                chef.ruta_objetivo,            # <-- olla que el chef tiene como objetivo actual
            )

            ruta_interceptor = interceptor.ruta
            interceptor_pos = interceptor.pos

            if 'freeze_until' in eventos:
                chef.freeze_until = eventos['freeze_until']
                print("Interceptor adjacent: congelando al chef")
                # Pausar temporizadores del chef durante la congelación (no cancelarlos)
                freeze_dur = chef.freeze_until - ahora
                if chef.esperando_accion:
                    chef.inicio_espera += freeze_dur
                    print("Pausando progreso de espera del chef durante la congelación.")
                if chef.lavando_plato:
                    chef.inicio_lavado += freeze_dur
                    print("Pausando progreso de lavado del chef durante la congelación.")

            if 'arrived' in eventos:
                objetivo_interceptor = eventos['arrived']
                if objetivo_interceptor in TIEMPOS_ESPERA:
                    interceptor.start_wait(TIEMPOS_ESPERA[objetivo_interceptor], ahora)
                    print(f"Interceptor esperando {TIEMPOS_ESPERA[objetivo_interceptor]/1000}s en {objetivo_interceptor}...")
                else:
                    if objetivo_interceptor == objetivo_platos_sucios:
                        if kitchen.platos_sucios > 0:
                            kitchen.platos_sucios -= 1
                            print(f"Interceptor recogió plato sucio en {objetivo_interceptor}. Sucios restantes: {kitchen.platos_sucios}")
                            interceptor.advance_objetivo()
                    elif objetivo_interceptor == objetivo_lavado:
                        interceptor.start_washing(ahora)
                        print("Interceptor lavando plato...")
                    elif objetivo_interceptor in PLATOS:
                        if kitchen.platos_limpios > 0:
                            kitchen.platos_limpios -= 1
                            print(f"Interceptor tomó plato limpio en {objetivo_interceptor}. Platos limpios restantes: {kitchen.platos_limpios}")
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
                        
                        monedas_propina_int, resumen_entrega, puntaje_comida_int, limpieza_txt_int = kitchen.entregar_pedido(
                            tiempo_platillo_seg_int, ingredientes_platillo_interceptor, podridos_platillo_interceptor
                        )
                        
                        entregas_interceptor += 1
                        kitchen.registrar_entrega(ahora, 10000)
                        
                        resumen_entrega_until = ahora + 9000
                        ingredientes_platillo_interceptor = 0
                        podridos_platillo_interceptor = 0
                        inicio_platillo_interceptor = 0

            if 'washer_done' in eventos:
                kitchen.platos_limpios += 1
                print(f"Interceptor completó lavado. Platos limpios disponibles: {kitchen.platos_limpios}")

            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    return False
                if evento.type == pygame.KEYDOWN:
                    if evento.key == pygame.K_ESCAPE:
                        return False
                    if evento.key == pygame.K_r:
                        return True

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
                chef,
                kitchen,
                zonas_olor,
                pozo_descubierto,
                pozos_pos,
                pisos_lentos,
                interceptor_pos,
                ruta_interceptor,
                interceptor_lavando,
                interceptor_progreso_lavado,
                interceptor_esperando,
                interceptor_progreso_espera,
                ahora,
                ('freeze_until' in eventos),
                self.map_surface,
                self.img_pozo,
                self.img_piso_mojado,
                self.img_chef_dir[chef.direccion],
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