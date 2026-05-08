import unittest
import hashlib
import bcrypt
from icontract import require, ensure

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

    # --- añadir credencial ----------------------------------------------------------------
    def añadir_credencial(self, clave_maestra: str, servicio: str, usuario: str, password: str) -> None:
        """Añade una nueva credencial al gestor."""
        pass
    # ----------------------------------------------------------------------------------------
    
    # --- obtener password ----------------------------------------------------------------
    def obtener_password(self, clave_maestra: str, servicio: str, usuario: str) -> str:
        """Recupera una contraseña almacenada."""
        pass
    # ----------------------------------------------------------------------------------------
    
    # --- eliminar credencial ----------------------------------------------------------------
    def eliminar_credencial(self, clave_maestra: str, servicio: str, usuario: str) -> None:
    """Elimina una credencial existente."""

    # Validación de tipos
    if (
        not isinstance(clave_maestra, str) or
        not isinstance(servicio, str) or
        not isinstance(usuario, str)
    ):
        raise TypeError

    # Validación de valores vacíos
    if (
        clave_maestra.strip() == "" or
        servicio.strip() == "" or
        usuario.strip() == ""
    ):
        raise ValueError

    # Verificar clave maestra
    if not self._verificar_clave(clave_maestra, self._clave_maestra_hashed):
        raise ErrorAutenticacion

    # Verificar que exista el servicio
    if servicio not in self._credenciales:
        raise ErrorServicioNoEncontrado

    # Verificar que exista el usuario
    if usuario not in self._credenciales[servicio]:
        raise ErrorServicioNoEncontrado

    # Eliminar credencial
    del self._credenciales[servicio][usuario]

    # Eliminar servicio vacío
    if len(self._credenciales[servicio]) == 0:
        del self._credenciales[servicio]

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
        """Lista todos los servicios almacenados."""
        pass
    # ----------------------------------------------------------------------------------------
    
    # --- hash clave -------------------------------------------------------------------------
    def _hash_clave(self, clave: str) -> str:
        """Hashea una clave usando bcrypt."""
        return bcrypt.hashpw(clave.encode('utf-8'), bcrypt.gensalt())
    # ----------------------------------------------------------------------------------------
    
    # --- verificar clave -------------------------------------------------------------------
    def _verificar_clave(self, clave: str, clave_hashed: str) -> bool:
        """Verifica si una clave coincide con su hash."""
        return bcrypt.checkpw(clave.encode('utf-8'), clave_hashed.encode('utf-8'))
    # ----------------------------------------------------------------------------------------
    
    # --- listar usuarios --------------------------------------------------------------------
    def listar_usuarios():
        pass
    # ----------------------------------------------------------------------------------------

    # --- cambiar usuario --------------------------------------------------------------------
    def cambiar_usuario():
        pass
    # ----------------------------------------------------------------------------------------

    # --- verificar fortaleza password -------------------------------------------------------
    def verificar_fortaleza_password():
        pass
    # ----------------------------------------------------------------------------------------

    # --- doble factor --------------------------------------------------------------------
    def doble_factor():
        pass
    # ----------------------------------------------------------------------------------------

#gestor = GestorCredenciales("claveMaestraSegura123!")
#print(gestor._verificar_clave("clave", gestor._hash_clave("clave")))
