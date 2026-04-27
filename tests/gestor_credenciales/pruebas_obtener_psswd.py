import pytest
from src.gestor_credenciales.gestor_credenciales import obtener_password

USUARIO_VALIDO = "usuario_valido"
"""
Especificación de la función obtener_password:

- Entrada: usuario (str)
- Salida: contraseña (str)
- Excepciones:
    - TypeError → si el tipo no es str
    - ValueError → si el usuario está vacío, no existe o es inválido
"""


# Caso correcto
def test_obtener_password_valido():
    password = obtener_password(USUARIO_VALIDO)
    assert isinstance(password, str)
    assert password is not None
    assert len(password) > 0


# Usuario no existe
def test_obtener_password_usuario_inexistente():
    with pytest.raises(ValueError):
        obtener_password("usuario_inexistente")


# Usuario vacío
def test_obtener_password_usuario_vacio():
    with pytest.raises(ValueError):
        obtener_password("")


# Tipo incorrecto
def test_obtener_password_tipo_incorrecto():
    with pytest.raises(TypeError):
        obtener_password(123)


# Input malicioso
def test_obtener_password_input_malicioso():
    with pytest.raises(ValueError):
        obtener_password("usuario@@@")


# No debe devolver None
def test_obtener_password_no_devuelve_none():
    password = obtener_password(USUARIO_VALIDO)
    assert password is not None


# Formato mínimo de contraseña
def test_obtener_password_formato_valido():
    password = obtener_password(USUARIO_VALIDO)
    assert isinstance(password, str)
    assert len(password) >= 8