import bcrypt
from icontract import require, ensure


class ErrorAutenticacion(Exception):
    pass


class GestorCredenciales:
    def __init__(self, clave_maestra: str):
        self._clave_maestra_hashed = self._hash_clave(clave_maestra)
        self._credenciales = {}

    def anadir_credencial(self, clave_maestra: str, servicio: str, usuario: str, password: str) -> bool:
        simbolos = "!>;'\\/$#[]{}:\n\r"
        palabras_peligrosas = [
            "DROP", "DELETE", "UPDATE", "ALTER", "CREATE",
            "TABLE", "ALERT", "SCRIPT", "EXECUTE", "IMMEDIATE"
        ]

        if not isinstance(usuario, str):
            raise TypeError
        if usuario.replace('.', '', 1).replace('-', '', 1).isdigit():
            raise ValueError

        usuario = usuario.strip()
        password = password.strip()
        servicio = servicio.strip()
        clave_maestra = clave_maestra.strip()

        if not self._verificar_clave(clave_maestra, self._clave_maestra_hashed):
            raise PermissionError

        if not servicio or not usuario or (len(usuario) > 255):
            raise ValueError

        if (
            any(c in simbolos for c in usuario)
            or any(c in simbolos for c in servicio)
            or any(p.upper() in palabras_peligrosas for p in servicio.split())
        ):
            raise ValueError

        if servicio not in self._credenciales:
            self._credenciales[servicio] = {}

        if usuario in self._credenciales[servicio]:
            p = self._credenciales[servicio][usuario]
            if bcrypt.checkpw(password.encode("utf-8"), p):
                raise ValueError

        self._credenciales[servicio][usuario] = bcrypt.hashpw(
            password.encode("utf-8"),
            bcrypt.gensalt()
        )

        return True

    @require(lambda clave_maestra: isinstance(clave_maestra, str) and len(clave_maestra.strip()) > 0)
    @require(lambda servicio: isinstance(servicio, str) and len(servicio.strip()) > 0)
    @require(lambda usuario: isinstance(usuario, str) and len(usuario.strip()) > 0)
    @require(lambda self, servicio: servicio.strip() in self._credenciales)
    @require(lambda self, servicio, usuario: usuario.strip() in self._credenciales[servicio.strip()])
    @ensure(lambda result: result is not None)
    def obtener_password(self, clave_maestra: str, servicio: str, usuario: str):
        clave_maestra = clave_maestra.strip()
        servicio = servicio.strip()
        usuario = usuario.strip()

        if not self._verificar_clave(clave_maestra, self._clave_maestra_hashed):
            raise ErrorAutenticacion

        password = self._credenciales[servicio][usuario]

        if password is None:
            raise ValueError

        return password

    def _hash_clave(self, clave: str):
        return bcrypt.hashpw(clave.encode("utf-8"), bcrypt.gensalt())

    def _verificar_clave(self, clave: str, clave_hashed) -> bool:
        return bcrypt.checkpw(clave.encode("utf-8"), clave_hashed)
