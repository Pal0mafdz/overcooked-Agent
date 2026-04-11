from src.systems.orders import expandir_objetivos, ENTREGAS
from unittest.mock import patch

def test_expandir_objetivos_caja_blanca():
    pedidos = ['sopa']

    with patch("src.systems.orders.random.choice") as mock_choice:
        # 1ra llamada: plato
        # 2da llamada: entrega final
        mock_choice.side_effect = [(1, 5), (16, 5)]

        resultado = expandir_objetivos(pedidos)

    print("\n === RESULTADO DE PRUEBA CAJA BLANCA ===")
    print("Secuencia generada: ", resultado)
    print("Longitud: ", len(resultado))
    print("Contiene olla (3,3): ", (3, 3) in resultado)
    print("Contiene plato (1,5): ", (1, 5) in resultado)
    print("Entrega final: ", resultado[-1] in ENTREGAS)
    print("Ultimo punto: ", resultado[-1])

    assert isinstance(resultado, list), "El resultado debe ser una lista"
    assert (3, 3) in resultado, "La secuencia debe contener el punto de la olla (3,3)"
    assert (1, 5) in resultado, "La secuencia debe contener el punto del plato (1,5)"
    assert resultado[-1] in ENTREGAS, "El último punto debe ser una entrega válida"
    assert len(resultado) > 4, "La secuencia debe contener al menos 3 puntos (olla, plato, entrega)"