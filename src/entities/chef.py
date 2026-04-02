import copy
from src.systems.pathfinding import Pathfinder

class Chef:
    def __init__(self, start_pos: list[int]):
        self.pos = list(start_pos)
        self.direccion = 0  # 0: Abajo, 1: Arriba, 2: Derecha, 3: Izquierda
        self.ruta_disponible: list[tuple[int, int]] = []
        self.ruta_objetivo = None
        self.contador_frames = 0
        self.freeze_until = 0

        # Estados de acción
        self.esperando_accion = False
        self.inicio_espera = 0
        self.tiempo_espera_actual = 0
        self.progreso_espera = 0.0

        # Platos y lavado
        self.en_reposicion_plato = False
        self.buscando_plato_sucio = False
        self.tiene_plato_sucio = False
        self.esperando_plato_sucio = False

        self.lavando_plato = False
        self.inicio_lavado = 0
        self.progreso_lavado = 0.0

        # Ingredientes en mano
        self.ingredientes_platillo = 0
        self.podridos_platillo = 0
        self.inicio_platillo = 0

        self.entregas = 0

    def clear_route(self):
        self.ruta_disponible = []
        self.ruta_objetivo = None
        self.contador_frames = 0

    def update(
        self, ahora, mapa_actual, lista_objetivos, index_objetivo, kitchen, pathfinder, 
        interceptor_pos, tiempo_lavado_ms, tiempos_espera, velocidad_movimiento, zona_lenta, 
        objetivo_platos_sucios, objetivo_lavado, prob_podrido,
        platos_coords, ingredientes_coords, entregas_coords
    ):
        """Gestiona todo el ciclo de acción, lavado, inventario y movimiento."""
        import pygame
        import random

        eventos = {}
        str_entrega = None
        duration_entrega = 0

        # Helper para ingredientes podridos
        def verificar_ingrediente_podrido(probabilidad=0.0):
            return random.random() < probabilidad

        # Helper para objetivos
        def es_objetivo_valido(coord):
            x, y = coord
            if 0 <= y < len(mapa_actual) and 0 <= x < len(mapa_actual[0]):
                return mapa_actual[y][x] == 1
            return False

        if self.esperando_accion:
            transcurrido_espera = ahora - self.inicio_espera
            self.progreso_espera = min(1.0, transcurrido_espera / self.tiempo_espera_actual)
            if transcurrido_espera >= self.tiempo_espera_actual:
                self.esperando_accion = False
                self.progreso_espera = 0.0
                index_objetivo += 1
                self.clear_route()

        if self.lavando_plato:
            transcurrido = ahora - self.inicio_lavado
            self.progreso_lavado = min(1.0, transcurrido / tiempo_lavado_ms)
            if transcurrido >= tiempo_lavado_ms:
                self.lavando_plato = False
                self.progreso_lavado = 0.0
                self.tiene_plato_sucio = False
                kitchen.platos_limpios += 1
                self.en_reposicion_plato = False
                self.esperando_plato_sucio = False
                index_objetivo += 1
                self.clear_route()

        if index_objetivo < len(lista_objetivos):
            objetivo_actual = lista_objetivos[index_objetivo]
        else:
            objetivo_actual = None

        if objetivo_actual is not None and not es_objetivo_valido(objetivo_actual):
            index_objetivo += 1
            self.clear_route()
            return eventos, index_objetivo, objetivo_actual, str_entrega, duration_entrega

        # --- Lógica de reposición de platos sucios ---
        if (
            objetivo_actual in platos_coords
            and kitchen.platos_limpios == 0
            and not self.en_reposicion_plato
            and not self.lavando_plato
        ):
            if kitchen.platos_sucios > 0:
                lista_objetivos[index_objetivo:index_objetivo] = [objetivo_platos_sucios, objetivo_lavado]
                self.en_reposicion_plato = True
                self.buscando_plato_sucio = True
                self.esperando_plato_sucio = False
                self.clear_route()
                objetivo_actual = lista_objetivos[index_objetivo]
            else:
                self.esperando_plato_sucio = True
                self.clear_route()

        # --- Interacciones ---
        while (
            objetivo_actual is not None
            and tuple(self.pos) == objetivo_actual
            and not self.lavando_plato
            and not self.esperando_accion
        ):
            if self.en_reposicion_plato and self.buscando_plato_sucio and objetivo_actual == objetivo_platos_sucios:
                if kitchen.platos_sucios > 0:
                    kitchen.platos_sucios -= 1
                    self.tiene_plato_sucio = True
                    self.buscando_plato_sucio = False

            elif self.en_reposicion_plato and self.tiene_plato_sucio and objetivo_actual == objetivo_lavado:
                self.lavando_plato = True
                self.inicio_lavado = ahora
                self.progreso_lavado = 0.0
                self.clear_route()
                break

            if objetivo_actual in platos_coords and kitchen.platos_limpios > 0:
                kitchen.platos_limpios -= 1

            if objetivo_actual in ingredientes_coords:
                if self.ingredientes_platillo == 0:
                    self.inicio_platillo = ahora
                self.ingredientes_platillo += 1
                if verificar_ingrediente_podrido(prob_podrido):
                    self.podridos_platillo += 1
                    eventos['ingrediente_podrido'] = True

            if objetivo_actual in entregas_coords:
                tiempo_platillo_seg = max(0.0, (ahora - self.inicio_platillo) / 1000.0) if self.inicio_platillo else 0.0
                
                # Delego a la cocina
                monedas, msg, _, _ = kitchen.entregar_pedido(
                    tiempo_platillo_seg, self.ingredientes_platillo, self.podridos_platillo
                )
                kitchen.registrar_entrega(ahora, 10000) # 10s default para retorno
                self.entregas += 1
                str_entrega = msg
                duration_entrega = 9000
                
                self.ingredientes_platillo = 0
                self.podridos_platillo = 0
                self.inicio_platillo = 0

            if objetivo_actual in tiempos_espera:
                self.esperando_accion = True
                self.inicio_espera = ahora
                self.tiempo_espera_actual = tiempos_espera[objetivo_actual]
                self.clear_route()
                break 
            else:
                index_objetivo += 1
                if index_objetivo < len(lista_objetivos):
                    objetivo_actual = lista_objetivos[index_objetivo]
                    self.clear_route()
                else:
                    objetivo_actual = None

        if objetivo_actual is not None and not es_objetivo_valido(objetivo_actual):
            index_objetivo += 1
            self.clear_route()
            return eventos, index_objetivo, objetivo_actual, str_entrega, duration_entrega

        # --- Pathfinding ---
        if (
            not self.lavando_plato
            and objetivo_actual is not None
            and (self.ruta_objetivo != objetivo_actual or not self.ruta_disponible)
        ):
            ix, iy = interceptor_pos[0], interceptor_pos[1]
            val_original = mapa_actual[iy][ix]
            if tuple(interceptor_pos) != objetivo_actual:
                mapa_actual[iy][ix] = 0
            pathfinder.set_matrix(mapa_actual)
            self.ruta_disponible = pathfinder.obtener_ruta(self.pos, objetivo_actual)

            if not self.ruta_disponible and val_original == 1 and tuple(interceptor_pos) != objetivo_actual:
                mapa_actual[iy][ix] = 1
                pathfinder.set_matrix(mapa_actual)
                self.ruta_disponible = pathfinder.obtener_ruta(self.pos, objetivo_actual)

            mapa_actual[iy][ix] = val_original
            pathfinder.set_matrix(mapa_actual)

            self.ruta_objetivo = objetivo_actual
            self.contador_frames = 0

            if not self.ruta_disponible and tuple(self.pos) != objetivo_actual:
                index_objetivo += 1
                self.clear_route()

        # --- Movimiento ---
        if self.ruta_disponible and not self.lavando_plato:
            self.contador_frames += 1
            vel = velocidad_movimiento
            if tuple(self.pos) in zona_lenta:
                vel *= 3
            if self.contador_frames >= vel and ahora >= self.freeze_until:
                sig = self.ruta_disponible[0]
                if list(sig) == interceptor_pos:
                    self.clear_route()
                else:
                    sig = self.ruta_disponible.pop(0)
                    if sig[0] > self.pos[0]: self.direccion = 2
                    elif sig[0] < self.pos[0]: self.direccion = 3
                    elif sig[1] < self.pos[1]: self.direccion = 1
                    elif sig[1] > self.pos[1]: self.direccion = 0
                    self.pos[0], self.pos[1] = sig[0], sig[1]
                    self.contador_frames = 0

                if not self.ruta_disponible and objetivo_actual is not None and tuple(self.pos) == objetivo_actual:
                    self.ruta_objetivo = None

        return eventos, index_objetivo, objetivo_actual, str_entrega, duration_entrega
