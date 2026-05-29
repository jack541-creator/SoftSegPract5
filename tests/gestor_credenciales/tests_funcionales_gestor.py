import os
import sys
import unittest
import warnings
import glob

from src.gestor_credenciales.gestor_credenciales import (
    GestorCredenciales,
    ErrorAutenticacion,
    ErrorCredencialExistente,
    ErrorPoliticaPassword,
    ValidadorPassword,
)
from src.gestor_credenciales.proxy_seguro import (
    ErrorAutorizacion,
    ProxySeguroGestorCredenciales,
)
from src.logger.access_control import ContextoSeguridad, RolUsuario

warnings.filterwarnings("ignore", category=ResourceWarning)

os.environ['TEST_MODE'] = '1'

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))


# Limpiar todos los logs antes de empezar
for log_file in glob.glob("test_*.log"):
    try:
        os.remove(log_file)
    except:
        pass


# =========================================================
#  TEST ANADIR CREDENCIALES
# =========================================================

class TestAnadirCredenciales(unittest.TestCase):

    def setUp(self):
        # Limpiar log específico antes de cada test
        if os.path.exists("test_anadir.log"):
            os.remove("test_anadir.log")
        self.clave = "1234"
        self.gestor = GestorCredenciales(clave_maestra=self.clave, log_file="test_anadir.log")
        ContextoSeguridad().iniciar_sesion("test_admin", RolUsuario.ADMIN)

    def tearDown(self):
        ContextoSeguridad().cerrar_sesion()

    def test_anadir_credencial_valida(self):
        resultado = self.gestor.anadir_credencial(
            servicio="GitHub",
            usuario="user1",
            password="Password123!",
            clave_maestra=self.clave
        )
        self.assertTrue(resultado)

    def test_anadir_credencial_clave_maestra_incorrecta(self):
        with self.assertRaises(ErrorAutenticacion):
            self.gestor.anadir_credencial(
                servicio="GitHub",
                usuario="user1",
                password="Password123!",
                clave_maestra="wrong"
            )

    def test_anadir_credencial_servicio_vacio(self):
        with self.assertRaises(ValueError):
            self.gestor.anadir_credencial(
                servicio="",
                usuario="user1",
                password="Password123!",
                clave_maestra=self.clave
            )

    def test_anadir_credencial_usuario_vacio(self):
        with self.assertRaises(ValueError):
            self.gestor.anadir_credencial(
                servicio="GitHub",
                usuario="",
                password="Password123!",
                clave_maestra=self.clave
            )

    def test_anadir_credencial_usuario_demasiado_largo(self):
        usuario_largo = "u" * 256
        with self.assertRaises(ValueError):
            self.gestor.anadir_credencial(
                servicio="GitHub",
                usuario=usuario_largo,
                password="Password123!",
                clave_maestra=self.clave
            )

    def test_anadir_credencial_usuario_longitud_maxima(self):
        usuario_max = "u" * 255
        resultado = self.gestor.anadir_credencial(
            servicio="GitHub",
            usuario=usuario_max,
            password="Password123!",
            clave_maestra=self.clave
        )
        self.assertTrue(resultado)

    def test_usuario_longitud_minima(self):
        resultado = self.gestor.anadir_credencial(
            servicio="GitHub",
            usuario="u",
            password="Password123!",
            clave_maestra=self.clave
        )
        self.assertTrue(resultado)

    def test_anadir_credencial_usuario_solo_espacios(self):
        with self.assertRaises(ValueError):
            self.gestor.anadir_credencial(
                servicio="GitHub",
                usuario="   ",
                password="Password123!",
                clave_maestra=self.clave
            )

    def test_anadir_credencial_usuario_caracteres_invalidos(self):
        with self.assertRaises(ValueError):
            self.gestor.anadir_credencial(
                servicio="GitHub",
                usuario="user<>",
                password="Password123!",
                clave_maestra=self.clave
            )

    def test_anadir_credencial_usuario_valido_con_guiones(self):
        resultado = self.gestor.anadir_credencial(
            servicio="GitHub",
            usuario="user_name-123",
            password="Password123!",
            clave_maestra=self.clave
        )
        self.assertTrue(resultado)

    def test_anadir_credencial_usuario_none(self):
        with self.assertRaises(TypeError):
            self.gestor.anadir_credencial(
                servicio="GitHub",
                usuario=None,
                password="Password123!",
                clave_maestra=self.clave
            )

    def test_usuario_tipo_invalido_int(self):
        with self.assertRaises(TypeError):
            self.gestor.anadir_credencial(
                servicio="GitHub",
                usuario=12345,
                password="Password123!",
                clave_maestra=self.clave
            )

    def test_usuario_tipo_invalido_lista(self):
        with self.assertRaises(TypeError):
            self.gestor.anadir_credencial(
                servicio="GitHub",
                usuario=["user"],
                password="Password123!",
                clave_maestra=self.clave
            )

    def test_anadir_credencial_inyeccion_servicio(self):
        with self.assertRaises(ValueError):
            self.gestor.anadir_credencial(
                servicio="GitHub; DROP TABLE",
                usuario="user1",
                password="Password123!",
                clave_maestra=self.clave
            )

    def test_usuario_script_injection(self):
        with self.assertRaises(ValueError):
            self.gestor.anadir_credencial(
                servicio="GitHub",
                usuario="<script>alert(1)</script>",
                password="Password123!",
                clave_maestra=self.clave
            )

    def test_anadir_credencial_duplicada(self):
        self.gestor.anadir_credencial(
            servicio="GitHub",
            usuario="user_duplicate",
            password="Password123!",
            clave_maestra=self.clave
        )
        with self.assertRaises(ErrorCredencialExistente):
            self.gestor.anadir_credencial(
                servicio="GitHub",
                usuario="user_duplicate",
                password="Password123!",
                clave_maestra=self.clave
            )


