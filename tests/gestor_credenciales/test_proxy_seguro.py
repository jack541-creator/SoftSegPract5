import pytest

from src.gestor_credenciales.gestor_credenciales import GestorCredenciales
from src.gestor_credenciales.proxy_seguro import (
    ErrorAutorizacion,
    ProxySeguroGestorCredenciales,
)


CLAVE = "ClaveMaestra123!"


def crear_proxy():
    gestor = GestorCredenciales(CLAVE)
    proxy = ProxySeguroGestorCredenciales(gestor)
    proxy.registrar_usuario_proxy("ana", "ana123", "admin")
    proxy.registrar_usuario_proxy("luis", "luis123", "lector")
    proxy.registrar_usuario_proxy("eva", "eva123", "editor")
    return proxy


def test_admin_puede_anadir_y_eliminar_credencial():
    proxy = crear_proxy()
    sesion_admin = proxy.iniciar_sesion("ana", "ana123")

    assert proxy.anadir_credencial(
        sesion_admin, CLAVE, "GitHub", "user1", "Password123!"
    ) is True
    assert proxy.eliminar_credencial(sesion_admin, CLAVE, "GitHub", "user1") is True


def test_lector_no_puede_anadir_credencial():
    proxy = crear_proxy()
    sesion_lector = proxy.iniciar_sesion("luis", "luis123")

    with pytest.raises(ErrorAutorizacion):
        proxy.anadir_credencial(
            sesion_lector, CLAVE, "GitHub", "user1", "Password123!"
        )


def test_editor_no_puede_eliminar_credencial():
    proxy = crear_proxy()
    admin = proxy.iniciar_sesion("ana", "ana123")
    editor = proxy.iniciar_sesion("eva", "eva123")

    proxy.anadir_credencial(admin, CLAVE, "GitHub", "user1", "Password123!")

    with pytest.raises(ErrorAutorizacion):
        proxy.eliminar_credencial(editor, CLAVE, "GitHub", "user1")


def test_auditoria_registra_denegaciones():
    proxy = crear_proxy()
    admin = proxy.iniciar_sesion("ana", "ana123")
    lector = proxy.iniciar_sesion("luis", "luis123")

    with pytest.raises(ErrorAutorizacion):
        proxy.anadir_credencial(lector, CLAVE, "GitHub", "user1", "Password123!")

    auditoria = proxy.obtener_auditoria(admin)
    assert any(e["resultado"] == "denegado" for e in auditoria)
