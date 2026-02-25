import random

PEDIDOS = ["sopa_tomate", "sopa"]

OBJETIVOS_POR_PEDIDO = {
    "sopa_tomate": [
        (13, 7),
        (5, 7),
        (3, 3),
        (16, 4),
    ],
    "sopa": [
        (15, 7),
        (5, 7),
        (3, 3),
        (16, 4),
    ],
}


def generar_pedidos(ordenes: int, rng: random.Random | None = None) -> list[str]:
    rng = rng or random
    return [rng.choice(PEDIDOS) for _ in range(ordenes)]


def expandir_objetivos(pedidos: list[str]) -> list[tuple[int, int]]:
    objetivos: list[tuple[int, int]] = []
    for pedido in pedidos:
        objetivos.extend(OBJETIVOS_POR_PEDIDO[pedido])
    return objetivos
