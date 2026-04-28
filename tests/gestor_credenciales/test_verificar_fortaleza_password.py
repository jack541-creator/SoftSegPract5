import unittest
from src.gestor_credenciales.verificar_fortaleza_password import verificar_fortaleza_password, ErrorPoliticaPassword

# contraseñas típicas
PASSWORDS_COMUNES = {
    "password", "123456", "12345678", "qwerty", "abc123",
    "111111", "123123", "admin", "user", "contraseña",
    "0000000", "seguro", "hola", "abcdefg", }

SIMBOLOS = set(r"!@#$%^&*()-_=+[]{}|;:',.<>?/`~")

class TestVerificarFortalezaPassword(unittest.TestCase):
    """
    tenemos en cuenta algunos criterios:

      LONGITUD: >= 7 caracteres  (estándar PCI mínimo)
      MEZCLA: mayúsculas (no solo al inicio),minúsculas, números, y sin ser típicas
      SÍMBOLOS: al menos uno y NO solo al final

    lanza ErrorPoliticaPassword si la entrada no es str o está vacía.
    """

    # entradas inválidas

    def test_entrada_entera_lanza_excepcion(self):
        """Un entero no es una contraseña válida."""
        with self.assertRaises(ErrorPoliticaPassword):
            verificar_fortaleza_password(12345)

    def test_entrada_none_lanza_excepcion(self):
        """None debe lanzar PasswordError."""
        with self.assertRaises(ErrorPoliticaPassword):
            verificar_fortaleza_password(None)

    def test_entrada_lista_lanza_excepcion(self):
        """Una lista no es una contraseña válida."""
        with self.assertRaises(ErrorPoliticaPassword):
            verificar_fortaleza_password(["abc", "123"])

    def test_password_vacia_lanza_excepcion(self):
        """Cadena vacía debe lanzar PasswordError."""
        with self.assertRaises(ErrorPoliticaPassword):
            verificar_fortaleza_password("")

    # longitud

    def test_menos_de_7_caracteres_penaliza(self):
        """Menos de 7 caracteres no cumple el criterio de longitud mínima PCI."""
        resultado = verificar_fortaleza_password("abc123")
        self.assertEqual(resultado, "débil")

    def test_exactamente_7_caracteres_cumple_longitud(self):
        """7 caracteres es el mínimo aceptable según el estándar PCI."""
        resultado = verificar_fortaleza_password("abcdef7")
        self.assertIn(resultado, ("media", "fuerte"))

    def test_contraseña_con_todos_criterios_es_fuerte(self):
        """Una contraseña muy larga con todos los criterios es fuerte."""
        resultado = verificar_fortaleza_password("miClave!Super73Segura")
        self.assertEqual(resultado, "fuerte")

    # mezcla de caracteres

    def test_mayuscula_solo_al_inicio_no_segura(self):
        """Mayúscula únicamente al inicio no es seguro."""
        resultado = verificar_fortaleza_password("Password")
        self.assertIn(resultado, ("débil", "media"))

    def test_mayuscula_interior_mejora_fortaleza(self):
        """Mayúscula dentro del cuerpo sí cuenta como mezcla."""
        resultado = verificar_fortaleza_password("paSSword7")
        self.assertIn(resultado, ("media", "fuerte"))

    def test_cadena_numerica_tipica_penaliza(self):
        """Secuencia trivial '12345' dentro de la contraseña penaliza."""
        resultado = verificar_fortaleza_password("Mi12345pass")
        self.assertIn(resultado, ("débil", "media"))

    def test_cadena_qwerty_penaliza(self):
        """Secuencia de teclado típica 'qwerty' penaliza."""
        resultado = verificar_fortaleza_password("MiQwerty!")
        self.assertIn(resultado, ("débil", "media"))

    def test_mezcla_real_sin_trivialidades_suma(self):
        """Mezcla de may/min/números sin cadenas triviales suma al criterio 2."""
        resultado = verificar_fortaleza_password("maCbook97")
        self.assertIn(resultado, ("media", "fuerte"))

    # símbolos

    def test_simbolo_solo_al_final_no_mejora_fortaleza(self):
        """Símbolo únicamente al final no suma."""
        resultado = verificar_fortaleza_password("abcdefg!")
        self.assertIn(resultado, ("débil", "media"))

    def test_simbolo_en_interior_mejora_fortaleza(self):
        """Símbolo dentro del cuerpo (no solo al final) sí suma."""
        resultado = verificar_fortaleza_password("ab!cdefg")
        self.assertIn(resultado, ("media", "fuerte"))

    def test_varios_simbolos_distribuidos_suman(self):
        """Varios símbolos distribuidos es fuerte."""
        resultado = verificar_fortaleza_password("m!Clave#99")
        self.assertEqual(resultado, "fuerte")

    def test_sin_simbolos_no_es_fuerte(self):
        """Sin ningún símbolo especial, no se cumple ese criterio"""
        resultado = verificar_fortaleza_password("MiClave99")
        self.assertIn(resultado, ("débil", "media"))

    # que no sea típica

    def test_password_en_lista_negra_es_debil(self):
        """La contraseña está en la lista de contraseñas comprometidas, es débil."""
        for p in PASSWORDS_COMUNES:
            resultado = verificar_fortaleza_password(p)
        self.assertEqual(resultado, "débil")

    def test_contraseña_no_comun_no_penaliza(self):
        """Una contraseña que no está en la lista negra es aceptable"""
        resultado = verificar_fortaleza_password("X!k9pLm2")
        self.assertEqual(resultado, "fuerte")

    # niveles de fortaleza combinados

    def test_cero_criterios_es_debil(self):
        """Sin cumplir ningún criterio es débil."""
        resultado = verificar_fortaleza_password("abc")
        self.assertEqual(resultado, "débil")

    def test_dos_criterios_es_media(self):
        """Cumplir exactamente 2 criterios la hace media."""
        # longitud (>=7) + no común, sin mezcla ni símbolo interior
        resultado = verificar_fortaleza_password("clavemediosegura")
        self.assertEqual(resultado, "media")

    def test_tres_criterios_es_media(self):
        """Cumplir 3 criterios → media."""
        # longitud + mezcla + no común, símbolo solo al final
        resultado = verificar_fortaleza_password("conTraSeña73")
        self.assertEqual(resultado, "media")

    def test_cuatro_criterios_es_fuerte(self):
        """Si cumple todos los criterios, es fuerte."""
        resultado = verificar_fortaleza_password("m!Clave#99")
        self.assertEqual(resultado, "fuerte")

    # retorno

    def test_retorno_es_siempre_string(self):
        """La función siempre devuelve un str."""
        for pwd in ("abc", "abcdefg", "MiClave99!", "m!Clave#99"):
            with self.subTest(password=pwd):
                self.assertIsInstance(verificar_fortaleza_password(pwd), str)

    def test_retorno_solo_valores_validos(self):
        """El retorno siempre es 'débil', 'media' o 'fuerte'."""
        resultado = {"débil", "media", "fuerte"}
        for pwd in ("abc", "abcdefg", "MiPassword!", "m!Clave#99"):
            with self.subTest(password=pwd):
                self.assertIn(verificar_fortaleza_password(pwd), resultado)

if __name__ == "__main__":
    unittest.main()
