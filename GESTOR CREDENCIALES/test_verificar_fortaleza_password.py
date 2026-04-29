import unittest
from icontract.errors import ViolationError
from hypothesis import given, assume, settings, HealthCheck
from hypothesis import strategies as st
from gestor_credenciales import GestorCredenciales, verificar_fortaleza_password, ErrorPoliticalPassword

PASSWORDS_COMUNES = {
    "password", "123456", "12345678", "qwerty", "abc123",
    "111111", "123123", "admin", "user", "contraseña",
    "0000000", "seguro", "hola", "abcdefg",
}

SIMBOLOS = set(r"!@#$%^&*()-_=+[]{}|;:',.<>?/`~")

VALORES_VALIDOS = {"débil", "media", "fuerte"}

class TestFuncionalVerificarFortalezaPassword(unittest.TestCase):
    """
    Criterios:
      LONGITUD   : >= 7 caracteres (estándar PCI mínimo)
      MEZCLA     : mayúsculas NO solo al inicio, minúsculas, números, sin trivialidades
      SÍMBOLOS   : al menos uno y NO solo al final
      NO COMÚN   : no presente en lista negra

    Lanza ErrorPoliticalPassword si la entrada no es str o está vacía.
    """

    # -- entradas inválidas ----------------------------------------------------

    def test_entrada_entera_lanza_excepcion(self):
        with self.assertRaises(ErrorPoliticalPassword):
            verificar_fortaleza_password(12345)

    def test_entrada_none_lanza_excepcion(self):
        with self.assertRaises(ErrorPoliticalPassword):
            verificar_fortaleza_password(None)

    def test_entrada_lista_lanza_excepcion(self):
        with self.assertRaises(ErrorPoliticalPassword):
            verificar_fortaleza_password(["abc", "123"])

    def test_password_vacia_lanza_excepcion(self):
        with self.assertRaises(ErrorPoliticalPassword):
            verificar_fortaleza_password("")

    # -- longitud --------------------------------------------------------------

    def test_menos_de_7_caracteres_penaliza(self):
        self.assertEqual(verificar_fortaleza_password("abc123"), "débil")

    def test_exactamente_7_caracteres_cumple_longitud(self):
        self.assertIn(verificar_fortaleza_password("abcdef7"), ("media", "fuerte"))

    def test_contraseña_con_todos_criterios_es_fuerte(self):
        self.assertEqual(verificar_fortaleza_password("miClave!Super73Segura"), "fuerte")

    # -- mezcla de caracteres --------------------------------------------------

    def test_mayuscula_solo_al_inicio_no_segura(self):
        self.assertIn(verificar_fortaleza_password("Password"), ("débil", "media"))

    def test_mayuscula_interior_mejora_fortaleza(self):
        self.assertIn(verificar_fortaleza_password("paSSword7"), ("media", "fuerte"))

    def test_cadena_numerica_tipica_penaliza(self):
        self.assertIn(verificar_fortaleza_password("Mi12345pass"), ("débil", "media"))

    def test_cadena_qwerty_penaliza(self):
        self.assertIn(verificar_fortaleza_password("MiQwerty!"), ("débil", "media"))

    def test_mezcla_real_sin_trivialidades_suma(self):
        self.assertIn(verificar_fortaleza_password("maCbook97"), ("media", "fuerte"))

    # -- símbolos --------------------------------------------------------------

    def test_simbolo_solo_al_final_no_mejora_fortaleza(self):
        self.assertIn(verificar_fortaleza_password("abcdefg!"), ("débil", "media"))

    def test_simbolo_en_interior_mejora_fortaleza(self):
        self.assertIn(verificar_fortaleza_password("ab!cdefg"), ("media", "fuerte"))

    def test_varios_simbolos_distribuidos_suman(self):
        self.assertEqual(verificar_fortaleza_password("m!Clave#99"), "fuerte")

    def test_sin_simbolos_no_es_fuerte(self):
        self.assertIn(verificar_fortaleza_password("MiClave99"), ("débil", "media"))

    # -- lista negra -----------------------------------------------------------

    def test_password_en_lista_negra_es_debil(self):
        for p in PASSWORDS_COMUNES:
            with self.subTest(password=p):
                self.assertEqual(verificar_fortaleza_password(p), "débil")

    def test_contraseña_no_comun_no_penaliza(self):
        self.assertEqual(verificar_fortaleza_password("X!k9pLm2"), "fuerte")

    # -- niveles de fortaleza combinados ---------------------------------------

    def test_cero_criterios_es_debil(self):
        self.assertEqual(verificar_fortaleza_password("abc"), "débil")

    def test_dos_criterios_es_media(self):
        # longitud + no común; sin mezcla interior ni símbolo interior
        self.assertEqual(verificar_fortaleza_password("contraseñanocomun"), "media")

    def test_tres_criterios_es_media(self):
        # longitud + mezcla + no común; símbolo solo al final
        self.assertEqual(verificar_fortaleza_password("conTraSeña73"), "media")

    def test_cuatro_criterios_es_fuerte(self):
        self.assertEqual(verificar_fortaleza_password("m!Clave#99"), "fuerte")

    # -- retorno ---------------------------------------------------------------

    def test_retorno_es_siempre_string(self):
        for pwd in ("abc", "abcdefg", "MiClave99!", "m!Clave#99"):
            with self.subTest(password=pwd):
                self.assertIsInstance(verificar_fortaleza_password(pwd), str)

    def test_retorno_solo_valores_validos(self):
        for pwd in ("abc", "abcdefg", "MiPassword!", "m!Clave#99"):
            with self.subTest(password=pwd):
                self.assertIn(verificar_fortaleza_password(pwd), VALORES_VALIDOS)

