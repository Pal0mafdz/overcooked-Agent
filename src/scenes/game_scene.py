import copy
import pygame

from config import TAM_CELDA, ANCHO_GRID, ALTO_GRID, VELOCIDAD_MOVIMIENTO
from src.systems.maps import MAPA_ORIGINAL, generar_pozos_y_olores
from src.systems.orders import PLATOS, ENTREGAS, generar_pedidos, expandir_objetivos
from src.systems.pathfinding import Pathfinder
from src.ui.render import render_frame

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

        pathfinder = Pathfinder(mapa_actual)

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
                    
                    mx_real = int(mx * self.ancho_logico / 950)
                    my_real = int(my * self.alto_logico / 650)
                    
                    cx, cy = mx_real // TAM_CELDA, my_real // TAM_CELDA
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

                if objetivo_actual in ENTREGAS:
                    registrar_entrega(ahora)
                    print("Pedido entregado. Plato sucio llegará en 15s.")

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
                ruta_disponible = pathfinder.obtener_ruta(chef_pos, objetivo_actual)
                ruta_objetivo = objetivo_actual
                contador_frames = 0

                if not ruta_disponible and tuple(chef_pos) != objetivo_actual:
                    print(f"Objetivo inalcanzable, saltando: {objetivo_actual}")
                    index_objetivo += 1
                    ruta_objetivo = None
                    ruta_disponible = []

            if ruta_disponible and not lavando_plato:
                contador_frames += 1
                if contador_frames >= VELOCIDAD_MOVIMIENTO:
                    siguiente_paso = ruta_disponible.pop(0)
                    chef_pos[0], chef_pos[1] = siguiente_paso[0], siguiente_paso[1]
                    contador_frames = 0

                    if not ruta_disponible:
                        print(f"Destino: {chef_pos}")
                        if objetivo_actual is not None and tuple(chef_pos) == objetivo_actual:
                            ruta_objetivo = None

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
                platos_limpios,
                platos_sucios,
                lavando_plato,
                progreso_lavado,
            )
            
            superficie_escalada = pygame.transform.smoothscale(self.pantalla_virtual, (950, 650))
            
            self.ventana.blit(superficie_escalada, (0, 0))
            
            pygame.display.flip()
            self.reloj.tick(60)

        return False