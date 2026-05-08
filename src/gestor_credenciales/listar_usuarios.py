def listar_usuarios(self, clave):
    if clave != self.clave_maestra:
        raise ErrorAutenticacion("Clave maestra incorrecta")

    usuarios = []

    for servicio in self.credenciales.values():
        for usuario in servicio.keys():
            if usuario not in usuarios:
                usuarios.append(usuario)

    return usuarios
