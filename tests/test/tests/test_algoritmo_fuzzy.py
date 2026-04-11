from src.systems.orders import (
    COMIDA_FUZZY,
    DEFAULT_COMIDA_FUZZY,
    DEFAULT_LIMPIEZA_FUZZY,
    DEFAULT_PROPINA_FUZZY,
    DEFAULT_TIEMPO_FUZZY,
    LIMPIEZA_FUZZY,
    PROPINA_FUZZY,
    TIEMPO_FUZZY,
    evaluar_propina_difusa,
)


def _config_valida(config, referencia, minimo, maximo):
    assert set(config.keys()) == set(referencia.keys())

    for etiqueta, shape in config.items():
        assert len(shape) == len(referencia[etiqueta])
        assert all(minimo <= valor <= maximo for valor in shape)
        assert all(shape[i] <= shape[i + 1] for i in range(len(shape) - 1))


def test_algoritmo_pesos_activos_respetan_dominios():
    _config_valida(TIEMPO_FUZZY, DEFAULT_TIEMPO_FUZZY, 0.0, 300.0)
    _config_valida(COMIDA_FUZZY, DEFAULT_COMIDA_FUZZY, 0.0, 5.0)
    _config_valida(LIMPIEZA_FUZZY, DEFAULT_LIMPIEZA_FUZZY, 0.0, 100.0)
    _config_valida(PROPINA_FUZZY, DEFAULT_PROPINA_FUZZY, 0.0, 20.0)


def test_algoritmo_monotonia_por_tiempo():
    rapido = evaluar_propina_difusa(30, 5.0, 5.0)["propina"]
    regular = evaluar_propina_difusa(80, 5.0, 5.0)["propina"]
    tardado = evaluar_propina_difusa(200, 5.0, 5.0)["propina"]

    assert rapido >= regular
    assert regular >= tardado


def test_algoritmo_monotonia_por_comida():
    mala = evaluar_propina_difusa(40, 1.0, 5.0)["propina"]
    normal = evaluar_propina_difusa(40, 3.0, 5.0)["propina"]
    sabrosa = evaluar_propina_difusa(40, 5.0, 5.0)["propina"]

    assert mala <= normal
    assert normal <= sabrosa


def test_algoritmo_monotonia_por_limpieza():
    impecable = evaluar_propina_difusa(40, 5.0, 5.0)["propina"]
    aceptable = evaluar_propina_difusa(40, 5.0, 40.0)["propina"]
    asquerosa = evaluar_propina_difusa(40, 5.0, 95.0)["propina"]

    assert impecable >= aceptable
    assert aceptable >= asquerosa


def test_algoritmo_escenarios_representativos():
    ideal = evaluar_propina_difusa(20, 5.0, 0.0)["propina"]
    malo = evaluar_propina_difusa(180, 1.5, 40.0)["propina"]
    sucio = evaluar_propina_difusa(40, 5.0, 95.0)["propina"]

    assert 16.0 <= ideal <= 20.0
    assert 0.0 <= malo <= 4.0
    assert 0.0 <= sucio <= 3.0