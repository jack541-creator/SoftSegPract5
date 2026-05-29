import unittest
import os
import sys

from src.ciphercoin.modelo import (SistemaCipherCoin, ComisionProgresiva, TipoWallet, Wallet, Transaccion, Blockchain, 
                                   ErrorSaldoInsuficiente, ErrorWalletNoEncontrada, AuditoriaArchivoLog, ErrorAutenticacion )
from src.logger.access_control import ContextoSeguridad, RolUsuario
from src.ciphercoin.autenticacion import ServicioAutenticacion, ErrorSesionciphercoin
import tkinter as tk
from unittest.mock import MagicMock, patch
from src.ciphercoin.gui import DashboardFrame, VentanaTransferencia, VentanaHistorial, LoginFrame
from datetime import datetime, UTC
from tkinter import ttk

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

# =========================================================
#  TESTS: ComisionProgresiva
# =========================================================

class TestComisionProgresiva(unittest.TestCase):
    """Verifica invariantes del cálculo de comisiones."""

    def setUp(self):
        
        self.comision = ComisionProgresiva()
        self.importes_muestra = [0.01, 0.5, 1.0, 5.0, 10.0, 25.0, 50.0, 100.0, 1000.0]
        self.reputaciones_muestra = [0, 5, 25, 50, 100, 500]

    # ── Invariantes básicos ───────────────────────────────────────

    def test_comision_no_negativa(self):
        for importe in self.importes_muestra:
            for rep in self.reputaciones_muestra:
                with self.subTest(importe=importe, rep=rep):
                    self.assertGreaterEqual(self.comision.calcular(importe, rep), 0)

    def test_comision_nunca_supera_importe(self):
        for importe in self.importes_muestra:
            for rep in self.reputaciones_muestra:
                with self.subTest(importe=importe, rep=rep):
                    self.assertLessEqual(self.comision.calcular(importe, rep), importe)

    def test_comision_respeta_comision_maxima(self):
        cap = ComisionProgresiva.COMISION_MAXIMA
        for importe in self.importes_muestra:
            for rep in self.reputaciones_muestra:
                with self.subTest(importe=importe, rep=rep):
                    self.assertLessEqual(
                        self.comision.calcular(importe, rep),
                        importe * cap + 1e-9
                    )

    # ── Monotonía ─────────────────────────────────────────────────

    def test_reputacion_no_aumenta_comision(self):
        """Más reputación nunca produce más comisión."""
        for importe in [1.0, 10.0, 50.0, 100.0]:
            comisiones = [
                self.comision.calcular(importe, rep)
                for rep in [0, 10, 25, 50, 100]
            ]
            for c_menor_rep, c_mayor_rep in zip(comisiones, comisiones[1:]):
                with self.subTest(importe=importe):
                    self.assertLessEqual(c_mayor_rep, c_menor_rep + 1e-9)

    def test_comision_no_decrece_con_importe(self):
        """Más importe nunca produce menos comisión absoluta."""
        for rep in [0, 25, 50]:
            comisiones = [
                self.comision.calcular(importe, rep)
                for importe in [1.0, 5.0, 10.0, 25.0, 50.0, 100.0]
            ]
            for c_menor_imp, c_mayor_imp in zip(comisiones, comisiones[1:]):
                with self.subTest(rep=rep):
                    self.assertLessEqual(c_menor_imp, c_mayor_imp + 1e-9)

    # ── Determinismo ──────────────────────────────────────────────

    def test_calculo_determinista(self):
        self.assertEqual(
            self.comision.calcular(10.0, 5),
            self.comision.calcular(10.0, 5) )

    # ── Precondiciones (icontract) ────────────────────────────────

    def test_importe_no_positivo_rechazado(self):
        with self.assertRaises(Exception):
            self.comision.calcular(0.0, 0)
        with self.assertRaises(Exception):
            self.comision.calcular(-1.0, 0)

    def test_reputacion_negativa_rechazada(self):
        with self.assertRaises(Exception):
            self.comision.calcular(10.0, -1)


