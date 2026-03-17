from src.systems.orders import generar_objetivos_interceptor, ENTREGAS
import time

def test_generar_objetivos_interceptor_estres():
    cantidad_ordenes = 500000

    inicio = time.time()
    resultado = generar_objetivos_interceptor(cantidad_ordenes)
    fin = time.time()

    duracion = fin - inicio

    print("\n === RESULTADO DE PRUEBA DE ESTRÉS ===")
    print("Cantidad de órdenes:", cantidad_ordenes)
    print("Longitud de la secuencia generada:", len(resultado))
    print("Tiempo de ejecución", duracion, "segundos")
    print("Ultimo punto: ", resultado[-1] if resultado else None)
    print("Terminación con una entrega válida:", resultado[-1] in ENTREGAS if resultado else False)

    assert isinstance(resultado, list), "El resultado debe ser una lista"
    assert len(resultado) > 0, "La secuencia no debe estar vacía"
    assert resultado[-1] in ENTREGAS, "El último punto debe ser una entrega válida"
    assert duracion < 1.5, "La función debe ejecutarse en menos de 1.5 segundos para las órdenes dadas"
    