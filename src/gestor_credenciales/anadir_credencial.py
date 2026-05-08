def anadir_credencial(self, clave_maestra: str, servicio: str, usuario: str, password: str) -> bool:
        simbolos = "!>;'\/$#[]{}:\n\r"
        palabras_peligrosas = ["DROP", "DELETE", "UPDATE", "ALTER", "CREATE", "TABLE", "ALERT", "SCRIPT", "EXECUTE", "IMMEDIATE"]
        
        if not isinstance(usuario, str):
            raise TypeError
        if usuario.replace('.', '', 1).replace('-', '', 1).isdigit():
            raise ValueError
        
        usuario = usuario.strip()
        password = password.strip()
        servicio = servicio.strip()
        clave_maestra = clave_maestra.strip()
    
        if not self._verificar_clave(clave_maestra, self._clave_maestra_hashed):
            raise PermissionError                                                   # ErrorAutenticacion
    
        if not servicio or not usuario or (len(usuario) > 255):
            raise ValueError
    
        if any(c in simbolos for c in usuario) or any(c in simbolos for c in servicio) or any(p.upper() in palabras_peligrosas for p in servicio.split()):
            raise ValueError
    
        # voy a asumir que verificar_fortaleza_password() es llamado antes de esta función
        if servicio not in self._credenciales:
            self._credenciales[servicio] = {}
        
        if usuario in self._credenciales[servicio]:
            p = self._credenciales[servicio][usuario]
            if bcrypt.checkpw(password.encode('utf-8'), p)::
                raise ValueError       # ErrorCredencialExistente
        
        self._credenciales[servicio][usuario] = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())  
        return True 
