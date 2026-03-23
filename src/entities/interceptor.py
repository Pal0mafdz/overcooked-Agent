import copy
from typing import List, Tuple

from src.systems.pathfinding import Pathfinder
from src.systems.orders import OLLAS, TABLAS


class Interceptor:
    def __init__(
        self,
        start_pos: List[int],
        mapa: list[list[int]],
        lista_objetivos: list[tuple[int, int]],
    ):
        self.pos = list(start_pos)
        self.mapa = copy.deepcopy(mapa)
        self.pathfinder = Pathfinder(copy.deepcopy(mapa))
        self.lista_objetivos = lista_objetivos

        self.ruta: list[tuple[int, int]] = []
        self.ruta_objetivo = None
        self.index_objetivo = 0

        self.contador_frames = 0
        self.direccion = 0  # 0: Abajo, 1: Arriba, 2: Derecha, 3: Izquierda

        # estados de acción
        self.lavando = False
        self.inicio_lavado = 0
        self.progreso_lavado = 0.0

        self.esperando = False
        self.inicio_espera = 0
        self.tiempo_espera_actual = 0
        self.progreso_espera = 0.0

        # evita re-triggers de congelamiento continuo
        self._freeze_active_until = 0
        # evita que el interceptor se cruce con la ruta del chef durante un periodo tras congelar
        self._avoid_until = 0

    def current_objetivo(self):
        if self.index_objetivo < len(self.lista_objetivos):
            return self.lista_objetivos[self.index_objetivo]
        return None

    def advance_objetivo(self):
        self.index_objetivo += 1
        self.ruta = []
        self.ruta_objetivo = None

    def reinsertar_objetivo(self, objetivo: tuple):
        """Reinserta un objetivo al frente de la lista pendiente (para reintentar ingrediente podrido)."""
        self.lista_objetivos.insert(self.index_objetivo, objetivo)
        self.ruta = []
        self.ruta_objetivo = None

    def start_washing(self, ahora: int):
        self.lavando = True
        self.inicio_lavado = ahora
        self.progreso_lavado = 0.0

    def start_wait(self, dur_ms: int, ahora: int):
        self.esperando = True
        self.inicio_espera = ahora
        self.tiempo_espera_actual = dur_ms

    def update(self, ahora: int, chef_pos: List[int], ruta_chef: list[tuple[int, int]], mapa: list[list[int]], lista_objetivos: list[tuple[int, int]], zona_lenta: set, tiempo_lavado_ms: int, velocidad_movimiento: int, tiempos_espera: dict, chef_objetivo=None) -> dict:
        """
        Actualiza estado del interceptor: planificación de ruta, movimiento, espera y lavado.
        Retorna dict con eventos posibles: {'freeze_until': ms, 'arrived': objetivo, 'washer_done': True}
        chef_objetivo: la coordenada que el chef principal tiene como objetivo actual.
        """
        eventos = {}

        # actualizar mapa local
        self.mapa = copy.deepcopy(mapa)

        # NOTA: mantener la lista de objetivos del interceptor independiente
        # para que siga acciones similares al chef pero en distinto orden/ruta.
        # Si se desea sincronizar dinámicamente, implementar aquí reglas específicas.

        objetivo = self.current_objetivo()

        # si está lavando, actualizar progreso y terminar si corresponde
        if self.lavando:
            trans = ahora - self.inicio_lavado
            self.progreso_lavado = min(1.0, trans / tiempo_lavado_ms)
            if trans >= tiempo_lavado_ms:
                self.lavando = False
                self.progreso_lavado = 0.0
                eventos['washer_done'] = True
                self.advance_objetivo()
            return eventos

        # si está esperando, actualizar
        if self.esperando:
            trans = ahora - self.inicio_espera
            # actualizar progreso de espera para la barra visual
            if self.tiempo_espera_actual > 0:
                self.progreso_espera = min(1.0, trans / self.tiempo_espera_actual)
            else:
                self.progreso_espera = 1.0
            if trans >= self.tiempo_espera_actual:
                self.esperando = False
                self.progreso_espera = 0.0
                eventos['wait_done'] = True
                self.advance_objetivo()
            return eventos

        # planear ruta si es necesario
        if objetivo is not None and (self.ruta_objetivo != objetivo or not self.ruta):

            # --- Lógica de selección de olla: evitar conflicto con el chef principal ---
            if objetivo in OLLAS:
                olla_alternativa = None
                for olla in OLLAS:
                    if olla != objetivo:
                        olla_alternativa = olla
                        break

                chef_en_olla = (
                    olla_alternativa is not None
                    and (
                        tuple(chef_pos) == objetivo
                        or chef_objetivo == objetivo
                    )
                )

                if chef_en_olla and olla_alternativa is not None:
                    # Redirigir al interceptor a la olla alternativa (todos los pasos: cocinar y servir)
                    for i in range(self.index_objetivo, len(self.lista_objetivos)):
                        if self.lista_objetivos[i] == objetivo:
                            self.lista_objetivos[i] = olla_alternativa
                    objetivo = olla_alternativa
                    print(f"Interceptor redirigido a olla alternativa {olla_alternativa}")

            # --- Lógica de selección de tabla de corte: evitar conflicto con el chef principal ---
            if objetivo in TABLAS:
                tabla_alternativa = None
                for tabla in TABLAS:
                    if tabla != objetivo:
                        tabla_alternativa = tabla
                        break

                chef_en_tabla = (
                    tabla_alternativa is not None
                    and (
                        tuple(chef_pos) == objetivo
                        or chef_objetivo == objetivo
                    )
                )

                if chef_en_tabla and tabla_alternativa is not None:
                    for i in range(self.index_objetivo, len(self.lista_objetivos)):
                        if self.lista_objetivos[i] == objetivo:
                            self.lista_objetivos[i] = tabla_alternativa
                    objetivo = tabla_alternativa
                    print(f"Interceptor redirigido a tabla alternativa {tabla_alternativa}")

            # crear mapa temporal que bloquea la ruta del chef para promover rutas distintas
            matriz_temp = copy.deepcopy(self.mapa)
            try:
                # construir conjunto de celdas a bloquear: la ruta del chef
                bloqueadas = set(ruta_chef or [])

                # si estamos dentro del periodo de evitación, expandir bloqueo a vecinos
                if ahora < self._avoid_until:
                    vecinos = []
                    for (bx, by) in list(bloqueadas):
                        for dx, dy in [(0,1),(0,-1),(1,0),(-1,0)]:
                            nx, ny = bx + dx, by + dy
                            vecinos.append((nx, ny))
                    # incluir además la posición actual del chef en bloqueo temporal
                    try:
                        chef_x, chef_y = ruta_chef[0]
                        vecinos.extend([(chef_x + dx, chef_y + dy) for dx, dy in [(0,0),(0,1),(0,-1),(1,0),(-1,0)]])
                    except Exception:
                        pass
                    bloqueadas.update(vecinos)

                for (bx, by) in bloqueadas:
                    if 0 <= by < len(matriz_temp) and 0 <= bx < len(matriz_temp[0]):
                        matriz_temp[by][bx] = 0
            except Exception:
                pass

            self.pathfinder.set_matrix(matriz_temp)
            self.ruta = self.pathfinder.obtener_ruta(self.pos, objetivo)
            self.ruta_objetivo = objetivo

            if not self.ruta and tuple(self.pos) != objetivo:
                # fallback
                self.pathfinder.set_matrix(self.mapa)
                self.ruta = self.pathfinder.obtener_ruta(self.pos, objetivo)
                self.ruta_objetivo = objetivo

        # movimiento
        if self.ruta:
            self.contador_frames += 1
            vel = velocidad_movimiento
            if tuple(self.pos) in zona_lenta:
                vel = velocidad_movimiento * 3
            if self.contador_frames >= vel:
                siguiente = self.ruta.pop(0)

                if siguiente[0] > self.pos[0]:
                    self.direccion = 2
                elif siguiente[0] < self.pos[0]:
                    self.direccion = 3
                elif siguiente[1] < self.pos[1]:
                    self.direccion = 1
                elif siguiente[1] > self.pos[1]:
                    self.direccion = 0

                self.pos[0], self.pos[1] = siguiente[0], siguiente[1]
                self.contador_frames = 0
                if not self.ruta:
                    eventos['arrived'] = self.ruta_objetivo

        # detectar adyacencia para congelar al chef (1 casilla de distancia)
        distancia = abs(self.pos[0] - chef_pos[0]) + abs(self.pos[1] - chef_pos[1])
        if distancia == 1 and ahora > self._freeze_active_until:
            # congelamiento de 3s
            self._freeze_active_until = ahora + 3000
            # evitar cruce con la ruta del chef durante los próximos 3s para dar tiempo al chef
            self._avoid_until = self._freeze_active_until
            eventos['freeze_until'] = self._freeze_active_until

        return eventos
