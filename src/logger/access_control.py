"""
Decorador access_control para control de acceso basado en roles y permisos.
"""
import functools
from typing import Callable, Any, Optional, List, Set, Dict
from enum import Enum
from datetime import datetime, UTC

# =========================================================
#  CONSTANTES
# =========================================================

class RolUsuario(str, Enum):
    """Roles de usuario para el control de acceso."""
    ADMIN = "admin"
    USUARIO = "usuario"
    INVITADO = "invitado"
    AUDITOR = "auditor"


class Permiso(str, Enum):
    """Permisos disponibles en el sistema."""
    # Credenciales
    CREAR_CREDENCIAL = "crear_credencial"
    LEER_CREDENCIAL = "leer_credencial"
    ACTUALIZAR_CREDENCIAL = "actualizar_credencial"
    ELIMINAR_CREDENCIAL = "eliminar_credencial"
    
    # Usuarios
    CREAR_USUARIO = "crear_usuario"
    MODIFICAR_USUARIO = "modificar_usuario"
    ELIMINAR_USUARIO = "eliminar_usuario"
    
    # OTPs
    GENERAR_OTP = "generar_otp"
    VERIFICAR_OTP = "verificar_otp"
    
    # Auditoría
    VER_AUDITORIA = "ver_auditoria"
    EXPORTAR_AUDITORIA = "exportar_auditoria"
    
    # Sistema
    CONFIGURAR_SISTEMA = "configurar_sistema"
    REINICIAR_SISTEMA = "reiniciar_sistema"

# =========================================================
#  MATRIZ DE PERMISOS POR ROL
# =========================================================

PERMISOS_POR_ROL: Dict[RolUsuario, Set[Permiso]] = {
    RolUsuario.ADMIN: {
        Permiso.CREAR_CREDENCIAL,
        Permiso.LEER_CREDENCIAL,
        Permiso.ACTUALIZAR_CREDENCIAL,
        Permiso.ELIMINAR_CREDENCIAL,
        Permiso.CREAR_USUARIO,
        Permiso.MODIFICAR_USUARIO,
        Permiso.ELIMINAR_USUARIO,
        Permiso.GENERAR_OTP,
        Permiso.VERIFICAR_OTP,
        Permiso.VER_AUDITORIA,
        Permiso.EXPORTAR_AUDITORIA,
        Permiso.CONFIGURAR_SISTEMA,
        Permiso.REINICIAR_SISTEMA,
    },
    RolUsuario.USUARIO: {
        Permiso.CREAR_CREDENCIAL,
        Permiso.LEER_CREDENCIAL,
        Permiso.ACTUALIZAR_CREDENCIAL,
        Permiso.ELIMINAR_CREDENCIAL,
        Permiso.GENERAR_OTP,
        Permiso.VERIFICAR_OTP,
    },
    RolUsuario.AUDITOR: {
        Permiso.VER_AUDITORIA,
        Permiso.EXPORTAR_AUDITORIA,
        Permiso.LEER_CREDENCIAL,
    },
    RolUsuario.INVITADO: set(),}

# =========================================================
#  CONTEXTO DE SEGURIDAD
# =========================================================

class ContextoSeguridad:
    """
    Contexto de seguridad para la sesión actual.
    Almacena información del usuario autenticado y sus roles.
    """
    _instancia = None
    _usuario_actual: Optional[str] = None
    _rol_actual: Optional[RolUsuario] = None
    _sesion_id: Optional[str] = None
    _timestamp_inicio: Optional[datetime] = None

    def __new__(cls):
        if cls._instancia is None:
            cls._instancia = super().__new__(cls)
        return cls._instancia

    def iniciar_sesion(self, usuario: str, rol: RolUsuario, sesion_id: str = None) -> None:
        """Inicia una sesión de usuario."""
        self._usuario_actual = usuario
        self._rol_actual = rol
        self._sesion_id = sesion_id or self._generar_sesion_id()
        self._timestamp_inicio = datetime.now(UTC)

    def cerrar_sesion(self) -> None:
        """Cierra la sesión actual."""
        self._usuario_actual = None
        self._rol_actual = None
        self._sesion_id = None
        self._timestamp_inicio = None

    @property
    def usuario_actual(self) -> Optional[str]:
        return self._usuario_actual

    @property
    def rol_actual(self) -> Optional[RolUsuario]:
        return self._rol_actual

    @property
    def sesion_id(self) -> Optional[str]:
        return self._sesion_id

    @property
    def esta_autenticado(self) -> bool:
        return self._usuario_actual is not None and self._rol_actual is not None

    def tiene_permiso(self, permiso: Permiso) -> bool:
        """Verifica si el usuario actual tiene un permiso específico."""
        if not self.esta_autenticado:
            return False
        return permiso in PERMISOS_POR_ROL.get(self._rol_actual, set())

    def _generar_sesion_id(self) -> str:
        """Genera un ID de sesión único."""
        import uuid
        return str(uuid.uuid4())

