import matplotlib.pyplot as plt

from src.ciphercoin.modelo import ComisionProgresiva


REPUTACION = 0

comision = ComisionProgresiva()

TARIFA_BASE = comision.TARIFA_BASE
COMISION_MAXIMA = comision.COMISION_MAXIMA
IMPORTE_LIMITE = comision.IMPORTE_LIMITE

# derivados
MAX_PORCENTAJE = COMISION_MAXIMA * 100
YLIM_TOP = MAX_PORCENTAJE + 1
N_TICKS = 6
YTICKS = [MAX_PORCENTAJE * i / (N_TICKS - 1) for i in range(N_TICKS)]


def porcentaje_comision(importe: float) -> float:
    return 100 * comision.calcular(importe, REPUTACION) / importe


def crear_importes(inicio: float, fin: float, pasos: int) -> list[float]:
    salto = (fin - inicio) / pasos
    return [inicio + i * salto for i in range(pasos + 1)]


# =========================================================
# 1. Comisión efectiva (%) hasta el importe límite y un poco más
# =========================================================

x_max = IMPORTE_LIMITE * 1.4
importes = crear_importes(0.01, x_max, 1000)
porcentajes = [porcentaje_comision(importe) for importe in importes]

plt.figure(figsize=(10, 6))
plt.plot(importes, porcentajes, linewidth=2)

plt.axhline(MAX_PORCENTAJE, linestyle="--", linewidth=1, label="Comisión máxima")
plt.axvline(IMPORTE_LIMITE, linestyle="--", linewidth=1, label="Importe límite")

plt.xlabel("Importe de la transacción")
plt.ylabel("Comisión efectiva (%)")
plt.title("Comisión efectiva hasta el importe límite")
plt.xlim(0, x_max)
plt.ylim(0, YLIM_TOP)
plt.yticks(YTICKS)
plt.grid(True)
plt.legend()
plt.show()


# =========================================================
# 2. Zoom en transacciones pequeñas
# =========================================================

x_max_pequenas = IMPORTE_LIMITE / 4
importes_pequenos = crear_importes(0.01, x_max_pequenas, 1000)
porcentajes_pequenos = [porcentaje_comision(importe) for importe in importes_pequenos]

plt.figure(figsize=(10, 6))
plt.plot(importes_pequenos, porcentajes_pequenos, linewidth=2)

plt.axhline(MAX_PORCENTAJE, linestyle="--", linewidth=1, label="Comisión máxima")

plt.xlabel("Importe de la transacción")
plt.ylabel("Comisión efectiva (%)")
plt.title("Comisión efectiva para transacciones pequeñas")
plt.xlim(0, x_max_pequenas)
plt.ylim(0, YLIM_TOP)
plt.xticks([x_max_pequenas * i / 10 for i in range(11)])
plt.yticks(YTICKS)
plt.grid(True)
plt.legend()
plt.show()


# =========================================================
# 3. Valor absoluto de la comisión
# =========================================================

x_max_valor = IMPORTE_LIMITE * 1.5
importes_valor = crear_importes(0.01, x_max_valor, 1000)
comisiones = [comision.calcular(importe, REPUTACION) for importe in importes_valor]

plt.figure(figsize=(10, 6))
plt.plot(importes_valor, comisiones, linewidth=2)

plt.axvline(IMPORTE_LIMITE, linestyle="--", linewidth=1, label="Importe límite")

plt.xlabel("Importe de la transacción")
plt.ylabel("Comisión")
plt.title("Valor absoluto de la comisión")
plt.xlim(0, x_max_valor)
plt.grid(True)
plt.legend()
plt.show()

# =========================================================
# 4. Comisión efectiva (%) para distintas reputaciones
# =========================================================

REPUTACIONES = [0, 25, 50, 75, 100]

x_max = IMPORTE_LIMITE * 1.4
importes = crear_importes(0.01, x_max, 1000)

plt.figure(figsize=(10, 6))
for rep in REPUTACIONES:
    porcentajes = [
        100 * comision.calcular(importe, rep) / importe
        for importe in importes
    ]
    plt.plot(importes, porcentajes, linewidth=2, label=f"reputación = {rep}")

plt.axhline(MAX_PORCENTAJE, linestyle="--", linewidth=1, color="gray")
plt.axvline(IMPORTE_LIMITE, linestyle="--", linewidth=1, color="gray")

plt.xlabel("Importe de la transacción")
plt.ylabel("Comisión efectiva (%)")
plt.title("Comisión efectiva según reputación")
plt.xlim(0, x_max)
plt.ylim(0, YLIM_TOP)
plt.yticks(YTICKS)
plt.grid(True)
plt.legend()
plt.show()