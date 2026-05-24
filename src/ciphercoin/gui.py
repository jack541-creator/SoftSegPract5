"""
gui.py — Interfaz gráfica de ciphercoin (tkinter).

Pantallas:
  • LoginFrame   — autenticación con el GestorCredenciales
  • DashboardFrame — vista principal del wallet activo
  • TransferFrame  — formulario de transferencia
  • HistorialFrame — historial de transacciones
  • AdminFrame     — vista de estado del sistema (solo admin)

Compatible con Debian Linux, Windows y macOS.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional
import threading

from src.ciphercoin.modelo import (
    SistemaCipherCoin,
    TipoWallet,
    ErrorSaldoInsuficiente,
    ErrorWalletNoEncontrada,
    ErrorTransaccionInvalida,
)
from ciphercoin.autenticacion import (
    ServicioAutenticacion,
    Sesionciphercoin,
    ErrorSesionciphercoin,
)


# =========================================================
# PALETA Y ESTILOS
# =========================================================

COLORES = {
    "fondo":          "#1a1d2e",
    "fondo_card":     "#252840",
    "fondo_input":    "#2e3150",
    "acento":         "#7c6af7",
    "acento_hover":   "#9b8cff",
    "texto":          "#e8e8f0",
    "texto_suave":    "#8a8aaa",
    "exito":          "#4caf82",
    "error":          "#f07575",
    "advertencia":    "#f0c060",
    "estado":         "#60b8f0",
    "pyme":           "#f0a060",
    "usuario":        "#7c6af7",
}

FUENTE_TITULO  = ("Segoe UI", 20, "bold")
FUENTE_GRANDE  = ("Segoe UI", 14, "bold")
FUENTE_NORMAL  = ("Segoe UI", 11)
FUENTE_PEQUEÑA = ("Segoe UI", 9)
FUENTE_MONO    = ("Courier New", 10)


def color_tipo(tipo: TipoWallet) -> str:
    mapa = {
        TipoWallet.ESTADO:  COLORES["estado"],
        TipoWallet.PYME:    COLORES["pyme"],
        TipoWallet.USUARIO: COLORES["usuario"],
    }
    return mapa.get(tipo, COLORES["texto"])


# =========================================================
# WIDGET AUXILIARES
# =========================================================

class Card(tk.Frame):
    """Panel con fondo redondeado simulado."""

    def __init__(self, parent, **kw):
        bg = kw.pop("bg", COLORES["fondo_card"])
        super().__init__(parent, bg=bg, padx=16, pady=14, **kw)


class Boton(tk.Button):
    """Botón estilizado."""

    def __init__(self, parent, texto: str, comando=None,
                 color=None, **kw):
        color = color or COLORES["acento"]
        super().__init__(
            parent,
            text=texto,
            command=comando,
            bg=color,
            fg=COLORES["texto"],
            activebackground=COLORES["acento_hover"],
            activeforeground=COLORES["texto"],
            relief="flat",
            font=FUENTE_NORMAL,
            padx=14,
            pady=7,
            cursor="hand2",
            **kw,
        )
        self.bind("<Enter>", lambda e: self.config(bg=COLORES["acento_hover"]))
        self.bind("<Leave>", lambda e: self.config(bg=color))


class EntradaLabel(tk.Frame):
    """Etiqueta + campo de entrada apilados verticalmente."""

    def __init__(self, parent, etiqueta: str, ocultar=False, **kw):
        super().__init__(parent, bg=COLORES["fondo_card"])
        tk.Label(
            self, text=etiqueta,
            bg=COLORES["fondo_card"],
            fg=COLORES["texto_suave"],
            font=FUENTE_PEQUEÑA,
        ).pack(anchor="w")
        show = "*" if ocultar else ""
        self.var = tk.StringVar()
        self.entry = tk.Entry(
            self,
            textvariable=self.var,
            show=show,
            bg=COLORES["fondo_input"],
            fg=COLORES["texto"],
            insertbackground=COLORES["texto"],
            relief="flat",
            font=FUENTE_NORMAL,
            **kw,
        )
        self.entry.pack(fill="x", ipady=6, pady=(2, 0))

    @property
    def valor(self) -> str:
        return self.var.get().strip()

    def limpiar(self):
        self.var.set("")


# =========================================================
# FRAME DE LOGIN
# =========================================================

class LoginFrame(tk.Frame):
    """
    Pantalla de inicio de sesión.
    Muestra las credenciales de demo y delega en ServicioAutenticacion.
    """

    def __init__(self, master: "Appciphercoin"):
        super().__init__(master, bg=COLORES["fondo"])
        self._app = master
        self._construir()

    def _construir(self):
        self.pack(fill="both", expand=True)

        # ── Logo / título ──────────────────────────────────────────
        tk.Label(
            self,
            text="₿ ciphercoin",
            bg=COLORES["fondo"],
            fg=COLORES["acento"],
            font=("Segoe UI", 32, "bold"),
        ).pack(pady=(50, 4))

        tk.Label(
            self,
            text="Sistema de criptomoneda seguro",
            bg=COLORES["fondo"],
            fg=COLORES["texto_suave"],
            font=FUENTE_NORMAL,
        ).pack(pady=(0, 30))

        # ── card de login ──────────────────────────────────────────
        card = Card(self)
        card.pack(padx=60, pady=10, ipadx=10, ipady=10)

        tk.Label(
            card,
            text="Iniciar sesión",
            bg=COLORES["fondo_card"],
            fg=COLORES["texto"],
            font=FUENTE_GRANDE,
        ).pack(anchor="w", pady=(0, 14))

        self._campo_usuario = EntradaLabel(card, "Usuario", width=32)
        self._campo_usuario.pack(fill="x", pady=5)

        self._campo_password = EntradaLabel(card, "Contraseña", ocultar=True, width=32)
        self._campo_password.pack(fill="x", pady=5)

        self._lbl_error = tk.Label(
            card,
            text="",
            bg=COLORES["fondo_card"],
            fg=COLORES["error"],
            font=FUENTE_PEQUEÑA,
        )
        self._lbl_error.pack(anchor="w", pady=(4, 0))

        Boton(card, "Entrar", self._login).pack(fill="x", pady=(14, 0))

        # ── credenciales de demo ───────────────────────────────────
        demo_frame = Card(self, bg=COLORES["fondo"])
        demo_frame.pack(pady=10)

        tk.Label(
            demo_frame,
            text="Credenciales de demo",
            bg=COLORES["fondo"],
            fg=COLORES["texto_suave"],
            font=FUENTE_PEQUEÑA,
        ).pack(anchor="w", pady=(0, 6))

        for cred in ServicioAutenticacion.credenciales_demo():
            fila = tk.Frame(demo_frame, bg=COLORES["fondo"])
            fila.pack(fill="x", pady=2)
            color = COLORES["pyme"] if cred["rol"] == "PYME" else (
                COLORES["estado"] if cred["rol"] == "Admin" else COLORES["usuario"]
            )
            tk.Label(
                fila,
                text=f"[{cred['rol']}]",
                bg=COLORES["fondo"],
                fg=color,
                font=FUENTE_PEQUEÑA,
                width=9,
                anchor="w",
            ).pack(side="left")
            tk.Label(
                fila,
                text=f"  {cred['usuario']}",
                bg=COLORES["fondo"],
                fg=COLORES["texto"],
                font=FUENTE_MONO,
                width=12,
                anchor="w",
            ).pack(side="left")
            tk.Label(
                fila,
                text=f"  {cred['password']}",
                bg=COLORES["fondo"],
                fg=COLORES["texto_suave"],
                font=FUENTE_MONO,
            ).pack(side="left")
            # Botón para autocompletar
            tk.Button(
                fila,
                text="↑",
                bg=COLORES["fondo_input"],
                fg=COLORES["texto"],
                relief="flat",
                cursor="hand2",
                command=lambda u=cred["usuario"], p=cred["password"]: (
                    self._campo_usuario.var.set(u),
                    self._campo_password.var.set(p),
                ),
            ).pack(side="left", padx=(6, 0))

        # bind Enter
        self._app.bind("<Return>", lambda e: self._login())

    def _login(self):
        usuario  = self._campo_usuario.valor
        password = self._campo_password.valor

        if not usuario or not password:
            self._lbl_error.config(text="Por favor rellena todos los campos.")
            return

        try:
            sesion = self._app.auth.login(usuario, password)
            self._lbl_error.config(text="")
            self._app.unbind("<Return>")
            self._app.mostrar_dashboard(sesion)
        except ErrorSesionciphercoin as e:
            self._lbl_error.config(text=str(e))


# =========================================================
# FRAME PRINCIPAL (DASHBOARD)
# =========================================================

class DashboardFrame(tk.Frame):
    """Panel principal tras el login."""

    def __init__(self, master: "Appciphercoin", sesion: Sesionciphercoin):
        super().__init__(master, bg=COLORES["fondo"])
        self._app    = master
        self._sesion = sesion
        self._construir()

    def _construir(self):
        self.pack(fill="both", expand=True)

        # ── Barra superior ─────────────────────────────────────────
        barra = tk.Frame(self, bg=COLORES["fondo_card"], padx=20, pady=10)
        barra.pack(fill="x")

        tk.Label(
            barra,
            text="₿ ciphercoin",
            bg=COLORES["fondo_card"],
            fg=COLORES["acento"],
            font=("Segoe UI", 16, "bold"),
        ).pack(side="left")

        Boton(barra, "Cerrar sesión", self._logout,
              color=COLORES["fondo_input"]).pack(side="right")

        # ── Contenido central ──────────────────────────────────────
        contenido = tk.Frame(self, bg=COLORES["fondo"])
        contenido.pack(fill="both", expand=True, padx=24, pady=16)

        # Columna izquierda
        izq = tk.Frame(contenido, bg=COLORES["fondo"])
        izq.pack(side="left", fill="y", padx=(0, 16))

        self._construir_info_wallet(izq)
        self._construir_wallets_disponibles(izq)

        # Columna derecha
        der = tk.Frame(contenido, bg=COLORES["fondo"])
        der.pack(side="left", fill="both", expand=True)

        self._construir_acciones(der)
        self._construir_historial_rapido(der)

    # ── info del wallet activo ─────────────────────────────────────

    def _construir_info_wallet(self, parent):
        wallet = self._sesion.wallet
        card = Card(parent)
        card.pack(fill="x", pady=(0, 12))

        tipo_color = color_tipo(wallet.tipo)
        tk.Label(
            card,
            text=f"● {wallet.tipo.value.upper()}",
            bg=COLORES["fondo_card"],
            fg=tipo_color,
            font=FUENTE_PEQUEÑA,
        ).pack(anchor="w")

        tk.Label(
            card,
            text=wallet.nombre,
            bg=COLORES["fondo_card"],
            fg=COLORES["texto"],
            font=FUENTE_GRANDE,
        ).pack(anchor="w", pady=(4, 2))

        tk.Label(
            card,
            text=wallet.direccion,
            bg=COLORES["fondo_card"],
            fg=COLORES["texto_suave"],
            font=("Courier New", 8),
        ).pack(anchor="w")

        # saldo
        self._var_saldo = tk.StringVar(value=f"{wallet.saldo:.4f} ₿")
        tk.Label(
            card,
            textvariable=self._var_saldo,
            bg=COLORES["fondo_card"],
            fg=COLORES["exito"],
            font=("Segoe UI", 26, "bold"),
        ).pack(anchor="w", pady=(14, 0))

        tk.Label(
            card,
            text="saldo disponible",
            bg=COLORES["fondo_card"],
            fg=COLORES["texto_suave"],
            font=FUENTE_PEQUEÑA,
        ).pack(anchor="w")

        # Reputación (solo para USUARIO)
        if wallet.tipo == TipoWallet.USUARIO:
            self._var_rep = tk.StringVar(value=f"⭐ Reputación: {wallet.reputacion}")
            tk.Label(
                card,
                textvariable=self._var_rep,
                bg=COLORES["fondo_card"],
                fg=COLORES["advertencia"],
                font=FUENTE_NORMAL,
            ).pack(anchor="w", pady=(8, 0))

    # ── Lista de wallets disponibles (para transferencias) ─────────

    def _construir_wallets_disponibles(self, parent):
        card = Card(parent)
        card.pack(fill="x")

        tk.Label(
            card,
            text="Wallets del sistema",
            bg=COLORES["fondo_card"],
            fg=COLORES["texto"],
            font=FUENTE_NORMAL,
        ).pack(anchor="w", pady=(0, 8))

        for w in self._app.sistema.listar_wallets():
            if w.direccion == self._sesion.wallet.direccion:
                continue
            fila = tk.Frame(card, bg=COLORES["fondo_card"])
            fila.pack(fill="x", pady=2)
            tk.Label(
                fila,
                text="●",
                bg=COLORES["fondo_card"],
                fg=color_tipo(w.tipo),
                font=FUENTE_PEQUEÑA,
            ).pack(side="left")
            tk.Label(
                fila,
                text=f"  {w.nombre}",
                bg=COLORES["fondo_card"],
                fg=COLORES["texto"],
                font=FUENTE_PEQUEÑA,
            ).pack(side="left")
            tk.Label(
                fila,
                text=f"  {w.saldo:.2f} ₿",
                bg=COLORES["fondo_card"],
                fg=COLORES["texto_suave"],
                font=FUENTE_PEQUEÑA,
            ).pack(side="right")

    # ── botones de acción ──────────────────────────────────────────

    def _construir_acciones(self, parent):
        card = Card(parent)
        card.pack(fill="x", pady=(0, 12))

        tk.Label(
            card,
            text="Acciones",
            bg=COLORES["fondo_card"],
            fg=COLORES["texto"],
            font=FUENTE_GRANDE,
        ).pack(anchor="w", pady=(0, 10))

        botones = tk.Frame(card, bg=COLORES["fondo_card"])
        botones.pack(fill="x")

        Boton(botones, "💸 Transferir", self._abrir_transferencia).pack(
            side="left", padx=(0, 8)
        )
        Boton(botones, "📋 Historial completo", self._abrir_historial,
              color=COLORES["fondo_input"]).pack(side="left", padx=(0, 8))

        # Botón admin solo para wallet estado
        if self._sesion.wallet.tipo == TipoWallet.ESTADO:
            Boton(botones, "🛡 Panel Admin", self._abrir_admin,
                  color=COLORES["estado"]).pack(side="left")

    # ── historial rápido (últimas 5) ───────────────────────────────

    def _construir_historial_rapido(self, parent):
        self._frame_historial = Card(parent)
        self._frame_historial.pack(fill="both", expand=True)

        tk.Label(
            self._frame_historial,
            text="Últimas transacciones",
            bg=COLORES["fondo_card"],
            fg=COLORES["texto"],
            font=FUENTE_GRANDE,
        ).pack(anchor="w", pady=(0, 8))

        self._tabla_rapida = ttk.Treeview(
            self._frame_historial,
            columns=("tipo", "contraparte", "importe", "comision", "fecha"),
            show="headings",
            height=7,
        )
        estilo = ttk.Style()
        estilo.theme_use("clam")
        estilo.configure(
            "Treeview",
            background=COLORES["fondo_input"],
            foreground=COLORES["texto"],
            rowheight=26,
            fieldbackground=COLORES["fondo_input"],
        )
        estilo.configure(
            "Treeview.Heading",
            background=COLORES["fondo_card"],
            foreground=COLORES["texto_suave"],
        )

        for col, ancho, encab in [
            ("tipo",        60,  "Tipo"),
            ("contraparte", 160, "Contraparte"),
            ("importe",     90,  "Importe ₿"),
            ("comision",    80,  "Comisión"),
            ("fecha",       150, "Fecha"),
        ]:
            self._tabla_rapida.heading(col, text=encab)
            self._tabla_rapida.column(col, width=ancho, anchor="center")

        self._tabla_rapida.pack(fill="both", expand=True)
        self._actualizar_historial_rapido()

    def _actualizar_historial_rapido(self):
        for row in self._tabla_rapida.get_children():
            self._tabla_rapida.delete(row)

        txs = self._app.sistema.historial_wallet(self._sesion.wallet.direccion)
        for tx in txs[-7:]:
            es_salida = tx["origen"] == self._sesion.wallet.direccion
            tipo = "⬆ Envío" if es_salida else "⬇ Recibo"
            otra_dir = tx["destino"] if es_salida else tx["origen"]
            try:
                otra_wallet = self._app.sistema.obtener_wallet(otra_dir)
                contraparte = otra_wallet.nombre
            except ErrorWalletNoEncontrada:
                contraparte = otra_dir[:12] + "…"
            self._tabla_rapida.insert(
                "", "end",
                values=(
                    tipo,
                    contraparte,
                    f"{tx['importe']:.4f}",
                    f"{tx['comision']:.4f}",
                    tx["timestamp"][:19].replace("T", " "),
                ),
            )

    # ── actualización del saldo en pantalla ────────────────────────

    def refrescar(self):
        w = self._sesion.wallet
        self._var_saldo.set(f"{w.saldo:.4f} ₿")
        if w.tipo == TipoWallet.USUARIO:
            self._var_rep.set(f"⭐ Reputación: {w.reputacion}")
        self._actualizar_historial_rapido()

    # ── navegación ─────────────────────────────────────────────────

    def _abrir_transferencia(self):
        VentanaTransferencia(self._app, self._sesion, self)

    def _abrir_historial(self):
        VentanaHistorial(self._app, self._sesion)

    def _abrir_admin(self):
        VentanaAdmin(self._app)

    def _logout(self):
        self._app.auth.logout()
        self.destroy()
        self._app.mostrar_login()


# =========================================================
# VENTANA DE TRANSFERENCIA
# =========================================================

class VentanaTransferencia(tk.Toplevel):
    """Diálogo para realizar una transferencia."""

    def __init__(
        self,
        master: "Appciphercoin",
        sesion: Sesionciphercoin,
        dashboard: DashboardFrame,
    ):
        super().__init__(master)
        self.title("Nueva transferencia — ciphercoin")
        self.configure(bg=COLORES["fondo"])
        self.resizable(False, False)
        self.grab_set()

        self._app       = master
        self._sesion    = sesion
        self._dashboard = dashboard

        # wallets destino disponibles
        self._wallets_destino = [
            w for w in master.sistema.listar_wallets()
            if w.direccion != sesion.wallet.direccion
        ]

        self._construir()
        self._centrar()

    def _construir(self):
        card = Card(self)
        card.pack(fill="both", expand=True, padx=24, pady=20)

        tk.Label(
            card,
            text="💸 Nueva transferencia",
            bg=COLORES["fondo_card"],
            fg=COLORES["texto"],
            font=FUENTE_GRANDE,
        ).pack(anchor="w", pady=(0, 14))

        # destino
        tk.Label(
            card,
            text="Destinatario",
            bg=COLORES["fondo_card"],
            fg=COLORES["texto_suave"],
            font=FUENTE_PEQUEÑA,
        ).pack(anchor="w")

        self._var_destino = tk.StringVar()
        opciones = [f"{w.nombre}  ({w.tipo.value})" for w in self._wallets_destino]
        self._combo_destino = ttk.Combobox(
            card,
            textvariable=self._var_destino,
            values=opciones,
            state="readonly",
            font=FUENTE_NORMAL,
            width=38,
        )
        if opciones:
            self._combo_destino.current(0)
        self._combo_destino.pack(fill="x", pady=(2, 10))
        self._combo_destino.bind("<<ComboboxSelected>>", self._actualizar_preview)

        # importe
        self._campo_importe = EntradaLabel(card, "Importe (₿)", width=38)
        self._campo_importe.pack(fill="x", pady=5)
        self._campo_importe.entry.bind("<KeyRelease>", self._actualizar_preview)

        # preview de comisión
        self._var_preview = tk.StringVar(value="")
        tk.Label(
            card,
            textvariable=self._var_preview,
            bg=COLORES["fondo_card"],
            fg=COLORES["advertencia"],
            font=FUENTE_PEQUEÑA,
            justify="left",
        ).pack(anchor="w", pady=(4, 8))

        self._lbl_error = tk.Label(
            card,
            text="",
            bg=COLORES["fondo_card"],
            fg=COLORES["error"],
            font=FUENTE_PEQUEÑA,
        )
        self._lbl_error.pack(anchor="w")

        btns = tk.Frame(card, bg=COLORES["fondo_card"])
        btns.pack(fill="x", pady=(10, 0))
        Boton(btns, "Confirmar transferencia", self._confirmar).pack(side="left")
        Boton(btns, "Cancelar", self.destroy,
              color=COLORES["fondo_input"]).pack(side="left", padx=8)

    def _destino_seleccionado(self):
        idx = self._combo_destino.current()
        if idx < 0:
            return None
        return self._wallets_destino[idx]

    def _actualizar_preview(self, event=None):
        try:
            importe = float(self._campo_importe.valor)
        except ValueError:
            self._var_preview.set("")
            return

        origen  = self._sesion.wallet
        destino = self._destino_seleccionado()
        if destino is None:
            return

        comision = self._app.sistema._comision.calcular(importe, origen.reputacion)
        total    = importe + comision
        rep_bonus = ""
        if origen.tipo == TipoWallet.USUARIO and destino.tipo == TipoWallet.PYME:
            rep_bonus = " (+1 reputación al completar)"

        self._var_preview.set(
            f"Comisión: {comision:.4f} ₿  |  Total a descontar: {total:.4f} ₿"
            f"{rep_bonus}"
        )

    def _confirmar(self):
        destino = self._destino_seleccionado()
        if destino is None:
            self._lbl_error.config(text="Selecciona un destinatario.")
            return

        try:
            importe = float(self._campo_importe.valor)
        except ValueError:
            self._lbl_error.config(text="El importe debe ser un número válido.")
            return

        if importe <= 0:
            self._lbl_error.config(text="El importe debe ser mayor que cero.")
            return

        try:
            tx = self._app.sistema.transferir(
                self._sesion.wallet.direccion,
                destino.direccion,
                importe,
            )
            self._dashboard.refrescar()
            messagebox.showinfo(
                "Transferencia completada",
                f"✅ Transferencia realizada correctamente.\n\n"
                f"Importe enviado:  {tx.importe:.4f} ₿\n"
                f"Comisión pagada:  {tx.comision:.4f} ₿\n"
                f"TX ID: {tx.tx_id[:20]}…",
                parent=self,
            )
            self.destroy()
        except ErrorSaldoInsuficiente as e:
            self._lbl_error.config(text=str(e))
        except Exception as e:
            self._lbl_error.config(text=f"Error inesperado: {e}")

    def _centrar(self):
        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        x = self.master.winfo_x() + (self.master.winfo_width()  - w) // 2
        y = self.master.winfo_y() + (self.master.winfo_height() - h) // 2
        self.geometry(f"+{x}+{y}")


# =========================================================
# VENTANA HISTORIAL COMPLETO
# =========================================================

class VentanaHistorial(tk.Toplevel):
    """Historial completo de transacciones de la wallet activa."""

    def __init__(self, master: "Appciphercoin", sesion: Sesionciphercoin):
        super().__init__(master)
        self.title("Historial de transacciones — ciphercoin")
        self.configure(bg=COLORES["fondo"])
        self.grab_set()

        self._app    = master
        self._sesion = sesion
        self._construir()
        self.geometry("820x480")

    def _construir(self):
        card = Card(self)
        card.pack(fill="both", expand=True, padx=16, pady=12)

        tk.Label(
            card,
            text=f"Historial — {self._sesion.wallet.nombre}",
            bg=COLORES["fondo_card"],
            fg=COLORES["texto"],
            font=FUENTE_GRANDE,
        ).pack(anchor="w", pady=(0, 10))

        cols = ("tx_id", "tipo", "contraparte", "importe", "comision", "fecha")
        tabla = ttk.Treeview(card, columns=cols, show="headings", height=16)

        for col, ancho, enc in [
            ("tx_id",       130, "TX ID"),
            ("tipo",         70, "Tipo"),
            ("contraparte", 180, "Contraparte"),
            ("importe",      90, "Importe ₿"),
            ("comision",     80, "Comisión"),
            ("fecha",       160, "Fecha UTC"),
        ]:
            tabla.heading(col, text=enc)
            tabla.column(col, width=ancho, anchor="center")

        scrollbar = ttk.Scrollbar(card, orient="vertical", command=tabla.yview)
        tabla.configure(yscrollcommand=scrollbar.set)
        tabla.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        txs = self._app.sistema.historial_wallet(self._sesion.wallet.direccion)
        for tx in reversed(txs):
            es_salida   = tx["origen"] == self._sesion.wallet.direccion
            tipo        = "⬆ Envío" if es_salida else "⬇ Recibo"
            otra_dir    = tx["destino"] if es_salida else tx["origen"]
            try:
                otra = self._app.sistema.obtener_wallet(otra_dir)
                contraparte = otra.nombre
            except ErrorWalletNoEncontrada:
                contraparte = otra_dir[:14] + "…"

            tabla.insert("", "end", values=(
                tx["tx_id"][:14] + "…",
                tipo,
                contraparte,
                f"{tx['importe']:.4f}",
                f"{tx['comision']:.4f}",
                tx["timestamp"][:19].replace("T", " "),
            ))


# =========================================================
# VENTANA ADMIN (solo Estado)
# =========================================================

class VentanaAdmin(tk.Toplevel):
    """Panel de administración del sistema (wallet de estado)."""

    def __init__(self, master: "Appciphercoin"):
        super().__init__(master)
        self.title("Panel de administración — ciphercoin")
        self.configure(bg=COLORES["fondo"])
        self.grab_set()
        self._app = master
        self._construir()
        self.geometry("700x520")

    def _construir(self):
        card = Card(self)
        card.pack(fill="both", expand=True, padx=16, pady=12)

        tk.Label(
            card,
            text="🛡 Panel de Administración",
            bg=COLORES["fondo_card"],
            fg=COLORES["estado"],
            font=FUENTE_GRANDE,
        ).pack(anchor="w", pady=(0, 12))

        # Estado de integridad
        integra = self._app.sistema.verificar_integridad()
        color_int = COLORES["exito"] if integra else COLORES["error"]
        tk.Label(
            card,
            text=f"Integridad blockchain: {'✅ CORRECTA' if integra else '❌ COMPROMETIDA'}",
            bg=COLORES["fondo_card"],
            fg=color_int,
            font=FUENTE_NORMAL,
        ).pack(anchor="w", pady=(0, 12))

        # Resumen de wallets
        tk.Label(
            card,
            text="Estado de wallets",
            bg=COLORES["fondo_card"],
            fg=COLORES["texto"],
            font=FUENTE_NORMAL,
        ).pack(anchor="w", pady=(0, 6))

        cols = ("nombre", "tipo", "saldo", "reputacion")
        tabla = ttk.Treeview(card, columns=cols, show="headings", height=5)
        for col, ancho, enc in [
            ("nombre",     200, "Wallet"),
            ("tipo",       100, "Tipo"),
            ("saldo",      120, "Saldo ₿"),
            ("reputacion",  90, "Reputación"),
        ]:
            tabla.heading(col, text=enc)
            tabla.column(col, width=ancho, anchor="center")

        for w in self._app.sistema.listar_wallets():
            tabla.insert("", "end", values=(
                w.nombre,
                w.tipo.value,
                f"{w.saldo:.4f}",
                w.reputacion,
            ))
        tabla.pack(fill="x", pady=(0, 14))

        # Historial completo
        tk.Label(
            card,
            text="Blockchain completa",
            bg=COLORES["fondo_card"],
            fg=COLORES["texto"],
            font=FUENTE_NORMAL,
        ).pack(anchor="w", pady=(0, 6))

        cols2 = ("indice", "origen", "destino", "importe", "comision", "fecha")
        tabla2 = ttk.Treeview(card, columns=cols2, show="headings", height=8)
        for col, ancho, enc in [
            ("indice",  50, "#"),
            ("origen",  140, "Origen"),
            ("destino", 140, "Destino"),
            ("importe",  80, "Importe"),
            ("comision", 80, "Comisión"),
            ("fecha",   140, "Fecha"),
        ]:
            tabla2.heading(col, text=enc)
            tabla2.column(col, width=ancho, anchor="center")

        sc2 = ttk.Scrollbar(card, orient="vertical", command=tabla2.yview)
        tabla2.configure(yscrollcommand=sc2.set)
        tabla2.pack(side="left", fill="both", expand=True)
        sc2.pack(side="right", fill="y")

        for bloque in self._app.sistema.historial_completo():
            tx = bloque["tx"]
            try:
                on = self._app.sistema.obtener_wallet(tx["origen"]).nombre
            except Exception:
                on = tx["origen"][:10]
            try:
                dn = self._app.sistema.obtener_wallet(tx["destino"]).nombre
            except Exception:
                dn = tx["destino"][:10]
            tabla2.insert("", "end", values=(
                bloque["indice"],
                on,
                dn,
                f"{tx['importe']:.4f}",
                f"{tx['comision']:.4f}",
                tx["timestamp"][:19].replace("T", " "),
            ))


# =========================================================
# APLICACIÓN PRINCIPAL
# =========================================================

class Appciphercoin(tk.Tk):
    """
    Ventana raíz de la aplicación ciphercoin.

    Instancia el SistemaCipherCoin y el ServicioAutenticacion
    y gestiona la navegación entre pantallas.
    """

    def __init__(self):
        super().__init__()
        self.title("ciphercoin — Sistema de Criptomoneda")
        self.configure(bg=COLORES["fondo"])
        self.geometry("900x680")
        self.minsize(760, 560)

        # modelo de dominio
        self.sistema = SistemaCipherCoin()
        self.auth    = ServicioAutenticacion(self.sistema)

        self._frame_actual: Optional[tk.Frame] = None
        self.mostrar_login()

    # ── navegación ─────────────────────────────────────────────────

    def mostrar_login(self):
        if self._frame_actual:
            self._frame_actual.destroy()
        self._frame_actual = LoginFrame(self)

    def mostrar_dashboard(self, sesion: Sesionciphercoin):
        if self._frame_actual:
            self._frame_actual.destroy()
        self._frame_actual = DashboardFrame(self, sesion)


# =========================================================
# MAIN
# =========================================================

def main():
    app = Appciphercoin()
    app.mainloop()


if __name__ == "__main__":
    main()
