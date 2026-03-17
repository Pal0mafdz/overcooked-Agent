from src.systems.orders import generar_pedidos, PEDIDOS
import random

def test_generar_pedidos():
    rng = random.Random(100)
    resultado = generar_pedidos(3, rng)
    
    print("Pedidos generados: ", resultado)
    print("Cantidad :", len(resultado))
    print("Pedidos válidos: ", all(pedido in PEDIDOS for pedido in resultado))

    assert isinstance(resultado, list), "El resultado debe ser una lista"
    assert len(resultado) == 3, "La lista debe contener 3 pedidos"
    assert all(pedido in PEDIDOS for pedido in resultado), "Todos los pedidos deben estar en la lista de pedidos disponibles"