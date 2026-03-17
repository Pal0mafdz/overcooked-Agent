from src.systems.orders import generar_objetivos_interceptor, ENTREGAS

def test_generar_objetivos_interceptor_caja_negra():
    cantidad_ordenes = 2

    resultado = generar_objetivos_interceptor(cantidad_ordenes)

    print("\n === RESULTADO DE PRUEBA CAJA NEGRA ===")
    print("Ordenes de entrada:", cantidad_ordenes)
    print("Secuencia generada:", resultado)
    print("Tipo de resultado:", type(resultado))
    print("Longitud de la secuencia:", len(resultado))
    print("Ultimo punto: ", resultado[-1] if resultado else None)
    print("Terminación con una entrega valida:", resultado[-1] in ENTREGAS if resultado else False)

    assert isinstance(resultado, list), "El resultado debe ser una lista"
    assert len(resultado) > 0, "La secuencia no debe estar vacía"
    assert all(isinstance(punto, tuple) for punto in resultado), "Todos los elementos de la secuencia deben ser tuplas"
    assert resultado[-1] in ENTREGAS, "El último punto debe ser una entrega válida"