# =========================================================
# TESTS: Wallet y dirección
# =========================================================

class TestWallet(unittest.TestCase):

    def setUp(self):
        self.wallet = Wallet.crear("WalletTest", TipoWallet.USUARIO, 10.0)

    def test_generar_direccion_determinista(self):
        d1 = Wallet.generar_direccion("Alice", TipoWallet.USUARIO)
        d2 = Wallet.generar_direccion("Alice", TipoWallet.USUARIO)
        self.assertEqual(d1, d2)

    def test_direcciones_distintas_para_distinto_tipo(self):
        d1 = Wallet.generar_direccion("Entidad", TipoWallet.ESTADO)
        d2 = Wallet.generar_direccion("Entidad", TipoWallet.USUARIO)
        self.assertNotEqual(d1, d2)

    def test_longitud_direccion(self):
        d = Wallet.generar_direccion("Test", TipoWallet.PYME)
        self.assertEqual(len(d), 40)

    def test_crear_wallet_factory_method(self):
        w = Wallet.crear("Factory", TipoWallet.USUARIO, 10.0)

        self.assertEqual(w.nombre, "Factory")
        self.assertEqual(w.tipo, TipoWallet.USUARIO)
        self.assertEqual(w.saldo, 10.0)
        self.assertEqual(w.reputacion, 0)
        self.assertEqual(len(w.direccion), 40)

    def test_crear_wallet_rechaza_datos_invalidos(self):
        casos = [("", TipoWallet.USUARIO, 10.0), ("Nombre", "usuario", 10.0), ("Nombre", TipoWallet.USUARIO, -1.0)]

        for nombre, tipo, saldo in casos:
            with self.subTest(nombre=nombre, tipo=tipo, saldo=saldo):
                with self.assertRaises(Exception):
                    Wallet.crear(nombre, tipo, saldo)

    def test_wallet_rechaza_estado_inicial_invalido(self):
        direccion = Wallet.generar_direccion("Test", TipoWallet.USUARIO)

        casos = [
            {"direccion": "", "nombre": "Test", "tipo": TipoWallet.USUARIO, "saldo": 0.0, "reputacion": 0},
            {"direccion": direccion, "nombre": "", "tipo": TipoWallet.USUARIO, "saldo": 0.0, "reputacion": 0},
            {"direccion": direccion, "nombre": "Test", "tipo": "usuario", "saldo": 0.0, "reputacion": 0},
            {"direccion": direccion, "nombre": "Test", "tipo": TipoWallet.USUARIO, "saldo": -1.0, "reputacion": 0},
            {"direccion": direccion, "nombre": "Test", "tipo": TipoWallet.USUARIO, "saldo": 0.0, "reputacion": -1},
        ]

        for caso in casos:
            with self.subTest(caso=caso):
                with self.assertRaises(Exception):
                    Wallet(**caso)

    def test_saldo_inicial_cero_por_defecto(self):
        d = Wallet.generar_direccion("X", TipoWallet.USUARIO)
        w = Wallet(direccion=d, nombre="X", tipo=TipoWallet.USUARIO)
        self.assertEqual(w.saldo, 0.0)

    def test_reputacion_inicial_cero(self):
        d = Wallet.generar_direccion("Y", TipoWallet.USUARIO)
        w = Wallet(direccion=d, nombre="Y", tipo=TipoWallet.USUARIO)
        self.assertEqual(w.reputacion, 0)

    def test_ingresar_aumenta_saldo(self):
        self.wallet.ingresar(5.5)
        self.assertEqual(self.wallet.saldo, 15.5)

    def test_ingresar_rechaza_cantidades_invalidas(self):
        for cantidad in [0, -1, "5"]:
            with self.subTest(cantidad=cantidad):
                with self.assertRaises(Exception):
                    self.wallet.ingresar(cantidad)

    def test_retirar_reduce_saldo(self):
        self.wallet.retirar(7.5)
        self.assertEqual(self.wallet.saldo, 2.5)

    def test_retirar_rechaza_cantidades_invalidas(self):
        for cantidad in [0, -1, "5"]:
            with self.subTest(cantidad=cantidad):
                with self.assertRaises(Exception):
                    self.wallet.retirar(cantidad)

    def test_retirar_saldo_insuficiente(self):
        with self.assertRaises(ErrorSaldoInsuficiente):
            self.wallet.retirar(20.0)

    def test_puede_transferir_devuelve_booleano_correcto(self):
        casos = [(5.0, True), (10.0, True), (10.01, False)]

        for cantidad, esperado in casos:
            with self.subTest(cantidad=cantidad):
                self.assertEqual(self.wallet.puede_transferir(cantidad), esperado)

    def test_puede_transferir_rechaza_cantidades_invalidas_por_contrato(self):
        for cantidad in [0, -1, "5"]:
            with self.subTest(cantidad=cantidad):
                with self.assertRaises(Exception):
                    self.wallet.puede_transferir(cantidad)

    def test_aumentar_reputacion(self):
        self.wallet.aumentar_reputacion()
        self.assertEqual(self.wallet.reputacion, 1)

        self.wallet.aumentar_reputacion(3)
        self.assertEqual(self.wallet.reputacion, 4)

    def test_aumentar_reputacion_rechaza_valores_invalidos(self):
        for puntos in [0, -1, 1.5, "1"]:
            with self.subTest(puntos=puntos):
                with self.assertRaises(Exception):
                    self.wallet.aumentar_reputacion(puntos)

    def test_helpers_tipo_wallet(self):
        casos = [(TipoWallet.ESTADO, True, False, False), (TipoWallet.USUARIO, False, True, False), (TipoWallet.PYME, False, False, True)]

        for tipo, es_estado, es_usuario, es_pyme in casos:
            with self.subTest(tipo=tipo):
                w = Wallet.crear(f"Wallet {tipo.value}", tipo, 10.0)

                self.assertEqual(w.es_estado(), es_estado)
                self.assertEqual(w.es_usuario(), es_usuario)
                self.assertEqual(w.es_pyme(), es_pyme)

    def test_to_dict_devuelve_datos_correctos(self):
        self.wallet.aumentar_reputacion(2)

        datos = self.wallet.to_dict()

        self.assertEqual(datos["direccion"], self.wallet.direccion)
        self.assertEqual(datos["nombre"], "WalletTest")
        self.assertEqual(datos["tipo"], "usuario")
        self.assertEqual(datos["saldo"], 10.0)
        self.assertEqual(datos["reputacion"], 2)

    def test_wallets_con_misma_direccion_son_iguales(self):
        direccion = Wallet.generar_direccion("Igual", TipoWallet.USUARIO)

        w1 = Wallet(direccion=direccion, nombre="Igual", tipo=TipoWallet.USUARIO)
        w2 = Wallet(direccion=direccion, nombre="Igual copia", tipo=TipoWallet.USUARIO)

        self.assertEqual(w1, w2)
        self.assertEqual(hash(w1), hash(w2))

    def test_repr_contiene_datos_basicos(self):
        texto = repr(self.wallet)

        self.assertIn("WalletTest", texto)
        self.assertIn("usuario", texto)
        self.assertIn("10.0000", texto)


