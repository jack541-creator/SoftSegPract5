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

    @require(lambda clave_maestra: isinstance(clave_maestra, str))
    @require(lambda servicio: isinstance(servicio, str))
    @require(lambda usuario: isinstance(usuario, str))
    @require(lambda nuevoServicio: isinstance(nuevoServicio, str))
    @require(lambda nuevoUsuario: isinstance(nuevoUsuario, str))
    @require(lambda nuevaContraseña: isinstance(nuevaContraseña, str))
    @ensure(lambda result: isinstance(result, str))
    def cambiar_credenciales(self, clave_maestra: str, servicio: str, usuario: str, nuevoServicio: str, nuevoUsuario: str, nuevaContraseña: str) -> str:
        out = "Error"
        
        if not clave_maestra:
            out = "Error: clave maestra vacía"
        elif not self._verificar_clave(clave_maestra, self._clave_maestra_hashed):
            out = "Error: clave maestra incorrecta"
        elif not servicio:
            out = "Error: servicio vacio"
        elif servicio not in self.listar_servicios(clave_maestra):
            out = "Error: el servicio no existe"
        elif not usuario:
            out = "Error: usuario vacio"
        elif usuario not in self.listar_usuarios(clave_maestra):
            out = "Error: el usuario no existe"
        elif not nuevoServicio:
            out = "Error: nuevo servicio vacio"
        elif not nuevoUsuario:
            out = "Error: nuevo usuario vacio"
        elif not nuevaContraseña:
            out = "Error: nueva contraseña vacia"
        elif len(nuevaContraseña) < 7:
            out = "Error contraseña demasiado corta"
        else:
            self.eliminar_credencial(clave_maestra, servicio, usuario)
            self.añadir_credencial(clave_maestra, nuevoServicio, nuevoUsuario, nuevaContraseña)

            out = "Credenciales actualizadas correctamente"
        return out

        

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