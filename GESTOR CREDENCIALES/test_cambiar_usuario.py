import unittest
import bcrypt
from icontract.errors import ViolationError

from src.gestor_credenciales.gestor_credenciales import GestorCredenciales, ErrorAutenticacion, ErrorServicioNoEncontrado


class TestCambiarUsuarioFuncional(unittest.TestCase):

    def setUp(self):
        self.gestor = GestorCredenciales("ClaveMaestra123!")
        self.password_original = "PasswordSegura123!"

        self.gestor._credenciales = {
            "gmail": {
                "user_antiguo": bcrypt.hashpw(
                    self.password_original.encode(),
                    bcrypt.gensalt()
                )
            }
        }

    def test_cambiar_usuario_correcto(self):
        self.gestor.cambiar_usuario(
            "ClaveMaestra123!",
            "gmail",
            "user_antiguo",
            "user_nuevo"
        )

        self.assertIn("user_nuevo", self.gestor._credenciales["gmail"])
        self.assertNotIn("user_antiguo", self.gestor._credenciales["gmail"])

    def test_password_se_mantiene(self):
        self.gestor.cambiar_usuario(
            "ClaveMaestra123!",
            "gmail",
            "user_antiguo",
            "user_nuevo"
        )

        hash_guardado = self.gestor._credenciales["gmail"]["user_nuevo"]

        self.assertTrue(
            bcrypt.checkpw(self.password_original.encode(), hash_guardado)
        )


class TestCambiarUsuarioSeguridad(unittest.TestCase):

    def setUp(self):
        self.gestor = GestorCredenciales("ClaveMaestra123!")
        self.gestor._credenciales = {
            "gmail": {
                "user_antiguo": bcrypt.hashpw(
                    "PasswordSegura123!".encode(),
                    bcrypt.gensalt()
                )
            }
        }

    def test_servicio_vacio(self):
        with self.assertRaises(ViolationError):
            self.gestor.cambiar_usuario(
                "ClaveMaestra123!",
                "",
                "user_antiguo",
                "user_nuevo"
            )

    def test_usuario_antiguo_vacio(self):
        with self.assertRaises(ViolationError):
            self.gestor.cambiar_usuario(
                "ClaveMaestra123!",
                "gmail",
                "",
                "user_nuevo"
            )

    def test_usuario_nuevo_vacio(self):
        with self.assertRaises(ViolationError):
            self.gestor.cambiar_usuario(
                "ClaveMaestra123!",
                "gmail",
                "user_antiguo",
                ""
            )

    def test_clave_maestra_incorrecta(self):
        with self.assertRaises(Exception):
            self.gestor.cambiar_usuario(
                "clave_incorrecta",
                "gmail",
                "user_antiguo",
                "user_nuevo"
            )

    def test_servicio_no_existente(self):
        with self.assertRaises(Exception):
            self.gestor.cambiar_usuario(
                "ClaveMaestra123!",
                "facebook",
                "user_antiguo",
                "user_nuevo"
            )

    def test_usuario_no_existente(self):
        with self.assertRaises(Exception):
            self.gestor.cambiar_usuario(
                "ClaveMaestra123!",
                "gmail",
                "otro_user",
                "user_nuevo"
            )

    def test_usuario_nuevo_ya_existe(self):
        self.gestor._credenciales["gmail"]["user_nuevo"] = bcrypt.hashpw(
            "OtraPassword123!".encode(),
            bcrypt.gensalt()
        )

        with self.assertRaises(Exception):
            self.gestor.cambiar_usuario(
                "ClaveMaestra123!",
                "gmail",
                "user_antiguo",
                "user_nuevo"
            )


if __name__ == "__main__":
    unittest.main()
