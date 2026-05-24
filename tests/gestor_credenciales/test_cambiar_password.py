import pytest
import bcrypt

from src.gestor_credenciales.gestor_credenciales import (
    GestorCredenciales,
    ErrorAutenticacion,
    ErrorServicioNoEncontrado,
    ErrorPoliticaPassword,
)


CLAVE = "ClaveSegura123!"
SERVICIO = "Binance"
USUARIO = "usuario_api"
PASSWORD_ACTUAL = "PasswordActual123!"
PASSWORD_NUEVA = "PasswordNueva123!"


class TestCambiarPasswordFuncional:

    def setup_method(self):
        self.gestor = GestorCredenciales(CLAVE)

        self.gestor.anadir_credencial(
            CLAVE,
            SERVICIO,
            USUARIO,
            PASSWORD_ACTUAL
        )

    def test_cambiar_password_correctamente(self):
        resultado = self.gestor.cambiar_password(
            CLAVE,
            SERVICIO,
            USUARIO,
            PASSWORD_ACTUAL,
            PASSWORD_NUEVA
        )

        assert resultado is True

        password_hashed = self.gestor.obtener_hash_password(
            CLAVE,
            SERVICIO,
            USUARIO
        )

        assert bcrypt.checkpw(
            PASSWORD_NUEVA.encode("utf-8"),
            password_hashed
        )


class TestCambiarPasswordSeguridad:

    def setup_method(self):
        self.gestor = GestorCredenciales(CLAVE)

        self.gestor.anadir_credencial(
            CLAVE,
            SERVICIO,
            USUARIO,
            PASSWORD_ACTUAL
        )

    def test_clave_maestra_incorrecta(self):
        with pytest.raises(ErrorAutenticacion):
            self.gestor.cambiar_password(
                "ClaveIncorrecta123!",
                SERVICIO,
                USUARIO,
                PASSWORD_ACTUAL,
                PASSWORD_NUEVA
            )

    def test_password_actual_incorrecta(self):
        with pytest.raises(ErrorAutenticacion):
            self.gestor.cambiar_password(
                CLAVE,
                SERVICIO,
                USUARIO,
                "PasswordIncorrecta123!",
                PASSWORD_NUEVA
            )

    def test_servicio_inexistente(self):
        with pytest.raises(ErrorServicioNoEncontrado):
            self.gestor.cambiar_password(
                CLAVE,
                "Kraken",
                USUARIO,
                PASSWORD_ACTUAL,
                PASSWORD_NUEVA
            )

    def test_usuario_inexistente(self):
        with pytest.raises(ErrorServicioNoEncontrado):
            self.gestor.cambiar_password(
                CLAVE,
                SERVICIO,
                "usuario_fake",
                PASSWORD_ACTUAL,
                PASSWORD_NUEVA
            )

    def test_password_nueva_debil(self):
        with pytest.raises(ErrorPoliticaPassword):
            self.gestor.cambiar_password(
                CLAVE,
                SERVICIO,
                USUARIO,
                PASSWORD_ACTUAL,
                "123"
            )

    def test_parametros_vacios(self):
        with pytest.raises(ValueError):
            self.gestor.cambiar_password(
                CLAVE,
                SERVICIO,
                "",
                PASSWORD_ACTUAL,
                PASSWORD_NUEVA
            )
