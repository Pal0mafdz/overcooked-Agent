import copy
import pygame

from config import TAM_CELDA, ANCHO_GRID, ALTO_GRID, VELOCIDAD_MOVIMIENTO
from src.systems.maps import MAPA_ORIGINAL, generar_pozos_y_olores
from src.systems.orders import PLATOS, generar_pedidos, expandir_objetivos
from src.systems.pathfinding import Pathfinder
from src.ui.render import render_frame


class GameScene:
    def __init__(self, ventana, reloj, ordenes: int):
        self.ventana = ventana
        self.reloj = reloj
        self.ordenes = ordenes

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

        print("\n" + "=" * 40)
        print("NUEVA SIMULACIÓN INICIADA")
        print(f"DEBUG: Pozos generados en {pozos_pos}")
        if lista_pedidos:
            print(f"Pedidos: {lista_pedidos}")
            print(f"Pedido actual: {lista_pedidos[0]}")
        print("=" * 40 + "\n")

        pathfinder = Pathfinder(mapa_actual)

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
                    cx, cy = mx // TAM_CELDA, my // TAM_CELDA
                    if 0 <= cx < ANCHO_GRID and 0 <= cy < ALTO_GRID:
                        if mapa_actual[cy][cx] == 1:
                            if evento.button == 3:
                                chef_pos = [cx, cy]
                                ruta_disponible = []
                                ruta_objetivo = None

            while objetivo_actual is not None and tuple(chef_pos) == objetivo_actual:
                index_objetivo += 1
                if index_objetivo < len(lista_objetivos):
                    objetivo_actual = lista_objetivos[index_objetivo]
                    ruta_disponible = []
                    ruta_objetivo = None
                    contador_frames = 0
                else:
                    objetivo_actual = None
                    print("Todos los pedidos completados.")

            if objetivo_actual is not None and (ruta_objetivo != objetivo_actual or not ruta_disponible):
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

                    if not ruta_disponible:
                        print(f"Destino: {chef_pos}")
                        if objetivo_actual is not None and tuple(chef_pos) == objetivo_actual:
                            index_objetivo += 1
                            ruta_objetivo = None

            render_frame(
                self.ventana,
                TAM_CELDA,
                ANCHO_GRID,
                ALTO_GRID,
                mapa_actual,
                chef_pos,
                ruta_disponible,
                zonas_olor,
                pozo_descubierto,
                pozos_pos,
            )
            pygame.display.flip()
            self.reloj.tick(60)

        return False
