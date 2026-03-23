import random

PEDIDOS = ["sopa_tomate", "sopa"]

PLATOS = [(1, 5), (1, 4), (1, 3)]

ENTREGAS = [(16, 4), (16, 5)]

# Dos ollas disponibles; la primera es la predeterminada
OLLAS = [(3, 3), (5, 3)]

# Dos tablas de corte disponibles; la primera es la predeterminada
TABLAS = [(5, 7), (3, 7)]

# Celdas donde se recogen ingredientes
INGREDIENTES = {(13, 7), (15, 7)}  # (13,7) = tomate, (15,7) = cebolla

OBJETIVOS_POR_PEDIDO = {
    "sopa_tomate": [
        ((13, 7), "Ir por tomate"),
        ((5, 7), "Cortar tomate"),
        ((3, 3), "Llevar tomate a la olla"),
        ((16, 4), "Entregar orden"),
    ],
    "sopa": [
        ((15, 7), "Ir por cebolla"),
        ((5, 7), "Cortar cebolla"),
        ((3, 3), "Llevar cebolla a la olla"),
        ((16, 4), "Entregar orden"),
    ],
}


def verificar_ingrediente_podrido(prob: float = 0.3, rng=None) -> bool:
    """Retorna True si el ingrediente recogido está podrido (probabilidad aleatoria)."""
    rng = rng or random
    return rng.random() < prob


def generar_pedidos(ordenes: int, rng: random.Random | None = None) -> list[str]:
    rng = rng or random
    return [rng.choice(PEDIDOS) for _ in range(ordenes)]


def expandir_objetivos(pedidos: list[str]) -> list[tuple[int, int]]:
    objetivos: list[tuple[int, int]] = []
    for pedido in pedidos:
        # Extraer solo las coordenadas para la lógica, descartando la descripción
        secuencia_con_desc = OBJETIVOS_POR_PEDIDO[pedido]
        secuencia = [coord for coord, desc in secuencia_con_desc]

        if (3, 3) in secuencia:
            idx = secuencia.index((3, 3))
            # PLATOS ya contiene coordenadas (x, y), no (coord, descripcion)
            plato_coord = random.choice(PLATOS)
            secuencia.insert(idx + 1, plato_coord)
            secuencia.insert(idx + 2, (3, 3))

        if secuencia and secuencia[-1] == (16, 4):
            secuencia[-1] = random.choice(ENTREGAS)
        objetivos.extend(secuencia)
    return objetivos


def generar_objetivos_interceptor(ordenes: int, rng: random.Random | None = None) -> list[tuple[int, int]]:
    """
    Genera una secuencia de objetivos independiente para el interceptor.
    Usa una distribución diferente de pedidos para evitar traslape con el chef.
    """
    rng = rng or random
    
    # Generar pedidos con distribución invertida para maximizar diferenciación
    pedidos_interceptor = []
    
    # Si el chef podría generar mostly random, el interceptor usa patrón opuesto
    for i in range(ordenes):
        # Invertir el patrón: posiciones pares = sopa, impares = sopa_tomate
        if i % 2 == 0:
            pedidos_interceptor.append("sopa")
        else:
            pedidos_interceptor.append("sopa_tomate")
    
    # Mezclar los pedidos para mayor aleatoriedad pero manteniendo diversidad
    rng.shuffle(pedidos_interceptor)
    
    # Expandir objetivos con variaciones adicionales
    objetivos = []
    for i, pedido in enumerate(pedidos_interceptor):
        secuencia_con_desc = OBJETIVOS_POR_PEDIDO[pedido]
        secuencia = [coord for coord, desc in secuencia_con_desc]

        if (3, 3) in secuencia:
            idx = secuencia.index((3, 3))
            # Usar diferentes platos para el interceptor basado en índice
            plato_coord = PLATOS[i % len(PLATOS)]
            secuencia.insert(idx + 1, plato_coord)
            secuencia.insert(idx + 2, (3, 3))

        if secuencia and secuencia[-1] == (16, 4):
            # Alternar puntos de entrega para evitar coincidencias
            secuencia[-1] = ENTREGAS[i % len(ENTREGAS)]
        objetivos.extend(secuencia)
    
    return objetivos
