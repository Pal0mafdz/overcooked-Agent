import random

from src.systems.orders import (
    ENTREGAS,
    INGREDIENTES,
    PLATOS,
    evaluar_propina_difusa,
    generar_objetivos_interceptor,
)


def test_caja_negra_interceptor_con_cero_ordenes():
    resultado = generar_objetivos_interceptor(0, rng=random.Random(7))
    assert resultado == []


def test_caja_negra_interceptor_estructura_valida():
    ordenes = 3
    resultado = generar_objetivos_interceptor(ordenes, rng=random.Random(7))

    puntos_validos = set(INGREDIENTES) | set(PLATOS) | {(5, 3), (3, 7)} | set(ENTREGAS)

    assert isinstance(resultado, list)
    assert len(resultado) == 12 * ordenes
    assert all(isinstance(p, tuple) and len(p) == 2 for p in resultado)
    assert all(p in puntos_validos for p in resultado)
    assert sum(1 for p in resultado if p in ENTREGAS) == ordenes
    assert resultado[-1] in ENTREGAS


def test_caja_negra_propina_recorta_entradas_fuera_de_rango():
    resultado = evaluar_propina_difusa(
        tiempo_segundos=-50,
        comida=9,
        limpieza=150,
    )

    assert 0.0 <= resultado["propina"] <= 20.0
    assert resultado["tiempo"] == 0.0
    assert resultado["comida"] == 5.0
    assert resultado["limpieza"] == 100.0


def test_caja_negra_propina_escenario_bueno_supera_al_malo():
    malo = evaluar_propina_difusa(
        tiempo_segundos=220,
        comida=1.0,
        limpieza=95.0,
    )["propina"]

    bueno = evaluar_propina_difusa(
        tiempo_segundos=20,
        comida=5.0,
        limpieza=0.0,
    )["propina"]

    assert 0.0 <= malo <= 20.0
    assert 0.0 <= bueno <= 20.0
    assert bueno > malo


def test_caja_negra_propina_escenario_intermedio_da_valor_intermedio():
    medio = evaluar_propina_difusa(
        tiempo_segundos=75,
        comida=3.0,
        limpieza=40.0,
    )["propina"]

    assert 4.0 <= medio <= 16.0