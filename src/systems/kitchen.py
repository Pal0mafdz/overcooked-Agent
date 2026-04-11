class KitchenState:
    def __init__(self, platos_iniciales=3, max_sucios=3):
        self.platos_limpios = platos_iniciales
        self.platos_sucios = 0
        self.temporizadores_sucios: list[int] = []
        self.max_sucios = max_sucios
        
        # Puntuaciones globales
        self.propinas_totales_monedas = 0
        self.acumulado_comida = 0.0
        self.acumulado_limpieza = 0.0
        self.acumulado_tiempo = 0.0
        self.acumulado_podridos = 0
        self.acumulado_ingredientes = 0

    def tick(self, ahora: int):
        """Actualiza los temporizadores de los platos sucios que van regresando a la zona sucia."""
        restantes = []
        for tiempo_objetivo in self.temporizadores_sucios:
            if ahora >= tiempo_objetivo:
                if self.platos_sucios < self.max_sucios:
                    self.platos_sucios += 1
            else:
                restantes.append(tiempo_objetivo)
        self.temporizadores_sucios = restantes

    def registrar_entrega(self, ahora: int, retraso_plato_sucio_ms: int):
        """Dispara un temporizador para que regrese un plato sucio en N segundos."""
        total_pendiente = self.platos_sucios + len(self.temporizadores_sucios)
        if total_pendiente < self.max_sucios:
            self.temporizadores_sucios.append(ahora + retraso_plato_sucio_ms)

    def entregar_pedido(self, tiempo_platillo_seg: float, num_ingredientes: int, num_podridos: int):
        from src.systems.orders import (
            calcular_puntaje_comida, 
            evaluar_propina_difusa, 
            calcular_limpieza_por_platos,
            TIEMPO_FUZZY, COMIDA_FUZZY, LIMPIEZA_FUZZY, PROPINA_FUZZY
        )

        # 1. Puntaje Comida
        puntaje_comida = calcular_puntaje_comida(num_ingredientes, num_podridos)
        self.acumulado_comida += puntaje_comida
        self.acumulado_podridos += num_podridos
        self.acumulado_ingredientes += num_ingredientes

        # 2. Puntaje Limpieza Actual
        limpieza_actual = calcular_limpieza_por_platos(self.platos_sucios, len(self.temporizadores_sucios), capacidad=self.max_sucios)
        self.acumulado_limpieza += limpieza_actual

        # 3. Guardar el tiempo
        self.acumulado_tiempo += tiempo_platillo_seg

        # 4. Propina fuzzy
        res_difusa = evaluar_propina_difusa(
            tiempo_segundos=tiempo_platillo_seg,
            comida=puntaje_comida,
            limpieza=limpieza_actual,
            config_tiempo=TIEMPO_FUZZY,
            config_comida=COMIDA_FUZZY,
            config_limpieza=LIMPIEZA_FUZZY,
            config_propina=PROPINA_FUZZY
        )
        monedas = res_difusa["propina"]

        self.propinas_totales_monedas += monedas
        higiene_visual = 100.0 - limpieza_actual
        msg = f"+${monedas:.2f} MXN | COMIDA: {puntaje_comida:.1f}/5.0 | HIGIENE: {higiene_visual:.0f}% | TIEMPO: {tiempo_platillo_seg:.1f}s"
        return monedas, msg, puntaje_comida, str(round(limpieza_actual, 1))
