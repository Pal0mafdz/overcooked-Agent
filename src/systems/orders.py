import random

PEDIDOS = ["sopa_tomate", "sopa"]

PLATOS = [
    ((12, 3), "Ir por plato 1"),
    ((13, 3), "Ir por plato 2"),
    ((14, 3), "Ir por plato 3"),
]

ENTREGAS = [(16, 4), (16, 5)]

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
            # Elegir un plato y extraer solo sus coordenadas
            plato_coord, plato_desc = random.choice(PLATOS)
            secuencia.insert(idx + 1, plato_coord)
            secuencia.insert(idx + 2, (3, 3))

        if secuencia and secuencia[-1] == (16, 4):
            secuencia[-1] = random.choice(ENTREGAS)
        objetivos.extend(secuencia)
    return objetivos
