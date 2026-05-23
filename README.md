# ₿ CriptoCoin

Sistema de criptomoneda con interfaz gráfica, gestor de credenciales integrado, sistema de reputación y comisiones por intervalos.

---

## Requisitos

- Python 3.11 o superior
- `tkinter` (incluido en Python estándar; en Debian/Ubuntu instalar con `sudo apt install python3-tk`)
- `icontract >= 2.6`
- `bcrypt >= 4.0`

---

## Instalación

### Opción A — ejecución directa (recomendada para desarrollo)

```bash
# 1. Instalar dependencias
pip install icontract bcrypt

# 2. Lanzar la aplicación
python main.py
```

### Opción B — instalar como paquete

```bash
pip install -e .
criptocoin
```

---

## Credenciales de demo

| Usuario    | Contraseña          | Rol     | Wallet             |
|------------|---------------------|---------|--------------------|
| `alice`    | `Alice#Coin2024!`   | Usuario | Alice (Usuario)    |
| `bob`      | `Bob#Coin2024!`     | Usuario | Bob (Usuario)      |
| `techpyme` | `TechPyme#Coin2024!`| PYME    | TechPyme S.L.      |
| `estado`   | `Estado#Coin2024!`  | Admin   | Estado CriptoCoin  |

> La pantalla de login muestra estas credenciales y permite autocompletarlas con el botón `↑`.

---

## Arquitectura

```
criptocoin/
├── main.py                          # Punto de entrada
├── pyproject.toml
├── README.md
├── src/
│   ├── gestor_credenciales/         # Gestor original (sin modificar)
│   │   ├── gestor_credenciales.py
│   │   ├── proxy_seguro.py
│   │   └── utils.py
│   └── criptocoin/
│       ├── modelo.py                # Dominio: Wallet, Transaccion, Blockchain, Comisiones
│       ├── autenticacion.py         # Integración GestorCredenciales ↔ Wallets
│       └── gui.py                   # Interfaz gráfica tkinter
└── tests/
    └── criptocoin/
        └── test_modelo.py           # Suite de tests
```

---

## Sistema de comisiones

| Intervalo de importe | Tasa base | Descuento por reputación |
|----------------------|-----------|--------------------------|
| [0, 5) ₿            | 1 %       | −0,1 % por punto         |
| [5, 20) ₿           | 5 %       | −0,1 % por punto         |
| [20, 50) ₿          | 10 %      | −0,1 % por punto         |
| [50, ∞) ₿           | 15 %      | −0,1 % por punto         |

La comisión mínima es siempre **0 %** (nunca negativa).

---

## Sistema de reputación

- Todos los usuarios comienzan con **0 puntos de reputación**.
- Cada vez que un usuario (tipo `USUARIO`) realiza una transferencia a una **PYME**, su reputación sube **+1 punto**.
- Los puntos de reputación reducen la tasa de comisión aplicable en todas sus futuras transferencias.

---

## Ejecutar los tests

```bash
# Desde la raíz del proyecto
python -m pytest

# O con unittest directamente
python -m unittest discover -s tests -v
```

---

## Patrones de diseño aplicados

| Patrón        | Dónde                                   |
|---------------|-----------------------------------------|
| Strategy      | `EstrategiaComision` / `ComisionPorIntervalos` |
| Facade        | `SistemaCriptoCoin`                     |
| Proxy         | `ProxySeguroGestorCredenciales` (original) |
| Factory Method| `Wallet.generar_direccion`              |
| Observer (log)| `ServicioAuditoriaCripto`               |

---

## Seguridad

- Las contraseñas se almacenan con **bcrypt** (vía `GestorCredenciales`).
- El `ProxySeguro` gestiona roles y autorización por operación.
- Cada transacción genera un **hash SHA-256** de integridad.
- La blockchain enlaza bloques mediante hash, permitiendo detectar manipulaciones.
- Todos los contratos de precondición/postcondición se validan con **icontract**.
- Se genera un log de auditoría en `criptocoin_audit.log`.