# =========================================================
#  TEST ELIMINAR CREDENCIAL
# =========================================================

class TestEliminarCredencial(unittest.TestCase):

    def setUp(self):
        if os.path.exists("test_eliminar.log"):
            os.remove("test_eliminar.log")
        self.clave = "claveMaestraSegura123!"
        self.gestor = GestorCredenciales(clave_maestra=self.clave, log_file="test_eliminar.log")
        ContextoSeguridad().iniciar_sesion("test_admin", RolUsuario.ADMIN)

    def tearDown(self):
        ContextoSeguridad().cerrar_sesion()

    def test_eliminar_credencial_existente(self):
        self.gestor.anadir_credencial(self.clave, "GitHub", "user1", "PasswordSegura123!")
        resultado = self.gestor.eliminar_credencial(self.clave, "GitHub", "user1")
        self.assertTrue(resultado)
        with self.assertRaises(Exception):
            self.gestor.obtener_hash_password(self.clave, "GitHub", "user1")

    def test_eliminar_credencial_inexistente(self):
        with self.assertRaises(Exception):
            self.gestor.eliminar_credencial(self.clave, "GitLab", "user1")

    def test_eliminar_credencial_clave_incorrecta(self):
        self.gestor.anadir_credencial(self.clave, "GitHub", "user2", "PasswordSegura123!")
        with self.assertRaises(ErrorAutenticacion):
            self.gestor.eliminar_credencial("abc", "GitHub", "user2")


# =========================================================
#  TEST LISTAR SERVICIOS
# =========================================================

class TestListarServicios(unittest.TestCase):

    def setUp(self):
        if os.path.exists("test_listar.log"):
            os.remove("test_listar.log")
        self.clave = "claveMaestraSegura123!"
        self.gestor = GestorCredenciales(self.clave, log_file="test_listar.log")
        ContextoSeguridad().iniciar_sesion("test_admin", RolUsuario.ADMIN)

    def tearDown(self):
        ContextoSeguridad().cerrar_sesion()

    def test_listar_servicios_lista_vacia(self):
        servicios = self.gestor.listar_servicios(self.clave)
        self.assertIsInstance(servicios, list)
        self.assertEqual(servicios, [])

    def test_listar_servicios_anadir_servicios_y_listar(self):
        self.gestor.anadir_credencial(self.clave, "GitHub", "user1", "PasswordSegura123!")
        self.gestor.anadir_credencial(self.clave, "Eduroam", "user2", "PasswordSegura123!")
        servicios = self.gestor.listar_servicios(self.clave)
        self.assertCountEqual(servicios, ["GitHub", "Eduroam"])

    def test_listar_servicios_autenticacion(self):
        with self.assertRaises(ErrorAutenticacion):
            self.gestor.listar_servicios("claveIncorrecta")


# =========================================================
#  TEST LISTAR USUARIOS
# =========================================================

class TestListarUsuarios(unittest.TestCase):

    def setUp(self):
        if os.path.exists("test_usuarios.log"):
            os.remove("test_usuarios.log")
        self.clave = "claveMaestraSegura123!"
        self.gestor = GestorCredenciales(self.clave, log_file="test_usuarios.log")
        ContextoSeguridad().iniciar_sesion("test_admin", RolUsuario.ADMIN)

    def tearDown(self):
        ContextoSeguridad().cerrar_sesion()

    def test_listar_usuarios_lista_inicial_vacia(self):
        usuarios = self.gestor.listar_usuarios(self.clave)
        self.assertIsInstance(usuarios, list)
        self.assertEqual(usuarios, [])

    def test_listar_usuarios_anadir_nuevos_usuarios(self):
        self.gestor.anadir_credencial(self.clave, "GitHub", "usuario1", "Clave1!Segura")
        self.gestor.anadir_credencial(self.clave, "Eduroam", "usuario2", "Clave2!Segura")
        usuarios = self.gestor.listar_usuarios(self.clave)
        self.assertCountEqual(usuarios, ["usuario1", "usuario2"])


