"""Proxy seguro para aplicar minimo privilegio sobre GestorCredenciales.

La idea es que el codigo cliente no use GestorCredenciales directamente,
sino esta fachada. El proxy valida identidad/rol, autoriza la operacion y
despues delega en el gestor real.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from functools import wraps
from typing import Callable

from .gestor_credenciales import ErrorAutenticacion, GestorCredenciales


class ErrorAutorizacion(Exception):
    """El usuario esta autenticado, pero no tiene permiso para esta accion."""


@dataclass(frozen=True)
class Sesion:
    usuario: str
    rol: str


class ProxySeguroGestorCredenciales:
    """Fachada de seguridad con minimo privilegio.

    Roles incluidos:
    - admin: puede crear, modificar, eliminar y listar.
    - editor: puede crear y cambiar credenciales, pero no eliminar.
    - lector: solo puede consultar y listar.
    - auditor: solo puede listar servicios y usuarios.
    """

    POLITICAS: dict[str, set[str]] = {
        "admin": {
            "anadir_credencial",
            "obtener_hash_password",
            "cambiar_password",
            "cambiar_usuario",
            "eliminar_credencial",
            "listar_servicios",
            "listar_usuarios",
        },
        "editor": {
            "anadir_credencial",
            "obtener_hash_password",
            "cambiar_password",
            "cambiar_usuario",
            "listar_servicios",
            "listar_usuarios",
        },
        "lector": {
            "obtener_hash_password",
            "listar_servicios",
            "listar_usuarios",
        },
        "auditor": {
            "listar_servicios",
            "listar_usuarios",
        },
    }

    def __init__(self, gestor: GestorCredenciales):
        self._gestor = gestor
        self._usuarios: dict[str, dict[str, str]] = {}
        self._auditoria: list[dict[str, str]] = []

    def registrar_usuario_proxy(self, usuario: str, password: str, rol: str) -> None:
        if rol not in self.POLITICAS:
            raise ValueError("Rol no soportado")
        if not usuario or not password:
            raise ValueError("Usuario y password son obligatorios")
        # Para la practica lo dejamos simple. En produccion, hashear este password.
        self._usuarios[usuario] = {"password": password, "rol": rol}

    def iniciar_sesion(self, usuario: str, password: str) -> Sesion:
        datos = self._usuarios.get(usuario)
        if datos is None or datos["password"] != password:
            raise ErrorAutenticacion()
        return Sesion(usuario=usuario, rol=datos["rol"])

    def _registrar_auditoria(self, sesion: Sesion, accion: str, resultado: str) -> None:
        self._auditoria.append(
            {
                "fecha": datetime.now(timezone.utc).isoformat(),
                "usuario": sesion.usuario,
                "rol": sesion.rol,
                "accion": accion,
                "resultado": resultado,
            }
        )

    def _autorizar(self, sesion: Sesion, accion: str) -> None:
        if accion not in self.POLITICAS.get(sesion.rol, set()):
            self._registrar_auditoria(sesion, accion, "denegado")
            raise ErrorAutorizacion(f"Rol '{sesion.rol}' no autorizado para '{accion}'")

    def _ejecutar(self, sesion: Sesion, accion: str, funcion: Callable, *args, **kwargs):
        self._autorizar(sesion, accion)
        try:
            resultado = funcion(*args, **kwargs)
            self._registrar_auditoria(sesion, accion, "permitido")
            return resultado
        except Exception:
            self._registrar_auditoria(sesion, accion, "error")
            raise

    def anadir_credencial(self, sesion: Sesion, *args, **kwargs):
        return self._ejecutar(
            sesion, "anadir_credencial", self._gestor.anadir_credencial, *args, **kwargs
        )

    def obtener_hash_password(self, sesion: Sesion, *args, **kwargs):
        return self._ejecutar(
            sesion,
            "obtener_hash_password",
            self._gestor.obtener_hash_password,
            *args,
            **kwargs,
        )

    def cambiar_password(self, sesion: Sesion, *args, **kwargs):
        return self._ejecutar(
            sesion, "cambiar_password", self._gestor.cambiar_password, *args, **kwargs
        )

    def cambiar_usuario(self, sesion: Sesion, *args, **kwargs):
        return self._ejecutar(
            sesion, "cambiar_usuario", self._gestor.cambiar_usuario, *args, **kwargs
        )

    def eliminar_credencial(self, sesion: Sesion, *args, **kwargs):
        return self._ejecutar(
            sesion,
            "eliminar_credencial",
            self._gestor.eliminar_credencial,
            *args,
            **kwargs,
        )

    def listar_servicios(self, sesion: Sesion, *args, **kwargs):
        return self._ejecutar(
            sesion, "listar_servicios", self._gestor.listar_servicios, *args, **kwargs
        )

    def listar_usuarios(self, sesion: Sesion, *args, **kwargs):
        return self._ejecutar(
            sesion, "listar_usuarios", self._gestor.listar_usuarios, *args, **kwargs
        )

    def obtener_auditoria(self, sesion: Sesion) -> list[dict[str, str]]:
        # Solo admin puede ver auditoria completa.
        self._autorizar(Sesion(sesion.usuario, sesion.rol), "listar_usuarios")
        if sesion.rol != "admin":
            self._registrar_auditoria(sesion, "obtener_auditoria", "denegado")
            raise ErrorAutorizacion("Solo admin puede ver la auditoria")
        self._registrar_auditoria(sesion, "obtener_auditoria", "permitido")
        return list(self._auditoria)
