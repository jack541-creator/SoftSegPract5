import unittest

from src.gestor_credenciales.gestor_credenciales import (
    GestorCredenciales,
    ErrorAutenticacion,
    ErrorCredencialExistente,
)


class TestAnadirCredenciales(unittest.TestCase):

    def setUp(self):
        self.gestor = GestorCredenciales(clave_maestra="1234")

    # Caso correcto
    def test_anadir_credencial_valida(self):
        resultado = self.gestor.anadir_credencial(
            servicio="GitHub",
            usuario="user1",
            password="Password123!",
            clave_maestra="1234"
        )

        self.assertTrue(resultado)

    # Clave maestra incorrecta
    def test_anadir_credencial_clave_maestra_incorrecta(self):
        with self.assertRaises(ErrorAutenticacion):
            self.gestor.anadir_credencial(
                servicio="GitHub",
                usuario="user1",
                password="Password123!",
                clave_maestra="wrong"
            )

    # Servicio vacío
    def test_anadir_credencial_servicio_vacio(self):
        with self.assertRaises(ValueError):
            self.gestor.anadir_credencial(
                servicio="",
                usuario="user1",
                password="Password123!",
                clave_maestra="1234"
            )

    # Usuario vacío
    def test_anadir_credencial_usuario_vacio(self):
        with self.assertRaises(ValueError):
            self.gestor.anadir_credencial(
                servicio="GitHub",
                usuario="",
                password="Password123!",
                clave_maestra="1234"
            )

    # Usuario demasiado largo
    def test_anadir_credencial_usuario_demasiado_largo(self):
        usuario_largo = "u" * 256

        with self.assertRaises(ValueError):
            self.gestor.anadir_credencial(
                servicio="GitHub",
                usuario=usuario_largo,
                password="Password123!",
                clave_maestra="1234"
            )

    # Usuario en el límite máximo permitido
    def test_anadir_credencial_usuario_longitud_maxima(self):
        usuario_max = "u" * 255

        resultado = self.gestor.anadir_credencial(
            servicio="GitHub",
            usuario=usuario_max,
            password="Password123!",
            clave_maestra="1234"
        )

        self.assertTrue(resultado)

    # Usuario de longitud mínima
    def test_usuario_longitud_minima(self):
        resultado = self.gestor.anadir_credencial(
            servicio="GitHub",
            usuario="u",
            password="Password123!",
            clave_maestra="1234"
        )

        self.assertTrue(resultado)

    # Usuario con solo espacios
    def test_anadir_credencial_usuario_solo_espacios(self):
        with self.assertRaises(ValueError):
            self.gestor.anadir_credencial(
                servicio="GitHub",
                usuario="   ",
                password="Password123!",
                clave_maestra="1234"
            )

    # Usuario con caracteres no permitidos
    def test_anadir_credencial_usuario_caracteres_invalidos(self):
        with self.assertRaises(ValueError):
            self.gestor.anadir_credencial(
                servicio="GitHub",
                usuario="user<>",
                password="Password123!",
                clave_maestra="1234"
            )

    # Usuario con caracteres válidos comunes
    def test_anadir_credencial_usuario_valido_con_guiones(self):
        resultado = self.gestor.anadir_credencial(
            servicio="GitHub",
            usuario="user_name-123",
            password="Password123!",
            clave_maestra="1234"
        )

        self.assertTrue(resultado)

    # Usuario tipo None
    def test_anadir_credencial_usuario_none(self):
        with self.assertRaises(TypeError):
            self.gestor.anadir_credencial(
                servicio="GitHub",
                usuario=None,
                password="Password123!",
                clave_maestra="1234"
            )

    # Usuario como número
    def test_usuario_tipo_invalido_int(self):
        with self.assertRaises(TypeError):
            self.gestor.anadir_credencial(
                servicio="GitHub",
                usuario=12345,
                password="Password123!",
                clave_maestra="1234"
            )

    # Usuario como lista
    def test_usuario_tipo_invalido_lista(self):
        with self.assertRaises(TypeError):
            self.gestor.anadir_credencial(
                servicio="GitHub",
                usuario=["user"],
                password="Password123!",
                clave_maestra="1234"
            )

    # Inyección en nombre de servicio
    def test_anadir_credencial_inyeccion_servicio(self):
        with self.assertRaises(ValueError):
            self.gestor.anadir_credencial(
                servicio="GitHub; DROP TABLE",
                usuario="user1",
                password="Password123!",
                clave_maestra="1234"
            )

    # XSS / scripts
    def test_usuario_script_injection(self):
        with self.assertRaises(ValueError):
            self.gestor.anadir_credencial(
                servicio="GitHub",
                usuario="<script>alert(1)</script>",
                password="Password123!",
                clave_maestra="1234"
            )

    # No duplicados
    def test_anadir_credencial_duplicada(self):
        self.gestor.anadir_credencial(
            servicio="GitHub",
            usuario="user1",
            password="Password123!",
            clave_maestra="1234"
        )

        with self.assertRaises(ErrorCredencialExistente):
            self.gestor.anadir_credencial(
                servicio="GitHub",
                usuario="user1",
                password="Password123!",
                clave_maestra="1234"
            )


if __name__ == "__main__":
    unittest.main()