# =========================================================
#  TEST OTP
# =========================================================

class TestOTP(unittest.TestCase):

    def setUp(self):
        if os.path.exists("test_otp.log"):
            os.remove("test_otp.log")
        self.clave = "claveMaestraSegura123!"
        self.gestor = GestorCredenciales(self.clave, log_file="test_otp.log")
        ContextoSeguridad().iniciar_sesion("test_admin", RolUsuario.ADMIN)
        self.gestor.anadir_credencial(self.clave, "Github", "user1", "Password123!")

    def tearDown(self):
        ContextoSeguridad().cerrar_sesion()

    def test_generar_otps(self):
        otps = self.gestor.generar_otps(8)
        self.assertIsInstance(otps, list)
        self.assertEqual(len(otps), 8)
        for i in otps:
            self.assertGreaterEqual(len(i), 6)

    def test_verificar_otp(self):
        otps = self.gestor.generar_otps(8)
        self.gestor.almacenar_otps(self.clave, "Github", "user1", otps)
        self.assertTrue(self.gestor.verificar_otp(self.clave, "Github", "user1", otps[0]))
        self.assertFalse(self.gestor.verificar_otp(self.clave, "Github", "user1", otps[0]))


# =========================================================
#  TEST PROXY SEGURO
# =========================================================

class TestProxySeguro(unittest.TestCase):

    def setUp(self):
        if os.path.exists("test_proxy.log"):
            os.remove("test_proxy.log")
        self.clave = "ClaveMaestra123!"
        self.gestor = GestorCredenciales(self.clave, log_file="test_proxy.log")
        self.proxy = ProxySeguroGestorCredenciales(self.gestor)
        self.proxy.registrar_usuario_proxy("ana", "ana123", "admin")
        self.proxy.registrar_usuario_proxy("luis", "luis123", "lector")
        self.proxy.registrar_usuario_proxy("eva", "eva123", "editor")
        ContextoSeguridad().iniciar_sesion("test_admin", RolUsuario.ADMIN)

    def tearDown(self):
        ContextoSeguridad().cerrar_sesion()

    def test_admin_puede_anadir_y_eliminar_credencial(self):
        sesion_admin = self.proxy.iniciar_sesion("ana", "ana123")
        self.assertTrue(
            self.proxy.anadir_credencial(sesion_admin, self.clave, "GitHub", "user1", "Password123!")
        )
        self.assertTrue(
            self.proxy.eliminar_credencial(sesion_admin, self.clave, "GitHub", "user1")
        )

    def test_lector_no_puede_anadir_credencial(self):
        sesion_lector = self.proxy.iniciar_sesion("luis", "luis123")
        with self.assertRaises(ErrorAutorizacion):
            self.proxy.anadir_credencial(sesion_lector, self.clave, "GitHub", "user1", "Password123!")

    def test_editor_no_puede_eliminar_credencial(self):
        sesion_admin = self.proxy.iniciar_sesion("ana", "ana123")
        sesion_editor = self.proxy.iniciar_sesion("eva", "eva123")
        
        self.proxy.anadir_credencial(sesion_admin, self.clave, "GitHub", "user1", "Password123!")
        
        with self.assertRaises(ErrorAutorizacion):
            self.proxy.eliminar_credencial(sesion_editor, self.clave, "GitHub", "user1")

    def test_auditoria_registra_denegaciones(self):
        sesion_admin = self.proxy.iniciar_sesion("ana", "ana123")
        sesion_lector = self.proxy.iniciar_sesion("luis", "luis123")
        
        with self.assertRaises(ErrorAutorizacion):
            self.proxy.anadir_credencial(sesion_lector, self.clave, "GitHub", "user1", "Password123!")
        
        auditoria = self.proxy.obtener_auditoria(sesion_admin)
        self.assertTrue(any(entry["resultado"] == "denegado" for entry in auditoria))


# =========================================================
#  TEST VALIDADOR PASSWORD
# =========================================================

class TestVerificarFortalezaPassword(unittest.TestCase):

    def setUp(self):
        self.validador = ValidadorPassword()

    def test_entrada_entera_lanza_excepcion(self):
        with self.assertRaises(ErrorPoliticaPassword):
            self.validador.verificar_fortaleza(12345)

    def test_password_vacia_lanza_excepcion(self):
        with self.assertRaises(ErrorPoliticaPassword):
            self.validador.verificar_fortaleza("")

    def test_menos_de_8_caracteres_penaliza(self):
        resultado = self.validador.verificar_fortaleza("abc123")
        self.assertEqual(resultado, "débil")

    def test_contraseña_con_todos_criterios_es_fuerte(self):
        resultado = self.validador.verificar_fortaleza("miClave!Super73Segura")
        self.assertEqual(resultado, "fuerte")


# =========================================================
#  EJECUTAR TESTS
# =========================================================

if __name__ == "__main__":
    unittest.main(verbosity=0)