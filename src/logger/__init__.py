"""
Módulo de logging seguro con control de acceso.
"""

from src.logger.log_util import (
    configure_logging,
    inicializar_log,
    anadir_al_log,
    leer_ultima_linea_log,
    verificar_cadena_hashes,
    hash_cadena,
    #SecureLogManager,
    #MonitorFunciones,
    LOG_FILE,                )

from src.logger.access_control import (
    access_control,
    access_control_simple,
    ContextoSeguridad,
    RolUsuario,
    Permiso,               )

__all__ = [
    # hash logging
    'configure_logging',
    'inicializar_log',
    'anadir_al_log',
    'leer_ultima_linea_log',
    'verificar_cadena_hashes',
    'hash_cadena',
    'SecureLogManager',
    'MonitorFunciones',
    'LOG_FILE',
    # access control
    'access_control',
    'access_control_simple',
    'ContextoSeguridad',
    'RolUsuario',
    'Permiso',                ]