import unittest
import hashlib
import bcrypt
import smtplib
from icontract import require, ensure

class ErrorPoliticaPassword(Exception):
    pass

class ErrorAutenticacion(Exception):
    pass

class ErrorServicioNoEncontrado(Exception):
    pass

class ErrorCredencialExistente(Exception):
    pass

class ErrorCorreoNoEstablecido(Exception):
    pass

class ErrorCodigoNoEstablecido(Exception):
    pass

class ErrorSinIntentosRestantes(Exception):
    pass

class ErrorUsuarioYaVerificado(Exception):
    pass

class GestorCredenciales:
    def __init__(self, clave_maestra: str):
        """Inicializa el gestor con una clave maestra."""
        self._clave_maestra_hashed = self._hash_clave(clave_maestra)
        self._credenciales = {}

    @require(lambda servicio, usuario: servicio and usuario)
    @require(lambda servicio: all(c not in ";&|" for c in servicio))
    @require(lambda password: len(password) >= 12)
    @require(lambda password: any(c.isupper() for c in password))
    @require(lambda password: any(c.islower() for c in password))
    @require(lambda password: any(c.isdigit() for c in password))
    @require(lambda password: any(c in "!@#$%^&*" for c in password))
    @ensure(lambda servicio, usuario, result: result is None)
    def añadir_credencial(self, clave_maestra: str, servicio: str, usuario: str, password: str) -> None:
        if servicio not in self._credenciales:
            self._credenciales[servicio] = {}

        self._credenciales[servicio][usuario] = password

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
        """Lista todos los servicios almacenados."""
        pass

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

    def obtener_correo(self, clave_maestra: str, servicio:str, usuario: str) -> str | None:
        try:
            correo = self._credenciales[servicio][usuario]["correo"]
        except KeyError:
            correo = None

        return correo

    def obtener_codigo2fa(self, clave_maestra: str, servicio:str, usuario: str) -> str | None:
        try:
            codigo_auth = self._credenciales[servicio][usuario]["codigo_auth"]
        except KeyError:
            codigo_auth = None

        return codigo_auth

    def obtener_intentos_restantes(self, clave_maestra: str, servicio:str, usuario: str) -> int | None:
        try:
            intentos = self._credenciales[servicio][usuario]["intentos_restantes"]
        except KeyError:
            intentos = None

        return intentos

    def comprobacion_verificacion_usuario(self, clave_maestra: str, servicio:str, usuario: str) -> bool:
        try:
            verificado = self._credenciales[servicio][usuario]["verificado"]
        except KeyError:
            verificado = False

        return verificado

    def establecer_correo(self, clave_maestra: str, servicio: str, usuario: str, correo: str) -> None:
        """Establece el correo verificando que este es correcto"""""
        pass

    def crear_codigo2fa(self, clave_maestra: str, servicio: str, usuario: str) -> None:
        """Crea el codigo de auntenticación aleatoriamente y establece los intentos_restantes en 3"""
        """El código tiene que tener una longitud mínima de 6"""
        pass

    def enviar_correo2fa(self, clave_maestra: str, servicio: str, usuario: str) -> None:
        """Envia un correo usando tls con el contenido"""
        """Debe llamar a los errores ErrorCorreoNoEstablecido o ErrorCodigoNoEstablecido si falta el correo o el codigo respectivamente"""
        pass

    def verificar_usuario(self, clave_maestra: str, servicio: str, usuario: str, codigo: str) -> None:
        """Intento de verificación con el código pasado por el usuario"""
        """Al llamar a la función:"""
        """Si el codigo introducido no coincide con el del usuario se le resta un intento"""
        """Si el codigo introducido coincide entonces (_credenciales[servicio][usuario]["verificado"] = True) y se cambia el codigo de autenticación y los intentos por 'None'"""
        """Si el usuario ya está verificado entonces salta la excepcion 'ErrorUsuarioYaVerificado'"""
        """Si los intentos están a 0 entonces salta la excepcion 'ErrorSinIntentosRestantes'"""
        """Si el codigo de autenticación es 'None' salta la excepción 'ErrorCodigoNoEstablecido'"""
        pass

#gestor = GestorCredenciales("claveMaestraSegura123!")
#print(gestor._verificar_clave("clave", gestor._hash_clave("clave")))