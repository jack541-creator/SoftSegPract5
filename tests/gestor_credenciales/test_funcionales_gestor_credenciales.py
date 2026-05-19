import unittest
from src.gestor_credenciales.gestor_credenciales import GestorCredenciales, ErrorPoliticaPassword, ErrorAutenticacion
from hypothesis import given
from hypothesis.strategies import text
import bcrypt


class TestFuncionalesGestorCredenciales(unittest.TestCase):
    def setUp(self):
        self.gestor = GestorCredenciales("claveMaestraSegura123!")


    def test_eliminar_credencial_existente(self):
        clave = "claveMaestraSegura123!"
        self.gestor.anadir_credencial(clave, "GitHub", "user1", "PasswordSegura123!")
        resultado = self.gestor.eliminar_credencial(clave, "GitHub", "user1")
        self.assertTrue(resultado)

        with self.assertRaises(Exception):
            self.gestor.obtener_password(clave, "GitHub", "user1")

    def test_eliminar_credencial_inexistente(self):
        clave = "claveMaestraSegura123!"

        with self.assertRaises(Exception):
            self.gestor.eliminar_credencial(clave, "GitLab", "user1")

    def test_eliminar_credencial_clave_incorrecta(self):
        clave = "claveMaestraSegura123!"

        self.gestor.anadir_credencial(clave, "GitHub", "user1", "PasswordSegura123!")

        with self.assertRaises(ErrorAutenticacion):
            self.gestor.eliminar_credencial("abc", "GitHub", "user1")

    def test_eliminar_credencial_valores_invalidos(self):
        clave_valida = "claveMaestraSegura123!"

        #Lo que es inválido es el uso de valores que no sean de tipo string
        casos_invalidos = [
            ("GitHub", ""),
            ("GitHub", None),
            (123, "user1"),
            ("GitHub", 456),
        ]

        for servicio, usuario in casos_invalidos:
            with self.assertRaises(Exception):
                self.gestor.eliminar_credencial(clave_valida, servicio, usuario)

        claves_invalidas = [
            "",
            None,
            123,
        ]

        for clave in claves_invalidas:
            with self.assertRaises(Exception):
                self.gestor.eliminar_credencial(clave, "GitHub", "user1")

    def test_eliminar_credencial_usuario_no_existente(self):
        clave = "claveMaestraSegura123!"
        self.gestor.anadir_credencial(clave, "GitHub", "user1", "PasswordSegura123!")

        with self.assertRaises(Exception):
            self.gestor.eliminar_credencial(clave, "GitHub", "user2")

        password_guardada = self.gestor.obtener_password(clave, "GitHub", "user1")

        self.assertIsInstance(password_guardada, bytes)
        self.assertNotEqual(password_guardada, b"PasswordSegura123!")
        self.assertTrue(
            bcrypt.checkpw("PasswordSegura123!".encode("utf-8"), password_guardada)
        )

    def test_listar_servicios(self):
        clave = "claveMaestraSegura123!"

        servicios = self.gestor.listar_servicios(clave)
        self.assertIsInstance(servicios, list)
        self.assertIsNotNone(servicios)
        self.assertEqual(servicios, [])

        self.gestor.anadir_credencial(clave, "GitHub", "user1", "PasswordSegura123!")
        self.gestor.anadir_credencial(clave, "Eduroam", "user2", "PasswordSegura123!")
        self.gestor.anadir_credencial(clave, "GitHub", "user3", "PasswordSegura123!")

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
        self.gestor.anadir_credencial(clave, "GitHub", "usuario1", "Clave1!Segura")
        self.gestor.anadir_credencial(clave, "Eduroam", "usuario2", "Clave2!Segura")
        self.gestor.anadir_credencial(clave, "GitHub", "usuario3", "Clave3!Segura")
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
