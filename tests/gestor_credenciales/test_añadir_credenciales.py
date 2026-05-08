import unittest
from gestor_credenciales.gestor_credenciales import GestorCredenciales
from icontract.errors import ViolationError
from hypothesis import given, strategies as st

# clase funcionales ---------------------------------------------------------------------------------------
class TestAnadirCredencialesFuncionales(unittest.TestCase):

    def setUp(self):
        self.gestor = GestorCredenciales(clave_maestra="1234")

    # Caso correcto =========
    def test_añadir_credencial_valida(self):
        resultado = self.gestor.añadir_credencial(
            servicio="GitHub",
            usuario="user1",
            password="Password123!",
            clave_maestra="1234"
        )
        self.assertIsNone(resultado)

# parametros vacios -------------------------------------------------------------------------------------------
		 # Servicio vacío =========
    def test_servicio_vacio(self):
        with self.assertRaises(ViolationError):
            self.gestor.añadir_credencial(
                servicio="",
                usuario="user1",
                password="Password123!",
                clave_maestra="1234"
            )

	    # Usuario vacío ==========
	    def test_usuario_vacio(self):
        with self.assertRaises(ViolationError):
            self.gestor.añadir_credencial(
                servicio="GitHub",
                usuario="",
                password="Password123!",
                clave_maestra="1234"
            )
# passwords -----------------------------------------------------------------------------------------------------
   # Password corta ==============
    def test_password_corta(self):
        with self.assertRaises(ViolationError):
            self.gestor.añadir_credencial(
                servicio="GitHub",
                usuario="user1",
                password="Short1!",
                clave_maestra="1234"
            )

    #Password sin mayúsculas ==============
    def test_password_sin_mayusculas(self):
        with self.assertRaises(ViolationError):
            self.gestor.añadir_credencial(
                servicio="GitHub",
                usuario="user1",
                password="password123!",
                clave_maestra="1234"
            )

    #Password sin números  =============
    def test_password_sin_numeros(self):
        with self.assertRaises(ViolationError):
            self.gestor.añadir_credencial(
                servicio="GitHub",
                usuario="user1",
                password="Password!!!",
                clave_maestra="1234"
            )

    # Hypothesis - casos válidos ===========
    @given(
	    servicio=st.text(min_size=1).filter(lambda s: all(c not in ";&|" for c in s)),
	    usuario=st.text(min_size=1).filter(lambda u: u.strip() != ""),
	    password=st.from_regex(
	        r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*]).{12,}$"
    )
	)
	def test_valores_validos_hypothesis(self, servicio, usuario, password):
	    resultado = self.gestor.añadir_credencial(
	        servicio=servicio,
	        usuario=usuario,
	        password=password,
	        clave_maestra="1234"
	    )
	    self.assertIsNone(resultado)
        
        
#clase de segururidad -------------------------------------------------------------------------------------------------------------------------------
class TestAnadirCredencialesSeguridad(unittest.TestCase):

    def setUp(self):
        self.gestor = GestorCredenciales(clave_maestra="1234")

    # Inyección en servicio ============
    def test_inyeccion_servicio(self):
        with self.assertRaises(ViolationError):
            self.gestor.añadir_credencial(
                servicio="GitHub; DROP TABLE",
                usuario="user1",
                password="Password123!",
                clave_maestra="1234"
            )

    # Caracteres peligrosos (Hypothesis) ===========
    @given(st.text().filter(lambda s: any(c in ";&|" for c in s)))
    def test_servicio_invalido_hypothesis(self, servicio):
        with self.assertRaises(ViolationError):
            self.gestor.añadir_credencial(
                servicio=servicio,
                usuario="user",
                password="Password123!",
                clave_maestra="1234"
            )
            
if __name__ == "__main__":
    unittest.main()