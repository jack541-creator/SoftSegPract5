import unittest
import os
import sys

from src.gestor_credenciales.gestor_credenciales import GestorCredenciales, ErrorPoliticaPassword, ErrorAutenticacion
from src.logger.access_control import ContextoSeguridad, RolUsuario
from hypothesis import given, settings
from hypothesis.strategies import text

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)


class TestSeguridadGestorCredenciales(unittest.TestCase):
    def setUp(self):
        if os.path.exists("log_gestor_credenciales.log"):
            os.remove("log_gestor_credenciales.log")
        ContextoSeguridad().iniciar_sesion("test_admin", RolUsuario.ADMIN)
        self.gestor = GestorCredenciales("claveMaestraSegura123!")

    def tearDown(self):
        ContextoSeguridad().cerrar_sesion()

    # Tests de seguridad

    # Política de passwords:
    #   Mínimo 8 caracteres
    #   Al menos una letra mayúscula
    #   Al menos una letra minúscula
    #   Al menos un número
    #   Al menos un símbolo especial(!@  # $%^&* etc.)


    def test_password_no_almacenado_en_plano(self):
        servicio = "GitHub"
        usuario = "user1"
        password = "PasswordSegura123!"

        self.gestor.anadir_credencial("claveMaestraSegura123!", servicio, usuario, password)

        # Verificar que el almacenamiento no contiene el password en plano
        self.assertNotEqual(self.gestor._credenciales[servicio][usuario], password)
        # anadir más chequeos

    # Este es un test parametrizado usando subTests
    def test_deteccion_inyeccion_servicio(self):
        casos_inyeccion = ["serv;icio", "servicio|mal", "servicio&", "servicio'--"]
        for servicio in casos_inyeccion:
            with self.subTest(servicio=servicio):
                with self.assertRaises(ValueError):
                    self.gestor.anadir_credencial(
                        "claveMaestraSegura123!",
                        servicio,
                        "usuario_test",
                        "PasswordSegura123!"
                    )

    # Test con Fuzzing (usa Hypothesis)
    @settings(deadline=None, max_examples=10)
    @given(text(min_size=1, max_size=20))  # Genera contraseñas de hasta 20 caracteres
    def test_fuzz_politica_passwords_con_passwords_debiles(self, contrasena_generada):
        """Prueba diferentes passwords que no cumplen la política
        Args:
            contrasena_generada (str): La contraseña generada por Hypothesis

        Returns:
            Nada. Es un test
        """

        try:
            usuario = f"usuario_{len(self.gestor._credenciales.get('servicio', {}))}"
            self.gestor.anadir_credencial("claveMaestraSegura123!", "servicio", usuario, contrasena_generada)
        except ErrorPoliticaPassword:
            pass  # ✅ Comportamiento esperado
        except Exception as e:
            self.fail(f"Se lanzó una excepción inesperada: {e}")
        else:
            # Si la contraseña fue aceptada, debería cumplir con las condiciones
            self.assertTrue(self.gestor.es_password_segura(contrasena_generada),
                            f"Se aceptó una contraseña débil: {contrasena_generada}")

    def test_acceso_con_clave_maestra_erronea(self):
        self.gestor.anadir_credencial("claveMaestraSegura123!", "GitHub", "user1", "PasswordSegura123!")

        with self.assertRaises(ErrorAutenticacion):
            self.gestor.obtener_hash_password("claveIncorrecta", "GitHub", "user1")


if __name__ == "__main__":
    unittest.main()
