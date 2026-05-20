import unittest

from src.gestor_credenciales.gestor_credenciales import GestorCredenciales
from src.gestor_credenciales.proxy_seguro import (
    ErrorAutorizacion,
    ProxySeguroGestorCredenciales,
)

CLAVE = "ClaveMaestra123!"


class TestProxySeguro(unittest.TestCase):

    def setUp(self):
        self.gestor = GestorCredenciales(CLAVE)
        self.proxy = ProxySeguroGestorCredenciales(self.gestor)

        self.proxy.registrar_usuario_proxy("ana", "ana123", "admin")
        self.proxy.registrar_usuario_proxy("luis", "luis123", "lector")
        self.proxy.registrar_usuario_proxy("eva", "eva123", "editor")

    def test_admin_puede_anadir_y_eliminar_credencial(self):
        sesion_admin = self.proxy.iniciar_sesion("ana", "ana123")

        self.assertTrue(
            self.proxy.anadir_credencial(
                sesion_admin, CLAVE, "GitHub", "user1", "Password123!"
            )
        )

        self.assertTrue(
            self.proxy.eliminar_credencial(
                sesion_admin, CLAVE, "GitHub", "user1"
            )
        )

    def test_lector_no_puede_anadir_credencial(self):
        sesion_lector = self.proxy.iniciar_sesion("luis", "luis123")

        with self.assertRaises(ErrorAutorizacion):
            self.proxy.anadir_credencial(
                sesion_lector, CLAVE, "GitHub", "user1", "Password123!"
            )

    def test_editor_no_puede_eliminar_credencial(self):
        sesion_admin = self.proxy.iniciar_sesion("ana", "ana123")
        sesion_editor = self.proxy.iniciar_sesion("eva", "eva123")

        self.proxy.anadir_credencial(
            sesion_admin, CLAVE, "GitHub", "user1", "Password123!"
        )

        with self.assertRaises(ErrorAutorizacion):
            self.proxy.eliminar_credencial(
                sesion_editor, CLAVE, "GitHub", "user1"
            )

    def test_auditoria_registra_denegaciones(self):
        sesion_admin = self.proxy.iniciar_sesion("ana", "ana123")
        sesion_lector = self.proxy.iniciar_sesion("luis", "luis123")

        with self.assertRaises(ErrorAutorizacion):
            self.proxy.anadir_credencial(
                sesion_lector, CLAVE, "GitHub", "user1", "Password123!"
            )

        auditoria = self.proxy.obtener_auditoria(sesion_admin)

        self.assertTrue(
            any(entry["resultado"] == "denegado" for entry in auditoria)
        )


if __name__ == "__main__":
    unittest.main()