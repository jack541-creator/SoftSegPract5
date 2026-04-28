import unittest
from src.gestor_credenciales.gestor_credenciales import GestorCredenciales


class TestCambiarCredenciales(unittest.TestCase):

    clave = "claveMaestraSegura123!"
      
    def setUp(self):
        self.gestor = GestorCredenciales(self.clave)

    def test_cambio_correcto(self):
        self.gestor.añadir_credencial(self.clave, "GitHub", "pablo", "aB123456789@")
        resultado = self.gestor.cambiar_credenciales(self.clave, "GitHub", "pablo", "GitHub", "miguel", "aB123456789@")
        self.assertEqual(resultado, "Credenciales actualizadas correctamente")

    def test_usuario_vacio(self):
        self.gestor.añadir_credencial(self.clave, "GitHub", "pablo", "aB123456789@")
        resultado = self.gestor.cambiar_credenciales(self.clave, "GitHub", "", "GitHub", "miguel", "aB123456789@")
        self.assertEqual(resultado, "Error: usuario vacío")

    def test_password_vacio(self):
        self.gestor.añadir_credencial(self.clave, "GitHub", "pablo", "aB123456789@")
        resultado = self.gestor.cambiar_credenciales(self.clave, "GitHub", "pablo", "GitHub", "miguel", "")
        self.assertEqual(resultado, "Error: contraseña vacía")

    def test_password_corto(self):
        self.gestor.añadir_credencial(self.clave, "GitHub", "pablo", "aB123456789@")
        resultado = self.gestor.cambiar_credenciales(self.clave, "GitHub", "pablo", "GitHub", "miguel", "aB123@")
        self.assertEqual(resultado, "Error: contraseña demasiado corta")

    def test_ambos_vacios(self):
        self.gestor.añadir_credencial(self.clave, "GitHub", "pablo", "aB123456789@")
        resultado = self.gestor.cambiar_credenciales(self.clave, "GitHub", "", "GitHub", "miguel", "")
        self.assertEqual(resultado, "Error: usuario vacío")


if __name__ == "__main__":
    unittest.main()