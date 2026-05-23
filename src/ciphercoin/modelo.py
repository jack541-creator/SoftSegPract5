import hashlib
import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, UTC
from enum import Enum
from typing import Optional
import icontract


# =========================================================
# EXCEPCIONES DE DOMINIO
# =========================================================

class ErrorSaldoInsuficiente(Exception):
    """Saldo insuficiente para la operación."""

class ErrorWalletNoEncontrada(Exception):
    """La dirección de wallet solicitada no existe."""

class ErrorTransaccionInvalida(Exception):
    """La transacción no cumple las reglas del protocolo."""

class ErrorAccesoNoAutorizado(Exception):
    """Intento de operación sin los privilegios necesarios."""

# =========================================================
# ENUMERADOS
# =========================================================

class TipoWallet(str, Enum):
    """Tipo de wallet dentro del ecosistema CriptoCoin."""
    ESTADO  = "estado"
    USUARIO = "usuario"
    PYME    = "pyme"

# =========================================================
# SISTEMA DE COMISIONES (Strategy)
# =========================================================

class EstrategiaComision(ABC):
    """
    Interfaz para el cálculo de comisiones (Strategy GoF).
    Abierta a extensión, cerrada a modificación.
    """

    @abstractmethod
    def calcular(self, importe: float, reputacion: int) -> float:
        """Devuelve la comisión absoluta a descontar del importe."""


class ComisionPorIntervalos(EstrategiaComision):
    """
    Comisión escalonada por intervalos de importe.

    Intervalos base (extensibles en _TRAMOS):
      [0,  5)  →  1 %
      [5,  20) →  5 %
      [20, 50) → 10 %
      [50,∞)   → 15 %

    Descuento por reputación: −0,1 % por punto de reputación del remitente.
    La comisión mínima es siempre 0 %.
    """

    # Tramos: (límite_superior_exclusivo, tasa_base_porcentual)
    # El último tramo cubre hasta infinito (None).
    _TRAMOS: list[tuple[Optional[float], float]] = [
        (5.0,   1.0),
        (20.0,  5.0),
        (50.0, 10.0),
        (None, 15.0),
    ]

    _DESCUENTO_POR_PUNTO = 0.1   # puntos porcentuales de descuento/reputación

    @icontract.require(lambda importe: importe >= 0,
                       "El importe no puede ser negativo")
    @icontract.require(lambda reputacion: reputacion >= 0,
                       "La reputación no puede ser negativa")
    @icontract.ensure(lambda result, importe: 0 <= result <= importe,
                      "La comisión debe estar en [0, importe]")
    def calcular(self, importe: float, reputacion: int) -> float:
        tasa_base = self._tasa_base(importe)
        descuento = reputacion * self._DESCUENTO_POR_PUNTO
        tasa_final = max(0.0, tasa_base - descuento)
        return round(importe * tasa_final / 100, 8)

    def _tasa_base(self, importe: float) -> float:
        for limite, tasa in self._TRAMOS:
            if limite is None or importe < limite:
                return tasa
        return self._TRAMOS[-1][1]   # salvaguarda (inalcanzable)


# =========================================================
# WALLET
# =========================================================

@dataclass
class Wallet:

    direccion:  str # (hash SHA-256 del nombre+tipo)
    nombre:     str
    tipo:       TipoWallet
    saldo:      float = 0.0
    reputacion: int   = 0

    # ------------------------------------------------------------------
    # Fábrica de dirección determinista
    # ------------------------------------------------------------------

    @staticmethod
    def generar_direccion(nombre: str, tipo: TipoWallet) -> str:
        """Genera una dirección determinista a partir del nombre y tipo."""
        raw = f"{tipo.value}:{nombre}".encode("utf-8")
        return hashlib.sha256(raw).hexdigest()[:40]

    # ------------------------------------------------------------------
    # Repr
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"Wallet({self.nombre!r}, tipo={self.tipo.value}, "
            f"saldo={self.saldo:.4f}, rep={self.reputacion})"
        )


# =========================================================
# TRANSACCIÓN
# =========================================================

@dataclass
class Transaccion:

    origen:      str           # dirección del remitente
    destino:     str           # dirección del destinatario
    importe:     float         # importe enviado (antes de comisiones)
    comision:    float         # comisión cobrada
    timestamp:   str           # ISO-8601 UTC
    tx_id:       str = field(init=False)  # hash de integridad

    def __post_init__(self):
        self.tx_id = self._calcular_hash()

    def _calcular_hash(self) -> str:
        payload = json.dumps({
            "origen":    self.origen,
            "destino":   self.destino,
            "importe":   self.importe,
            "comision":  self.comision,
            "timestamp": self.timestamp,
        }, sort_keys=True)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict:
        return {
            "tx_id":     self.tx_id,
            "origen":    self.origen,
            "destino":   self.destino,
            "importe":   self.importe,
            "comision":  self.comision,
            "timestamp": self.timestamp,
        }