# =========================================================
# TESTS: Blockchain
# =========================================================

class TestBlockchain(unittest.TestCase):

    def _tx(self, importe=1.0) -> Transaccion:
        return Transaccion(
            origen="aaa",
            destino="bbb",
            importe=importe,
            comision=0.01,
            timestamp=datetime.now(UTC).isoformat(),
        )

    def test_blockchain_vacia_es_integra(self):
        bc = Blockchain()
        self.assertTrue(bc.es_integra())

    def test_anadir_transaccion(self):
        bc = Blockchain()
        bc.anadir(self._tx())
        self.assertEqual(len(bc.historial()), 1)

    def test_multiples_transacciones_integridad(self):
        bc = Blockchain()
        for _ in range(5):
            bc.anadir(self._tx())
        self.assertTrue(bc.es_integra())

    def test_manipulacion_rompe_integridad(self):
        bc = Blockchain()
        bc.anadir(self._tx())
        # Manipular el hash_previo del bloque 0
        bc._bloques[0]["hash_previo"] = "manipulado"
        self.assertFalse(bc.es_integra())


# =========================================================
# TESTS: SistemaCipherCoin — wallets iniciales
# =========================================================

class TestSistemaCipherCoinWallets(unittest.TestCase):

    def setUp(self):
        # AuditoriaArchivoLog en modo silencioso (fichero /dev/null en Linux/Mac)
        log_path = os.devnull
        self.sistema = SistemaCipherCoin(
            auditoria=AuditoriaArchivoLog(log_path)
        )

    def test_se_crean_cuatro_wallets(self):
        self.assertEqual(len(self.sistema.listar_wallets()), 4)

    def test_existe_wallet_estado(self):
        estado = self.sistema.wallet_estado()
        self.assertEqual(estado.tipo, TipoWallet.ESTADO)

    def test_existen_dos_wallets_usuario(self):
        usuarios = [
            w for w in self.sistema.listar_wallets()
            if w.tipo == TipoWallet.USUARIO
        ]
        self.assertEqual(len(usuarios), 2)

    def test_existe_una_wallet_pyme(self):
        pymes = [
            w for w in self.sistema.listar_wallets()
            if w.tipo == TipoWallet.PYME
        ]
        self.assertEqual(len(pymes), 1)

    def test_obtener_wallet_inexistente_lanza_error(self):
        with self.assertRaises(ErrorWalletNoEncontrada):
            self.sistema.obtener_wallet("dirección_falsa")

    def test_direccion_por_nombre_correcto(self):
        dir_ = self.sistema.direccion_por_nombre("Alice (Usuario)")
        wallet = self.sistema.obtener_wallet(dir_)
        self.assertEqual(wallet.nombre, "Alice (Usuario)")

    def test_direccion_por_nombre_inexistente_lanza_error(self):
        with self.assertRaises(ErrorWalletNoEncontrada):
            self.sistema.direccion_por_nombre("No Existe")


