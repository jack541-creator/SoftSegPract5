import unittest
from src.gestor_credenciales.gestor_credenciales import (
    GestorCredenciales,
    ErrorAutenticacion,
    ErrorUsuarioNoEncontrado,
    ErrorServicioNoEncontrado,
    ErrorTokenCaducado,
    ErrorTokenNoCreado
)

class Test_Tokens(unittest.TestCase):

    def setUp(self):
        self.gestor = GestorCredenciales("claveMaestraSegura123!")
        self.clave = "claveMaestraSegura123!"
        self.gestor.anadir_credencial(self.clave, "Github", "user1", "Password123!")

    def test_generar_tokens(self):
        token = self.gestor.generar_token(self.clave, "Github", "user1", "Password123!")
        self.assertIsInstance(token, str)

    def test_generar_tokens_servicio_incorrecto(self):
        with self.assertRaises(ErrorServicioNoEncontrado):
            token = self.gestor.generar_token(self.clave, "ServicioDesconocido", "user1", "Password123!")

    def test_generar_tokens_usuario_incorrecto(self):
        with self.assertRaises(ErrorUsuarioNoEncontrado):
            token = self.gestor.generar_token(self.clave, "Github", "UsuarioDesconocido", "Password123!")

    def test_generar_tokens_contrasena_incorrecta(self):
        with self.assertRaises(ErrorAutenticacion):
            token = self.gestor.generar_token(self.clave, "Github", "user1", "PasswordIncorrecta")

    def test_autenticar_token(self):
        token = self.gestor.generar_token(self.clave, "Github", "user1", "Password123!")
        self.assertTrue(self.gestor.autenticar_token(self.clave, "Github", "user1", token))
        self.assertFalse(self.gestor.autenticar_token(self.clave, "Github", "user1", "Tokenincorrecto"))

    def test_autenticar_tokens_servicio_incorrecto(self):
        with self.assertRaises(ErrorServicioNoEncontrado):
            token = self.gestor.generar_token(self.clave, "Github", "user1", "Password123!")
            ok = self.gestor.autenticar_token(self.clave, "ServicioDesconocido", "user1", token)

    def test_autenticar_tokens_usuario_incorrecto(self):
        with self.assertRaises(ErrorUsuarioNoEncontrado):
            token = self.gestor.generar_token(self.clave, "Github", "user1", "Password123!")
            ok = self.gestor.autenticar_token(self.clave, "Github", "UsuarioDesconocido", token)

    def test_autenticar_token_no_creado(self):
        with self.assertRaises(ErrorTokenNoCreado):
            ok = self.gestor.autenticar_token(self.clave, "Github", "user1", "...")

    def test_renovar_tokens_servicio_incorrecto(self):
        with self.assertRaises(ErrorServicioNoEncontrado):
            token = self.gestor.generar_token(self.clave, "Github", "user1", "Password123!")
            self.gestor.renovar_sesion(self.clave, "ServicioDesconocido", "user1")

    def test_renovar_tokens_usuario_incorrecto(self):
        with self.assertRaises(ErrorUsuarioNoEncontrado):
            token = self.gestor.generar_token(self.clave, "Github", "user1", "Password123!")
            self.gestor.renovar_sesion(self.clave, "Github", "UsuarioDesconocido")

    def test_renovar_token_no_creado(self):
        with self.assertRaises(ErrorTokenNoCreado):
            self.gestor.renovar_sesion(self.clave, "Github", "user1")

    

    

        