class TestSeguridadVerificarFortalezaPassword(unittest.TestCase):
    
    # -- tipos inválidos siempre lanzan ErrorPoliticalPassword --------------------------

    @given(st.integers())
    def test_cualquier_entero_lanza_password_error(self, valor):
        with self.assertRaises(PasswordError):
            verificar_fortaleza_password(valor)

    @given(st.floats(allow_nan=False))
    def test_cualquier_float_lanza_password_error(self, valor):
        with self.assertRaises(PasswordError):
            verificar_fortaleza_password(valor)

    @given(st.lists(st.text()))
    def test_cualquier_lista_lanza_password_error(self, valor):
        with self.assertRaises(ErrorPoliticalPassword):
            verificar_fortaleza_password(valor)

    @given(st.binary())
    def test_bytes_lanza_password_error(self, valor):
        with self.assertRaises(ErrorPoliticalPassword):
            verificar_fortaleza_password(valor)

    @given(st.dictionaries(st.text(), st.text()))
    def test_diccionario_lanza_password_error(self, valor):
        with self.assertRaises(ErrorPoliticalPassword):
            verificar_fortaleza_password(valor)

    # -- el retorno siempre es uno de los tres valores válidos -----------------

    @given(st.text(min_size=1))
    def test_retorno_siempre_es_valor_valido(self, pwd):
        resultado = verificar_fortaleza_password(pwd)
        self.assertIn(resultado, VALORES_VALIDOS)

    @given(st.text(min_size=1))
    def test_retorno_siempre_es_str(self, pwd):
        self.assertIsInstance(verificar_fortaleza_password(pwd), str)

    # -- passwords de la lista negra siempre son débiles ----------------------

    @given(st.sampled_from(sorted(PASSWORDS_COMUNES)))
    def test_lista_negra_siempre_debil(self, pwd):
        self.assertEqual(verificar_fortaleza_password(pwd), "débil")

    # -- passwords cortos (< 7 chars) nunca son fuertes -----------------------

    @given(st.text(min_size=1, max_size=6))
    def test_password_corto_nunca_es_fuerte(self, pwd):
        assume(pwd not in PASSWORDS_COMUNES)
        resultado = verificar_fortaleza_password(pwd)
        self.assertNotEqual(resultado, "fuerte")

    # -- cadena vacía siempre lanza PasswordError ------------------------------

    def test_cadena_vacia_siempre_lanza(self):
        with self.assertRaises(PasswordError):
            verificar_fortaleza_password("")

    # -- idempotencia: llamar dos veces da el mismo resultado ------------------

    @given(st.text(min_size=1))
    def test_idempotencia(self, pwd):
        self.assertEqual(
            verificar_fortaleza_password(pwd),
            verificar_fortaleza_password(pwd),
        )

    # -- passwords con todos los criterios nunca son débiles -------------------

    @given(
        st.text(alphabet=st.characters(whitelist_categories=("Ll",)), min_size=3),
        st.text(alphabet=st.characters(whitelist_categories=("Lu",)), min_size=1),
        st.text(alphabet="0123456789", min_size=1),
        st.sampled_from(sorted(SIMBOLOS - {"'", "\\"})),
    )
    @settings(suppress_health_checks=[HealthCheck.too_slow])
    def test_password_con_todos_criterios_nunca_es_debil(
        self, minusculas, mayusculas, digitos, simbolo
    ):
        # símbolo en el interior garantizado, mayúscula no solo al inicio
        pwd = minusculas[:2] + simbolo + mayusculas + digitos + minusculas[2:]
        assume(len(pwd) >= 7)
        assume(pwd not in PASSWORDS_COMUNES)
        assume("12345" not in pwd and "qwerty" not in pwd.lower())
        resultado = verificar_fortaleza_password(pwd)
        self.assertNotEqual(resultado, "débil")

    # -- espacios en blanco no deben provocar excepciones inesperadas ----------

    @given(st.text(alphabet=" \t\n", min_size=1))
    def test_espacios_no_crashean(self, pwd):
        try:
            resultado = verificar_fortaleza_password(pwd)
            self.assertIn(resultado, VALORES_VALIDOS)
        except ErrorPoliticalPassword:
            pass  # también es aceptable rechazarlos

    # -- caracteres unicode no deben provocar excepciones inesperadas ----------

    @given(st.text(alphabet=st.characters(whitelist_categories=("Lo", "Ll", "Lu")), min_size=1))
    def test_unicode_no_crashea(self, pwd):
        try:
            resultado = verificar_fortaleza_password(pwd)
            self.assertIn(resultado, VALORES_VALIDOS)
        except ErrorPoliticalPassword:
            pass

    # -- passwords muy largos no deben crashear --------------------------------

    @given(st.text(min_size=100, max_size=10_000))
    @settings(max_examples=20)
    def test_passwords_muy_largos_no_crashean(self, pwd):
        resultado = verificar_fortaleza_password(pwd)
        self.assertIn(resultado, VALORES_VALIDOS)


if __name__ == "__main__":
    unittest.main(verbosity=2)