# =========================================================
# TESTS: SistemaCipherCoin — gestor de credenciales
# =========================================================

class TestGestorCredenciales(unittest.TestCase):

    def setUp(self):

        self.sistema = SistemaCipherCoin(
            auditoria=AuditoriaArchivoLog(os.devnull)
        )

        self.alice_dir    = self.sistema.direccion_por_nombre("Alice (Usuario)")
        self.master_key   = "claveMaestraSegura123!"
        self.password     = "4nv=8GsOy94R"

    def test_inicio_sesion(self):
        self.assertIsInstance(self.sistema.iniciar_sesion(self.master_key, self.alice_dir, self.password), str)

    def test_autenticacion(self):
        token = self.sistema.iniciar_sesion(self.master_key, self.alice_dir, self.password)
        self.assertTrue(self.sistema.autenticar_wallet(self.master_key, self.alice_dir, token))

    def test_autenticacion_fallida(self):
        token = self.sistema.iniciar_sesion(self.master_key, self.alice_dir, self.password)
        self.assertFalse(self.sistema.autenticar_wallet(self.master_key, self.alice_dir, "AAAA"))

# =========================================================
# TESTS: SistemaCipherCoin — transferencias
# =========================================================

class TestTransferencias(unittest.TestCase):

    def setUp(self):
        self.sistema = SistemaCipherCoin(
            auditoria=AuditoriaArchivoLog(os.devnull)
        )
        self.alice_dir    = self.sistema.direccion_por_nombre("Alice (Usuario)")
        self.bob_dir      = self.sistema.direccion_por_nombre("Bob (Usuario)")
        self.pyme_dir     = self.sistema.direccion_por_nombre("TechPyme S.L.")
        self.estado_dir   = self.sistema.wallet_estado().direccion

        self.master_key   = "claveMaestraSegura123!"
        self.password     = "4nv=8GsOy94R"
        self.alice_token  = self.sistema.iniciar_sesion(self.master_key, self.alice_dir, self.password)

    def test_transferencia_usuario_a_usuario_correcta(self):
        alice = self.sistema.obtener_wallet(self.alice_dir)
        bob   = self.sistema.obtener_wallet(self.bob_dir)
        saldo_alice_ini = alice.saldo
        saldo_bob_ini   = bob.saldo

        tx = self.sistema.transferir(self.alice_dir, self.bob_dir, 10.0, self.alice_token)

        self.assertEqual(tx.importe, 10.0)
        self.assertGreater(tx.comision, 0)
        self.assertAlmostEqual(alice.saldo, saldo_alice_ini - 10.0 - tx.comision, places=6)
        self.assertAlmostEqual(bob.saldo,   saldo_bob_ini   + 10.0, places=6)

    def test_comision_va_a_wallet_estado(self):
        estado = self.sistema.obtener_wallet(self.estado_dir)
        saldo_estado_ini = estado.saldo

        tx = self.sistema.transferir(self.alice_dir, self.bob_dir, 10.0, self.alice_token)

        self.assertAlmostEqual(estado.saldo, saldo_estado_ini + tx.comision, places=6)

    def test_transferencia_usuario_a_pyme_suma_reputacion(self):
        alice = self.sistema.obtener_wallet(self.alice_dir)
        rep_ini = alice.reputacion

        self.sistema.transferir(self.alice_dir, self.pyme_dir, 5.0, self.alice_token)

        self.assertEqual(alice.reputacion, rep_ini + 1)

    def test_transferencia_usuario_a_usuario_no_suma_reputacion(self):
        alice = self.sistema.obtener_wallet(self.alice_dir)
        rep_ini = alice.reputacion

        self.sistema.transferir(self.alice_dir, self.bob_dir, 5.0, self.alice_token)

        self.assertEqual(alice.reputacion, rep_ini)

    def test_reputacion_reduce_comision_progresivamente(self):
        alice = self.sistema.obtener_wallet(self.alice_dir)

        # Primera transferencia (rep=0)
        tx1 = self.sistema.transferir(self.alice_dir, self.pyme_dir, 10.0, self.alice_token)
        com1 = tx1.comision   # rep=0 → 5%

        # Aumentar reputación manualmente para aislar el efecto
        alice.reputacion = 10
        tx2 = self.sistema.transferir(self.alice_dir, self.pyme_dir, 10.0, self.alice_token)
        com2 = tx2.comision   # rep=10 → 4%

        self.assertLess(com2, com1)

    def test_saldo_insuficiente_lanza_error(self):
        with self.assertRaises(ErrorSaldoInsuficiente):
            self.sistema.transferir(self.alice_dir, self.bob_dir, 999_999.0, self.alice_token)

    def test_importe_cero_lanza_error(self):
        with self.assertRaises(Exception):
            self.sistema.transferir(self.alice_dir, self.bob_dir, 0.0, self.alice_token)

    def test_importe_negativo_lanza_error(self):
        with self.assertRaises(Exception):
            self.sistema.transferir(self.alice_dir, self.bob_dir, -5.0, self.alice_token)

    def test_wallet_origen_inexistente_lanza_error(self):
        with self.assertRaises(ErrorWalletNoEncontrada):
            self.sistema.transferir("falso", self.bob_dir, 5.0, self.alice_token)

    def test_wallet_destino_inexistente_lanza_error(self):
        with self.assertRaises(ErrorWalletNoEncontrada):
            self.sistema.transferir(self.alice_dir, "falso", 5.0, self.alice_token)

    def test_historial_registra_transacciones(self):
        self.sistema.transferir(self.alice_dir, self.bob_dir, 3.0, self.alice_token)
        self.sistema.transferir(self.alice_dir, self.pyme_dir, 2.0, self.alice_token)

        hist = self.sistema.historial_wallet(self.alice_dir)
        self.assertEqual(len(hist), 2)

    def test_integridad_blockchain_tras_multiples_txs(self):
        for _ in range(5):
            self.sistema.transferir(self.alice_dir, self.bob_dir, 1.0, self.alice_token)
        self.assertTrue(self.sistema.verificar_integridad())

    def test_conservacion_de_valor_total(self):
        """La suma total de saldos debe conservarse (comisión redistribuida)."""
        suma_ini = sum(w.saldo for w in self.sistema.listar_wallets())
        self.sistema.transferir(self.alice_dir, self.bob_dir, 20.0, self.alice_token)
        suma_fin = sum(w.saldo for w in self.sistema.listar_wallets())
        self.assertAlmostEqual(suma_ini, suma_fin, places=6)

    def test_token_incorrecto(self):
        with self.assertRaises(ErrorAutenticacion):
            self.sistema.transferir(self.alice_dir, self.bob_dir, 20.0, "ÑLASJ")


