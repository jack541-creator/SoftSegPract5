# La contraseña de prueba de los usuarios es "4nv=8GsOy94R" y la clave maestra del gestor de prueba es "claveMaestraSegura123!"
from __future__ import annotations
import functools
import hashlib
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, UTC
from enum import Enum
from typing import Optional
import icontract
from src.logger.access_control import ContextoSeguridad, RolUsuario
from logger.log_util import (anadir_al_log, verificar_cadena_hashes, 
    inicializar_log, configure_logging, existe_archivo, archivo_vacio)

from src.gestor_credenciales.gestor_credenciales import (GestorCredenciales, ErrorAutenticacion)

# =========================================================
# EXCEPCIONES
# =========================================================

class ErrorSaldoInsuficiente(Exception):
    """Saldo insuficiente para la operación."""

class ErrorWalletNoEncontrada(Exception):
    """La dirección de wallet solicitada no existe."""

class ErrorTransaccionInvalida(Exception):
    """La transacción no cumple las reglas del protocolo."""

class ErrorAccesoNoAutorizado(Exception):
    """Intento de operación sin los privilegios necesarios."""

class ErrorGestorYaInicializado(Exception):
    """Intento de iniciar el gestor cuando este ya existe"""

# =========================================================
# ENUMERADOS
# =========================================================

class TipoWallet(str, Enum):
    """Tipo de wallet dentro del ecosistema ciphercoin."""
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


class ComisionProgresiva(EstrategiaComision):
    """
    Comisión progresiva.

    La comisión tiene:
      - una tarifa base fija (cubre el coste fijo por transacción)
      - una comisión variable que aumenta con el importe

    La comisión total nunca supera el 5 % del importe.
    """

    TARIFA_BASE = 0.02 # 0.02 monedas
    COMISION_MAXIMA = 0.05 # 5%
    IMPORTE_LIMITE = 50.0  # a partir de aquí se aplica la comisión máxima
    DESCUENTO_REPUTACION = 0.01

    @icontract.require(lambda importe: importe > 0,
                       "El importe debe ser positivo")
    @icontract.require(lambda reputacion: reputacion >= 0,
                       "La reputación no puede ser negativa")
    @icontract.ensure(lambda result, importe: 0 <= result <= importe,
                      "La comisión debe estar en [0, importe]")
    def calcular(self, importe: float, reputacion: int) -> float:
        importe_para_calculo = min(importe, self.IMPORTE_LIMITE)

        comision_aplicable = (
            self.COMISION_MAXIMA
            * importe_para_calculo
            / self.IMPORTE_LIMITE
        )

        factor_descuento = max(0.1, 1.0 - reputacion * self.DESCUENTO_REPUTACION)
        tarifa_base = self.TARIFA_BASE * factor_descuento
        comision_aplicable *= factor_descuento

        comision_total = tarifa_base + importe * comision_aplicable
        comision_maxima = importe * self.COMISION_MAXIMA

        return round(min(comision_total, comision_maxima), 8)


# =========================================================
#  WALLET
# =========================================================

