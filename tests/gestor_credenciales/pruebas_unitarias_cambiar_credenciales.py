import unittest
from src.gestor_credenciales.gestor_credenciales import cambiar_credenciales


class TestCambiarCredenciales(unittest.TestCase):

    def test_cambio_correcto(self):
        resultado = cambiar_credenciales("pablo", "123456")
        self.assertEqual(resultado, "Credenciales actualizadas correctamente")

    def test_usuario_vacio(self):
        resultado = cambiar_credenciales("", "123456")
        self.assertEqual(resultado, "Error: usuario vacío")

    def test_password_vacio(self):
        resultado = cambiar_credenciales("pablo", "")
        self.assertEqual(resultado, "Error: contraseña vacía")

    def test_password_corto(self):
        resultado = cambiar_credenciales("pablo", "123")
        self.assertEqual(resultado, "Error: contraseña demasiado corta")

    def test_ambos_vacios(self):
        resultado = cambiar_credenciales("", "")
        self.assertEqual(resultado, "Error: usuario vacío")


if __name__ == "__main__":
    unittest.main()