# =========================================================
# TESTS: Autenticación
# =========================================================

class TestAutenticacion(unittest.TestCase):

    def setUp(self):
        import os
        
        # para pasar los @access_control
        ContextoSeguridad().iniciar_sesion(usuario="test_user", rol=RolUsuario.ADMIN,
            sesion_id="miClave!Super73Segura")
        
        sistema = SistemaCipherCoin(auditoria=AuditoriaArchivoLog(os.devnull))
        self.auth = ServicioAutenticacion(sistema)

    def test_login_correcto_alice(self):
        sesion = self.auth.login("alice", "Alice#Coin2024!")
        self.assertEqual(sesion.nombre_usuario, "alice")

    def test_login_correcto_techpyme(self):
        sesion = self.auth.login("techpyme", "TechPyme#Coin2024!")
        self.assertIsNotNone(sesion)

    def test_login_password_incorrecta_lanza_error(self):
        with self.assertRaises((ErrorSesionciphercoin, Exception)):
                self.auth.login("alice", "wrongpassword")

    def test_login_usuario_inexistente_lanza_error(self):
        with self.assertRaises((ErrorSesionciphercoin, Exception)):
                self.auth.login("noexiste", "cualquier")


    def test_logout_limpia_sesion(self):
        self.auth.login("bob", "Bob#Coin2024!")
        self.assertTrue(self.auth.esta_autenticado())
        self.auth.logout()
        self.assertFalse(self.auth.esta_autenticado())

    def test_sesion_contiene_wallet_correcta(self):
        sesion = self.auth.login("alice", "Alice#Coin2024!")
        self.assertEqual(sesion.wallet.nombre, "Alice (Usuario)")

    def test_sesion_estado_tiene_wallet_estado(self):
        sesion = self.auth.login("estado", "Estado#Coin2024!")
        self.assertEqual(sesion.wallet.tipo, TipoWallet.ESTADO)

