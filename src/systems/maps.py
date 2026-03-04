import random

MAPA_ORIGINAL = [
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0],
    [0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
    [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
    [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
    [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
    [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0],
    [0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
]


def generar_pozo_y_olores(mapa: list[list[int]], chef_pos: list[int], objetivos: list[tuple[int, int]]):
    celdas_libres = []
    for y in range(len(mapa)):
        for x in range(len(mapa[0])):
            if mapa[y][x] == 1 and (x, y) != tuple(chef_pos) and (x, y) not in objetivos:
                celdas_libres.append((x, y))

    pozo = random.choice(celdas_libres)
    olores = []
    for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
        nx, ny = pozo[0] + dx, pozo[1] + dy
        if 0 <= nx < len(mapa[0]) and 0 <= ny < len(mapa) and mapa[ny][nx] == 1:
            olores.append((nx, ny))

    return pozo, olores


def generar_pozos_y_olores(
    mapa: list[list[int]],
    chef_pos: list[int],
    objetivos: list[tuple[int, int]],
    cantidad_pozos: int = 2,
    celdas_prohibidas: list[tuple[int, int]] | None = None,
):
    celdas_libres = []
    prohibidas = set(celdas_prohibidas or [])
    for y in range(len(mapa)):
        for x in range(len(mapa[0])):
            if (
                mapa[y][x] == 1
                and (x, y) != tuple(chef_pos)
                and (x, y) not in objetivos
                and (x, y) not in prohibidas
            ):
                celdas_libres.append((x, y))

    cantidad = min(cantidad_pozos, len(celdas_libres))
    pozos = random.sample(celdas_libres, k=cantidad)

    zonas_olor: list[tuple[int, int]] = []
    for pozo in pozos:
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = pozo[0] + dx, pozo[1] + dy
            if 0 <= nx < len(mapa[0]) and 0 <= ny < len(mapa) and mapa[ny][nx] == 1:
                zonas_olor.append((nx, ny))

    zonas_olor = list(dict.fromkeys(zonas_olor))
    return pozos, zonas_olor
