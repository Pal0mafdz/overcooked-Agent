import random

PEDIDOS = ["sopa_tomate", "sopa"]

PLATOS = [(12, 3), (13, 3), (14, 3)]

ENTREGAS = [(16, 4), (16, 5)]

OBJETIVOS_POR_PEDIDO = {
    "sopa_tomate": [
        (13, 7), # Ir por tomate
        (5, 7),  # Cortar tomate
        (3, 3),  # Llevar tomate a la olla
        (16, 4), # Entregar orden
    ],
    "sopa": [
        (15, 7), # Ir por cebolla
        (5, 7),  # Cortar cebolla
        (3, 3),  # Llevar cebolla a la olla
        (16, 4), # Entregar orden
    ],
}


def generar_pedidos(ordenes: int, rng: random.Random | None = None) -> list[str]:
    rng = rng or random
    return [rng.choice(PEDIDOS) for _ in range(ordenes)]


def expandir_objetivos(pedidos: list[str]) -> list[tuple[int, int]]:
    objetivos: list[tuple[int, int]] = []
    for pedido in pedidos:
        secuencia = list(OBJETIVOS_POR_PEDIDO[pedido])
        if (3, 3) in secuencia:
            idx = secuencia.index((3, 3))
            plato = random.choice(PLATOS)
            secuencia.insert(idx + 1, plato)
            secuencia.insert(idx + 2, (3, 3))

        if secuencia and secuencia[-1] == (16, 4):
            secuencia[-1] = random.choice(ENTREGAS)
        objetivos.extend(secuencia)
    return objetivos
