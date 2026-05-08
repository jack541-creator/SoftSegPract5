import unittest
import icontract
from unittest.mock import patch
from src.gestor_credenciales.gestor_credenciales import GestorCredenciales, ErrorCodigoNoEstablecido, ErrorSinIntentosRestantes, ErrorUsuarioYaVerificado , ErrorCorreoNoEstablecido


class Test2FA(unittest.TestCase):

    def setUp(self):
        self.gestor = GestorCredenciales("claveMaestraSegura123!")
        self.clave = "claveMaestraSegura123!"
        self.gestor.añadir_credencial(self.clave, "Github", "user1", "Password123!")

    def test_estalecer_correo(self):

        correo = "prueba@gmail.com"

        self.gestor.establecer_correo(self.clave, "Github", "user1", correo)

        # Comprueba que se ha añadido el correo
        self.assertEqual(self.gestor.obtener_correo(self.clave, "Github", "user1"), correo)

    # Comprobación de que se ha validado el correo usando @require de icontract
    def test_validacion_correo(self):

        # Sin usuario
        with self.assertRaises(icontract.ViolationError):
            self.gestor.establecer_correo(self.clave, "Github", "user1", "@gmail.com")
            
        # Sin dominio
        with self.assertRaises(icontract.ViolationError):
            self.gestor.establecer_correo(self.clave, "Github", "user1", "abcdf.com")

        # Sin extensión
        with self.assertRaises(icontract.ViolationError):
            self.gestor.establecer_correo(self.clave, "Github", "user1", "test@gmail")


    def test_creacion_codigo(self):

        self.gestor.crear_codigo2fa(self.clave, "Github", "user1")

        # La longitud del código es al menos de 6 y los intentos se establecen en 3
        self.assertGreaterEqual(len(self.gestor.obtener_codigo2fa(self.clave, "Github", "user1")), 6)
        self.assertEqual(self.gestor.obtener_intentos_restantes(self.clave, "Github", "user1"), 3)


    @patch("gestor_credenciales.gestor_credenciales.smtplib.SMTP")
    def test_correo2FA(self, mock_smtp):
        
        correo = "prueba@gmail.com"
        self.gestor.establecer_correo(self.clave, "Github", "user1", correo)
        self.gestor.crear_codigo2fa(self.clave, "Github", "user1")

        self.gestor.enviar_correo2fa(self.clave, "Github", "user1")

        # Comprobación de la conexión SMTP
        mock_smtp.assert_called_once_with("smtp.gmail.com", 587)

        smtp_instance = mock_smtp.return_value

        # Comprobación de TLS
        smtp_instance.starttls.assert_called_once()

        # Comprobación del login de la cuenta que envia el correo
        smtp_instance.login.assert_called_once()

        # 4. Se envía el mensaje
        smtp_instance.sendmail.assert_called_once()

        # 5. El mensaje contiene el código
        args = smtp_instance.sendmail.call_args[0]
        mensaje = args[2]

        self.assertIn(self.gestor.obtener_codigo2fa(self.clave, "Github", "user1"), mensaje)

        # 6. Se cierra conexión
        smtp_instance.quit.assert_called_once()

    @patch("gestor_credenciales.gestor_credenciales.smtplib.SMTP")
    def test_correo_sin_establecer(self, mock_smtp):

        self.gestor.crear_codigo2fa(self.clave, "Github", "user1")
        
        with self.assertRaises(ErrorCorreoNoEstablecido):
            self.gestor.enviar_correo2fa(self.clave, "Github", "user1")


    @patch("gestor_credenciales.gestor_credenciales.smtplib.SMTP")
    def test_codigo_sin_establecer(self, mock_smtp):

        correo = "prueba@gmail.com"
        self.gestor.establecer_correo(self.clave, "Github", "user1", correo)

        with self.assertRaises(ErrorCodigoNoEstablecido):
            self.gestor.enviar_correo2fa(self.clave, "Github", "user1")


    def test_verificacion2fa_codigo_sin_crear(self):
        with self.assertRaises(ErrorCodigoNoEstablecido):
            self.gestor.verificar_usuario(self.clave, "Github", "user1", "123456")

    def test_verificacion2fa(self):

        correo = "prueba@gmail.com"
        self.gestor.establecer_correo(self.clave, "Github", "user1", correo)
        self.gestor.crear_codigo2fa(self.clave, "Github", "user1")

        # Verifica que se resta un intento a cada llamada erronea
        self.gestor.verificar_usuario(self.clave, "Github", "user1", "1")
        self.assertEqual(self.gestor.obtener_intentos_restantes(self.clave, "Github", "user1"), 2)
        self.gestor.verificar_usuario(self.clave, "Github", "user1", "1")
        self.assertEqual(self.gestor.obtener_intentos_restantes(self.clave, "Github", "user1"), 1)
        self.gestor.verificar_usuario(self.clave, "Github", "user1", "1")
        self.assertEqual(self.gestor.obtener_intentos_restantes(self.clave, "Github", "user1"), 0)

    def test_verificacion2fa_sin_intentos(self):

        correo = "prueba@gmail.com"
        self.gestor.establecer_correo(self.clave, "Github", "user1", correo)
        self.gestor.crear_codigo2fa(self.clave, "Github", "user1")

        self.gestor.verificar_usuario(self.clave, "Github", "user1", "1")
        self.gestor.verificar_usuario(self.clave, "Github", "user1", "1")
        self.gestor.verificar_usuario(self.clave, "Github", "user1", "1")

        with self.assertRaises(ErrorSinIntentosRestantes):
            self.gestor.verificar_usuario(self.clave, "Github", "user1", "1")

    def test_verificacion2fa_usuario_verificado(self):

        correo = "prueba@gmail.com"
        self.gestor.establecer_correo(self.clave, "Github", "user1", correo)
        self.gestor.crear_codigo2fa(self.clave, "Github", "user1")

        self.gestor.verificar_usuario(self.clave, "Github", "user1", self.gestor.obtener_codigo2fa(self.clave, "Github", "user1"))

        # Comprueba que el usuario se ha verificado con la llamada anterior
        self.assertTrue(self.gestor.comprobacion_verificacion_usuario(self.clave, "Github", "user1"))

        # Comprueba que el codigo_auth es None tras la verificacion
        self.assertIsNone(self.gestor.obtener_codigo2fa(self.clave, "Github", "user1"))

        # Comprueba que salta la excepcion al intentar verificar al usuario que ya esta verificado
        with self.assertRaises(ErrorUsuarioYaVerificado):
            self.gestor.verificar_usuario(self.clave, "Github", "user1", "1")


if __name__ == "__main__":
    unittest.main()
