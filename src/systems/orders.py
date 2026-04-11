import json
import os
import json
import os
import random
from typing import Dict
from typing import Dict

PEDIDOS = ["sopa_tomate", "sopa"]

PLATOS = [(1, 5), (1, 4), (1, 3)]
PLATOS = [(1, 5), (1, 4), (1, 3)]

ENTREGAS = [(16, 4), (16, 5)]

# Dos ollas disponibles; la primera es la predeterminada
OLLAS = [(3, 3), (5, 3)]

# Dos tablas de corte disponibles; la primera es la predeterminada
TABLAS = [(5, 7), (3, 7)]

# Celdas donde se recogen ingredientes
INGREDIENTES = {(13, 7), (15, 7)}  # (13,7) = tomate, (15,7) = cebolla

# Dos ollas disponibles; la primera es la predeterminada
OLLAS = [(3, 3), (5, 3)]

# Dos tablas de corte disponibles; la primera es la predeterminada
TABLAS = [(5, 7), (3, 7)]

# Celdas donde se recogen ingredientes
INGREDIENTES = {(13, 7), (15, 7)}  # (13,7) = tomate, (15,7) = cebolla

OBJETIVOS_POR_PEDIDO = {
    "sopa_tomate": [
        ((13, 7), "Ir por tomate 1"),
        ((5, 7), "Cortar tomate 1"),
        ((3, 3), "Llevar tomate 1 a la olla"),
        ((13, 7), "Ir por tomate 2"),
        ((5, 7), "Cortar tomate 2"),
        ((3, 3), "Llevar tomate 2 a la olla"),
        ((13, 7), "Ir por tomate 3"),
        ((5, 7), "Cortar tomate 3"),
        ((3, 3), "Llevar tomate 3 a la olla"),
        ((16, 4), "Entregar orden"),
        ((13, 7), "Ir por tomate 1"),
        ((5, 7), "Cortar tomate 1"),
        ((3, 3), "Llevar tomate 1 a la olla"),
        ((13, 7), "Ir por tomate 2"),
        ((5, 7), "Cortar tomate 2"),
        ((3, 3), "Llevar tomate 2 a la olla"),
        ((13, 7), "Ir por tomate 3"),
        ((5, 7), "Cortar tomate 3"),
        ((3, 3), "Llevar tomate 3 a la olla"),
        ((16, 4), "Entregar orden"),
    ],
    "sopa": [
        ((15, 7), "Ir por cebolla 1"),
        ((5, 7), "Cortar cebolla 1"),
        ((3, 3), "Llevar cebolla 1 a la olla"),
        ((15, 7), "Ir por cebolla 2"),
        ((5, 7), "Cortar cebolla 2"),
        ((3, 3), "Llevar cebolla 2 a la olla"),
        ((15, 7), "Ir por cebolla 3"),
        ((5, 7), "Cortar cebolla 3"),
        ((3, 3), "Llevar cebolla 3 a la olla"),
        ((16, 4), "Entregar orden"),
    ],
}


def verificar_ingrediente_podrido(prob: float = 0.3, rng=None) -> bool:
    """Retorna True si el ingrediente recogido está podrido (probabilidad aleatoria)."""
    rng = rng or random
    return rng.random() < prob


def _triangular(x: float, a: float, b: float, c: float) -> float:
    if x <= a or x >= c:
        return 0.0
    if x == b:
        return 1.0
    if x < b:
        return (x - a) / (b - a)
    return (c - x) / (c - b)


def _trapezoidal(x: float, a: float, b: float, c: float, d: float) -> float:
    if x < a or x > d:
        return 0.0
    if b <= x <= c:
        return 1.0
    if a <= x < b:
        # Soporta hombro izquierdo cuando a == b
        return 1.0 if b == a else (x - a) / (b - a)
    if c < x <= d:
        # Soporta hombro derecho cuando c == d
        return 1.0 if d == c else (d - x) / (d - c)
    # Soporta hombro derecho cuando c == d
    return 0.0


