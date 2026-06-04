from datetime import datetime, UTC
import logging
import os

from src.logger.hash_util import hash_cadena

LOG_FILE = "ciphercoin_audit.log"

# Definir el formateador personalizado
formatter = logging.Formatter(
    fmt="%(asctime)s: %(levelname)-8s | %(message)s |", datefmt="%Y-%m-%d %H:%M:%S"
)


def existe_archivo(archivo):
    return os.path.exists(archivo)


def archivo_vacio(archivo):
    return os.path.getsize(archivo) == 0


def get_tiempo_legible():
    """
    Devuelve el tiempo actual en un formato legible
    """
    # obtener la hora actual en UTC
    tiempo_utc = datetime.now(UTC)

    # formatear la hora en UTC con la zona horaria
    tiempo_legible = tiempo_utc.strftime("%Y-%m-%d %H:%M:%S %Z")
    return tiempo_legible


# función para configurar el logging en un fichero
def configure_logging(log_file=LOG_FILE):
    """Configura el logger y lee el dato de la última línea del archivo de log."""
    # crear o obtener el logger raíz
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # cerrar y eliminar handlers existentes para evitar duplicados
    for handler in logger.handlers[:]:
        handler.close()
        logger.removeHandler(handler)

    # crear handler para archivo
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)

    return logger


def inicializar_log(log_file=LOG_FILE):
    """Inicializa el archivo de log con una línea de encabezado si está vacío."""
    if not existe_archivo(log_file) or archivo_vacio(log_file):
        configure_logging(log_file)
        hash_inicial = hash_cadena("INICIO_LOG")
        entrada = f"'{hash_inicial}': INICIO_LOG - Log inicializado"
        logging.info(entrada)


def anadir_al_log(nivel_log, log_string, log_file=LOG_FILE):
    log_levels = {
        "debug": logging.debug,
        "info": logging.info,
        "warning": logging.warning,
        "error": logging.error,
        "critical": logging.critical,
    }

    # asegurar que el logging está configurado
    if not logging.getLogger().handlers:
        configure_logging(log_file)

    # calcular el hash encadenado
    ultimo_hash = leer_ultima_linea_log(log_file) or ""
    nuevo_hash = hash_cadena(log_string + ultimo_hash)
    entrada = f"'{nuevo_hash}': {log_string}"

    # llamar a la función de log correspondiente
    log_fn = log_levels.get(nivel_log.lower(), logging.info)
    log_fn(entrada)


def leer_ultima_linea_log(log_file):
    if not existe_archivo(log_file) or archivo_vacio(log_file):
        return None

    ultima_linea = None
    with open(log_file, encoding="utf-8") as f:
        for linea in f:
            if linea.strip():
                ultima_linea = linea.strip()

    if ultima_linea is None:
        return None

    # el formato es: "timestamp: LEVEL | 'hash': mensaje |"
    try:
        # buscar después del primer | y luego la primera comilla
        pipe_pos = ultima_linea.find("|")
        if pipe_pos == -1:
            return None
        after_pipe = ultima_linea[pipe_pos + 1 :]
        start = after_pipe.find("'")
        if start == -1:
            return None
        end = after_pipe.find("'", start + 1)
        if end == -1:
            return None
        return after_pipe[start + 1 : end]
    except (ValueError, IndexError):
        return None


def verificar_cadena_hashes(log_file=LOG_FILE):
    if not existe_archivo(log_file) or archivo_vacio(log_file):
        return False

    with open(log_file, encoding="utf-8") as f:
        lineas = [line.strip() for line in f if line.strip()]

    if not lineas:
        return False

    hash_anterior = ""
    for linea in lineas:
        try:
            # extraer el hash
            pipe_pos = linea.find("|")
            if pipe_pos == -1:
                return False
            after_pipe = linea[pipe_pos + 1 :]
            start = after_pipe.find("'")
            if start == -1:
                return False
            end = after_pipe.find("'", start + 1)
            if end == -1:
                return False
            hash_guardado = after_pipe[start + 1 : end]

            # extraer el mensaje
            mensaje = after_pipe[end + 3 :].rstrip(" |")
        except (ValueError, IndexError):
            return False

        # recomputar y comparar
        if hash_cadena(mensaje + hash_anterior) != hash_guardado:
            return False

        hash_anterior = hash_guardado

    return True
