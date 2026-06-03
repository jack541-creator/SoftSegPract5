from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable
from src.logger.log_util import anadir_al_log


# =========================
# Exceptions
# =========================

class ErrorAutenticacion(Exception):
    pass


class ErrorAutorizacion(Exception):
    pass


# =========================
# Core session + request
# =========================

@dataclass(frozen=True)
class Sesion:
    usuario: str


@dataclass
class Request:
    sesion: Sesion
    accion: str
    funcion: Callable
    args: tuple
    kwargs: dict


# =========================
# Chain of Responsibility
# =========================

class SecurityHandler:
    def __init__(self, next_handler=None):
        self._next = next_handler

    def handle(self, request: Request):
        if self._next:
            return self._next.handle(request)
        return None


# =========================
# Authentication Layer
# =========================

class AuthHandler(SecurityHandler):
    def __init__(self, proxy, next_handler=None):
        super().__init__(next_handler)
        self._proxy = proxy

    def handle(self, request: Request):
        user = self._proxy._usuarios.get(request.sesion.usuario)

        if not user:
            raise ErrorAutenticacion("Usuario no autenticado")

        return super().handle(request)


# =========================
# Authorization Layer (RBAC)
# =========================

class RBACHandler(SecurityHandler):
    def __init__(self, proxy, policies, next_handler=None):
        super().__init__(next_handler)
        self._proxy = proxy
        self._policies = policies

    def handle(self, request: Request):
        user = self._proxy._usuarios.get(request.sesion.usuario)

        if not user:
            raise ErrorAutenticacion("Usuario no existe")

        rol_real = user["rol"]
        permisos = self._policies.get(rol_real, set())

        if request.accion not in permisos:
            raise ErrorAutorizacion(
                f"Rol '{rol_real}' no autorizado para '{request.accion}'"
            )

        return super().handle(request)


# =========================
# Validation Layer
# =========================

class ValidationHandler(SecurityHandler):
    def handle(self, request: Request):
        if request.accion == "anadir_credencial":
            if not request.args:
                raise ValueError("Datos insuficientes para credencial")

        return super().handle(request)


# =========================
# Audit Layer
# =========================

class AuditHandler(SecurityHandler):
    def __init__(self, auditoria, next_handler=None):
        super().__init__(next_handler)
        self._auditoria = auditoria

    def handle(self, request: Request):
        try:
            result = super().handle(request)

            anadir_al_log("info", f"{request.sesion.usuario} : {request.accion} --> permitido")
            self._auditoria.append({
                "fecha": datetime.now(timezone.utc).isoformat(),
                "usuario": request.sesion.usuario,
                "accion": request.accion,
                "resultado": "permitido",
            })

            return result

        except Exception as e:
            anadir_al_log("info", f"{request.sesion.usuario} : {request.accion} --> denegado")
            self._auditoria.append({
                "fecha": datetime.now(timezone.utc).isoformat(),
                "usuario": request.sesion.usuario,
                "accion": request.accion,
                "resultado": "denegado",
            })
            raise


# =========================
# Execution Layer
# =========================

class ExecutionHandler(SecurityHandler):
    def handle(self, request: Request):
        return request.funcion(*request.args, **request.kwargs)


# =========================
# Proxy
# =========================

class ProxySeguroGestorCredenciales:

    POLITICAS = {
        "admin": {
            "anadir_credencial",
            "obtener_hash_password",
            "cambiar_password",
            "cambiar_usuario",
            "eliminar_credencial",
            "listar_servicios",
            "listar_usuarios",
            "ver_auditoria",
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

    def __init__(self, gestor):
        self._gestor = gestor
        self._usuarios = {}
        self._auditoria = []

        handler = ExecutionHandler()
        handler = ValidationHandler(handler)
        handler = RBACHandler(self, self.POLITICAS, handler)
        handler = AuthHandler(self, handler)
        handler = AuditHandler(self._auditoria, handler)
        self._chain = handler

    # -------------------------
    # User system
    # -------------------------

    def registrar_usuario_proxy(self, usuario: str, password: str, rol: str):
        if rol not in self.POLITICAS:
            raise ValueError("Rol no soportado")

        self._usuarios[usuario] = {
            "password": password,
            "rol": rol,
        }

    def iniciar_sesion(self, usuario: str, password: str) -> Sesion:
        data = self._usuarios.get(usuario)

        if not data or data["password"] != password:
            try:
                anadir_al_log("info", f"{usuario} login -> denegado")
            except:
                pass
            raise ErrorAutenticacion()

        try:
            anadir_al_log("info", f"{usuario} login -> permitido")
        except:
            pass
        return Sesion(usuario=usuario)

    # -------------------------
    # Core executor
    # -------------------------

    def _ejecutar(self, sesion: Sesion, accion: str, funcion, *args, **kwargs):
        request = Request(
            sesion=sesion,
            accion=accion,
            funcion=funcion,
            args=args,
            kwargs=kwargs,
        )

        return self._chain.handle(request)

    # -------------------------
    # Public API
    # -------------------------

    def anadir_credencial(self, sesion, *args, **kwargs):
        return self._ejecutar(
            sesion, "anadir_credencial",
            self._gestor.anadir_credencial,
            *args, **kwargs
        )

    def eliminar_credencial(self, sesion, *args, **kwargs):
        return self._ejecutar(
            sesion, "eliminar_credencial",
            self._gestor.eliminar_credencial,
            *args, **kwargs
        )

    def obtener_hash_password(self, sesion, *args, **kwargs):
        return self._ejecutar(
            sesion, "obtener_hash_password",
            self._gestor.obtener_hash_password,
            *args, **kwargs
        )

    def cambiar_password(self, sesion, *args, **kwargs):
        return self._ejecutar(
            sesion, "cambiar_password",
            self._gestor.cambiar_password,
            *args, **kwargs
        )

    def cambiar_usuario(self, sesion, *args, **kwargs):
        return self._ejecutar(
            sesion, "cambiar_usuario",
            self._gestor.cambiar_usuario,
            *args, **kwargs
        )

    def listar_servicios(self, sesion, *args, **kwargs):
        return self._ejecutar(
            sesion, "listar_servicios",
            self._gestor.listar_servicios,
            *args, **kwargs
        )

    def listar_usuarios(self, sesion, *args, **kwargs):
        return self._ejecutar(
            sesion, "listar_usuarios",
            self._gestor.listar_usuarios,
            *args, **kwargs
        )

    # -------------------------
    # Audit access (RBAC-based)
    # -------------------------

    def obtener_auditoria(self, sesion: Sesion):
        user = self._usuarios.get(sesion.usuario)

        if not user:
            raise ErrorAutorizacion("Usuario no válido")

        permisos = self.POLITICAS.get(user["rol"], set())

        if "ver_auditoria" not in permisos:
            raise ErrorAutorizacion("No autorizado para ver auditoria")

        return list(self._auditoria)