@dataclass
class Wallet:

    direccion:  str
    nombre:     str
    tipo:       TipoWallet
    saldo:      float = 0.0
    reputacion: int   = 0

    def __post_init__(self):
        if not isinstance(self.direccion, str) or self.direccion.strip() == "":
            raise ErrorTransaccionInvalida("La dirección de la wallet no puede estar vacía")

        if not isinstance(self.nombre, str) or self.nombre.strip() == "":
            raise ErrorTransaccionInvalida("El nombre de la wallet no puede estar vacío")

        if not isinstance(self.tipo, TipoWallet):
            raise ErrorTransaccionInvalida("El tipo de wallet no es válido")

        if not isinstance(self.saldo, (int, float)) or self.saldo < 0:
            raise ErrorSaldoInsuficiente("El saldo inicial no puede ser negativo")

        if not isinstance(self.reputacion, int) or self.reputacion < 0:
            raise ErrorTransaccionInvalida("La reputación inicial no puede ser negativa")

        self.saldo = round(float(self.saldo), 8)

    @staticmethod
    @icontract.require(lambda nombre: isinstance(nombre, str) and nombre.strip() != "", "El nombre no puede estar vacío")
    @icontract.require(lambda tipo: isinstance(tipo, TipoWallet), "El tipo de wallet no es válido")
    @icontract.ensure(lambda result: isinstance(result, str) and len(result) == 40, "La dirección debe tener 40 caracteres")
    def generar_direccion(nombre: str, tipo: TipoWallet) -> str:
        raw = f"{tipo.value}:{nombre}".encode("utf-8")
        return hashlib.sha256(raw).hexdigest()[:40]

    @classmethod
    @icontract.require(lambda nombre: isinstance(nombre, str) and nombre.strip() != "", "El nombre no puede estar vacío")
    @icontract.require(lambda tipo: isinstance(tipo, TipoWallet), "El tipo de wallet no es válido")
    @icontract.require(lambda saldo: isinstance(saldo, (int, float)) and saldo >= 0, "El saldo inicial no puede ser negativo")
    @icontract.ensure(lambda result: isinstance(result, Wallet), "Debe devolver una Wallet")
    def crear(cls, nombre: str, tipo: TipoWallet, saldo: float = 0.0) -> "Wallet":
        """Crea una wallet válida generando automáticamente la dirección"""
        direccion = cls.generar_direccion(nombre, tipo)
        return cls(direccion=direccion, nombre=nombre, tipo=tipo, saldo=saldo)

    @icontract.require(lambda cantidad: isinstance(cantidad, (int, float)) and cantidad > 0, "La cantidad a ingresar debe ser positiva")
    def ingresar(self, cantidad: float) -> None:
        """Se ingresan monedas en la cartera"""
        self.saldo = round(self.saldo + cantidad, 8)

    @icontract.require(lambda cantidad: isinstance(cantidad, (int, float)) and cantidad > 0, "La cantidad a retirar debe ser positiva")
    @icontract.ensure(lambda self: self.saldo >= 0, "El saldo no puede quedar negativo")
    def retirar(self, cantidad: float) -> None:  
        """ Se retira el saldo especificado de la cartera para realizar las acciones necesarias"""
        if self.saldo < cantidad:
            raise ErrorSaldoInsuficiente(f"Saldo insuficiente: disponible {self.saldo:.4f}, requerido {cantidad:.4f}")
        self.saldo = round(self.saldo - cantidad, 8)

    @icontract.require(lambda puntos: isinstance(puntos, int) and puntos > 0, "Los puntos de reputación deben ser positivos")
    def aumentar_reputacion(self, puntos: int = 1) -> None:
        self.reputacion += puntos

    """En caso de haber penalizaciones se añadiría una función de restar reputación"""

    @icontract.require(lambda cantidad: isinstance(cantidad, (int, float)) and cantidad > 0, "La cantidad debe ser positiva")
    @icontract.ensure(lambda result: isinstance(result, bool), "Debe devolver un booleano")
    def puede_transferir(self, cantidad: float) -> bool:
        """Confirma que se tenga el saldo suficiente para hacer la transferencia"""
        return self.saldo >= cantidad

    def es_estado(self) -> bool:
        return self.tipo == TipoWallet.ESTADO

    def es_usuario(self) -> bool:
        return self.tipo == TipoWallet.USUARIO

    def es_pyme(self) -> bool:
        return self.tipo == TipoWallet.PYME

    @icontract.ensure(lambda result: isinstance(result, dict), "Debe devolver un diccionario")
    def to_dict(self) -> dict:
        return {
            "direccion": self.direccion,
            "nombre": self.nombre,
            "tipo": self.tipo.value,
            "saldo": self.saldo,
            "reputacion": self.reputacion,
        }

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Wallet):
            return NotImplemented
        return self.direccion == other.direccion

    def __hash__(self) -> int:
        return hash(self.direccion)

    def __repr__(self) -> str:
        return (f"Wallet({self.nombre!r}, tipo={self.tipo.value}, "f"saldo={self.saldo:.4f}, rep={self.reputacion})")
