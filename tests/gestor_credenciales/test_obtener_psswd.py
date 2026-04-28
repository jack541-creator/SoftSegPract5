import pytest
from src.gestor_credenciales.gestor_credenciales import GestorCredenciales

CLAVE = "claveMaestraSegura123!"
SERVICIO = "GitHub"
USUARIO_VALIDO = "usuario_valido"
PASSWORD = "PasswordSegura123!"
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
    gestor = GestorCredenciales(CLAVE)
    gestor.añadir_credencial(CLAVE, SERVICIO, USUARIO_VALIDO, PASSWORD)

    password = gestor.obtener_password(CLAVE, SERVICIO, USUARIO_VALIDO)
    assert isinstance(password, str)
    assert password is not None
    assert len(password) > 0


# Usuario no existe
def test_obtener_password_usuario_inexistente():
    gestor = GestorCredenciales(CLAVE)
    
    with pytest.raises(ValueError):
        gestor.obtener_password(CLAVE, SERVICIO, "usuario_inexistente")


# Usuario vacío
def test_obtener_password_usuario_vacio():
    gestor = GestorCredenciales(CLAVE)

    with pytest.raises(Exception):
        gestor.obtener_password(CLAVE, SERVICIO, "")
# Tipo incorrecto
def test_obtener_password_tipo_incorrecto():
    gestor = GestorCredenciales(CLAVE)

    with pytest.raises(Exception):
        gestor.obtener_password(CLAVE, SERVICIO, 123)


# Input malicioso
def test_obtener_password_input_malicioso():
    gestor = GestorCredenciales(CLAVE)

    with pytest.raises(Exception):
        gestor.obtener_password(CLAVE, SERVICIO, "usuario@@@")


# No debe devolver None
def test_obtener_password_no_devuelve_none():
    gestor = GestorCredenciales(CLAVE)
    gestor.añadir_credencial(CLAVE, SERVICIO, USUARIO_VALIDO, PASSWORD)

    password = gestor.obtener_password(CLAVE, SERVICIO, USUARIO_VALIDO)
    assert password is not None


# Formato mínimo de contraseña
def test_obtener_password_formato_valido():
    gestor = GestorCredenciales(CLAVE)
    gestor.añadir_credencial(CLAVE, SERVICIO, USUARIO_VALIDO, PASSWORD)

    password = gestor.obtener_password(CLAVE, SERVICIO, USUARIO_VALIDO)
    assert isinstance(password, str)
    assert len(password) >= 8