# =========================================================
#  DECORADOR ACCESS_CONTROL
# =========================================================

def access_control(
    permisos_requeridos: Optional[List[Permiso]] = None,
    roles_requeridos: Optional[List[RolUsuario]] = None,
    registrar_intentos: bool = True,):

    # Manejar el caso @access_control sin paréntesis
    if callable(permisos_requeridos):
        func = permisos_requeridos
        # Crear un decorador con valores por defecto
        def decorador_simple(f):
            @functools.wraps(f)
            def wrapper_simple(*args, **kwargs):
                ctx = ContextoSeguridad()
                if not ctx.esta_autenticado:
                    error_msg = f"Acceso denegado: Usuario no autenticado para {f.__name__}"
                    raise PermissionError(error_msg)
                return f(*args, **kwargs)
            return wrapper_simple
        return decorador_simple(func)
    
    if permisos_requeridos is None:
        permisos_requeridos = []
    if roles_requeridos is None:
        roles_requeridos = []
    
    def decorador(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            ctx = ContextoSeguridad()
            
            # verificar autenticación
            if not ctx.esta_autenticado:
                error_msg = f"Acceso denegado: Usuario no autenticado para {func.__name__}"
                if registrar_intentos:
                    _registrar_intento_acceso(func.__name__, "DENEGADO", 
                        f"Usuario no autenticado - {args}, {kwargs}")
                raise PermissionError(error_msg)
            
            # verificar roles
            tiene_rol = False
            if roles_requeridos:
                if ctx.rol_actual not in roles_requeridos:
                    error_msg = (f"Acceso denegado: Rol '{ctx.rol_actual}' "
                                f"no tiene permisos para {func.__name__}")
                    if registrar_intentos:
                        _registrar_intento_acceso(func.__name__, "DENEGADO",
                            f"Rol no autorizado - Rol actual: {ctx.rol_actual}")
                    raise PermissionError(error_msg)
                tiene_rol = True
            
            # verificar permisos
            tiene_permiso = False
            if permisos_requeridos:
                for permiso in permisos_requeridos:
                    if ctx.tiene_permiso(permiso):
                        tiene_permiso = True
                        break
                
                if not tiene_permiso:
                    permisos_str = ", ".join(p.value for p in permisos_requeridos)
                    error_msg = (f"Acceso denegado: Usuario '{ctx.usuario_actual}' "
                                f"no tiene permisos requeridos [{permisos_str}] "
                                f"para {func.__name__}")
                    if registrar_intentos:
                        _registrar_intento_acceso(func.__name__, "DENEGADO",
                            f"Permisos insuficientes - Permisos requeridos: {permisos_str}")
                    raise PermissionError(error_msg)
            
            if not roles_requeridos and not permisos_requeridos:
                # solo requiere autenticación (ya verificada)
                pass
            
            # registrar acceso exitoso
            if registrar_intentos:
                rol_permiso_info = ""
                if roles_requeridos:
                    rol_permiso_info = f"Roles: {[r.value for r in roles_requeridos]}"
                if permisos_requeridos:
                    rol_permiso_info += f" Permisos: {[p.value for p in permisos_requeridos]}"
                
                _registrar_intento_acceso(func.__name__, "PERMITIDO",
                    f"Usuario: {ctx.usuario_actual}, Rol: {ctx.rol_actual}, {rol_permiso_info}" )
            
            # ejecutar la función original
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorador


# =========================================================
#  FUNCIONES AUXILIARES
# =========================================================

def _registrar_intento_acceso(funcion: str, resultado: str, detalle: str) -> None:
    """
    Registra intentos de acceso (puede conectarse al sistema de logging).
    """
    try:
        # usar el logger seguro si está disponible
        from src.logger.hash_logging import anadir_al_log
        anadir_al_log("info", f"ACCESS_CONTROL | {funcion} | {resultado} | {detalle}")
    except ImportError:
        # fallback a logging estándar
        import logging
        timestamp = datetime.now(UTC).isoformat()
        logging.info(f"{timestamp} | ACCESS_CONTROL | {funcion} | {resultado} | {detalle}")


# =========================================================
#  DECORADOR SIMPLIFICADO (para compatibilidad)
# =========================================================

# Versión simple del decorador (sin parámetros) para compatibilidad
def simple_access_control(func: Callable) -> Callable:
    """
    Versión simple del decorador que solo requiere autenticación.
    Uso: @access_control (sin parámetros)
    """
    return access_control()(func)

access_control_simple = simple_access_control