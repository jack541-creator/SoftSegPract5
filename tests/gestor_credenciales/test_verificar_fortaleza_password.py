import unittest
from src.gestor_credenciales.gestor_credenciales import ValidadorPassword, ErrorPoliticaPassword

# contraseñas típicas
PASSWORDS_COMUNES = {
    "password", "123456", "12345678", "qwerty", "abc123",
    "111111", "123123", "admin", "user", "contraseña",
    "0000000", "seguro", "hola", "abcdefg", }

SIMBOLOS = set(r"!@#$%^&*()-_=+[]{}|;:',.<>?/`~")

class TestVerificarFortalezaPassword(unittest.TestCase):
    """
    tenemos en cuenta algunos criterios:

      LONGITUD: >= 8 caracteres
      MEZCLA: mayúsculas (no solo al inicio),minúsculas, números, y sin ser típicas
      SÍMBOLOS: al menos uno y NO solo al final

    lanza ErrorPoliticaPassword si la entrada no es str o está vacía.
    """

    def setUp(self):
        self.validador = ValidadorPassword()

    # entradas inválidas

    def test_entrada_entera_lanza_excepcion(self):
        """Un entero no es una contraseña válida."""
        with self.assertRaises(ErrorPoliticaPassword):
            self.validador.verificar_fortaleza(12345)

    def test_entrada_none_lanza_excepcion(self):
        """None debe lanzar PasswordError."""
        with self.assertRaises(ErrorPoliticaPassword):
            self.validador.verificar_fortaleza(None)

    def test_entrada_lista_lanza_excepcion(self):
        """Una lista no es una contraseña válida."""
        with self.assertRaises(ErrorPoliticaPassword):
            self.validador.verificar_fortaleza(["abc", "123"])

    def test_password_vacia_lanza_excepcion(self):
        """Cadena vacía debe lanzar PasswordError."""
        with self.assertRaises(ErrorPoliticaPassword):
            self.validador.verificar_fortaleza("")

    # longitud

    def test_menos_de_8_caracteres_penaliza(self):
        resultado = self.validador.verificar_fortaleza("abc123")
        self.assertEqual(resultado, "débil")

    def test_exactamente_8_caracteres_cumple_longitud(self):
        resultado = self.validador.verificar_fortaleza("abcdefg8")
        self.assertIn(resultado, ("media", "fuerte"))

    def test_contraseña_con_todos_criterios_es_fuerte(self):
        """Una contraseña muy larga con todos los criterios es fuerte."""
        resultado = self.validador.verificar_fortaleza("miClave!Super73Segura")
        self.assertEqual(resultado, "fuerte")

    # mezcla de caracteres

    def test_mayuscula_solo_al_inicio_no_segura(self):
        """Mayúscula únicamente al inicio no es seguro."""
        resultado = self.validador.verificar_fortaleza("Password")
        self.assertIn(resultado, ("débil", "media"))

    def test_mayuscula_interior_mejora_fortaleza(self):
        """Mayúscula dentro del cuerpo sí cuenta como mezcla."""
        resultado = self.validador.verificar_fortaleza("paSSword7")
        self.assertIn(resultado, ("media", "fuerte"))

    def test_cadena_numerica_tipica_penaliza(self):
        """Secuencia trivial '12345' dentro de la contraseña penaliza."""
        resultado = self.validador.verificar_fortaleza("Mi12345pass")
        self.assertIn(resultado, ("débil", "media"))

    def test_cadena_qwerty_penaliza(self):
        """Secuencia de teclado típica 'qwerty' penaliza."""
        resultado = self.validador.verificar_fortaleza("MiQwerty!")
        self.assertIn(resultado, ("débil", "media"))

    def test_mezcla_real_sin_trivialidades_suma(self):
        """Mezcla de may/min/números sin cadenas triviales suma al criterio 2."""
        resultado = self.validador.verificar_fortaleza("maCbook97")
        self.assertIn(resultado, ("media", "fuerte"))

    # símbolos

    def test_simbolo_solo_al_final_no_mejora_fortaleza(self):
        """Símbolo únicamente al final no suma."""
        resultado = self.validador.verificar_fortaleza("abcdefg!")
        self.assertIn(resultado, ("débil", "media"))

    def test_simbolo_en_interior_mejora_fortaleza(self):
        """Símbolo dentro del cuerpo (no solo al final) sí suma."""
        resultado = self.validador.verificar_fortaleza("ab!cdefg")
        self.assertIn(resultado, ("media", "fuerte"))

    def test_varios_simbolos_distribuidos_suman(self):
        """Varios símbolos distribuidos es fuerte."""
        resultado = self.validador.verificar_fortaleza("m!Clave#99")
        self.assertEqual(resultado, "fuerte")

    def test_sin_simbolos_no_es_fuerte(self):
        """Sin ningún símbolo especial, no se cumple ese criterio"""
        resultado = self.validador.verificar_fortaleza("MiClave99")
        self.assertIn(resultado, ("débil", "media"))

    # que no sea típica

    def test_password_en_lista_negra_es_debil(self):
        """La contraseña está en la lista de contraseñas comprometidas, es débil."""
        for p in PASSWORDS_COMUNES:
            with self.subTest(password=p):
                self.assertEqual(self.validador.verificar_fortaleza(p), "débil")

    def test_contraseña_no_comun_no_penaliza(self):
        """Una contraseña que no está en la lista negra es aceptable"""
        resultado = self.validador.verificar_fortaleza("X!k9pLm2")
        self.assertEqual(resultado, "fuerte")

    # niveles de fortaleza combinados

    def test_cero_criterios_es_debil(self):
        """Sin cumplir ningún criterio es débil."""
        resultado = self.validador.verificar_fortaleza("abc")
        self.assertEqual(resultado, "débil")

    def test_dos_criterios_es_media(self):
        """Cumplir exactamente 2 criterios la hace media."""
        # longitud (>=8) + no común, sin mezcla ni símbolo interior
        resultado = self.validador.verificar_fortaleza("clavemediosegura")
        self.assertEqual(resultado, "media")

    def test_tres_criterios_es_media(self):
        """Cumplir 3 criterios → media."""
        # longitud + mezcla + no común, símbolo solo al final
        resultado = self.validador.verificar_fortaleza("conTraSeña73")
        self.assertEqual(resultado, "media")

    def test_cuatro_criterios_es_fuerte(self):
        """Si cumple todos los criterios, es fuerte."""
        resultado = self.validador.verificar_fortaleza("m!Clave#99")
        self.assertEqual(resultado, "fuerte")

    # retorno

    def test_retorno_es_siempre_string(self):
        """La función siempre devuelve un str."""
        for pwd in ("abc", "abcdefg", "MiClave99!", "m!Clave#99"):
            with self.subTest(password=pwd):
                self.assertIsInstance(self.validador.verificar_fortaleza(pwd), str)

    def test_retorno_solo_valores_validos(self):
        """El retorno siempre es 'débil', 'media' o 'fuerte'."""
        resultado = {"débil", "media", "fuerte"}
        for pwd in ("abc", "abcdefg", "MiPassword!", "m!Clave#99"):
            with self.subTest(password=pwd):
                self.assertIn(self.validador.verificar_fortaleza(pwd), resultado)

if __name__ == "__main__":
    unittest.main()