def _membership(x: float, shape: tuple[float, ...]) -> float:
    if len(shape) == 3:
        return _triangular(x, shape[0], shape[1], shape[2])
    return _trapezoidal(x, shape[0], shape[1], shape[2], shape[3])


DEFAULT_TIEMPO_FUZZY = {
    "muy_tardado": (130.0, 180.0, 300.0, 300.0),
    "tardado": (90.0, 120.0, 150.0),
    "regular": (55.0, 75.0, 100.0),
    "rapido": (35.0, 50.0, 65.0),
    "muy_rapido": (0.0, 0.0, 30.0, 45.0),
}

DEFAULT_COMIDA_FUZZY = {
    "muy_mala": (0.0, 0.0, 1.0, 2.0),
    "mala": (1.0, 2.0, 3.0),
    "normal": (2.0, 3.0, 4.0),
    "buena": (3.0, 4.0, 4.5),
    "sabrosa": (4.0, 4.5, 5.0, 5.0),
}

DEFAULT_LIMPIEZA_FUZZY = {
    "asquerosa": (80.0, 90.0, 100.0, 100.0),
    "descuidada": (50.0, 70.0, 85.0),
    "aceptable": (15.0, 40.0, 60.0),
    "impecable": (0.0, 0.0, 10.0, 20.0),
}

DEFAULT_PROPINA_FUZZY = {
    "nada": (0.0, 0.0, 1.0, 2.5),
    "poca": (1.0, 5.0, 7.0),
    "normal": (6.0, 10.0, 12.5),
    "suficiente": (11.0, 15.0, 18.0),
    "mucha": (17.0, 19.0, 20.0, 20.0),
}
FUZZY_DOMAIN_SPECS = {
    "TIEMPO_FUZZY": (DEFAULT_TIEMPO_FUZZY, 0.0, 300.0),
    "COMIDA_FUZZY": (DEFAULT_COMIDA_FUZZY, 0.0, 5.0),
    "LIMPIEZA_FUZZY": (DEFAULT_LIMPIEZA_FUZZY, 0.0, 100.0),
    "PROPINA_FUZZY": (DEFAULT_PROPINA_FUZZY, 0.0, 20.0),
}


def _shape_is_valid(shape: tuple[float, ...], expected_len: int, min_value: float, max_value: float) -> bool:
    if len(shape) != expected_len:
        return False
    numeric = []
    for value in shape:
        if not isinstance(value, (int, float)):
            return False
        numeric.append(float(value))
    if any(value < min_value or value > max_value for value in numeric):
        return False
    return all(numeric[i] <= numeric[i + 1] for i in range(len(numeric) - 1))


def _validate_fuzzy_block(block_name: str, raw_block: dict) -> dict[str, tuple[float, ...]]:
    defaults, min_value, max_value = FUZZY_DOMAIN_SPECS[block_name]
    if set(raw_block.keys()) != set(defaults.keys()):
        raise ValueError(f"Las etiquetas de {block_name} no coinciden con la configuración base")

    validated = {}
    for label, default_shape in defaults.items():
        raw_shape = raw_block[label]
        shape = tuple(float(value) for value in raw_shape)
        if not _shape_is_valid(shape, len(default_shape), min_value, max_value):
            raise ValueError(
                f"La etiqueta '{label}' de {block_name} tiene puntos fuera de rango o desordenados: {shape}"
            )
        validated[label] = shape
    return validated


def _load_valid_trained_weights(weights_path: str):
    with open(weights_path, 'r', encoding='utf-8') as file:
        data = json.load(file)

    validated_blocks = {}
    for block_name in FUZZY_DOMAIN_SPECS:
        if block_name in data:
            validated_blocks[block_name] = _validate_fuzzy_block(block_name, data[block_name])
    return validated_blocks

# Asignaciones Activas
TIEMPO_FUZZY = DEFAULT_TIEMPO_FUZZY.copy()
COMIDA_FUZZY = DEFAULT_COMIDA_FUZZY.copy()
LIMPIEZA_FUZZY = DEFAULT_LIMPIEZA_FUZZY.copy()
PROPINA_FUZZY = DEFAULT_PROPINA_FUZZY.copy()

