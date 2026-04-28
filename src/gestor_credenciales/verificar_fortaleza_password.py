class ErrorPoliticaPassword(Exception):
    pass


PASSWORDS_COMUNES = {
    "password", "123456", "12345678", "qwerty", "abc123",
    "111111", "123123", "admin", "user", "contraseña",
    "0000000", "seguro", "hola", "abcdefg",
}

SIMBOLOS = set(r"!@#$%^&*()-_=+[]{}|;:',.<>?/`~")

TRIVIALES = ["12345", "qwerty"]


def verificar_fortaleza_password(password: str) -> str:
    # ---------- Validación de entrada ----------
    if not isinstance(password, str) or password == "":
        raise ErrorPoliticaPassword()

    # ---------- Criterio 1: longitud ----------
    cumple_longitud = len(password) >= 7

    # ---------- Criterio 2: mezcla ----------
    tiene_mayus = any(c.isupper() for c in password)
    tiene_minus = any(c.islower() for c in password)
    tiene_num = any(c.isdigit() for c in password)

    # penalizar mayúscula solo al inicio
    resto_sin_mayus = all(not c.isupper() for c in password[1:])
    mayus_solo_inicio = tiene_mayus and password[0].isupper() and resto_sin_mayus

    # cadenas triviales
    lower_pwd = password.lower()
    contiene_trivial = any(x in lower_pwd for x in TRIVIALES)

    cumple_mezcla = (
        tiene_mayus and tiene_minus and tiene_num
        and not mayus_solo_inicio
        and not contiene_trivial
    )

    # ---------- Criterio 3: símbolos ----------
    posiciones_simbolos = [i for i, c in enumerate(password) if c in SIMBOLOS]

    cumple_simbolos = (
        len(posiciones_simbolos) > 0 and
        not all(i == len(password) - 1 for i in posiciones_simbolos)
    )

    # ---------- Criterio 4: no común ----------
    no_comun = password.lower() not in PASSWORDS_COMUNES

    # ---------- Score ----------
    criterios = sum([
        cumple_longitud,
        cumple_mezcla,
        cumple_simbolos,
        no_comun
    ])

    # ---------- Clasificación ----------
    if criterios <= 1:
        return "débil"
    elif criterios <= 3:
        return "media"
    else:
        return "fuerte"