# =========================================================
#  TRANSACCIÓN
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
#  AUDITORÍA
# =========================================================

class ServicioAuditoriaCripto(ABC):
    """Interfaz de auditoría (ISP: mínima y cohesionada)."""

    @abstractmethod
    def registrar(self, accion: str, detalle: str) -> None:
        pass


class AuditoriaArchivoLog(ServicioAuditoriaCripto):
    """Implementación que escribe en un archivo de texto plano."""

    def __init__(self, ruta: str = "ciphercoin_audit.log"):
        self._ruta = ruta

    def registrar(self, accion: str, detalle: str) -> None:
        ts = datetime.now(UTC).isoformat()
        anadir_al_log("debug", f" {accion}. Detalle: {detalle}")


# =========================================================
#  BLOCKCHAIN (registro de transacciones) (R)
# =========================================================

class Blockchain:

    def __init__(self):
        self._bloques: list[dict] = []
        self._hash_ultimo: str = "0" * 64   # hash génesis

    @icontract.require(lambda tx: tx.importe > 0, "Solo se registran transacciones con importe positivo")
    def anadir(self, tx: Transaccion) -> None:
        """añade una transacción a la cadena."""
        bloque = {
            "indice":      len(self._bloques),
            "hash_previo": self._hash_ultimo,
            "tx":          tx.to_dict(),       }
        bloque_bytes = json.dumps(bloque, sort_keys=True).encode("utf-8")
        bloque["hash"] = hashlib.sha256(bloque_bytes).hexdigest()
        self._bloques.append(bloque)
        self._hash_ultimo = bloque["hash"]

    def historial(self) -> list[dict]:
        """copia del historial completo."""
        return list(self._bloques)

    def es_integra(self) -> bool:
        """verifica la integridad de la cadena completa."""
        for i, bloque in enumerate(self._bloques):
            esperado = bloque["hash_previo"]
            anterior = "0" * 64 if i == 0 else self._bloques[i - 1]["hash"]
            if esperado != anterior:
                return False
        return True

def validar_transferencia(metodo):
    @functools.wraps(metodo)
    def wrapper(self, origen_dir, destino_dir, importe, *args, **kwargs):
        # El importe tiene que ser un número positivo
        if importe <= 0:
            raise ErrorTransaccionInvalida("El importe debe ser mayor que 0, se recibio: {}".format(importe))
        # Comprobamos que la wallet de origen existe en el sistema
        if origen_dir not in self._wallets:
            raise ErrorWalletNoEncontrada("Wallet origen no encontrada: {}".format(origen_dir))
        # Comprobamos que la wallet de destino también existe
        if destino_dir not in self._wallets:
            raise ErrorWalletNoEncontrada("Wallet destino no encontrada: {}".format(destino_dir))
        # No tiene sentido enviarte dinero a ti mismo
        if origen_dir == destino_dir:
            raise ErrorTransaccionInvalida("El origen y el destino no pueden ser la misma wallet")
        # Todo correcto, dejamos pasar la llamada al método real
        return metodo(self, origen_dir, destino_dir, importe, *args, **kwargs)
    return wrapper


def registrar_inicio_transferencia(metodo):
    @functools.wraps(metodo)
    def wrapper(self, origen_dir, destino_dir, importe, *args, **kwargs):
        # Sacamos los nombres de las wallets para que el log sea legible
        nombre_origen  = self._wallets[origen_dir].nombre if origen_dir in self._wallets else origen_dir
        nombre_destino = self._wallets[destino_dir].nombre if destino_dir in self._wallets else destino_dir
        # Anotamos en el log que se va a iniciar una transferencia
        self._auditoria.registrar(
            "TRANSFERENCIA_INICIADA",
            "de={} | a={} | importe={:.4f}".format(nombre_origen, nombre_destino, importe))
        # Ejecutamos la transferencia
        return metodo(self, origen_dir, destino_dir, importe, *args, **kwargs)
    return wrapper