# Auto-cargar pesos entrenados (JSON) si existen
_weights_path = os.path.join(os.path.dirname(__file__), "fuzzy_weights.json")
if os.path.exists(_weights_path):
    try:
        _validated_data = _load_valid_trained_weights(_weights_path)
        if "TIEMPO_FUZZY" in _validated_data:
            TIEMPO_FUZZY = _validated_data["TIEMPO_FUZZY"]
        if "COMIDA_FUZZY" in _validated_data:
            COMIDA_FUZZY = _validated_data["COMIDA_FUZZY"]
        if "LIMPIEZA_FUZZY" in _validated_data:
            LIMPIEZA_FUZZY = _validated_data["LIMPIEZA_FUZZY"]
        if "PROPINA_FUZZY" in _validated_data:
            PROPINA_FUZZY = _validated_data["PROPINA_FUZZY"]
        print(f"[Orders] Cargados pesos difusos optimizados desde {_weights_path}")
    except Exception as _e:
        print(f"[Orders] Pesos entrenados ignorados por inválidos: {_e}")
        
REGLAS_PROPINA = [
    ({"limpieza": "asquerosa"}, "nada"),
    ({"comida": "muy_mala"}, "nada"),
    ({"tiempo": "muy_tardado", "comida": "mala"}, "nada"),
    ({"comida": "sabrosa", "tiempo": "muy_rapido", "limpieza": "impecable"}, "mucha"),
    ({"comida": "sabrosa", "tiempo": "rapido", "limpieza": "impecable"}, "mucha"),
    ({"comida": "sabrosa", "tiempo": "regular", "limpieza": "aceptable"}, "suficiente"),
    ({"comida": "sabrosa", "tiempo": "tardado", "limpieza": "aceptable"}, "suficiente"),
    ({"comida": "sabrosa", "tiempo": "muy_tardado", "limpieza": "aceptable"}, "suficiente"),
    ({"comida": "buena", "tiempo": "muy_rapido", "limpieza": "impecable"}, "suficiente"),
    ({"comida": "buena", "tiempo": "rapido", "limpieza": "impecable"}, "suficiente"),
    ({"comida": "buena", "tiempo": "regular", "limpieza": "aceptable"}, "suficiente"),
    ({"comida": "buena", "tiempo": "tardado", "limpieza": "aceptable"}, "suficiente"),
    ({"comida": "buena", "tiempo": "muy_tardado", "limpieza": "aceptable"}, "normal"),
    ({"comida": "normal", "tiempo": "muy_rapido", "limpieza": "aceptable"}, "normal"),
    ({"comida": "normal", "tiempo": "rapido", "limpieza": "aceptable"}, "normal"),
    ({"comida": "normal", "tiempo": "regular", "limpieza": "aceptable"}, "normal"),
    ({"comida": "normal", "tiempo": "tardado", "limpieza": "aceptable"}, "poca"),
    ({"comida": "normal", "tiempo": "muy_tardado", "limpieza": "aceptable"}, "poca"),
    ({"comida": "mala", "tiempo": "muy_rapido", "limpieza": "aceptable"}, "poca"),
    ({"comida": "mala", "tiempo": "rapido", "limpieza": "aceptable"}, "poca"),
    ({"comida": "mala", "tiempo": "regular", "limpieza": "aceptable"}, "poca"),
    ({"comida": "mala", "tiempo": "tardado"}, "nada"),
    ({"comida": "mala", "tiempo": "muy_tardado"}, "nada"),
    ({"limpieza": "descuidada", "comida": "sabrosa"}, "normal"),
    ({"limpieza": "descuidada", "comida": "buena"}, "poca"),
    ({"limpieza": "descuidada", "tiempo": "tardado"}, "nada"),
]


def calcular_puntaje_comida(total_ingredientes: int, ingredientes_podridos: int) -> float:
    """Convierte ingredientes podridos en puntaje de comida [0, 5]."""
    total = max(1, total_ingredientes)
    podridos = max(0, min(ingredientes_podridos, total))
    frescura = 1.0 - (podridos / total)
    return round(max(0.0, min(5.0, frescura * 5.0)), 3)


