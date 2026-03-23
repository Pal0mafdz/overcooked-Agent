import random
import pytest

from src.systems.orders import verificar_ingrediente_podrido, INGREDIENTES


class TestVerificarIngredientePodrido:

    def test_siempre_podrido_con_probabilidad_1(self):
        """Con prob=1.0, el ingrediente SIEMPRE debe estar podrido."""
        for _ in range(20):
            assert verificar_ingrediente_podrido(prob=1.0) is True

    def test_nunca_podrido_con_probabilidad_0(self):
        """Con prob=0.0, el ingrediente NUNCA debe estar podrido."""
        for _ in range(20):
            assert verificar_ingrediente_podrido(prob=0.0) is False

    def test_determinismo_con_semilla_fija(self):
        """Con la misma semilla, el resultado siempre debe ser igual."""
        rng1 = random.Random(42)
        rng2 = random.Random(42)
        resultado1 = verificar_ingrediente_podrido(prob=0.3, rng=rng1)
        resultado2 = verificar_ingrediente_podrido(prob=0.3, rng=rng2)
        assert resultado1 == resultado2

    def test_retorna_booleano(self):
        """La función siempre debe retornar un booleano."""
        resultado = verificar_ingrediente_podrido(prob=0.5)
        assert isinstance(resultado, bool)

    def test_probabilidad_media_distribucion(self):
        """Con prob=0.5 y muchas muestras, ~50% deben ser podridos."""
        rng = random.Random(0)
        resultados = [verificar_ingrediente_podrido(prob=0.5, rng=rng) for _ in range(1000)]
        tasa_podridos = sum(resultados) / len(resultados)
        # Tolerancia del 10%
        assert 0.40 <= tasa_podridos <= 0.60, f"Tasa fuera de rango: {tasa_podridos}"

    def test_probabilidad_por_defecto(self):
        """La función debe aceptar llamada sin argumentos (usa prob=0.3 por defecto)."""
        resultado = verificar_ingrediente_podrido()
        assert isinstance(resultado, bool)


class TestIngredientes:

    def test_ingredientes_contiene_tomate(self):
        """La celda del tomate (13,7) debe estar en INGREDIENTES."""
        assert (13, 7) in INGREDIENTES

    def test_ingredientes_contiene_cebolla(self):
        """La celda de la cebolla (15,7) debe estar en INGREDIENTES."""
        assert (15, 7) in INGREDIENTES

    def test_ingredientes_es_conjunto(self):
        """INGREDIENTES debe ser un set para O(1) de búsqueda."""
        assert isinstance(INGREDIENTES, set)

    def test_ingredientes_tamano(self):
        """INGREDIENTES debe tener exactamente 2 posiciones."""
        assert len(INGREDIENTES) == 2
