
import unittest
from src.gestor_credenciales.gestor_credenciales import GestorCredenciales

class Test_OTP(unittest.TestCase):

    def setUp(self):
        self.gestor = GestorCredenciales("claveMaestraSegura123!")
        self.clave = "claveMaestraSegura123!"
        self.gestor.anadir_credencial(self.clave, "Github", "user1", "Password123!")

    def test_generar_otps(self):

        # Comprobación de que la función devuelve una lista
        otps = self.gestor.generar_otps(8)
        self.assertIsInstance(otps, list)

        # Comprobación de la longitud de la lista
        self.assertEqual(len(otps), 8)

        # Comprobación de la longitud de las OTP
        for i in otps:
            self.assertGreaterEqual(len(i), 6)

    def test_verificar_otp(self):

        otps = self.gestor.generar_otps(8)
        self.gestor.almacenar_otps(self.clave, "Github", "user1", otps)

        # Pruebas de la verificación
        self.assertFalse(self.gestor.verificar_otp(self.clave, "Github", "user1", "123"))

        self.assertFalse(self.gestor.verificar_otp(self.clave, "Github", "user1", "123456"))

        self.assertFalse(self.gestor.verificar_otp(self.clave, "Github", "user1", "123456789"))

        # Se elimina una otp al usarse
        self.assertTrue(self.gestor.verificar_otp(self.clave, "Github", "user1", otps[0]))
        self.assertFalse(self.gestor.verificar_otp(self.clave, "Github", "user1", otps[0]))

        # Pruebas de la eliminación de las OTPs antiguas al almacenar la nueva
        otps2 = self.gestor.generar_otps(8)
        self.gestor.almacenar_otps(self.clave, "Github", "user1", otps2)

        self.assertFalse(self.gestor.verificar_otp(self.clave, "Github", "user1", otps[1]))

        self.assertFalse(self.gestor.verificar_otp(self.clave, "Github", "user1", otps[7]))



if __name__ == "__main__":
    unittest.main()
