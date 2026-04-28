import unittest

# Importamos la clase que vamos a proba
from src.gestor_credenciales.gestor_credenciales import GestorCredenciales, ErrorAutenticacion



class test_listar_usuarios(unittest.TestCase):
    clave = "claveMaestraSegura123!"
      
    def setUp(self):
        self.gestor = GestorCredenciales(self.clave)

    def test_listar_usuarios_lista_incial_vacia(self):
        usuarios = self.gestor.listar_usuarios(self.clave)
        self.assertIsInstance(usuarios, list)
        self.assertIsNotNone(usuarios)
        self.assertEqual(usuarios, [])

    def test_listar_usuarios_añadir_nuevos_usuarios(self):
        self.gestor.añadir_credencial(self.clave, "GitHub", "usuario1", "clave1")
        self.gestor.añadir_credencial(self.clave, "Eduroam", "usuario2", "clave2")
        self.gestor.añadir_credencial(self.clave, "GitHub", "usuario3", "clave3")

        usuarios = self.gestor.listar_usuarios(self.clave)

        self.assertCountEqual(usuarios, ["usuario1", "usuario2", "usuario3"])

    def test_listar_usuarios_eliminar_usuarios(self):
        self.gestor.eliminar_credencial(self.clave, "Eduroam", "usuario2")
        usuarios = self.gestor.listar_usuarios(self.clave)
        self.assertCountEqual(usuarios, ["usuario1", "usuario3"])

    def test_listar_usuarios_eliminar_todo(self):
        self.gestor.eliminar_credencial(self.clave, "GitHub", "usuario1")
        self.gestor.eliminar_credencial(self.clave, "GitHub", "usuario3")
        usuarios = self.gestor.listar_usuarios(self.clave)
        self.assertEqual(usuarios, [])

    
    def test_listar_usuarios_error_autenticacion(self):
        with self.assertRaises(ErrorAutenticacion):
            self.gestor.listar_usuarios("claveIncorrecta")


if __name__ == "__main__":
    unittest.main()