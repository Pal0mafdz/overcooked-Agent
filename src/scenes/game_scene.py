import copy
import pygame
import random
import time

from config import (
    TAM_CELDA, ANCHO_GRID, ALTO_GRID, VELOCIDAD_MOVIMIENTO,
    VELOCIDAD_PERSECUCION, DISTANCIA_PERSECUCION
)
from src.systems.maps import MAPA_ORIGINAL, generar_pozos_y_olores
from src.systems.orders import PLATOS, ENTREGAS, generar_pedidos, expandir_objetivos
from src.systems.pathfinding import Pathfinder
from src.ui.render import render_frame
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
        
        # --- CARGAR IMÁGENES ---
        self.img_escenario = pygame.image.load("assets/escenario_2.jpg").convert()
        self.img_escenario = pygame.transform.scale(
            self.img_escenario, 
            (self.ancho_logico, self.alto_logico)
        )
        
        self.img_chef = pygame.image.load("assets/chef01_front.png").convert_alpha()
        self.img_chef = pygame.transform.scale(self.img_chef, (TAM_CELDA, TAM_CELDA))

    def run(self) -> bool:
        objetivo_platos_sucios = (16, 6)
        objetivo_lavado = (1, 6)
        retraso_plato_sucio_ms = 15000
        tiempo_lavado_ms = 5000

        mapa_actual = copy.deepcopy(MAPA_ORIGINAL)
        chef_pos = [1, 3]
        ruta_chef: list[tuple[int, int]] = []
        contador_frames_chef = 0
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

        # Estado del interceptor
        interceptor_pos = [15, 7]  # Posición inicial opuesta
        ruta_interceptor: list[tuple[int, int]] = []
        contador_frames_interceptor = 0
        index_objetivo_interceptor = 0
        ruta_objetivo_interceptor = None

        # Estados de persecución y distracción
        esta_persiguiendo = False
        tiempo_distraccion = 0.0
        inicio_distraccion = 0.0

        lista_pedidos = generar_pedidos(self.ordenes)
        lista_objetivos = expandir_objetivos(lista_pedidos)

        pozos_pos, zonas_olor = generar_pozos_y_olores(
            mapa_actual,
            chef_pos,
            lista_objetivos,
            cantidad_pozos=2,
            celdas_prohibidas=PLATOS,
        )
        for (px, py) in pozos_pos:
            mapa_actual[py][px] = 0
        pozo_descubierto = True

        pisos_lentos = generar_pisos_lentos(
            mapa_actual,
            chef_pos,
            lista_objetivos,
            cantidad=8,
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
        print("NUEVA SIMULACIÓN INICIADA - CON AGENTE INTERCEPTOR")
        print(f"DEBUG: Pozos generados en {pozos_pos}")
        if lista_pedidos:
            print(f"Pedidos: {lista_pedidos}")
            print(f"Pedido actual: {lista_pedidos[0]}")
        print("=" * 40 + "\n")

        pathfinder = Pathfinder(mapa_actual)

        # Tiempo de la última intercepción que provocó distracción
        ultima_intercepcion = 0.0

        # Helper: obtener ruta alternativa evitando posiciones concretas
        def obtener_ruta_alternativa(start_pos, end_pos, evitar_positions=None):
            evitar_positions = set(tuple(p) for p in (evitar_positions or []))
            # copiar mapa y marcar como obstáculos las posiciones a evitar
            matrix_copy = [row[:] for row in mapa_actual]
            for (ex, ey) in list(evitar_positions):
                if 0 <= ey < len(matrix_copy) and 0 <= ex < len(matrix_copy[0]):
                    matrix_copy[ey][ex] = 0
            pf_alt = Pathfinder(matrix_copy)
            return pf_alt.obtener_ruta(start_pos, end_pos)

        ejecutando = True
        while ejecutando:
            ahora = pygame.time.get_ticks()

            temporizadores_restantes: list[int] = []
            for tiempo_objetivo in temporizadores_sucios:
                if ahora >= tiempo_objetivo:
                    if platos_sucios < 3:
                        platos_sucios += 1
                        print(f"Plato sucio disponible en (17,6). Total sucios: {platos_sucios}")
                else:
                    temporizadores_restantes.append(tiempo_objetivo)
            temporizadores_sucios = temporizadores_restantes

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

            # Calcular distancia entre agentes
            distancia_al_chef = abs(interceptor_pos[0] - chef_pos[0]) + abs(interceptor_pos[1] - chef_pos[1])

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
                    
                    mx_real = int(mx * self.ancho_logico / 950)
                    my_real = int(my * self.alto_logico / 650)
                    
                    cx, cy = mx_real // TAM_CELDA, my_real // TAM_CELDA
                    if 0 <= cx < ANCHO_GRID and 0 <= cy < ALTO_GRID:
                        if mapa_actual[cy][cx] == 1:
                            if evento.button == 1:  # Click izquierdo: teletransportar chef
                                chef_pos = [cx, cy]
                                ruta_chef = []
                                ruta_objetivo = None
                                tiempo_distraccion = 0.0
                            elif evento.button == 3:  # Click derecho: nuevo objetivo interceptor
                                objetivo_interceptor = [cx, cy]
                                ruta_interceptor = pathfinder.obtener_ruta(interceptor_pos, objetivo_interceptor)
                                contador_frames_interceptor = 0

            # Gestionar tiempo de distracción del chef
            tiempo_actual = time.time()
            if tiempo_distraccion > 0:
                if tiempo_actual - inicio_distraccion >= tiempo_distraccion:
                    tiempo_distraccion = 0.0
                    print("Distracción terminada - Chef puede moverse nuevamente")
                else:
                    # Chef está distraído, no se mueve
                    pass
            else:
                # Lógica normal del chef
                while objetivo_actual is not None and tuple(chef_pos) == objetivo_actual:
                    index_objetivo += 1
                    if index_objetivo < len(lista_objetivos):
                        objetivo_actual = lista_objetivos[index_objetivo]
                        ruta_chef = []
                        ruta_objetivo = None
                        contador_frames_chef = 0
                    else:
                        objetivo_actual = None
                        print("Todos los pedidos completados.")

                if objetivo_actual is not None and (ruta_objetivo != objetivo_actual or not ruta_chef):
                    ruta_chef = pathfinder.obtener_ruta(chef_pos, objetivo_actual)
                    ruta_objetivo = objetivo_actual
                    contador_frames_chef = 0

                    if not ruta_chef and tuple(chef_pos) != objetivo_actual:
                        print(f"Objetivo inalcanzable, saltando: {objetivo_actual}")
                        index_objetivo += 1
                        ruta_objetivo = None
                        ruta_chef = []

                if ruta_chef:
                    contador_frames_chef += 1
                    if contador_frames_chef >= VELOCIDAD_MOVIMIENTO:
                        siguiente_paso = ruta_chef.pop(0)
                        chef_pos[0], chef_pos[1] = siguiente_paso[0], siguiente_paso[1]
                        contador_frames_chef = 0

                        if not ruta_chef:
                            print(f"Chef llegó a: {chef_pos}")
                            if objetivo_actual is not None and tuple(chef_pos) == objetivo_actual:
                                index_objetivo += 1
                                ruta_objetivo = None

            # Lógica del interceptor: usa la misma lista de objetivos que el chef
            # pero mantiene su propio índice y calcula rutas alternativas para
            # evitar ocupar exactamente la "siguente" celda del chef cuando esté cerca.
            chef_next_pos = ruta_chef[0] if ruta_chef else None

            # Actualizar objetivo del interceptor desde la misma lista compartida
            if index_objetivo_interceptor < len(lista_objetivos):
                objetivo_actual_interceptor = lista_objetivos[index_objetivo_interceptor]
            else:
                objetivo_actual_interceptor = None

            # Si estamos cerca del chef y no hay distracción, intentar interceptar
            if distancia_al_chef <= DISTANCIA_PERSECUCION and tiempo_distraccion == 0.0:
                if not esta_persiguiendo:
                    esta_persiguiendo = True
                    print(f"¡Interceptor activado! Distancia: {distancia_al_chef}")

                # Perseguir al chef directamente
                ruta_interceptor = pathfinder.obtener_ruta(interceptor_pos, chef_pos)
                contador_frames_interceptor += 1

                if ruta_interceptor and contador_frames_interceptor >= VELOCIDAD_PERSECUCION:
                    siguiente_paso = ruta_interceptor.pop(0)
                    interceptor_pos[0], interceptor_pos[1] = siguiente_paso[0], siguiente_paso[1]
                    contador_frames_interceptor = 0

                # Si alcanza al chef, realiza la distracción pero no bloquea el flujo
                if tuple(interceptor_pos) == tuple(chef_pos):
                    ahora = time.time()
                    # Respetar un delay mínimo entre intercepciones
                    if ahora - ultima_intercepcion >= 2.0:
                        tiempo_distraccion = random.uniform(3, 5)
                        inicio_distraccion = ahora
                        ultima_intercepcion = ahora
                        esta_persiguiendo = False
                        ruta_interceptor = []
                        print(f"Distracción activada por {tiempo_distraccion:.2f} segundos")
                    else:
                        # Ignorar intercepción si ocurrió muy recientemente
                        esta_persiguiendo = False
                        ruta_interceptor = []
                        restante = 2.0 - (ahora - ultima_intercepcion)
                        if restante < 0:
                            restante = 0.0
                        print(f"Intercepción ignorada, esperar {restante:.2f}s más")

            else:
                # Volver a tareas: seguir los mismos objetivos que el chef
                if esta_persiguiendo:
                    esta_persiguiendo = False
                    print("Interceptor vuelve a tareas normales")

                # Si necesita calcular ruta hacia su objetivo, intentar evitar la siguiente celda del chef
                if objetivo_actual_interceptor is not None and (ruta_objetivo_interceptor != objetivo_actual_interceptor or not ruta_interceptor):
                    evitar = []
                    if distancia_al_chef <= DISTANCIA_PERSECUCION:
                        # evitar la celda actual y la siguiente del chef para forzar ruta alternativa
                        evitar.append(tuple(chef_pos))
                        if chef_next_pos:
                            evitar.append(tuple(chef_next_pos))

                    if evitar:
                        ruta_interceptor = obtener_ruta_alternativa(interceptor_pos, objetivo_actual_interceptor, evitar_positions=evitar)
                        if not ruta_interceptor:
                            # fallback a ruta normal
                            ruta_interceptor = pathfinder.obtener_ruta(interceptor_pos, objetivo_actual_interceptor)
                    else:
                        ruta_interceptor = pathfinder.obtener_ruta(interceptor_pos, objetivo_actual_interceptor)

                    ruta_objetivo_interceptor = objetivo_actual_interceptor
                    contador_frames_interceptor = 0

                # Mover interceptor normalmente
                if ruta_interceptor:
                    contador_frames_interceptor += 1
                    if contador_frames_interceptor >= VELOCIDAD_MOVIMIENTO:
                        siguiente_paso = ruta_interceptor.pop(0)
                        interceptor_pos[0], interceptor_pos[1] = siguiente_paso[0], siguiente_paso[1]
                        contador_frames_interceptor = 0

                        # Si llega a su objetivo, avanzar su índice (aunque sea el mismo objetivo del chef)
                        if objetivo_actual_interceptor is not None and tuple(interceptor_pos) == objetivo_actual_interceptor:
                            index_objetivo_interceptor += 1
                            ruta_objetivo_interceptor = None

            render_frame(
                self.pantalla_virtual, 
                TAM_CELDA,
                ANCHO_GRID,
                ALTO_GRID,
                mapa_actual,
                chef_pos,
                ruta_chef,
                zonas_olor,
                pozo_descubierto,
                pozos_pos,
                interceptor_pos,
                ruta_interceptor,
                tiempo_distraccion,
                distancia_al_chef,
                esta_persiguiendo,
            )
            
            superficie_escalada = pygame.transform.smoothscale(self.pantalla_virtual, (950, 650))
            
            self.ventana.blit(superficie_escalada, (0, 0))
            
            pygame.display.flip()
            self.reloj.tick(60)

        return False