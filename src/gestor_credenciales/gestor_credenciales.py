import unittest
import hashlib
import bcrypt

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
        pass
    # ----------------------------------------------------------------------------------------
    
    # --- listar servicios -------------------------------------------------------------------
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
