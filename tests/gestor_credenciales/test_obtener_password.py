import pytest
from hypothesis import given, strategies as st
from src.gestor_credenciales.gestor_credenciales import obtener_password

USUARIO_VALIDO = "usuario_valido"


# -----------------------
# TESTS FUNCIONALES
# -----------------------

class TestObtenerPasswordFuncional:

    def test_obtener_password_valido(self):
        password = obtener_password(USUARIO_VALIDO)

        assert isinstance(password, str)
        assert password is not None
        assert len(password) >= 7

    def test_usuario_inexistente(self):
        with pytest.raises(ValueError):
            obtener_password("usuario_inexistente")


# -----------------------
# TESTS DE SEGURIDAD
# -----------------------

class TestObtenerPasswordSeguridad:

    def test_usuario_vacio(self):
        with pytest.raises(ValueError):
            obtener_password("")

    def test_tipo_incorrecto(self):
        with pytest.raises(TypeError):
            obtener_password(123)

    def test_input_invalido(self):
        with pytest.raises(ValueError):
            obtener_password("usuario@@@")

    @given(st.text())
    def test_inputs_aleatorios(self, usuario):
        """
        Test de robustez con Hypothesis
        """
        if usuario == USUARIO_VALIDO:
            return

        with pytest.raises((ValueError, TypeError)):
            obtener_password(usuario)