def calcular_limpieza_por_platos(platos_sucios: int, platos_pendientes: int, capacidad: int = 3) -> float:
    """Mapea la suciedad de cocina a rango [0, 100], donde 0 es impecable."""
    total_sucios = max(0, platos_sucios) + max(0, platos_pendientes)
    capacidad_segura = max(1, capacidad)
    ratio = min(1.0, total_sucios / capacidad_segura)
    return round(ratio * 100.0, 3)


def evaluar_propina_difusa(
    tiempo_segundos: float, 
    comida: float, 
    limpieza: float,
    config_tiempo: dict = None,
    config_comida: dict = None,
    config_limpieza: dict = None,
    config_propina: dict = None
) -> Dict[str, float]:
    """Evalua la propina (0-20) con inferencia difusa tipo Mamdani + centroide."""
    config_tiempo = config_tiempo if config_tiempo is not None else TIEMPO_FUZZY
    config_comida = config_comida if config_comida is not None else COMIDA_FUZZY
    config_limpieza = config_limpieza if config_limpieza is not None else LIMPIEZA_FUZZY
    config_propina = config_propina if config_propina is not None else PROPINA_FUZZY

    tiempo_val = max(0.0, min(300.0, float(tiempo_segundos)))
    comida_val = max(0.0, min(5.0, float(comida)))
    limpieza_val = max(0.0, min(100.0, float(limpieza)))

    grados_tiempo = {k: _membership(tiempo_val, v) for k, v in config_tiempo.items()}
    grados_comida = {k: _membership(comida_val, v) for k, v in config_comida.items()}
    grados_limpieza = {k: _membership(limpieza_val, v) for k, v in config_limpieza.items()}

    activaciones_salida = {etiqueta: 0.0 for etiqueta in config_propina}
    for antecedente, consecuente in REGLAS_PROPINA:
        grados = []
        if "tiempo" in antecedente:
            grados.append(grados_tiempo[antecedente["tiempo"]])
        if "comida" in antecedente:
            grados.append(grados_comida[antecedente["comida"]])
        if "limpieza" in antecedente:
            grados.append(grados_limpieza[antecedente["limpieza"]])

        fuerza_regla = min(grados) if grados else 0.0
        if fuerza_regla > activaciones_salida[consecuente]:
            activaciones_salida[consecuente] = fuerza_regla

    universo = [i / 10 for i in range(0, 201)]  # 0.0 .. 20.0
    numerador = 0.0
    denominador = 0.0
    for x in universo:
        pertenencia_agregada = 0.0
        for etiqueta, shape in config_propina.items():
            pertenencia = _membership(x, shape)
            recorte = min(activaciones_salida[etiqueta], pertenencia)
            if recorte > pertenencia_agregada:
                pertenencia_agregada = recorte
        numerador += x * pertenencia_agregada
        denominador += pertenencia_agregada

    if denominador == 0.0:
        propina = 0.0
    else:
        propina = numerador / denominador

    return {
        "propina": round(max(0.0, min(20.0, propina)), 3),
        "tiempo": tiempo_val,
        "comida": comida_val,
        "limpieza": limpieza_val,
    }


def generar_pedidos(ordenes: int, rng: random.Random | None = None) -> list[str]:
    rng = rng or random
    return [rng.choice(PEDIDOS) for _ in range(ordenes)]


