import unittest

from ciphercoin.modelo import (
    SistemaCipherCoin,
    ComisionPorIntervalos,
    TipoWallet,
    Wallet,
    Transaccion,
    Blockchain,
    ErrorSaldoInsuficiente,
    ErrorWalletNoEncontrada,
    AuditoriaArchivoLog,)


# =========================================================
# TESTS: ComisionPorIntervalos
# =========================================================

class TestComisionPorIntervalos(unittest.TestCase):
    """Verifica el cálculo de comisiones para cada tramo y con reputación."""

    def setUp(self):
        self.comision = ComisionPorIntervalos()

    # ── tramo [0, 5) → 1 % ────────────────────────────────────────

    def test_tramo_bajo_sin_reputacion(self):
        resultado = self.comision.calcular(4.0, 0)
        self.assertAlmostEqual(resultado, 0.04, places=6)

    def test_tramo_bajo_con_reputacion_reduce_comision(self):
        # 1% - (5 * 0.1%) = 0.5%  →  4.0 * 0.005 = 0.02
        resultado = self.comision.calcular(4.0, 5)
        self.assertAlmostEqual(resultado, 0.02, places=6)

    def test_tramo_bajo_reputacion_excesiva_no_produce_negativo(self):
        # 100 puntos * 0.1% = 10% de descuento > 1% base → comisión = 0
        resultado = self.comision.calcular(4.0, 100)
        self.assertEqual(resultado, 0.0)

    # ── tramo [5, 20) → 5 % ───────────────────────────────────────

    def test_tramo_medio_sin_reputacion(self):
        resultado = self.comision.calcular(10.0, 0)
        self.assertAlmostEqual(resultado, 0.5, places=6)

    def test_tramo_medio_con_reputacion(self):
        # 5% - (3 * 0.1%) = 4.7%  →  10 * 0.047 = 0.47
        resultado = self.comision.calcular(10.0, 3)
        self.assertAlmostEqual(resultado, 0.47, places=6)

    # ── tramo [20, 50) → 10 % ─────────────────────────────────────

    def test_tramo_alto_sin_reputacion(self):
        resultado = self.comision.calcular(30.0, 0)
        self.assertAlmostEqual(resultado, 3.0, places=6)

    # ── tramo [50, ∞) → 15 % ──────────────────────────────────────

    def test_tramo_maximo_sin_reputacion(self):
        resultado = self.comision.calcular(100.0, 0)
        self.assertAlmostEqual(resultado, 15.0, places=6)

    def test_tramo_maximo_con_reputacion_alta(self):
        # 15% - (10 * 0.1%) = 14%  →  100 * 0.14 = 14.0
        resultado = self.comision.calcular(100.0, 10)
        self.assertAlmostEqual(resultado, 14.0, places=6)

    # ── casos borde ────────────────────────────────────────────────

    def test_importe_cero(self):
        resultado = self.comision.calcular(0.0, 0)
        self.assertEqual(resultado, 0.0)

    def test_importe_exactamente_en_limite_tramo(self):
        # 5.0 entra en el segundo tramo [5, 20) → 5%
        resultado = self.comision.calcular(5.0, 0)
        self.assertAlmostEqual(resultado, 0.25, places=6)

    # ── postcondición: comisión siempre ≤ importe ──────────────────

    def test_comision_nunca_supera_importe(self):
        for importe in [0.5, 5.0, 20.0, 50.0, 200.0]:
            for rep in [0, 5, 100]:
                with self.subTest(importe=importe, rep=rep):
                    c = self.comision.calcular(importe, rep)
                    self.assertLessEqual(c, importe)


# =========================================================
# TESTS: Wallet y dirección
# =========================================================

