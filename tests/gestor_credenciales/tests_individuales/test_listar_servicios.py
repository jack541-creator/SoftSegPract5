import unittest

from src.gestor_credenciales.gestor_credenciales import (
    GestorCredenciales,
    ErrorAutenticacion,
)


class TestListarServicios(unittest.TestCase):
     
	def setUp(self):
		self.clave = "claveMaestraSegura123!"
		self.gestor = GestorCredenciales(self.clave) 
	
	def test_listar_servicios_lista_vacia(self):
		servicios = self.gestor.listar_servicios(self.clave)
		self.assertIsInstance(servicios, list)
		self.assertIsNotNone(servicios)
		self.assertEqual(servicios, [])
	
	def test_listar_servicios_anadir_servicios_y_listar(self):
		self.gestor.anadir_credencial(self.clave, "GitHub", "user1", "PasswordSegura123!")
		self.gestor.anadir_credencial(self.clave, "Eduroam", "user2", "PasswordSegura123!")
		self.gestor.anadir_credencial(self.clave, "GitHub", "user3", "PasswordSegura123!")

		servicios = self.gestor.listar_servicios(self.clave)
		self.assertCountEqual(servicios, ["GitHub", "Eduroam"])

	def test_listar_servicios_eliminar_servicios_y_listar(self):
		self.gestor.anadir_credencial(self.clave, "GitHub", "user1", "PasswordSegura123!")
		self.gestor.anadir_credencial(self.clave, "Eduroam", "user2", "PasswordSegura123!")
		self.gestor.anadir_credencial(self.clave, "GitHub", "user3", "PasswordSegura123!")

		self.gestor.eliminar_credencial(self.clave, "Eduroam", "user2")
		servicios = self.gestor.listar_servicios(self.clave)
		self.assertEqual(servicios, ["GitHub"])

	def test_listar_servicios_anadir_y_vaciar_servicios(self):
		self.gestor.anadir_credencial(self.clave, "GitHub", "user1", "PasswordSegura123!")
		self.gestor.anadir_credencial(self.clave, "Eduroam", "user2", "PasswordSegura123!")
		self.gestor.anadir_credencial(self.clave, "GitHub", "user3", "PasswordSegura123!")

		self.gestor.eliminar_credencial(self.clave, "GitHub", "user1")
		self.gestor.eliminar_credencial(self.clave, "Eduroam", "user2")
		self.gestor.eliminar_credencial(self.clave, "GitHub", "user3")

		servicios = self.gestor.listar_servicios(self.clave)
		self.assertEqual(servicios, [])

	def test_listar_servicios_autenticacion(self):
		with self.assertRaises(ErrorAutenticacion):
			self.gestor.listar_servicios("claveIncorrecta")

if __name__ == "__main__":
    unittest.main()