# ---------------------------------------------------------------------------
#  TESTS PARA LA GUI E INTERFAZ DE LOGIN
# ---------------------------------------------------------------------------

# helpers de mock

def _wallet_mock(nombre="Wallet Test", tipo_val="usuario", saldo=10.0, direccion="ADDR_TEST_001", reputacion=5):
    """Devuelve un wallet mock con los atributos mínimos necesarios."""
    tipo_map = {
        "usuario": TipoWallet.USUARIO,
        "pyme":    TipoWallet.PYME,
        "estado":  TipoWallet.ESTADO, }
    w = MagicMock()
    w.nombre     = nombre
    w.tipo       = tipo_map[tipo_val]
    w.saldo      = saldo
    w.direccion  = direccion
    w.reputacion = reputacion
    return w

def _sesion_mock(wallet=None):
    sesion = MagicMock()
    sesion.wallet = wallet or _wallet_mock()
    return sesion

def _app_mock(root: tk.Tk):
    """objeto app simulado que hereda de tk.Tk pero con sistema y auth mockeados"""

    app = root                        # reutilizamos la Tk raíz
    app.sistema  = MagicMock()
    app.auth     = MagicMock()

    # listar_wallets devuelve dos wallets de ejemplo
    w1 = _wallet_mock("Alice",  "usuario", 50.0,  "ADDR_ALICE")
    w2 = _wallet_mock("BizCo", "pyme",    200.0, "ADDR_BIZCO")
    app.sistema.listar_wallets.return_value = [w1, w2]
    app.sistema.historial_wallet.return_value = []
    app.sistema.historial_completo.return_value = []
    app.sistema.verificar_integridad.return_value = True

    comision_mock = MagicMock()
    comision_mock.calcular.return_value = 0.01
    app.sistema._comision = comision_mock

    # poner mostrar_login / mostrar_dashboard a no-ops en los tests
    app.mostrar_login     = MagicMock()
    app.mostrar_dashboard = MagicMock()
    return app

