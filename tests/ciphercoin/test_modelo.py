import unittest
import os, sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from src.ciphercoin.modelo import (SistemaCipherCoin, ComisionProgresiva, TipoWallet, Wallet, Transaccion, Blockchain, 
                                   ErrorSaldoInsuficiente, ErrorWalletNoEncontrada, AuditoriaArchivoLog, ErrorAutenticacion )
from src.logger.access_control import ContextoSeguridad, RolUsuario

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
        from datetime import datetime, UTC
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
        import os
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
        import os
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
        
        from src.ciphercoin.autenticacion import ServicioAutenticacion
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
        from src.ciphercoin.autenticacion import ErrorSesionciphercoin
        with self.assertRaises((ErrorSesionciphercoin, Exception)):
                self.auth.login("alice", "wrongpassword")

    def test_login_usuario_inexistente_lanza_error(self):
        from src.ciphercoin.autenticacion import ErrorSesionciphercoin
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
        from src.ciphercoin.modelo import TipoWallet
        self.assertEqual(sesion.wallet.tipo, TipoWallet.ESTADO)


if __name__ == "__main__":
    unittest.main(verbosity=2)
