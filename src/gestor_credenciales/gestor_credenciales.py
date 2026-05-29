import bcrypt
import string
import random
from abc import ABC, abstractmethod
from datetime import datetime, UTC, timedelta
from enum import Enum

# sistema de logging seguro
from src.logger.access_control import access_control
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logger.log_util import (anadir_al_log, verificar_cadena_hashes, 
    inicializar_log, configure_logging, existe_archivo, archivo_vacio)

# =========================================================
#  EXCEPCIONES
# =========================================================

class ErrorPoliticaPassword(Exception):
    pass


class ErrorAutenticacion(Exception):
    pass


class ErrorServicioNoEncontrado(Exception):
    pass


class ErrorUsuarioNoEncontrado(Exception):
    pass


class ErrorCredencialExistente(Exception):
    pass


class ErrorTokenNoCreado(Exception):
    pass


class ErrorTokenCaducado(Exception):
    pass

# =========================================================
#  INTERFAZ HASH
# =========================================================

class ServicioHash(ABC):
    @abstractmethod
    def hash_clave(self, clave: str) -> bytes:
        pass

    @abstractmethod
    def verificar_clave(self, clave: str, clave_hashed: bytes) -> bool:
        pass


# ISP: interfaz pequeña solo para auditoría
class ServicioAuditoria(ABC):
    @abstractmethod
    def registrar_evento(self, accion: str, detalle: str) -> None:
        pass


# =========================================================
#  FORTALEZA
# =========================================================

class FortalezaPassword(str, Enum):
    DEBIL  = "débil"
    MEDIA  = "media"
    FUERTE = "fuerte"


# =========================================================
#  OCP: INTERFAZ POLÍTICA DE PASSWORD (Strategy)
# =========================================================

class PoliticaPassword(ABC):
    """Interfaz para la política de validación de contraseñas.

    Abierta a extensión (nuevas políticas heredan de aquí)
    y cerrada a modificación (GestorCredenciales no necesita cambiar).
    """

    @abstractmethod
    def verificar_fortaleza(self, password: str) -> FortalezaPassword:
        """Devuelve 'débil', 'media' o 'fuerte' desde FortalezaPassword"""
        pass

    def es_aceptable(self, password: str) -> bool:
        """
        Define qué fortalezas se consideran suficientes.
        Las subclases pueden sobrescribir esto si necesitan
        un umbral distinto, pero siempre operan sobre FortalezaPassword.
        """
        return self.verificar_fortaleza(password) in (
            FortalezaPassword.MEDIA,
            FortalezaPassword.FUERTE,)


class AuditLogger(ServicioAuditoria):
    def __init__(self, archivo: str = "audit.log"):
        self.archivo = archivo

    def registrar_evento(self, accion: str, detalle: str) -> None:
        timestamp = datetime.now(UTC).isoformat()
        with open(self.archivo, "a", encoding="utf-8") as f:
            f.write(f"{timestamp} | {accion} | {detalle}\n")


# =========================================================
#  IMPLEMENTACIÓN BCRYPT
# =========================================================

class ServicioHashBcrypt(ServicioHash):
    def hash_clave(self, clave: str) -> bytes:
        return bcrypt.hashpw(clave.encode("utf-8"), bcrypt.gensalt())

    def verificar_clave(self, clave: str, clave_hashed: bytes) -> bool:
        return bcrypt.checkpw(clave.encode("utf-8"), clave_hashed)


# =========================================================
#  FACTORY METHOD  (GoF)
# =========================================================

class HashFactory(ABC):
    """clase base abstracta, declara el factory method"""

    @abstractmethod
    def crear(self) -> ServicioHash:
        """las subclases deciden qué instanciar."""
        pass

    # método que usa el producto sin conocer su clase concreta
    def obtener_servicio(self) -> ServicioHash:
        servicio = self.crear()
        return servicio


class BcryptFactory(HashFactory):
    """fábrica concreta, produce ServicioHashBcrypt."""

    def crear(self) -> ServicioHash:
        return ServicioHashBcrypt()


# registro abierto a extensión sin modificar HashFactory ni BcryptFactory
_FACTORIES: dict[str, type[HashFactory]] = {"bcrypt": BcryptFactory,}


