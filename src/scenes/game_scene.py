import copy
import pygame

from config import TAM_CELDA, ANCHO_GRID, ALTO_GRID, VELOCIDAD_MOVIMIENTO, TIEMPOS_ESPERA
from src.systems.maps import MAPA_ORIGINAL, generar_pozos_y_olores
from src.systems.orders import PLATOS, generar_pedidos, expandir_objetivos
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
        mapa_actual = copy.deepcopy(MAPA_ORIGINAL)
        chef_pos = [1, 3]
        ruta_disponible: list[tuple[int, int]] = []
        contador_frames = 0
        index_objetivo = 0
        ruta_objetivo = None

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

        esperando_accion = False
        tiempo_fin_espera = 0

        ejecutando = True
        while ejecutando:
            if index_objetivo < len(lista_objetivos):
                objetivo_actual = lista_objetivos[index_objetivo]
            else:
                objetivo_actual = None

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

            # --- ESPERA Y AVANCE DE TAREAS ---
            if objetivo_actual is not None and tuple(chef_pos) == objetivo_actual:
                if not esperando_accion:
                    tiempo_espera = TIEMPOS_ESPERA.get(objetivo_actual, 0)
                    
                    if tiempo_espera > 0:
                        esperando_accion = True
                        tiempo_fin_espera = pygame.time.get_ticks() + tiempo_espera
                        print(f"Chef trabajando en {objetivo_actual}... ({tiempo_espera/1000}s)")
                    else:
                        index_objetivo += 1
                        ruta_disponible = []
                        ruta_objetivo = None
                        contador_frames = 0
                        if index_objetivo >= len(lista_objetivos):
                            print("Todos los pedidos completados.")
                else:
                    if pygame.time.get_ticks() >= tiempo_fin_espera:
                        esperando_accion = False
                        index_objetivo += 1
                        ruta_disponible = []
                        ruta_objetivo = None
                        contador_frames = 0
                        print(f"¡Acción en {objetivo_actual} completada!")
                        if index_objetivo >= len(lista_objetivos):
                            print("Todos los pedidos completados.")

            # --- MOVIMIENTO ---
            if not esperando_accion and objetivo_actual is not None and tuple(chef_pos) != objetivo_actual:
                
                if ruta_objetivo != objetivo_actual or not ruta_disponible:
                    ruta_disponible = pathfinder.obtener_ruta(chef_pos, objetivo_actual)
                    ruta_objetivo = objetivo_actual
                    contador_frames = 0

                    if not ruta_disponible and tuple(chef_pos) != objetivo_actual:
                        print(f"Objetivo inalcanzable, saltando: {objetivo_actual}")
                        index_objetivo += 1
                        ruta_objetivo = None
                        ruta_disponible = []

                if ruta_disponible:
                    contador_frames += 1
                    if contador_frames >= VELOCIDAD_MOVIMIENTO:
                        siguiente_paso = ruta_disponible.pop(0)
                        chef_pos[0], chef_pos[1] = siguiente_paso[0], siguiente_paso[1]
                        contador_frames = 0

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
                img_escenario=self.img_escenario, 
                img_chef=self.img_chef            
            )
            
            superficie_escalada = pygame.transform.smoothscale(self.pantalla_virtual, (950, 650))
            
            self.ventana.blit(superficie_escalada, (0, 0))
            
            pygame.display.flip()
            self.reloj.tick(60)

        return False