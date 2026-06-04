import hashlib


def hash_cadena(cadena, algoritmo="sha256"):
    cadena_bytes = cadena.encode("utf-8")
    hash_obj = hashlib.new(algoritmo)
    hash_obj.update(cadena_bytes)
    return hash_obj.hexdigest()


def hash_archivo(ruta_archivo, algoritmo="sha256", tamano_bloque=65536):
    hash_obj = hashlib.new(algoritmo)
    with open(ruta_archivo, "rb") as archivo:
        while bloque := archivo.read(tamano_bloque):
            hash_obj.update(bloque)
    return hash_obj.hexdigest()
