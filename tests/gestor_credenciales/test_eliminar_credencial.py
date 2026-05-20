import unittest
from src.gestor_credenciales.gestor_credenciales import GestorCredenciales, ErrorPoliticaPassword, ErrorAutenticacion
import bcrypt

class TestEliminiarCredencial(unittest.TestCase):

    def setUp(self):
        self.clave = "claveMaestraSegura123!"
        self.gestor = GestorCredenciales(clave_maestra=self.clave)
        

    def test_eliminar_credencial_existente(self):
        self.gestor.anadir_credencial(self.clave, "GitHub", "user1", "PasswordSegura123!")

        resultado = self.gestor.eliminar_credencial(self.clave, "GitHub", "user1")

        self.assertTrue(resultado)

        with self.assertRaises(Exception):
            self.gestor.obtener_hash_password(self.clave, "GitHub", "user1")


    def test_eliminar_credencial_inexistente(self):
        with self.assertRaises(Exception):
            self.gestor.eliminar_credencial(self.clave, "GitLab", "user1")


    def test_eliminar_credencial_clave_incorrecta(self):
        self.gestor.anadir_credencial(self.clave, "GitHub", "user1", "PasswordSegura123!")

        with self.assertRaises(ErrorAutenticacion):
            self.gestor.eliminar_credencial("abc", "GitHub", "user1")


    def test_eliminar_credencial_valores_invalidos(self):
        clave_valida = "claveMaestraSegura123!"

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
        self.gestor.anadir_credencial(self.clave, "GitHub", "user1", "PasswordSegura123!")

        with self.assertRaises(Exception):
            self.gestor.eliminar_credencial(self.clave, "GitHub", "user2")

        password_guardada = self.gestor.obtener_hash_password(self.clave, "GitHub", "user1")

        self.assertIsInstance(password_guardada, bytes)
        self.assertNotEqual(password_guardada, b"PasswordSegura123!")
        self.assertTrue(
            bcrypt.checkpw("PasswordSegura123!".encode("utf-8"), password_guardada)
        )

if __name__ == "__main__":
    unittest.main()
