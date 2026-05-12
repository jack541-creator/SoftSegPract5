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

    # MEDIACION COMPLETA
    def cambiar_usuario(self, servicio, usuario_antiguo, usuario_nuevo, clave_maestra):	
        if not isinstance(servicio, str) or not isinstance(usuario_antiguo, str) or not isinstance(usuario_nuevo, str) or not isinstance(clave_maestra, str):
            raise TypeError

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
        
        if not self._verificar_clave(clave_maestra, self._clave_maestra_hashed): # Mediación completa -> Verificación de permiso ante acceso a cambiar el usuario
            raise PermissionError
        

        contraseña_hashed = self._credenciales[servicio].pop(usuario_antiguo)
        self._credenciales[servicio][usuario_nuevo] = contraseña_hashed

        return True

        
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
        if isinstance(clave_hashed, str):
            clave_hashed = clave_hashed.encode("utf-8")
        return bcrypt.checkpw(clave.encode('utf-8'), clave_hashed)
    # ----------------------------------------------------------------------------------------
    
    # --- listar usuarios --------------------------------------------------------------------
    def listar_usuarios():
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
