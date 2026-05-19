import pytest
from icontract import ViolationError

from src.gestor_credenciales.gestor_credenciales import GestorCredenciales


class TestObtenerPasswordFuncional:

    def setup_method(self):

        self.clave = "ClaveSegura123!"

        self.gestor = GestorCredenciales(self.clave)

        # Credencial válida para los tests
        self.gestor.anadir_credencial(
            self.clave,
            "Github",
            "usuario1",
            "Password123!"
        )

    def test_obtener_password_valido(self):

        password = self.gestor.obtener_password(
            self.clave,
            "Github",
            "usuario1"
        )

        assert isinstance(password, str)
        assert password == "Password123!"


class TestObtenerPasswordSeguridad:

    def setup_method(self):

        self.clave = "ClaveSegura123!"

        self.gestor = GestorCredenciales(self.clave)

        self.gestor.anadir_credencial(
            self.clave,
            "Github",
            "usuario1",
            "Password123!"
        )

    def test_usuario_inexistente(self):

        with pytest.raises(ViolationError):

            self.gestor.obtener_password(
                self.clave,
                "Github",
                "usuario_fake"
            )

    def test_servicio_inexistente(self):

        with pytest.raises(ViolationError):

            self.gestor.obtener_password(
                self.clave,
                "Steam",
                "usuario1"
            )

    def test_usuario_vacio(self):

        with pytest.raises(ViolationError):

            self.gestor.obtener_password(
                self.clave,
                "Github",
                ""
            )

    def test_tipo_incorrecto(self):

        with pytest.raises(ViolationError):

            self.gestor.obtener_password(
                self.clave,
                "Github",
                123
            )
