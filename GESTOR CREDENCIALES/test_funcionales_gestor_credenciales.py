import unittest
from src.gestor_credenciales.gestor_credenciales import GestorCredenciales, ErrorPoliticaPassword, ErrorAutenticacion
from hypothesis import given
from hypothesis.strategies import text


class TestFuncionalesGestorCredenciales(unittest.TestCase):
    def setUp(self):
        self.gestor = GestorCredenciales("claveMaestraSegura123!")

    # Tests funcionales
    def test_añadir_credencial(self):
        
        self.fail()

    def test_recuperar_credencial(self):
        
        self.fail()

    def test_listar_servicios(self):
        
        self.fail()

if __name__ == "__main__":
    unittest.main()