def registrar_factory(tipo: str, factory: type[HashFactory]) -> None:
    """permite anadir nuevos algoritmos sin tocar el código existente."""
    _FACTORIES[tipo] = factory


def obtener_factory(tipo: str = "bcrypt") -> HashFactory:
    if tipo not in _FACTORIES:
        raise ValueError(f"Tipo de hash no soportado: {tipo}")
    return _FACTORIES[tipo]()


# =========================================================
#  VALIDADOR PASSWORD (R)
# =========================================================

class ValidadorPassword(PoliticaPassword):  # <- hereda de PoliticaPassword
    PASSWORDS_COMUNES = {"password", "123456", "12345678", "qwerty", "abc123","111111",
        "123123", "admin", "user", "contraseña", "0000000", "seguro", "hola", "abcdefg",}
    SIMBOLOS = set(r"!@#$%^&*()-_=+[]{}|;:',.<>?/`~")
    TRIVIALES = ["12345", "qwerty"]

    def verificar_fortaleza(self, password: str) -> FortalezaPassword:
        
        if not isinstance(password, str) or password == "":
            raise ErrorPoliticaPassword()

        # ---------- Criterio 1: longitud ----------
        cumple_longitud = len(password) >= 8

        # ---------- Criterio 2: mezcla ----------
        tiene_mayus = any(c.isupper() for c in password)
        tiene_minus = any(c.islower() for c in password)
        tiene_num = any(c.isdigit() for c in password)

        # penalizar mayúscula solo al inicio
        resto_sin_mayus = all(not c.isupper() for c in password[1:])
        mayus_solo_inicio = tiene_mayus and password[0].isupper() and resto_sin_mayus

        # cadenas triviales
        lower_pwd = password.lower()
        contiene_trivial = any(x in lower_pwd for x in self.TRIVIALES)

        cumple_mezcla = (tiene_mayus and tiene_minus and tiene_num and not mayus_solo_inicio and not contiene_trivial)

        # ---------- Criterio 3: símbolos ----------
        posiciones_simbolos = [i for i, c in enumerate(password) if c in self.SIMBOLOS]

        cumple_simbolos = len(posiciones_simbolos) > 0 and not all(i == len(password) - 1 for i in posiciones_simbolos)

        # ---------- Criterio 4: no común ----------
        no_comun = password.lower() not in self.PASSWORDS_COMUNES

        # ---------- puntos ----------
        criterios = sum([cumple_longitud, cumple_mezcla, cumple_simbolos, no_comun])

        # ---------- clasificación ----------
        if criterios <= 1:
            return FortalezaPassword.DEBIL
        elif criterios <= 3:
            return FortalezaPassword.MEDIA
        else:
            return FortalezaPassword.FUERTE

# =========================================================
#  GESTOR CREDENCIALES
# =========================================================

