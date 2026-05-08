import unittest
from src.gestor_credenciales.gestor_credenciales import GestorCredenciales

class TestCambiarUsuarioFuncional(unittest.TestCase):

    def setUp(self):
        self.gestor = GestorCredenciales(clave_maestra="1234")

        # Credencial base
        self.gestor.añadir_credencial(
            servicio="GitHub",
            usuario="user1",
            contraseña="Password123!",
            clave_maestra="1234"
        )

    def test_cambiar_usuario_valido(self):
        resultado = self.gestor.cambiar_usuario(
            servicio="GitHub",
            usuario_antiguo="user1",
            usuario_nuevo="user2",
            clave_maestra="1234"
        )
        self.assertTrue(resultado)

    def test_clave_maestra_incorrecta(self):
        with self.assertRaises(PermissionError):
            self.gestor.cambiar_usuario(
                servicio="GitHub",
                usuario_antiguo="user1",
                usuario_nuevo="user2",
                clave_maestra="wrong"
            )


    def test_usuario_antiguo_no_existe(self):
        with self.assertRaises(ValueError):
            self.gestor.cambiar_usuario(
                servicio="GitHub",
                usuario_antiguo="no_existe",
                usuario_nuevo="user2",
                clave_maestra="1234"
            )


    def test_usuario_nuevo_vacio(self):
        with self.assertRaises(ValueError):
            self.gestor.cambiar_usuario(
                servicio="GitHub",
                usuario_antiguo="user1",
                usuario_nuevo="",
                clave_maestra="1234"
            )


    def test_usuario_nuevo_demasiado_largo(self):
        usuario_largo = "u" * 256

        with self.assertRaises(ValueError):
            self.gestor.cambiar_usuario(
                servicio="GitHub",
                usuario_antiguo="user1",
                usuario_nuevo=usuario_largo,
                clave_maestra="1234"
            )


    def test_usuario_nuevo_longitud_maxima(self):
        usuario_max = "u" * 255

        resultado = self.gestor.cambiar_usuario(
            servicio="GitHub",
            usuario_antiguo="user1",
            usuario_nuevo=usuario_max,
            clave_maestra="1234"
        )

        self.assertTrue(resultado)


    def test_usuario_duplicado(self):
        self.gestor.añadir_credencial(
            servicio="GitHub",
            usuario="user2",
            contraseña="Password123!",
            clave_maestra="1234"
        )

        with self.assertRaises(ValueError):
            self.gestor.cambiar_usuario(
                servicio="GitHub",
                usuario_antiguo="user1",
                usuario_nuevo="user2",
                clave_maestra="1234"
            )


class TestCambiarUsuarioSeguridad(unittest.TestCase):

    def setUp(self):
        self.gestor = GestorCredenciales(clave_maestra="1234")

        self.gestor.añadir_credencial(
            servicio="GitHub",
            usuario="user1",
            contraseña="Password123!",
            clave_maestra="1234"
        )


    def test_usuario_solo_espacios(self):
        with self.assertRaises(ValueError):
            self.gestor.cambiar_usuario(
                servicio="GitHub",
                usuario_antiguo="user1",
                usuario_nuevo="   ",
                clave_maestra="1234"
            )


    def test_usuario_script_injection(self):
        with self.assertRaises(ValueError):
            self.gestor.cambiar_usuario(
                servicio="GitHub",
                usuario_antiguo="user1",
                usuario_nuevo="<script>alert(1)</script>",
                clave_maestra="1234"
            )


    def test_usuario_caracteres_invalidos(self):
        with self.assertRaises(ValueError):
            self.gestor.cambiar_usuario(
                servicio="GitHub",
                usuario_antiguo="user1",
                usuario_nuevo="user<>",
                clave_maestra="1234"
            )


    def test_usuario_none(self):
        with self.assertRaises(TypeError):
            self.gestor.cambiar_usuario(
                servicio="GitHub",
                usuario_antiguo="user1",
                usuario_nuevo=None,
                clave_maestra="1234"
            )


    def test_usuario_tipo_int(self):
        with self.assertRaises(TypeError):
            self.gestor.cambiar_usuario(
                servicio="GitHub",
                usuario_antiguo="user1",
                usuario_nuevo=123,
                clave_maestra="1234"
            )


    def test_usuario_tipo_lista(self):
        with self.assertRaises(TypeError):
            self.gestor.cambiar_usuario(
                servicio="GitHub",
                usuario_antiguo="user1",
                usuario_nuevo=["user2"],
                clave_maestra="1234"
            )


if __name__ == "__main__":
    unittest.main()