# ---------------------------------------------------------------------------
#  TESTS
# ---------------------------------------------------------------------------

class GuiTestCase(unittest.TestCase):
    """crea y destruye una Tk raíz para cada test."""

    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()       # no mostrar la ventana durante los tests
        self.app  = _app_mock(self.root)

    def tearDown(self):
        try:
            self.root.destroy()
        except tk.TclError:
            pass


#  loginframe

class TestLoginFrame(GuiTestCase):
    """Pruebas sobre la interfaz de login."""

    def _make_frame(self):
        return LoginFrame(self.app)

    def test_campos_vacios_muestran_error(self):
        """si se pulsa 'Enter' sin rellenar nada, aparece el mensaje de error."""
        frame = self._make_frame()
        frame._login()
        self.assertNotEqual(frame._lbl_error.cget("text"), "")

    def test_login_exitoso_llama_mostrar_dashboard(self):
        """login correcto debe llamar a mostrar_dashboard con la sesión."""
        frame = self._make_frame()
        sesion = _sesion_mock()
        self.app.auth.login.return_value = sesion

        frame._campo_usuario.var.set("alice")
        frame._campo_password.var.set("1234")
        frame._login()

        self.app.mostrar_dashboard.assert_called_once_with(sesion)

    def test_credenciales_incorrectas_muestran_error(self):
        """si auth.login lanza ErrorSesionCiphercoin se muestra el mensaje."""
        frame = self._make_frame()
        self.app.auth.login.side_effect = ErrorSesionciphercoin("Credenciales inválidas")

        frame._campo_usuario.var.set("unknown")
        frame._campo_password.var.set("wrong")
        frame._login()

        self.assertIn("Credenciales", frame._lbl_error.cget("text"))

# dashboard

class TestDashboardFrame(GuiTestCase):
    """Pruebas sobre el panel principal."""

    def _make_dashboard(self, tipo="usuario"):
        w = _wallet_mock(tipo_val=tipo, saldo=42.5, reputacion=7)
        sesion = _sesion_mock(wallet=w)
        return DashboardFrame(self.app, sesion)

    def test_saldo_se_muestra_correctamente(self):
        """saldo debe reflejar el saldo del wallet."""
        dash = self._make_dashboard()
        self.assertIn("42.5", dash._var_saldo.get())

    def test_reputacion_visible_solo_para_usuario(self):
        """_var_rep solo existe en wallets de tipo USUARIO."""
        dash_usuario = self._make_dashboard("usuario")
        self.assertTrue(hasattr(dash_usuario, "_var_rep"))
        dash_pyme = self._make_dashboard("pyme")
        self.assertFalse(hasattr(dash_pyme, "_var_rep"))

    def test_refrescar_actualiza_saldo(self):
        """refrescar() debe actualizar _var_saldo con el nuevo saldo."""
        dash = self._make_dashboard()
        dash._sesion.wallet.saldo = 99.9999
        dash.refrescar()
        self.assertIn("99.9999", dash._var_saldo.get())

    def test_boton_admin_solo_wallet_estado(self):
        """botón 'Panel Admin' solo se crea para wallets de tipo ESTADO"""
        w_estado = _wallet_mock(tipo_val="estado", direccion="ADDR_ESTADO")
        # listar_wallets no debe devolver el mismo wallet como destino
        self.app.sistema.listar_wallets.return_value = [_wallet_mock("Otro", "usuario", 10.0, "ADDR_OTRO")]
        sesion = _sesion_mock(wallet=w_estado)
        dash = DashboardFrame(self.app, sesion)   # no debe lanzar excepción
        self.assertTrue(callable(dash._abrir_admin))

