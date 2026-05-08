import unittest
import hashlib
import bcrypt
from icontract import require, ensure
from .verificar_fortaleza_password import verificar_fortaleza_password

class ErrorPoliticaPassword(Exception):
    pass

class ErrorAutenticacion(Exception):
    pass

class ErrorServicioNoEncontrado(Exception):
    pass

class ErrorCredencialExistente(Exception):
    pass


class GestorCredenciales:
    def __init__(self, clave_maestra: str):
        """Inicializa el gestor con una clave maestra."""
        self._clave_maestra_hashed = self._hash_clave(clave_maestra)
        self._credenciales = {}

    @require(lambda servicio, usuario: servicio and usuario)
    @require(lambda servicio: all(c not in ";&|" for c in servicio))
    @require(lambda password: isinstance(password, str) and len(password) > 0)
    @ensure(lambda servicio, usuario, result: result is None)
    def añadir_credencial(self, clave_maestra: str, servicio: str, usuario: str, password: str) -> None:

        if verificar_fortaleza_password(password) == "débil":
            raise ErrorPoliticaPassword()

        if servicio not in self._credenciales:
            self._credenciales[servicio] = {}

        self._credenciales[servicio][usuario] = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

    @require(lambda clave_maestra: isinstance(clave_maestra, str) and len(clave_maestra.strip()) > 0)
    @require(lambda servicio: isinstance(servicio, str) and len(servicio.strip()) > 0)
    @require(lambda usuario: isinstance(usuario, str) and len(usuario.strip()) > 0)
    @require(lambda servicio: all(c not in ";&|@" for c in servicio))
    @require(lambda usuario: all(c not in ";&|@" for c in usuario))
    @ensure(lambda result: isinstance(result, str))
    def obtener_password(self, clave_maestra: str, servicio: str, usuario: str) -> str:
        if not self._verificar_clave(clave_maestra, self._clave_maestra_hashed):
            raise ErrorAutenticacion

        if servicio not in self._credenciales:
            raise ValueError

        if usuario not in self._credenciales[servicio]:
            raise ValueError

        password = self._credenciales[servicio][usuario]

        if password is None:
            raise ValueError

        return password
    
    @require(lambda servicio: servicio)
    @ensure(lambda servicio, result: result is None)
    def eliminar_credencial(self, clave_maestra: str, servicio: str, usuario: str) -> None:
        """Elimina una credencial existente."""
        pass

    def cambiar_usuario(servicio, usuario_antiguo, usuario_nuevo, clave_maestra):	
        if not servicio or not isinstance(servicio, str) or not usuario_antiguo or not isinstance(usuario_antiguo, str) or not usuario_nuevo or not isinstance(usuario_nuevo, str) or not clave_maestra or not isinstance(clave_maestra, str):
            raise TypeError
        
        if not verificar_clave(clave_maestra, self._clave_maestra_hashed):
            raise PermissionError

        if len(servicio) < 1 or len(usuario_antiguo) < 1 or len(usuario_nuevo) < 1:
            raise ValueError
        
        if servicio not in self._credenciales or usuario_antiguo not in self._credenciales[servicio]:
            raise ValueError
        
        if len(usuario_nuevo) > 255:
            raise ValueError
        
        if usuario_nuevo in self._credenciales[servicio]:
            raise ValueError
        
        if usuario_nuevo.strip() == "":
            raise ValueError
        
        substrings = ['<', '>']
        if any(sub in usuario_nuevo for sub in substrings):
            raise ValueError
        

        contraseña_hashed = self._credenciales[servicio].pop(usuario_antiguo)
        self._credenciales[servicio][usuario_nuevo] = contraseña_hashed

        return True

        

    @ensure(lambda result: isinstance(result, list))
    def listar_servicios(self, clave_maestra: str) -> list:
        return list(self._credenciales.keys())

    @ensure(lambda result: isinstance(result, list))
    def listar_usuarios(self, clave_maestra:str) -> list:
        """Lista todos los usuarios en la base de datos."""
        pass

    def _hash_clave(self, clave: str) -> str:
        """Hashea una clave usando bcrypt."""
        return bcrypt.hashpw(clave.encode('utf-8'), bcrypt.gensalt())

    def _verificar_clave(self, clave: str, clave_hashed: str) -> bool:
        """Verifica si una clave coincide con su hash."""
        return bcrypt.checkpw(clave.encode('utf-8'), clave_hashed)

    def generar_otps(self, n: int) -> list:
        """Crea una lista de n OTPs"""
        """Las OTPs tienen que tener una longitud mínima de 6 y estar generadas aleatoriamente"""
        pass

    def almacenar_otps(self, clave_maestra: str, servicio: str, usuario: str, opts: list) -> None:
        """Almacena la lista de OTPs pasadas por parametro, elimina la OTP antigua en caso de que existiera"""
        pass

    def verificar_otp(self, clave_maestra: str, servicio: str, usuario: str, otp: str) -> bool:
        """Devuelve true si la OTP pasada está en la lista de OTPs del usuario y elimina la OTP de dicha lista"""
        """Devuelve false si la OTP pasada no está en la lista"""
        pass

#gestor = GestorCredenciales("claveMaestraSegura123!")
#print(gestor._verificar_clave("clave", gestor._hash_clave("clave")))