from src.systems.orders import (
    calcular_limpieza_por_platos,
    calcular_puntaje_comida,
    evaluar_propina_difusa,
    TIEMPO_FUZZY,
    COMIDA_FUZZY,
    LIMPIEZA_FUZZY,
    PROPINA_FUZZY,
)


def test_calcular_puntaje_comida_sin_podridos():
    assert calcular_puntaje_comida(total_ingredientes=3, ingredientes_podridos=0) == 5.0


def test_calcular_puntaje_comida_todo_podrido():
    assert calcular_puntaje_comida(total_ingredientes=3, ingredientes_podridos=3) == 0.0


def test_calcular_limpieza_por_platos_basico():
    assert calcular_limpieza_por_platos(platos_sucios=0, platos_pendientes=0, capacidad=3) == 0.0
    assert calcular_limpieza_por_platos(platos_sucios=2, platos_pendientes=1, capacidad=3) == 100.0


def test_propina_alta_en_escenario_ideal():
    resultado = evaluar_propina_difusa(tiempo_segundos=20, comida=5, limpieza=5)
    assert 16.0 <= resultado["propina"] <= 20.0


def test_propina_baja_en_escenario_malo():
    resultado = evaluar_propina_difusa(tiempo_segundos=180, comida=1.5, limpieza=40)
    assert 0.0 <= resultado["propina"] <= 4.0


def test_propina_cero_por_limpieza_asquerosa():
    resultado = evaluar_propina_difusa(tiempo_segundos=40, comida=5, limpieza=95)
    assert 0.0 <= resultado["propina"] <= 3.0

def test_pesos_difusos_activos_respetan_dominios():
    dominios = [
        (TIEMPO_FUZZY, 0.0, 300.0),
        (COMIDA_FUZZY, 0.0, 5.0),
        (LIMPIEZA_FUZZY, 0.0, 100.0),
        (PROPINA_FUZZY, 0.0, 20.0),
    ]

    for config, minimo, maximo in dominios:
        for shape in config.values():
            assert all(minimo <= value <= maximo for value in shape)
            assert all(shape[i] <= shape[i + 1] for i in range(len(shape) - 1))
