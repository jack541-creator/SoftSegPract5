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