# ventana transferencia

class TestVentanaTransferencia(GuiTestCase):
    """Pruebas sobre el formulario de transferencia."""

    def _make_ventana(self):
        origen  = _wallet_mock("Origen", "usuario", 100.0, "ADDR_ORI")
        destino = _wallet_mock("Destino", "pyme",  200.0, "ADDR_DST")
        self.app.sistema.listar_wallets.return_value = [origen, destino]

        sesion    = _sesion_mock(wallet=origen)
        dashboard = MagicMock()
        ven = VentanaTransferencia(self.app, sesion, dashboard)
        return ven, dashboard

    def test_transferencia_exitosa_llama_refrescar(self):
        """Una transferencia válida debe llamar a dashboard.refrescar()."""
        ven, dashboard = self._make_ventana()

        tx_mock = MagicMock()
        tx_mock.importe  = 10.0
        tx_mock.comision = 0.01
        tx_mock.tx_id    = "ABCDEF1234567890ABCDEF"
        self.app.sistema.transferir.return_value = tx_mock

        ven._campo_importe.var.set("10")
        with patch("tkinter.messagebox.showinfo"):   # silenciamos el popup
            ven._confirmar()

        dashboard.refrescar.assert_called_once()

    def test_saldo_insuficiente_muestra_error(self):
        """ErrorSaldoInsuficiente debe reflejarse en el label de error."""
        ven, _ = self._make_ventana()
        self.app.sistema.transferir.side_effect = ErrorSaldoInsuficiente("Saldo insuficiente")

        ven._campo_importe.var.set("9999")
        ven._confirmar()

        self.assertIn("Saldo", ven._lbl_error.cget("text"))


#  ventana historial

class TestVentanaHistorial(GuiTestCase):
    """Pruebas sobre la ventana de historial de transacciones."""

    def _make_ventana(self, txs=None):
        wallet = _wallet_mock(direccion="ADDR_ALICE")

        self.app.sistema.historial_wallet.return_value = txs or []
        self.app.sistema.obtener_wallet.return_value = _wallet_mock("Contraparte")

        sesion = _sesion_mock(wallet=wallet)

        ven = VentanaHistorial(self.app, sesion)
        ven.withdraw()

        return ven

    def test_historial_vacio_no_lanza_excepcion(self):
        """con historial vacío la ventana debe construirse sin errores."""
        ven = self._make_ventana(txs=[])
        self.assertIsNotNone(ven)

    def test_filas_se_insertan_correctamente(self):
        """cada transacción genera exactamente una fila en la tabla."""
        txs = [
            {"tx_id": "TX001", "origen": "ADDR_ALICE", "destino": "ADDR_OTRO",
             "importe": 1.0, "comision": 0.01, "timestamp": "2024-01-15T10:30:00Z"},
            {"tx_id": "TX002", "origen": "ADDR_OTRO", "destino": "ADDR_ALICE",
             "importe": 2.5, "comision": 0.02, "timestamp": "2024-01-16T11:00:00Z"},]
        ven = self._make_ventana(txs=txs)
        # buscamos el Treeview dentro de la ventana
        tabla = None
        for widget in ven.winfo_children():
            for child in widget.winfo_children():
                if isinstance(child, ttk.Treeview):
                    tabla = child
                    break
        self.assertIsNotNone(tabla, "No se encontró el Treeview en VentanaHistorial")
        self.assertEqual(len(tabla.get_children()), 2)

if __name__ == "__main__":
    unittest.main(verbosity=2)
