import unittest

from src.gestor_credenciales.gestor_credenciales import (
    GestorCredenciales,
    ErrorAutenticacion,
)


class TestListarUsuarios(unittest.TestCase):
    clave = "claveMaestraSegura123!"

    def setUp(self):
        self.gestor = GestorCredenciales(self.clave)

    def test_listar_usuarios_lista_inicial_vacia(self):
        usuarios = self.gestor.listar_usuarios(self.clave)

        self.assertIsInstance(usuarios, list)
        self.assertIsNotNone(usuarios)
        self.assertEqual(usuarios, [])

    def test_listar_usuarios_anadir_nuevos_usuarios(self):
        self.gestor.anadir_credencial(self.clave, "GitHub", "usuario1", "Clave1!Segura")
        self.gestor.anadir_credencial(self.clave, "Eduroam", "usuario2", "Clave2!Segura")
        self.gestor.anadir_credencial(self.clave, "GitHub", "usuario3", "Clave3!Segura")

        usuarios = self.gestor.listar_usuarios(self.clave)

        self.assertCountEqual(usuarios, ["usuario1", "usuario2", "usuario3"])

    def test_listar_usuarios_eliminar_usuarios(self):
        self.gestor.anadir_credencial(self.clave, "GitHub", "usuario1", "Clave1!Segura")
        self.gestor.anadir_credencial(self.clave, "Eduroam", "usuario2", "Clave2!Segura")
        self.gestor.anadir_credencial(self.clave, "GitHub", "usuario3", "Clave3!Segura")

        resultado = self.gestor.eliminar_credencial(self.clave, "Eduroam", "usuario2")
        usuarios = self.gestor.listar_usuarios(self.clave)

        self.assertTrue(resultado)
        self.assertCountEqual(usuarios, ["usuario1", "usuario3"])

    def test_listar_usuarios_eliminar_todo(self):
        self.gestor.anadir_credencial(self.clave, "GitHub", "usuario1", "Clave1!Segura")
        self.gestor.anadir_credencial(self.clave, "GitHub", "usuario3", "Clave3!Segura")

        resultado1 = self.gestor.eliminar_credencial(self.clave, "GitHub", "usuario1")
        resultado2 = self.gestor.eliminar_credencial(self.clave, "GitHub", "usuario3")

        usuarios = self.gestor.listar_usuarios(self.clave)

        self.assertTrue(resultado1)
        self.assertTrue(resultado2)
        self.assertEqual(usuarios, [])

    def test_listar_usuarios_error_autenticacion(self):
        with self.assertRaises(ErrorAutenticacion):
            self.gestor.listar_usuarios("claveIncorrecta")


if __name__ == "__main__":
    unittest.main()