def verificar_integridad_post(metodo):
    @functools.wraps(metodo)
    def wrapper(self, *args, **kwargs):
        # Primero dejamos que la transferencia se complete
        resultado = metodo(self, *args, **kwargs)
        # Luego comprobamos la integridad de la cadena de bloques
        if not self._blockchain.es_integra():
            self._auditoria.registrar(
                "ALERTA_INTEGRIDAD", "La blockchain ha perdido integridad tras la ultima transferencia")
        return resultado
    return wrapper
# =========================================================
# SISTEMA ciphercoin (Facade)
# =========================================================

class SistemaCipherCoin:
    """
    componente principal del sistema de criptomoneda.

    gestiona wallets, transferencias, comisiones y reputación.
    Los 4 wallets predefinidos se inicializan con fondos de ejemplo.
    """

    # clave maestra interna del sistema (solo para operaciones de estado)
    _CLAVE_SISTEMA = "ciphercoinSistema#2026!"

    def __init__(self, estrategia_comision: Optional[EstrategiaComision] = None, auditoria: Optional[ServicioAuditoriaCripto] = None, ):
        # strategy: comisión inyectable, por defecto intervalos
        self._comision: EstrategiaComision = (estrategia_comision or ComisionProgresiva())
        self._auditoria: ServicioAuditoriaCripto = (auditoria or AuditoriaArchivoLog())
        self._blockchain = Blockchain()
        self._wallets: dict[str, Wallet] = {}


        # inicializar las 4 wallets predefinidas
        self._inicializar_wallets()
        
    # ------------------------------------------------------------------
    # Inicialización de wallets
    # ------------------------------------------------------------------

    def _inicializar_wallets(self) -> None:
        """crea los cuatro wallets del ecosistema con fondos iniciales."""
        definiciones = [
            ("Estado ciphercoin",  TipoWallet.ESTADO,  100.0),
            ("Alice (Usuario)",    TipoWallet.USUARIO,  25.0),
            ("Bob (Usuario)",      TipoWallet.USUARIO,  25.0),
            ("TechPyme S.L.",      TipoWallet.PYME,     50.0), ]
        for nombre, tipo, saldo_inicial in definiciones:
            direccion = Wallet.generar_direccion(nombre, tipo)
            wallet = Wallet.crear(nombre, tipo, saldo_inicial)
            self._wallets[wallet.direccion] = wallet
            self._auditoria.registrar("WALLET_CREADA", f"{nombre} | tipo={tipo.value} | dir={wallet.direccion}")
        

    # ------------------------------------------------------------------
    # Consultas
    # ------------------------------------------------------------------

    def obtener_wallet(self, direccion: str) -> Wallet:
        """devuelve la wallet correspondiente a la dirección."""
        if direccion not in self._wallets:
            raise ErrorWalletNoEncontrada(f"Dirección no encontrada: {direccion}")
        return self._wallets[direccion]

    def listar_wallets(self) -> list[Wallet]:
        """devuelve todas las wallets del sistema."""
        return list(self._wallets.values())

    def direccion_por_nombre(self, nombre: str) -> str:
        """busca la dirección de una wallet por nombre."""
        for w in self._wallets.values():
            if w.nombre == nombre:
                return w.direccion
        raise ErrorWalletNoEncontrada(f"Wallet no encontrada: {nombre!r}")

    def wallet_estado(self) -> Wallet:
        """devuelve la wallet de estado del sistema."""
        for w in self._wallets.values():
            if w.es_estado():
                return w
        raise ErrorWalletNoEncontrada("No hay wallet de estado configurada")

    # ------------------------------------------------------------------
    # Transferencia
    # ------------------------------------------------------------------

    @verificar_integridad_post
    @validar_transferencia
    @registrar_inicio_transferencia
    def transferir(self, origen_dir: str, destino_dir: str, importe: float) -> Transaccion:
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



        # calcular comisión
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
            if b["tx"]["origen"] == direccion or b["tx"]["destino"] == direccion]

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