def expandir_objetivos(pedidos: list[str]) -> list[tuple[int, int]]:
    objetivos: list[tuple[int, int]] = []
    # Chef 1: Olla 1 (3, 3) y Tabla 1 (5, 7)
    olla_asignada = (3, 3)
    tabla_asignada = (5, 7)

    # Chef 1: Olla 1 (3, 3) y Tabla 1 (5, 7)
    olla_asignada = (3, 3)
    tabla_asignada = (5, 7)

    for pedido in pedidos:
        secuencia_con_desc = OBJETIVOS_POR_PEDIDO[pedido]
        secuencia = []
        for coord, desc in secuencia_con_desc:
            if coord == (3, 3):
                secuencia.append(olla_asignada)
            elif coord == (5, 7):
                secuencia.append(tabla_asignada)
            else:
                secuencia.append(coord)

        if olla_asignada in secuencia:
            # Buscar el último index() invirtiendo la lista
            idx = len(secuencia) - 1 - secuencia[::-1].index(olla_asignada)
            plato_coord = random.choice(PLATOS)
            secuencia.insert(idx + 1, plato_coord)
            secuencia.insert(idx + 2, olla_asignada)
        secuencia_con_desc = OBJETIVOS_POR_PEDIDO[pedido]
        secuencia = []
        for coord, desc in secuencia_con_desc:
            if coord == (3, 3):
                secuencia.append(olla_asignada)
            elif coord == (5, 7):
                secuencia.append(tabla_asignada)
            else:
                secuencia.append(coord)

        if olla_asignada in secuencia:
            # Buscar el último index() invirtiendo la lista
            idx = len(secuencia) - 1 - secuencia[::-1].index(olla_asignada)
            plato_coord = random.choice(PLATOS)
            secuencia.insert(idx + 1, plato_coord)
            secuencia.insert(idx + 2, olla_asignada)

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
    
    # Interceptor: Olla 2 (5, 3) y Tabla 2 (3, 7)
    olla_asignada = (5, 3)
    tabla_asignada = (3, 7)

    # Mezclar los pedidos para mayor aleatoriedad pero manteniendo diversidad
    rng.shuffle(pedidos_interceptor)
    
    # Expandir objetivos con variaciones adicionales
    objetivos = []
    for i, pedido in enumerate(pedidos_interceptor):
        secuencia_con_desc = OBJETIVOS_POR_PEDIDO[pedido]
        secuencia = []
        for coord, desc in secuencia_con_desc:
            if coord == (3, 3):
                secuencia.append(olla_asignada)
            elif coord == (5, 7):
                secuencia.append(tabla_asignada)
            else:
                secuencia.append(coord)

        if olla_asignada in secuencia:
            # Buscar el último index() invirtiendo la lista
            idx = len(secuencia) - 1 - secuencia[::-1].index(olla_asignada)
            # Usar diferentes platos para el interceptor basado en índice
            plato_coord = PLATOS[i % len(PLATOS)]
            secuencia.insert(idx + 1, plato_coord)
            secuencia.insert(idx + 2, olla_asignada)

        if secuencia and secuencia[-1] == (16, 4):
            # Alternar puntos de entrega para evitar coincidencias
            secuencia[-1] = ENTREGAS[i % len(ENTREGAS)]
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
    
    # Interceptor: Olla 2 (5, 3) y Tabla 2 (3, 7)
    olla_asignada = (5, 3)
    tabla_asignada = (3, 7)

    # Mezclar los pedidos para mayor aleatoriedad pero manteniendo diversidad
    rng.shuffle(pedidos_interceptor)
    
    # Expandir objetivos con variaciones adicionales
    objetivos = []
    for i, pedido in enumerate(pedidos_interceptor):
        secuencia_con_desc = OBJETIVOS_POR_PEDIDO[pedido]
        secuencia = []
        for coord, desc in secuencia_con_desc:
            if coord == (3, 3):
                secuencia.append(olla_asignada)
            elif coord == (5, 7):
                secuencia.append(tabla_asignada)
            else:
                secuencia.append(coord)

        if olla_asignada in secuencia:
            # Buscar el último index() invirtiendo la lista
            idx = len(secuencia) - 1 - secuencia[::-1].index(olla_asignada)
            # Usar diferentes platos para el interceptor basado en índice
            plato_coord = PLATOS[i % len(PLATOS)]
            secuencia.insert(idx + 1, plato_coord)
            secuencia.insert(idx + 2, olla_asignada)

        if secuencia and secuencia[-1] == (16, 4):
            # Alternar puntos de entrega para evitar coincidencias
            secuencia[-1] = ENTREGAS[i % len(ENTREGAS)]
        objetivos.extend(secuencia)
    
    return objetivos