class GestorCredenciales:
    
    def __init__(self, clave_maestra: str, tipo_hash: str = "bcrypt", log_file="log_gestor_credenciales.log", politica_password: PoliticaPassword | None = None,):

        # inicializar logging seguro
        self.log_file = log_file
        configure_logging(log_file)
        inicializar_log(log_file)
        # verificar integridad del log al iniciar
        if not existe_archivo(log_file) or archivo_vacio(log_file):
            # no debería entrar aquí porque cada vez que se inicia no está vacío
            anadir_al_log("info", f"SISTEMA INICIADO: Nuevo archivo de log ({log_file})")
        elif verificar_cadena_hashes(log_file):
            anadir_al_log("info", f"SISTEMA INICIADO: Log íntegro ({log_file})", log_file)
        else:
            anadir_al_log("warning", f"LOG CORRUPTO: El archivo {log_file} ha sido modificado", log_file)
            print(f"ADVERTENCIA: El archivo de log {log_file} puede estar corrupto", log_file)
        
        factory = obtener_factory(tipo_hash)
        self._hash_service = factory.obtener_servicio()

        self._audit_logger = AuditLogger("ciphercoin_audit.log")

        # OCP/Strategy: si no se inyecta ninguna política, se usa la por defecto
        self._validator = politica_password if politica_password is not None else ValidadorPassword()

        self._clave_maestra_hashed = self._hash_service.hash_clave(clave_maestra)

        self._credenciales = {}
        anadir_al_log("info", "GestorCredenciales inicializado correctamente")

    # =====================================================
    #  autenticación
    # =====================================================

    def _autenticar(self, clave_maestra: str, contexto: str = ""):
        if not self._hash_service.verificar_clave(clave_maestra, self._clave_maestra_hashed):
            self._audit_logger.registrar_evento("AUTENTICACION_FALLIDA", "Clave maestra incorrecta",)
            raise ErrorAutenticacion()
        if contexto:
            anadir_al_log("debug", f"AUTENTICACION_EXITOSA - {contexto}") 
        else:
            anadir_al_log("debug", "AUTENTICACION_EXITOSA") 
            anadir_al_log("debug", f"AUTENTICACION_EXITOSA {contexto}") 

    # =====================================================
    #  anadir credencial (R)
    # =====================================================

    @access_control
    def anadir_credencial(self, clave_maestra, servicio, usuario, password):
        simbolos = "!>;'\\/[]{}:\n\r|&"
        palabras_peligrosas = ["DROP", "DELETE", "UPDATE", "ALTER", "CREATE",
                                "TABLE", "ALERT", "SCRIPT", "EXECUTE", "IMMEDIATE",]

        for valor in [clave_maestra, servicio, usuario, password]:
            if not isinstance(valor, str):
                raise TypeError("Parámetros de tipo inadecuado.")
                anadir_al_log("error", f"ERROR_ANADIR_CREDENCIAL: {error_msg}")

        clave_maestra = clave_maestra.strip()
        servicio = servicio.strip()
        usuario = usuario.strip()
        password = password.strip()

        if not self.es_password_segura(password):
            raise ErrorPoliticaPassword()

        if usuario.replace(".", "", 1).replace("-", "", 1).isdigit():
            raise ValueError()

        if not servicio or not usuario or len(usuario) > 255:
            raise ValueError()

        if any(c in simbolos for c in usuario) or any(c in simbolos for c in servicio):
            anadir_al_log("error", f"Símbolos no permitidos. Servicio: {servicio}, Usuario: {usuario}")
            raise ValueError()

        if any(p.upper() in palabras_peligrosas for p in servicio.split()):
            anadir_al_log("critical", f"Posible explotación. Servicio: {servicio}")
            raise ValueError()

        if servicio not in self._credenciales:
            self._autenticar(clave_maestra)
            self._credenciales[servicio] = {}

        self._autenticar(clave_maestra)
        if usuario in self._credenciales[servicio]:
            raise ErrorCredencialExistente()

        self._autenticar(clave_maestra)
        self._credenciales[servicio][usuario] = {"hash": self._hash_service.hash_clave(password)}

        anadir_al_log("info", f"CREDENCIAL_ANADIDA: Servicio={servicio}, Usuario={usuario}")
        return True

    # =====================================================
    #  obtener password
    # =====================================================

    def obtener_hash_password(self, clave_maestra: str, servicio: str, usuario: str) -> bytes:
        for valor in [clave_maestra, servicio, usuario]:
            if not isinstance(valor, str):
                raise TypeError("Todos los parámetros deben ser str")

            if not valor.strip():
                raise ValueError("Los campos no deben estar vacíos")

        clave_maestra = clave_maestra.strip()
        servicio = servicio.strip()
        usuario = usuario.strip()

        self._autenticar(clave_maestra)

        if (
            servicio not in self._credenciales
            or usuario not in self._credenciales[servicio]
        ):
            raise ErrorServicioNoEncontrado()

        self._audit_logger.registrar_evento(
            "CREDENCIAL_CONSULTADA",
            f"Servicio={servicio}, Usuario={usuario}",)

        return self._credenciales[servicio][usuario]["hash"]

    # =====================================================
    #  Cambiar password
    # =====================================================

    def cambiar_password(
        self,
        clave_maestra: str,
        servicio: str,
        usuario: str,
        password_actual: str,
        password_nueva: str,) -> bool:
        for valor in [clave_maestra, password_actual, password_nueva]:
            if not isinstance(valor, str):
                raise TypeError("Todos los parámetros deben ser str")
            if not valor.strip():
                raise ValueError("Los campos no deben estar vacíos")

        clave_maestra = clave_maestra.strip()
        password_actual = password_actual.strip()
        password_nueva = password_nueva.strip()

        password_hashed = self.obtener_hash_password(
            clave_maestra,
            servicio,
            usuario,
        )

        if not self._hash_service.verificar_clave(password_actual, password_hashed):
            self._audit_logger.registrar_evento(
                "CAMBIO_PASSWORD_FALLIDO",
                f"Servicio={servicio}, Usuario={usuario}",
            )
            raise ErrorAutenticacion()

        if not self.es_password_segura(password_nueva):
            raise ErrorPoliticaPassword()

        self._credenciales[servicio.strip()][usuario.strip()]["hash"] = self._hash_service.hash_clave(password_nueva)

        self._audit_logger.registrar_evento(
            "PASSWORD_CAMBIADA",
            f"Servicio={servicio.strip()}, Usuario={usuario.strip()}",
        )

        return True

    # =====================================================
    #  es_password_segura (wrapper de es_aceptable)
    # =====================================================
    def es_password_segura(self, password: str) -> bool:
        return self._validator.es_aceptable(password)

    # =====================================================
    #  listar servicios
    # =====================================================

    def listar_servicios(self, clave_maestra: str) -> list:
        self._autenticar(clave_maestra)
        return list(self._credenciales.keys())

    # =====================================================
    #  listar usuarios
    # =====================================================
    def listar_usuarios(self, clave_maestra: str) -> list:
        self._autenticar(clave_maestra)

        usuarios = []
        for usuarios_servicio in self._credenciales.values():
            usuarios.extend(usuarios_servicio.keys())

        return usuarios

    # =====================================================
    #  eliminar credencial
    # =====================================================
    def eliminar_credencial(self, clave_maestra: str, servicio: str, usuario: str) -> bool:
        if servicio not in self._credenciales:
            raise ErrorServicioNoEncontrado()

        if usuario not in self._credenciales[servicio]:
            raise ErrorServicioNoEncontrado()

        self._autenticar(clave_maestra)
        del self._credenciales[servicio][usuario]

        self._autenticar(clave_maestra)
        if not self._credenciales[servicio]:
            del self._credenciales[servicio]

        self._audit_logger.registrar_evento(
            "CREDENCIAL_ELIMINADA",
            f"Servicio={servicio}, Usuario={usuario}",)

        return True

    # =====================================================
    #  cambiar usuario
    # =====================================================
    def cambiar_usuario(
        self,
        servicio: str,
        usuario_antiguo: str,
        usuario_nuevo: str,
        clave_maestra: str,) -> bool:
        if not all(
            isinstance(x, str) and x.strip()
            for x in [servicio, usuario_antiguo, usuario_nuevo]
        ):
            raise ValueError()

        servicio = servicio.strip()
        usuario_antiguo = usuario_antiguo.strip()
        usuario_nuevo = usuario_nuevo.strip()

        simbolos_invalidos = "!>;'\\/[]{}:\n\r"
        palabras_peligrosas = [
            "DROP", "DELETE", "UPDATE", "ALTER", "CREATE",
            "TABLE", "ALERT", "SCRIPT", "EXECUTE", "IMMEDIATE",
        ]

        if len(usuario_nuevo) > 255:
            raise ValueError()

        if any(c in simbolos_invalidos for c in usuario_nuevo):
            raise ValueError()

        if any(p in usuario_nuevo.upper() for p in palabras_peligrosas):
            raise ValueError()

        if usuario_nuevo.replace(".", "", 1).replace("-", "", 1).isdigit():
            raise ValueError()

        self._autenticar(clave_maestra)
        if servicio not in self._credenciales:
            raise ErrorServicioNoEncontrado()

        self._autenticar(clave_maestra)
        if usuario_antiguo not in self._credenciales[servicio]:
            raise ErrorServicioNoEncontrado()

        self._autenticar(clave_maestra)
        if usuario_nuevo in self._credenciales[servicio]:
            raise ErrorCredencialExistente()

        self._autenticar(clave_maestra)
        password_hashed = self._credenciales[servicio].pop(usuario_antiguo)

        self._autenticar(clave_maestra)
        self._credenciales[servicio][usuario_nuevo] = password_hashed

        self._audit_logger.registrar_evento(
            "USUARIO_CAMBIADO",
            f"Servicio={servicio}, Usuario antiguo={usuario_antiguo}, Usuario nuevo={usuario_nuevo}",
        )

        return True

    # =====================================================
    #  OTPs
    # =====================================================


    def generar_otps(self, cantidad: int) -> list:

        if not isinstance(cantidad, int):
            raise TypeError

        if cantidad <= 0:
            raise ValueError

        caracteres = string.ascii_letters + string.digits

        otps = set()

        while len(otps) < cantidad:

            otp = "".join(
                random.choice(caracteres)
                for _ in range(6)
        )

            otps.add(otp)

        return list(otps)


    def almacenar_otps(
    self,
    clave_maestra: str,
    servicio: str,
    usuario: str,
    otps: list
) -> None:

        if not isinstance(otps, list):
            raise TypeError

        self._autenticar(clave_maestra)

        self._credenciales[servicio][usuario]["otps"] = (
            otps.copy()
    )

        self._audit_logger.registrar_evento(
            "OTPS_ALMACENADAS",
            f"Servicio={servicio}, Usuario={usuario}"
        )


    def verificar_otp(
        self,
        clave_maestra: str,
        servicio: str,
        usuario: str,
        otp: str
    ) -> bool:

        if not isinstance(otp, str):
            return False

        if len(otp) != 6:
            return False

        self._autenticar(clave_maestra)

        if otp in self._credenciales[servicio][usuario]["otps"]:

            self._credenciales[servicio][usuario]["otps"].remove(
                otp
        )

            self._audit_logger.registrar_evento(
                "OTP_VERIFICADO",
                f"Servicio={servicio}, Usuario={usuario}"
        )

            return True

        return False
    
    # =====================================================
    #  TOKENS
    # =====================================================

    def generar_token(self, clave_maestra: str, servicio: str, usuario: str, password: str) -> str:

        self._autenticar(clave_maestra)
        
        # Comprobación de existencia de servicio y usuario
        if servicio not in self._credenciales:
            raise ErrorServicioNoEncontrado
        elif usuario not in self._credenciales[servicio]:
            raise ErrorUsuarioNoEncontrado
        
        # Auntenticación del usuario
        hash = self.obtener_hash_password(clave_maestra, servicio, usuario)
        if not self._hash_service.verificar_clave(password, hash):
            raise ErrorAutenticacion
        
        # Creación del token
        caracteres = string.ascii_letters + string.digits
        token = "".join(
                random.choice(caracteres)
                for _ in range(16)
        )

        
        self._credenciales[servicio][usuario]["token"] = {
            "hash" : self._hash_service.hash_clave(token),
            "expiration" : datetime.now(UTC) + timedelta(hours=1)
        }

        return token
    
    
    def autenticar_token(self, clave_maestra: str, servicio: str, usuario: str, token: str) -> bool:
        
        self._autenticar(clave_maestra)

        # Comprobación de existencia de servicio y usuario
        if servicio not in self._credenciales:
            raise ErrorServicioNoEncontrado
        elif usuario not in self._credenciales[servicio]:
            raise ErrorUsuarioNoEncontrado
        elif "token" not in self._credenciales[servicio][usuario]:
            raise ErrorTokenNoCreado
        
        # Auntenticación del token y comprobación de la caducidad
        if datetime.now(UTC) > self._credenciales[servicio][usuario]["token"]["expiration"]:
            raise ErrorTokenCaducado
        
        return self._hash_service.verificar_clave(token, self._credenciales[servicio][usuario]["token"]["hash"])
    
    def renovar_sesion(self, clave_maestra: str, servicio: str, usuario: str) -> None:

        self._autenticar(clave_maestra)

        # Comprobación de existencia de servicio y usuario
        if servicio not in self._credenciales:
            raise ErrorServicioNoEncontrado
        elif usuario not in self._credenciales[servicio]:
            raise ErrorUsuarioNoEncontrado
        elif "token" not in self._credenciales[servicio][usuario]:
            raise ErrorTokenNoCreado
        
        self._credenciales[servicio][usuario]["token"]["expiration"] = datetime.now(UTC) + timedelta(hours=1)
