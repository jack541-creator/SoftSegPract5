import bcrypt
from abc import ABC, abstractmethod

# =========================================================
# EXCEPCIONES
# =========================================================

class ErrorPoliticaPassword(Exception):
    pass

class ErrorAutenticacion(Exception):
    pass

class ErrorServicioNoEncontrado(Exception):
    pass

class ErrorCredencialExistente(Exception):
    pass

# =========================================================
# INTERFAZ HASH
# =========================================================

class ServicioHash(ABC):
    @abstractmethod
    def hash_clave(self, clave: str) -> bytes:
        pass
    @abstractmethod
    def verificar_clave(self, clave: str, clave_hashed: bytes) -> bool:
        pass


# =========================================================
# IMPLEMENTACIÓN BCRYPT
# =========================================================

class ServicioHashBcrypt(ServicioHash):
    def hash_clave(self, clave: str) -> bytes:
        return bcrypt.hashpw(clave.encode("utf-8"), bcrypt.gensalt())

    def verificar_clave(self, clave: str, clave_hashed: bytes) -> bool:
        return bcrypt.checkpw(clave.encode("utf-8"), clave_hashed)

# =========================================================
# FACTORY METHOD  (GoF)
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
    """permite añadir nuevos algoritmos sin tocar el código existente."""
    _FACTORIES[tipo] = factory

def obtener_factory(tipo: str = "bcrypt") -> HashFactory:
    if tipo not in _FACTORIES:
        raise ValueError(f"Tipo de hash no soportado: {tipo}")
    return _FACTORIES[tipo]()

# =========================================================
# VALIDADOR PASSWORD
# =========================================================

class ValidadorPassword:

    PASSWORDS_COMUNES = {
        "password", "123456", "12345678",
        "qwerty", "abc123", "111111",
        "123123", "admin", "user",
        "contraseña", "0000000",
        "seguro", "hola", "abcdefg",
    }

    SIMBOLOS = set(r"!@#$%^&*()-_=+[]{}|;:',.<>?/`~")

    def verificar_fortaleza(self, password: str) -> str:
        pass


# =========================================================
# GESTOR CREDENCIALES
# =========================================================

class GestorCredenciales:

    def __init__(self, clave_maestra: str, tipo_hash: str = "bcrypt"):

        # FACTORY METHOD — la fábrica concreta decide qué ServicioHash crear
        factory = obtener_factory(tipo_hash)
        self._hash_service = factory.obtener_servicio()

        self._validator = ValidadorPassword()

        self._clave_maestra_hashed = self._hash_service.hash_clave(clave_maestra)

        self._credenciales = {}

    # =====================================================
    # autenticación
    # =====================================================

    def _autenticar(self, clave_maestra: str):

        if not self._hash_service.verificar_clave(clave_maestra, self._clave_maestra_hashed):
            raise ErrorAutenticacion()

    # =====================================================
    # añadir credencial
    # =====================================================

    # access_control encima para que se ejecute primero
    @access_control
    @registry(nivel_log="warning")
    def anadir_credencial(self, clave_maestra: str, servicio: str, usuario: str, password: str) -> bool:
        simbolos = "!>;'\\/[]{}:\n\r"
        palabras_peligrosas = ["DROP", "DELETE", "UPDATE", "ALTER", "CREATE", "TABLE", "ALERT", "SCRIPT", "EXECUTE", "IMMEDIATE"]

        for valor in [clave_maestra, servicio, usuario, password]:
            if not isinstance(valor, str):
                raise TypeError("Todos los parámetros deben ser str")

        clave_maestra = clave_maestra.strip()
        servicio = servicio.strip()
        usuario = usuario.strip()
        password = password.strip()

        if usuario.replace('.', '', 1).replace('-', '', 1).isdigit():
            raise ValueError
        if not self._verificar_clave(clave_maestra, self._clave_maestra_hashed):
            raise PermissionError

        if not servicio or not usuario or len(usuario) > 255:
            raise ValueError

        if any(c in simbolos for c in usuario) or any(c in simbolos for c in servicio):
            raise ValueError

        if any(p.upper() in palabras_peligrosas for p in servicio.split()):
            raise ValueError

        # voy a asumir que verificar_fortaleza_password() es llamado antes de esta función
        if servicio not in self._credenciales:
            self._credenciales[servicio] = {}

        if usuario in self._credenciales[servicio]:
            raise ValueError("Credencial ya existente")

        self._credenciales[servicio][usuario] = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

        return True

    # =====================================================
    # obtener password
    # =====================================================

    def obtener_password(self, clave_maestra: str, servicio: str, usuario: str) -> bytes:

        self._autenticar(clave_maestra)

        if (servicio not in self._credenciales or usuario not in self._credenciales[servicio]):
            raise ErrorServicioNoEncontrado()

        return self._credenciales[servicio][usuario]

    # =====================================================
    # listar servicios
    # =====================================================

    def listar_servicios(self, clave_maestra: str) -> list:

        self._autenticar(clave_maestra)

        return list(self._credenciales.keys())

    # =====================================================
    # cambiar usuario
    # =====================================================

    def cambiar_usuario(self, servicio: str, usuario_antiguo: str, usuario_nuevo: str, clave_maestra: str) -> bool:

        self._autenticar(clave_maestra)

        if not all(isinstance(x, str) and x.strip() for x in [servicio, usuario_antiguo, usuario_nuevo]):
            raise ValueError()

        if servicio not in self._credenciales:
            raise ErrorServicioNoEncontrado()

        if usuario_antiguo not in self._credenciales[servicio]:
            raise ErrorServicioNoEncontrado()

        if usuario_nuevo in self._credenciales[servicio]:
            raise ErrorCredencialExistente()

        password_hashed = self._credenciales[servicio].pop(usuario_antiguo)

        self._credenciales[servicio][usuario_nuevo] = password_hashed

        return True

#gestor = GestorCredenciales("claveMaestraSegura123!")
#print(gestor._verificar_clave("clave", gestor._hash_clave("clave")))
