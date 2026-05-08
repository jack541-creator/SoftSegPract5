import unittest
from src.gestor_credenciales.gestor_credenciales import GestorCredenciales

class TestAñadirCredenciales(unittest.TestCase):

    def setUp(self):
        self.gestor = GestorCredenciales(clave_maestra="1234")

    # Caso correcto
    def test_añadir_credencial_valida(self):
         # Llamamos al método con datos válidos
        resultado = self.gestor.añadir_credencial(
            servicio="GitHub",
            usuario="user1",
            contraseña="Password123!",
            clave_maestra="1234"
        )
        # Comprobamos que el método devuelve True 
        self.assertTrue(resultado)

    # Clave maestra incorrecta
    def test_añadir_credencial_clave_maestra_incorrecta(self):
        with self.assertRaises(PermissionError):
            self.gestor.añadir_credencial(
                servicio="GitHub",
                usuario="user1",
                contraseña="Password123!",
                clave_maestra="wrong" # Clave incorrecta
            )

    # Servicio vacío
    def test_añadir_credencial_servicio_vacio(self):
        with self.assertRaises(ValueError):
            self.gestor.añadir_credencial(
                servicio="",
                usuario="user1",
                contraseña="Password123!",
                clave_maestra="1234"
            )

    # Usuario vacío
    def test_añadir_credencial_usuario_vacio(self):
        with self.assertRaises(ValueError):
            self.gestor.añadir_credencial(
                servicio="GitHub",
                usuario="",
                contraseña="Password123!",
                clave_maestra="1234"
            )

        #Usuario demasiado largo (límite superior)
    def test_añadir_credencial_usuario_demasiado_largo(self):
        usuario_largo = "u" * 256  # Supongamos límite máximo = 255

        with self.assertRaises(ValueError):
            self.gestor.añadir_credencial(
                servicio="GitHub",
                usuario=usuario_largo,
                contraseña="Password123!",
                clave_maestra="1234"
            )

    #Usuario en el límite máximo permitido
    def test_añadir_credencial_usuario_longitud_maxima(self):
        usuario_max = "u" * 255  # Límite exacto permitido

        resultado = self.gestor.añadir_credencial(
            servicio="GitHub",
            usuario=usuario_max,
            contraseña="Password123!",
            clave_maestra="1234"
        )

        self.assertTrue(resultado)
    
    #Usuario de longitud mínima (1 carácter)
    def test_usuario_longitud_minima(self):
        resultado = self.gestor.añadir_credencial(
            servicio="GitHub",
            usuario="u",
            contraseña="Password123!",
            clave_maestra="1234"
        )
        self.assertTrue(resultado)

    #Usuario con solo espacios
    def test_añadir_credencial_usuario_solo_espacios(self):
        with self.assertRaises(ValueError):
            self.gestor.añadir_credencial(
                servicio="GitHub",
                usuario="   ",  # inválido
                contraseña="Password123!",
                clave_maestra="1234"
            )

    #Usuario con caracteres no permitidos
    def test_añadir_credencial_usuario_caracteres_invalidos(self):
        with self.assertRaises(ValueError):
            self.gestor.añadir_credencial(
                servicio="GitHub",
                usuario="user<>",  # posible inyección 
                contraseña="Password123!",
                clave_maestra="1234"
            )

    # Usuario con caracteres válidos comunes
    def test_añadir_credencial_usuario_valido_con_guiones(self):
        resultado = self.gestor.añadir_credencial(
            servicio="GitHub",
            usuario="user_name-123",  # formato típico válido
            contraseña="Password123!",
            clave_maestra="1234"
        )

        self.assertTrue(resultado)

    # Usuario tipo None (error de tipo)
    def test_añadir_credencial_usuario_none(self):
        with self.assertRaises(TypeError):
            self.gestor.añadir_credencial(
                servicio="GitHub",
                usuario=None,  # tipo inválido
                contraseña="Password123!",
                clave_maestra="1234"
            )

    # Usuario como número
    def test_usuario_tipo_invalido_int(self):
        with self.assertRaises(TypeError):
            self.gestor.añadir_credencial(
                servicio="GitHub",
                usuario=12345,
                contraseña="Password123!",
                clave_maestra="1234"
            )

    #Usuario como lista
    def test_usuario_tipo_invalido_lista(self):
        with self.assertRaises(TypeError):
            self.gestor.añadir_credencial(
                servicio="GitHub",
                usuario=["user"],
                contraseña="Password123!",
                clave_maestra="1234"
            )
            
    #Inyección en nombre de servicio (seguridad)
    def test_añadir_credencial_inyeccion_servicio(self):
        with self.assertRaises(ValueError):
            self.gestor.añadir_credencial(
                servicio="GitHub; DROP TABLE",
                usuario="user1",
                contraseña="Password123!",
                clave_maestra="1234"
            )
    # XSS / scripts
    def test_usuario_script_injection(self):
        with self.assertRaises(ValueError):
            self.gestor.añadir_credencial(
                servicio="GitHub",
                usuario="<script>alert(1)</script>",
                contraseña="Password123!",
                clave_maestra="1234"
            )

    # No duplicados
    def test_añadir_credencial_duplicada(self):
         # Primero añadimos una credencial válida
        self.gestor.añadir_credencial(
            servicio="GitHub",
            usuario="user1",
            contraseña="Password123!",
            clave_maestra="1234"
        )
        # Intentamos añadir la misma otra vez
        # Debe fallar porque ya existe
        with self.assertRaises(ValueError):
            self.gestor.añadir_credencial(
                servicio="GitHub",
                usuario="user1",
                contraseña="Password123!",
                clave_maestra="1234"
            )

if __name__ == "__main__":
    unittest.main()
