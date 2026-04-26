import unittest
from src.gestor_credenciales.gestor_credenciales import GestorCredenciales, ErrorPoliticaPassword, ErrorAutenticacion
from hypothesis import given
from hypothesis.strategies import text


class TestFuncionalesGestorCredenciales(unittest.TestCase):
    def setUp(self):
        self.gestor = GestorCredenciales("claveMaestraSegura123!")

    # Tests funcionales
    def test_añadir_credencial(self):
        # Implementar según TDD
        self.fail()

    def test_recuperar_credencial(self):
        # Implementar según TDD
        self.fail()

    def test_listar_servicios(self):
        clave = "claveMaestraSegura123!"

        servicios = self.gestor.listar_servicios(clave)
        self.assertIsInstance(servicios, list)
        self.assertIsNotNone(servicios)
        self.assertEqual(servicios, [])

        self.gestor.añadir_credencial(clave, "GitHub", "user1", "PasswordSegura123!")
        self.gestor.añadir_credencial(clave, "Eduroam", "user2", "PasswordSegura123!")
        self.gestor.añadir_credencial(clave, "GitHub", "user3", "PasswordSegura123!")

        servicios = self.gestor.listar_servicios(clave)
        self.assertCountEqual(servicios, ["GitHub", "Eduroam"])

        self.gestor.eliminar_credencial(clave, "Eduroam", "user2")
        servicios = self.gestor.listar_servicios(clave)
        self.assertEqual(servicios, ["GitHub"])

        # eliminar todo
        self.gestor.eliminar_credencial(clave, "GitHub", "user1")
        self.gestor.eliminar_credencial(clave, "GitHub", "user3")

        servicios = self.gestor.listar_servicios(clave)
        self.assertEqual(servicios, [])

        # autenticación
        with self.assertRaises(ErrorAutenticacion):
            self.gestor.listar_servicios("claveIncorrecta")

if __name__ == "__main__":
    unittest.main()
