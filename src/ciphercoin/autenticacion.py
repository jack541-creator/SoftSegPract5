"""
Integra el GestorCredenciales del proyecto original con el sistema de wallets,
usando el ProxySeguro como guardián de acceso.
"""

from __future__ import annotations

import icontract
from typing import Optional

from src.gestor_credenciales.gestor_credenciales import (
    GestorCredenciales,
    ErrorCredencialExistente,
)
from src.gestor_credenciales.proxy_seguro import (
    ProxySeguroGestorCredenciales,
    Sesion,
    ErrorAutenticacion,   # viene del proxy_seguro, no del gestor
)
from src.ciphercoin.modelo import SistemaCipherCoin, Wallet


# =========================================================
# EXCEPCIÓN DE SESIÓN ciphercoin
# =========================================================

class ErrorSesionciphercoin(Exception):
    """Error durante autenticación o sesión en ciphercoin."""


# =========================================================
# SESIÓN DE USUARIO ciphercoin
# =========================================================

class Sesionciphercoin:
    """
    Encapsula una sesión de usuario autenticada en ciphercoin.

    Combina la Sesion del ProxySeguro con la dirección de wallet
    del usuario activo, para que la GUI sepa qué wallet mostrar.
    """

    def __init__(self, sesion_proxy: Sesion, wallet: Wallet):
        self._sesion_proxy = sesion_proxy
        self._wallet = wallet

    @property
    def sesion_proxy(self) -> Sesion:
        return self._sesion_proxy

    @property
    def wallet(self) -> Wallet:
        return self._wallet

    @property
    def nombre_usuario(self) -> str:
        return self._sesion_proxy.usuario

    @property
    def direccion_wallet(self) -> str:
        return self._wallet.direccion

    def __repr__(self) -> str:
        return f"Sesionciphercoin(usuario={self.nombre_usuario!r})"


# =========================================================
# SERVICIO DE AUTENTICACIÓN
# =========================================================

class ServicioAutenticacion:
    """
    Orquesta el GestorCredenciales y el ProxySeguro para
    proveer login/logout a la GUI de ciphercoin.

    Usa el GestorCredenciales como almacén de contraseñas y
    el ProxySeguro como guardián de roles (usuario / pyme / admin).
    """

    # Clave maestra interna: solo la conoce el sistema.
    _CLAVE_MAESTRA = "ciphercoin#Master2024!"
    # Nombre del servicio en el gestor de credenciales
    _SERVICIO = "ciphercoin"

    def __init__(self, sistema: SistemaCipherCoin):
        self._sistema = sistema

        # GestorCredenciales: almacena las contraseñas
        self._gestor = GestorCredenciales(clave_maestra=self._CLAVE_MAESTRA, log_file="ciphercoin_audit.log")

        # ProxySeguro: controla el acceso por rol
        self._proxy = ProxySeguroGestorCredenciales(self._gestor)

        # Mapa usuario → dirección de wallet
        self._usuario_a_wallet: dict[str, str] = {}

        # Sesión activa (solo una por instancia de GUI)
        self._sesion_activa: Optional[Sesionciphercoin] = None

        # Registrar los 4 wallets predefinidos
        self._registrar_wallets_predefinidos()

    # ------------------------------------------------------------------
    #  Inicialización
    # ------------------------------------------------------------------

    def _registrar_wallets_predefinidos(self) -> None:
        """
        Registra los 4 wallets predefinidos con credenciales de demo.
        Las contraseñas cumplen la política de fortaleza del GestorCredenciales.
        """
        wallets_config = [
            # (nombre_usuario, contraseña, rol_proxy, nombre_wallet)
            ("estado",   "Estado#Coin2024!",  "admin",  "Estado ciphercoin"),
            ("alice",    "Alice#Coin2024!",    "editor", "Alice (Usuario)"),
            ("bob",      "Bob#Coin2024!",      "editor", "Bob (Usuario)"),
            ("techpyme", "TechPyme#Coin2024!", "editor", "TechPyme S.L."),
        ]
        for usuario, password, rol, nombre_wallet in wallets_config:
            # Registrar en el GestorCredenciales
            try:
                self._gestor.anadir_credencial(
                    clave_maestra=self._CLAVE_MAESTRA,
                    servicio=self._SERVICIO,
                    usuario=usuario,
                    password=password,
                )
            except ErrorCredencialExistente:
                pass  # ya registrado (re-inicialización)

            # Registrar en el ProxySeguro
            try:
                self._proxy.registrar_usuario_proxy(usuario, password, rol)
            except Exception:
                pass  # ya registrado

            # Mapear usuario → dirección de wallet
            wallet_dir = self._sistema.direccion_por_nombre(nombre_wallet)
            self._usuario_a_wallet[usuario] = wallet_dir

    # ------------------------------------------------------------------
    #  Login / Logout
    # ------------------------------------------------------------------

    @icontract.require(lambda usuario: isinstance(usuario, str) and usuario.strip(),
                       "El nombre de usuario no puede estar vacío")
    @icontract.require(lambda password: isinstance(password, str) and password,
                       "La contraseña no puede estar vacía")
    def login(self, usuario: str, password: str) -> Sesionciphercoin:
        """
        Autentica al usuario y devuelve una Sesionciphercoin.

        Lanza ErrorSesionciphercoin si las credenciales son incorrectas.
        """
        usuario = usuario.strip()
        try:
            sesion_proxy = self._proxy.iniciar_sesion(usuario, password)
        except (ErrorAutenticacion, Exception) as e:
            # Capturamos tanto ErrorAutenticacion del proxy como cualquier
            # excepción de autenticación del GestorCredenciales
            if "ErrorAutenticacion" in type(e).__name__ or isinstance(e, ErrorAutenticacion):
                raise ErrorSesionciphercoin("Usuario o contraseña incorrectos.")
            raise ErrorSesionciphercoin("Usuario o contraseña incorrectos.")

        wallet_dir = self._usuario_a_wallet.get(usuario)
        if not wallet_dir:
            raise ErrorSesionciphercoin(
                f"No se encontró wallet para el usuario {usuario!r}"
            )

        wallet = self._sistema.obtener_wallet(wallet_dir)
        self._sesion_activa = Sesionciphercoin(sesion_proxy, wallet)
        return self._sesion_activa

    def logout(self) -> None:
        """Cierra la sesión activa."""
        self._sesion_activa = None

    @property
    def sesion_activa(self) -> Optional[Sesionciphercoin]:
        return self._sesion_activa

    def esta_autenticado(self) -> bool:
        return self._sesion_activa is not None

    # ------------------------------------------------------------------
    #  Credenciales de demo (para la pantalla de login)
    # ------------------------------------------------------------------

    @staticmethod
    def credenciales_demo() -> list[dict]:
        """Devuelve las credenciales predefinidas para mostrar en la GUI."""
        return [
            {"usuario": "alice",    "password": "Alice#Coin2024!",    "rol": "Usuario"},
            {"usuario": "bob",      "password": "Bob#Coin2024!",      "rol": "Usuario"},
            {"usuario": "techpyme", "password": "TechPyme#Coin2024!", "rol": "PYME"},
            {"usuario": "estado",   "password": "Estado#Coin2024!",   "rol": "Admin"},   ]
