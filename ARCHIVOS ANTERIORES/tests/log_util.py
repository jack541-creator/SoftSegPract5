from datetime import datetime, timezone
import logging
import os

from src.python.hash_util import hash_cadena

LOG_FILE = "RegistroSeguro.log"

# Definir el formateador personalizado
formatter = logging.Formatter(
    fmt="%(asctime)s: %(levelname)-8s | %(message)s |",
    datefmt="%Y-%m-%d %H:%M:%S"
)

def existe_archivo(archivo):
    return os.path.exists(archivo)

def archivo_vacio(archivo):
    return  os.path.getsize(archivo) == 0

def get_tiempo_legible():
    """
    Devuelve el tiempo actual en un formato legible
    """
    # obtener la hora actual en UTC
    tiempo_utc = datetime.now(timezone.utc)

    # formatear la hora en UTC con la zona horaria
    tiempo_legible = tiempo_utc.strftime("%Y-%m-%d %H:%M:%S %Z")
    return tiempo_legible

# función para configurar el logging en un fichero
def configure_logging(log_file=LOG_FILE):
    """
    Configura el logger y lee el dato de la última línea del archivo de log.

    Parámetros:
        log_file (str): Ruta del archivo de log.
    """
    pass

def inicializar_log():
    pass

def anadir_al_log(nivel_log, log_string):
    log_levels = {
        "warning": logging.warning,
        "error":   logging.error,
        "debug":   logging.debug,
        "info":    logging.info
    }

    # calcular el hash encadenado: hash(mensaje_actual + hash_anterior)
    ultimo_hash = leer_ultima_linea_log(LOG_FILE) or ""
    nuevo_hash = hash_cadena(log_string + ultimo_hash)
    entrada = f"'{nuevo_hash}': {log_string}"

    # llamar a la función de log correspondiente al nivel indicado
    log_fn = log_levels.get(nivel_log.lower(), logging.info)
    log_fn(entrada)


def leer_ultima_linea_log(log_file):
    if not existe_archivo(log_file) or archivo_vacio(log_file):
        return None

    ultima_linea = None
    with open(log_file, 'r', encoding='utf-8') as f:
        for linea in f:
            if linea.strip():
                ultima_linea = linea.strip()

    if ultima_linea is None:
        return None

    # extraer el hash: está entre las primeras comillas simples
    # formato: "timestamp: LEVEL | 'hash': mensaje |"
    try:
        start = ultima_linea.index("'") + 1
        end   = ultima_linea.index("'", start)
        return ultima_linea[start:end]
    except ValueError:
        return None


def verificar_cadena_hashes(log_file=LOG_FILE):
    if not existe_archivo(log_file) or archivo_vacio(log_file):
        return False

    with open(log_file, 'r', encoding='utf-8') as f:
        lineas = [l.strip() for l in f if l.strip()]

    if not lineas:
        return False

    hash_anterior = ""
    for linea in lineas:
        # extraer el hash guardado
        try:
            start = linea.index("'") + 1
            end   = linea.index("'", start)
            hash_guardado = linea[start:end]
        except ValueError:
            return False

        # extraer el mensaje (todo lo que va después de "'hash': ")
        mensaje = linea[end + 3:].rstrip(" |")

        # recomputar y comparar
        if hash_cadena(mensaje + hash_anterior) != hash_guardado:
            return False

        hash_anterior = hash_guardado

    return True

