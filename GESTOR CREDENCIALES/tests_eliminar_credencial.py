import unittest
from src.gestor_credenciales.gestor_credenciales import GestorCredenciales, ErrorPoliticaPassword, ErrorAutenticacion


def test_eliminar_credencial_existente(self):
    clave = "claveMaestraSegura123!"
    self.gestor.añadir_credencial(clave, "GitHub", "user1", "PasswordSegura123!")

    resultado = self.gestor.eliminar_credencial(clave, "GitHub", "user1")

    self.assertIsNone(resultado)

    with self.assertRaises(Exception):
        self.gestor.obtener_password(clave, "GitHub", "user1")


def test_eliminar_credencial_inexistente(self):
    clave = "claveMaestraSegura123!"

    with self.assertRaises(Exception):
        self.gestor.eliminar_credencial(clave, "GitLab", "user1")


def test_eliminar_credencial_clave_incorrecta(self):
    clave = "claveMaestraSegura123!"

    self.gestor.añadir_credencial(clave, "GitHub", "user1", "PasswordSegura123!")

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
    clave = "claveMaestraSegura123!"
    self.gestor.añadir_credencial(clave, "GitHub", "user1", "PasswordSegura123!")

    with self.assertRaises(Exception):
        self.gestor.eliminar_credencial(clave, "GitHub", "user2")

    self.assertEqual(
        self.gestor.obtener_password(clave, "GitHub", "user1"),
        "PasswordSegura123!"
    )