class TestWallet(unittest.TestCase):

    def test_generar_direccion_determinista(self):
        """La misma entrada siempre produce la misma dirección."""
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

    def test_saldo_inicial_cero_por_defecto(self):
        d = Wallet.generar_direccion("X", TipoWallet.USUARIO)
        w = Wallet(direccion=d, nombre="X", tipo=TipoWallet.USUARIO)
        self.assertEqual(w.saldo, 0.0)

    def test_reputacion_inicial_cero(self):
        d = Wallet.generar_direccion("Y", TipoWallet.USUARIO)
        w = Wallet(direccion=d, nombre="Y", tipo=TipoWallet.USUARIO)
        self.assertEqual(w.reputacion, 0)


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

class TestSistemaCriptoCoinWallets(unittest.TestCase):

    def setUp(self):
        # AuditoriaArchivoLog en modo silencioso (fichero /dev/null en Linux/Mac)
        import os
        log_path = os.devnull
        self.sistema = SistemaCriptoCoin(
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
# TESTS: SistemaCipherCoin — transferencias
# =========================================================

class TestTransferencias(unittest.TestCase):

    def setUp(self):
        import os
        self.sistema = SistemaCriptoCoin(
            auditoria=AuditoriaArchivoLog(os.devnull)
        )
        self.alice_dir    = self.sistema.direccion_por_nombre("Alice (Usuario)")
        self.bob_dir      = self.sistema.direccion_por_nombre("Bob (Usuario)")
        self.pyme_dir     = self.sistema.direccion_por_nombre("TechPyme S.L.")
        self.estado_dir   = self.sistema.wallet_estado().direccion

    def test_transferencia_usuario_a_usuario_correcta(self):
        alice = self.sistema.obtener_wallet(self.alice_dir)
        bob   = self.sistema.obtener_wallet(self.bob_dir)
        saldo_alice_ini = alice.saldo
        saldo_bob_ini   = bob.saldo

        tx = self.sistema.transferir(self.alice_dir, self.bob_dir, 10.0)

        self.assertEqual(tx.importe, 10.0)
        self.assertGreater(tx.comision, 0)
        self.assertAlmostEqual(alice.saldo, saldo_alice_ini - 10.0 - tx.comision, places=6)
        self.assertAlmostEqual(bob.saldo,   saldo_bob_ini   + 10.0, places=6)

    def test_comision_va_a_wallet_estado(self):
        estado = self.sistema.obtener_wallet(self.estado_dir)
        saldo_estado_ini = estado.saldo

        tx = self.sistema.transferir(self.alice_dir, self.bob_dir, 10.0)

        self.assertAlmostEqual(
            estado.saldo, saldo_estado_ini + tx.comision, places=6
        )

    def test_transferencia_usuario_a_pyme_suma_reputacion(self):
        alice = self.sistema.obtener_wallet(self.alice_dir)
        rep_ini = alice.reputacion

        self.sistema.transferir(self.alice_dir, self.pyme_dir, 5.0)

        self.assertEqual(alice.reputacion, rep_ini + 1)

    def test_transferencia_usuario_a_usuario_no_suma_reputacion(self):
        alice = self.sistema.obtener_wallet(self.alice_dir)
        rep_ini = alice.reputacion

        self.sistema.transferir(self.alice_dir, self.bob_dir, 5.0)

        self.assertEqual(alice.reputacion, rep_ini)

    def test_reputacion_reduce_comision_progresivamente(self):
        alice = self.sistema.obtener_wallet(self.alice_dir)

        # Primera transferencia (rep=0)
        tx1 = self.sistema.transferir(self.alice_dir, self.pyme_dir, 10.0)
        com1 = tx1.comision   # rep=0 → 5%

        # Aumentar reputación manualmente para aislar el efecto
        alice.reputacion = 10
        tx2 = self.sistema.transferir(self.alice_dir, self.pyme_dir, 10.0)
        com2 = tx2.comision   # rep=10 → 4%

        self.assertLess(com2, com1)

    def test_saldo_insuficiente_lanza_error(self):
        with self.assertRaises(ErrorSaldoInsuficiente):
            self.sistema.transferir(self.alice_dir, self.bob_dir, 999_999.0)

    def test_importe_cero_lanza_error(self):
        with self.assertRaises(Exception):
            self.sistema.transferir(self.alice_dir, self.bob_dir, 0.0)

    def test_importe_negativo_lanza_error(self):
        with self.assertRaises(Exception):
            self.sistema.transferir(self.alice_dir, self.bob_dir, -5.0)

    def test_wallet_origen_inexistente_lanza_error(self):
        with self.assertRaises(ErrorWalletNoEncontrada):
            self.sistema.transferir("falso", self.bob_dir, 5.0)

    def test_wallet_destino_inexistente_lanza_error(self):
        with self.assertRaises(ErrorWalletNoEncontrada):
            self.sistema.transferir(self.alice_dir, "falso", 5.0)

    def test_historial_registra_transacciones(self):
        self.sistema.transferir(self.alice_dir, self.bob_dir, 3.0)
        self.sistema.transferir(self.alice_dir, self.pyme_dir, 2.0)

        hist = self.sistema.historial_wallet(self.alice_dir)
        self.assertEqual(len(hist), 2)

    def test_integridad_blockchain_tras_multiples_txs(self):
        for _ in range(5):
            self.sistema.transferir(self.alice_dir, self.bob_dir, 1.0)
        self.assertTrue(self.sistema.verificar_integridad())

    def test_conservacion_de_valor_total(self):
        """La suma total de saldos debe conservarse (comisión redistribuida)."""
        suma_ini = sum(w.saldo for w in self.sistema.listar_wallets())
        self.sistema.transferir(self.alice_dir, self.bob_dir, 50.0)
        suma_fin = sum(w.saldo for w in self.sistema.listar_wallets())
        self.assertAlmostEqual(suma_ini, suma_fin, places=6)


# =========================================================
# TESTS: Autenticación
# =========================================================

class TestAutenticacion(unittest.TestCase):

    def setUp(self):
        import os
        sistema = SistemaCriptoCoin(auditoria=AuditoriaArchivoLog(os.devnull))
        from criptocoin.autenticacion import ServicioAutenticacion
        self.auth = ServicioAutenticacion(sistema)

    def test_login_correcto_alice(self):
        sesion = self.auth.login("alice", "Alice#Coin2024!")
        self.assertEqual(sesion.nombre_usuario, "alice")

    def test_login_correcto_techpyme(self):
        sesion = self.auth.login("techpyme", "TechPyme#Coin2024!")
        self.assertIsNotNone(sesion)

    def test_login_password_incorrecta_lanza_error(self):
        from criptocoin.autenticacion import ErrorSesionCriptoCoin
        with self.assertRaises((ErrorSesionCriptoCoin, Exception)):
            try:
                self.auth.login("alice", "wrongpassword")
                self.fail("Debería haber lanzado una excepción")
            except ErrorSesionCriptoCoin:
                raise
            except Exception as e:
                if "Autenticacion" in type(e).__name__ or "autenticacion" in str(e).lower():
                    raise ErrorSesionCriptoCoin(str(e))
                raise

    def test_login_usuario_inexistente_lanza_error(self):
        from criptocoin.autenticacion import ErrorSesionCriptoCoin
        with self.assertRaises((ErrorSesionCriptoCoin, Exception)):
            try:
                self.auth.login("noexiste", "cualquier")
                self.fail("Debería haber lanzado una excepción")
            except ErrorSesionCriptoCoin:
                raise
            except Exception as e:
                if "Autenticacion" in type(e).__name__ or "autenticacion" in str(e).lower():
                    raise ErrorSesionCriptoCoin(str(e))
                raise

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
        from criptocoin.modelo import TipoWallet
        self.assertEqual(sesion.wallet.tipo, TipoWallet.ESTADO)


if __name__ == "__main__":
    unittest.main(verbosity=2)