# =========================================================
# AUDITORÍA
# =========================================================

class ServicioAuditoriaCripto(ABC):
    """Interfaz de auditoría (ISP: mínima y cohesionada)."""

    @abstractmethod
    def registrar(self, accion: str, detalle: str) -> None:
        pass


class AuditoriaArchivoLog(ServicioAuditoriaCripto):
    """Implementación que escribe en un archivo de texto plano."""

    def __init__(self, ruta: str = "criptocoin_audit.log"):
        self._ruta = ruta

    def registrar(self, accion: str, detalle: str) -> None:
        ts = datetime.now(UTC).isoformat()
        with open(self._ruta, "a", encoding="utf-8") as f:
            f.write(f"{ts} | {accion} | {detalle}\n")


# =========================================================
# BLOCKCHAIN (registro de transacciones)
# =========================================================

class Blockchain:

    def __init__(self):
        self._bloques: list[dict] = []
        self._hash_ultimo: str = "0" * 64   # hash génesis

    @icontract.require(lambda tx: tx.importe > 0,
                       "Solo se registran transacciones con importe positivo")
    def anadir(self, tx: Transaccion) -> None:
        """Añade una transacción a la cadena."""
        bloque = {
            "indice":      len(self._bloques),
            "hash_previo": self._hash_ultimo,
            "tx":          tx.to_dict(),
        }
        bloque_bytes = json.dumps(bloque, sort_keys=True).encode("utf-8")
        bloque["hash"] = hashlib.sha256(bloque_bytes).hexdigest()
        self._bloques.append(bloque)
        self._hash_ultimo = bloque["hash"]

    def historial(self) -> list[dict]:
        """Devuelve una copia del historial completo."""
        return list(self._bloques)

    def es_integra(self) -> bool:
        """Verifica la integridad de la cadena completa."""
        for i, bloque in enumerate(self._bloques):
            esperado = bloque["hash_previo"]
            anterior = "0" * 64 if i == 0 else self._bloques[i - 1]["hash"]
            if esperado != anterior:
                return False
        return True


# =========================================================
# SISTEMA CRIPTOCOIN (Facade)
# =========================================================

