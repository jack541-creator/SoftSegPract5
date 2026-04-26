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
            
    def test_listar_usuarios(self):
        clave = "claveMaestraSegura123!"

        # Comprobación con lista vacía
        usuarios = self.gestor.listar_usuarios(clave)
        self.assertIsInstance(usuarios, list)
        self.assertIsNotNone(usuarios)
        self.assertEqual(usuarios, [])
        
        # Añadimos usuarios
        self.gestor.añadir_credencial(clave, "GitHub", "usuario1", "clave1")
        self.gestor.añadir_credencial(clave, "Eduroam", "usuario2", "clave2")
        self.gestor.añadir_credencial(clave, "GitHub", "usuario3", "clave3")
        usuarios = self.gestor.listar_usuarios(clave)
        self.assertCountEqual(usuarios, ["usuario1", "usuario2", "usuario3"])
        

        # Eliminamos usuarios
        self.gestor.eliminar_credencial(clave, "Eduroam", "usuario2")
        usuarios = self.gestor.listar_usuarios(clave)
        self.assertCountEqual(usuarios, ["usuario1", "usuario3"])
        

        # Eliminamos todo
        self.gestor.eliminar_credencial(clave, "GitHub", "usuario1")
        self.gestor.eliminar_credencial(clave, "GitHub", "usuario3")
        usuarios = self.gestor.listar_usuarios(clave)
        self.assertEqual(usuarios, [])
        
        # Error de autenticación
        with self.assertRaises(ErrorAutenticacion):
            self.gestor.listar_usuarios("claveIncorrecta")

if __name__ == "__main__":
    unittest.main()
