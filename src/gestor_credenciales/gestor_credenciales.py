import bcrypt, string, random
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


class ErrorCodigoNoEstablecido(Exception):
    pass


class ErrorSinIntentosRestantes(Exception):
    pass


class ErrorUsuarioYaVerificado(Exception):
    pass


class ErrorCorreoNoEstablecido(Exception):
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
_FACTORIES: dict[str, type[HashFactory]] = {
    "bcrypt": BcryptFactory,
}


def registrar_factory(tipo: str, factory: type[HashFactory]) -> None:
    """permite anadir nuevos algoritmos sin tocar el código existente."""
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
        "password",
        "123456",
        "12345678",
        "qwerty",
        "abc123",
        "111111",
        "123123",
        "admin",
        "user",
        "contraseña",
        "0000000",
        "seguro",
        "hola",
        "abcdefg",
    }

    SIMBOLOS = set(r"!@#$%^&*()-_=+[]{}|;:',.<>?/`~")

    TRIVIALES = ["12345", "qwerty"]

    def verificar_fortaleza(self, password: str) -> str:
        # ---------- Validación de entrada ----------
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

        cumple_mezcla = (
            tiene_mayus
            and tiene_minus
            and tiene_num
            and not mayus_solo_inicio
            and not contiene_trivial
        )

        # ---------- Criterio 3: símbolos ----------
        posiciones_simbolos = [i for i, c in enumerate(password) if c in self.SIMBOLOS]

        cumple_simbolos = len(posiciones_simbolos) > 0 and not all(
            i == len(password) - 1 for i in posiciones_simbolos
        )

        # ---------- Criterio 4: no común ----------
        no_comun = password.lower() not in self.PASSWORDS_COMUNES

        # ---------- Score ----------
        criterios = sum([cumple_longitud, cumple_mezcla, cumple_simbolos, no_comun])

        # ---------- Clasificación ----------
        if criterios <= 1:
            return "débil"
        elif criterios <= 3:
            return "media"
        else:
            return "fuerte"


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
        if not self._hash_service.verificar_clave(
            clave_maestra, self._clave_maestra_hashed
        ):
            raise ErrorAutenticacion()

    # =====================================================
    # anadir credencial
    # =====================================================

    # access_control encima para que se ejecute primero
    # @access_control
    # @registry(nivel_log="warning")
    def anadir_credencial(
        self,
        clave_maestra: str,
        servicio: str,
        usuario: str,
        password: str | None = None,
        contraseña: str | None = None,
    ) -> bool:
        if password is None:
            password = contraseña

        simbolos = "!>;'\\/[]{}:\n\r|&"
        palabras_peligrosas = [
            "DROP",
            "DELETE",
            "UPDATE",
            "ALTER",
            "CREATE",
            "TABLE",
            "ALERT",
            "SCRIPT",
            "EXECUTE",
            "IMMEDIATE",
        ]

        for valor in [clave_maestra, servicio, usuario, password]:
            if not isinstance(valor, str):
                raise TypeError("Todos los parámetros deben ser str")

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
            raise ValueError()

        if any(p.upper() in palabras_peligrosas for p in servicio.split()):
            raise ValueError()

        # voy a asumir que verificar_fortaleza_password() es llamado antes de esta función
        if servicio not in self._credenciales:
            self._autenticar(clave_maestra) # Mediación completa
            self._credenciales[servicio] = {}

        self._autenticar(clave_maestra) # Mediación completa
        if usuario in self._credenciales[servicio]:
            raise ErrorCredencialExistente()

        self._autenticar(clave_maestra) # Mediación completa
        self._credenciales[servicio][usuario] = {"hash" : bcrypt.hashpw(
            password.encode("utf-8"), bcrypt.gensalt()
        )}

        return True

    # =====================================================
    # obtener password
    # =====================================================

    def obtener_password(
        self, clave_maestra: str, servicio: str, usuario: str
    ) -> bytes:
        self._autenticar(clave_maestra)

        if (
            servicio not in self._credenciales
            or usuario not in self._credenciales[servicio]
        ):
            raise ErrorServicioNoEncontrado()

        return self._credenciales[servicio][usuario]["hash"]
    
    # =====================================================
    # es_password_segura (wrapper de verificar_fortaleza)
    # =====================================================
    def es_password_segura(self, password: str) -> bool:
        return self._validator.verificar_fortaleza(password) in ["media", "fuerte"]

    # =====================================================
    # listar servicios
    # =====================================================

    def listar_servicios(self, clave_maestra: str) -> list:
        self._autenticar(clave_maestra)

        return list(self._credenciales.keys())

    # =====================================================
    # listar usuarios
    # =====================================================
    def listar_usuarios(self, clave_maestra: str) -> list:
        self._autenticar(clave_maestra)

        usuarios = []
        for usuarios_servicio in self._credenciales.values():
            usuarios.extend(usuarios_servicio.keys())

        return usuarios

    # =====================================================
    # eliminar credencial
    # =====================================================
    def eliminar_credencial(
        self, clave_maestra: str, servicio: str, usuario: str
    ) -> bool:

        if servicio not in self._credenciales:
            raise ErrorServicioNoEncontrado()

        if usuario not in self._credenciales[servicio]:
            raise ErrorServicioNoEncontrado()

        self._autenticar(clave_maestra) # Mediación Completa
        del self._credenciales[servicio][usuario]

        self._autenticar(clave_maestra) # Mediación Completa
        if not self._credenciales[servicio]:
            del self._credenciales[servicio]

        return True

    # =====================================================
    # cambiar usuario
    # =====================================================
    def cambiar_usuario(
        self,
        servicio: str,
        usuario_antiguo: str,
        usuario_nuevo: str,
        clave_maestra: str,
    ) -> bool:

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
            "DROP",
            "DELETE",
            "UPDATE",
            "ALTER",
            "CREATE",
            "TABLE",
            "ALERT",
            "SCRIPT",
            "EXECUTE",
            "IMMEDIATE",
        ]

        if len(usuario_nuevo) > 255:
            raise ValueError()

        if any(c in simbolos_invalidos for c in usuario_nuevo):
            raise ValueError()

        if any(p in usuario_nuevo.upper() for p in palabras_peligrosas):
            raise ValueError()

        if usuario_nuevo.replace(".", "", 1).replace("-", "", 1).isdigit():
            raise ValueError()

        self._autenticar(clave_maestra) # Mediación Completa
        if servicio not in self._credenciales:
            raise ErrorServicioNoEncontrado()

        self._autenticar(clave_maestra) # Mediación Completa
        if usuario_antiguo not in self._credenciales[servicio]:
            raise ErrorServicioNoEncontrado()

        self._autenticar(clave_maestra) # Mediación Completa
        if usuario_nuevo in self._credenciales[servicio]:
            raise ErrorCredencialExistente()

        self._autenticar(clave_maestra) # Mediación Completa
        password_hashed = self._credenciales[servicio].pop(usuario_antiguo)

        self._autenticar(clave_maestra) # Mediación Completa
        self._credenciales[servicio][usuario_nuevo] = password_hashed

        return True

    # =====================================================
    # OTPs
    # =====================================================

    def generar_otps(self, cantidad: int) -> list:

        if not isinstance(cantidad, int):
            raise TypeError

        if cantidad <= 0: 
            raise ValueError


        caracteres = string.ascii_letters + string.digits

    # SET = no permite duplicados
        otps = set()

        while len(otps) < cantidad:

            otp = ''.join(random.choice(caracteres) for _ in range(6))

            otps.add(otp)

        return list(otps)

    def almacenar_otps(self, clave_maestra: str, servicio: str, usuario: str, otps: list) -> None:
        """
        Almacena las OTPs del usuario.
        Reemplaza las anteriores si existían.
        """

    # Validación básica
        if not isinstance(otps, list):
            raise TypeError

    # Guardar OTPs
        # Guardar COPIA independiente
        self._credenciales[servicio][usuario]["otps"] = otps.copy()


    def verificar_otp(self, clave_maestra, servicio, usuario, otp):

        print("ENTRANDO EN verificar_otp")

        if not isinstance(otp, str):
            return False

        if len(otp) != 6:
            return False

        if otp in self._credenciales[servicio][usuario]["otps"]:

            print("ELIMINANDO OTP")

            self._credenciales[servicio][usuario]["otps"].remove(otp)

            return True

        return False

        return True
