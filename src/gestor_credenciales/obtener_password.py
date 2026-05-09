@require(lambda clave_maestra: isinstance(clave_maestra, str) and len(clave_maestra.strip()) > 0)
@require(lambda servicio: isinstance(servicio, str) and len(servicio.strip()) > 0)
@require(lambda usuario: isinstance(usuario, str) and len(usuario.strip()) > 0)
@require(lambda self, servicio: servicio in self._credenciales)
@require(lambda self, servicio, usuario: usuario in self._credenciales.get(servicio, {}))
@ensure(lambda result: isinstance(result, str))
def obtener_password(self, clave_maestra: str, servicio: str, usuario: str) -> str:

    clave_maestra = clave_maestra.strip()
    servicio = servicio.strip()
    usuario = usuario.strip()

    if not self._verificar_clave(clave_maestra, self._clave_maestra_hashed):
        raise ErrorAutenticacion

    password = self._credenciales[servicio][usuario]

    if isinstance(password, bytes):
        return password.decode("utf-8")

    return password
    
def _hash_clave_obtener_password(self, clave: str):
    return bcrypt.hashpw(clave.encode("utf-8"), bcrypt.gensalt())