class SistemaCriptoCoin:
    """
    Fachada principal del sistema de criptomoneda.

    Orquesta wallets, transferencias, comisiones y reputación.
    Los 4 wallets predefinidos se inicializan con fondos de ejemplo.
    """

    # clave maestra interna del sistema (solo para operaciones de estado)
    _CLAVE_SISTEMA = "CriptoCoinSistema#2026!"

    def __init__(
        self,
        estrategia_comision: Optional[EstrategiaComision] = None,
        auditoria: Optional[ServicioAuditoriaCripto] = None,
    ):
        # strategy: comisión inyectable, por defecto intervalos
        self._comision: EstrategiaComision = (
            estrategia_comision or ComisionPorIntervalos()
        )
        self._auditoria: ServicioAuditoriaCripto = (
            auditoria or AuditoriaArchivoLog()
        )
        self._blockchain = Blockchain()
        self._wallets: dict[str, Wallet] = {}

        # inicializar las 4 wallets predefinidas
        self._inicializar_wallets()

    # ------------------------------------------------------------------
    # Inicialización de wallets
    # ------------------------------------------------------------------

    def _inicializar_wallets(self) -> None:
        """Crea los cuatro wallets del ecosistema con fondos iniciales."""
        definiciones = [
            ("Estado CriptoCoin",  TipoWallet.ESTADO,  10_000.0),
            ("Alice (Usuario)",    TipoWallet.USUARIO,  1_000.0),
            ("Bob (Usuario)",      TipoWallet.USUARIO,  1_000.0),
            ("TechPyme S.L.",      TipoWallet.PYME,     5_000.0),
        ]
        for nombre, tipo, saldo_inicial in definiciones:
            direccion = Wallet.generar_direccion(nombre, tipo)
            wallet = Wallet(
                direccion=direccion,
                nombre=nombre,
                tipo=tipo,
                saldo=saldo_inicial,
            )
            self._wallets[direccion] = wallet
            self._auditoria.registrar(
                "WALLET_CREADA",
                f"{nombre} | tipo={tipo.value} | dir={direccion}"
            )

    # ------------------------------------------------------------------
    # Consultas
    # ------------------------------------------------------------------

    def obtener_wallet(self, direccion: str) -> Wallet:
        """Devuelve la wallet correspondiente a la dirección dada."""
        if direccion not in self._wallets:
            raise ErrorWalletNoEncontrada(f"Dirección no encontrada: {direccion}")
        return self._wallets[direccion]

    def listar_wallets(self) -> list[Wallet]:
        """Devuelve todas las wallets del sistema."""
        return list(self._wallets.values())

    def direccion_por_nombre(self, nombre: str) -> str:
        """Busca la dirección de una wallet por nombre (coincidencia exacta)."""
        for w in self._wallets.values():
            if w.nombre == nombre:
                return w.direccion
        raise ErrorWalletNoEncontrada(f"Wallet no encontrada: {nombre!r}")

    def wallet_estado(self) -> Wallet:
        """Devuelve la wallet de estado del sistema."""
        for w in self._wallets.values():
            if w.tipo == TipoWallet.ESTADO:
                return w
        raise ErrorWalletNoEncontrada("No hay wallet de estado configurada")

    # ------------------------------------------------------------------
    # Transferencia
    # ------------------------------------------------------------------

    @icontract.require(lambda importe: importe > 0,
                       "El importe debe ser positivo")
    def transferir(
        self,
        origen_dir:  str,
        destino_dir: str,
        importe:     float,
    ) -> Transaccion:
        """
        Ejecuta una transferencia entre dos wallets.

        Flujo:
          1. Validar existencia de wallets y fondos.
          2. Calcular comisión según estrategia activa y reputación del remitente.
          3. Descontar (importe + comisión) del origen.
          4. Acreditar importe en el destino.
          5. Acreditar comisión en la wallet de estado.
          6. Actualizar reputación del remitente si el destino es PYME.
          7. Registrar en blockchain y auditoría.
        """
        origen  = self._obtener_wallet_validada(origen_dir)
        destino = self._obtener_wallet_validada(destino_dir)

        # Calcular comisión
        comision = self._comision.calcular(importe, origen.reputacion)
        total    = round(importe + comision, 8)

        # Validar saldo
        if origen.saldo < total:
            raise ErrorSaldoInsuficiente(
                f"Saldo insuficiente: se necesitan {total:.4f} "
                f"(importe {importe:.4f} + comisión {comision:.4f}), "
                f"disponible {origen.saldo:.4f}"
            )

        # Ejecutar movimientos
        origen.saldo  = round(origen.saldo - total, 8)
        destino.saldo = round(destino.saldo + importe, 8)
        self.wallet_estado().saldo = round(
            self.wallet_estado().saldo + comision, 8
        )

        # Reputación: solo si el remitente es USUARIO y el destino es PYME
        if origen.tipo == TipoWallet.USUARIO and destino.tipo == TipoWallet.PYME:
            origen.reputacion += 1
            self._auditoria.registrar(
                "REPUTACION_INCREMENTADA",
                f"Usuario={origen.nombre} | nueva_rep={origen.reputacion}"
            )

        # Crear y registrar transacción
        tx = Transaccion(
            origen=origen_dir,
            destino=destino_dir,
            importe=importe,
            comision=comision,
            timestamp=datetime.now(UTC).isoformat(),
        )
        self._blockchain.anadir(tx)
        self._auditoria.registrar(
            "TRANSFERENCIA",
            (
                f"de={origen.nombre} | a={destino.nombre} | "
                f"importe={importe:.4f} | comision={comision:.4f} | "
                f"tx_id={tx.tx_id[:12]}…"
            ),
        )
        return tx

    # ------------------------------------------------------------------
    # Historial
    # ------------------------------------------------------------------

    def historial_wallet(self, direccion: str) -> list[dict]:
        """Devuelve todas las transacciones en que participó la wallet."""
        self._obtener_wallet_validada(direccion)   # valida existencia
        return [
            b["tx"] for b in self._blockchain.historial()
            if b["tx"]["origen"] == direccion or b["tx"]["destino"] == direccion
        ]

    def historial_completo(self) -> list[dict]:
        """Devuelve toda la blockchain como lista de dicts."""
        return self._blockchain.historial()

    def verificar_integridad(self) -> bool:
        """Delega la verificación en la blockchain."""
        return self._blockchain.es_integra()

    # ------------------------------------------------------------------
    # Helpers privados
    # ------------------------------------------------------------------

    def _obtener_wallet_validada(self, direccion: str) -> Wallet:
        if direccion not in self._wallets:
            raise ErrorWalletNoEncontrada(f"Dirección desconocida: {direccion}")
        return self._wallets[direccion]
